import re
import hmac
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.limiter import limiter, email_rate_limiter, daily_email_tracker
from app.models.user import User, UserVerification
from app.services.auth_service import (
    auth_service,
    get_current_user,
    hash_password,
    verify_password,
    create_access_token,
)
from app.services.notification_service import notification_service
from app.utils.normalization import normalize_phone
from app.utils.password_strength import (
    PASSWORD_MIN_LENGTH,
    PASSWORD_MAX_LENGTH,
    check_password_strength,
    rate_strength,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[a-zA-Z0-9\.\-]+\.[a-zA-Z]{2,}$")
_last_resend_timestamps: Dict[str, float] = {}


# ---------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------

class TokenVerifyRequest(BaseModel):
    access_token: str = Field(..., description="Access token to verify")


class AuthConfigResponse(BaseModel):
    supabase_url: str
    supabase_anon_key: str
    configured: bool
    auth_required: bool


class CheckEmailRequest(BaseModel):
    email: str = Field(..., description="Email address to check")


class RegisterInitiateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80, description="Full name")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    password: str = Field(..., description="Password")
    role: Optional[str] = Field("Investigator", description="Role (e.g., Investigator, Analyst)")
    organization: Optional[str] = Field("", description="Agency or organization name")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if v is None:
            raise ValueError("Full name is required.")
        v_clean = v.strip()
        if len(v_clean) < 2 or len(v_clean) > 80:
            raise ValueError("Full name must be between 2 and 80 characters.")
        disallowed = {'<', '>', '"', '`'}
        if any(ch in disallowed for ch in v_clean):
            raise ValueError("Full name cannot contain HTML or script characters (<, >, \", `).")
        if any(ord(ch) < 32 or ord(ch) == 127 for ch in v_clean):
            raise ValueError("Full name cannot contain control characters.")
        return v_clean


class RegisterVerifyRequest(BaseModel):
    email: str = Field(..., description="Email address")
    email_otp: str = Field(..., description="6-digit email verification code")


class ResendOTPRequest(BaseModel):
    email: str = Field(..., description="Email address")


class LoginRequest(BaseModel):
    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Password")


class CheckPasswordRequest(BaseModel):
    password: str = Field(..., description="Password to evaluate")


class PasswordStrengthResponse(BaseModel):
    score: int
    max_score: int
    grade: str
    rating: str
    reasons: List[str]
    acceptable: bool


# ---------------------------------------------------------
# Authentication & Verification Endpoints
# ---------------------------------------------------------

@router.post("/check-password", response_model=PasswordStrengthResponse)
def check_password(payload: CheckPasswordRequest):
    """
    Evaluates password strength and returns score, grade, rating, and improvement tips.
    """
    score, max_score, grade, rating, reasons = check_password_strength(payload.password)
    return {
        "score": score,
        "max_score": max_score,
        "grade": grade,
        "rating": rating,
        "reasons": reasons,
        "acceptable": rating in ("STRONG", "MEDIUM"),
    }


@router.post("/check-email")
@limiter.limit("10/minute")
def check_email(request: Request, payload: CheckEmailRequest, db: Session = Depends(get_db)):
    """
    Checks if a user with this email already exists in the users table.
    """
    normalized_email = payload.email.strip().lower()
    if not normalized_email:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Email address cannot be empty.", "code": "INVALID_EMAIL"}
        )

    user = db.query(User).filter(User.email == normalized_email).first()
    exists = user is not None
    return {
        "exists": exists,
        "message": "An account with this email already exists." if exists else "Email available."
    }


@router.post("/register/initiate")
@limiter.limit("3/hour")
def register_initiate(request: Request, payload: RegisterInitiateRequest, db: Session = Depends(get_db)):
    """
    Validates registration input, checks email uniqueness,
    generates 6-digit email OTP, stores pending verification,
    and dispatches verification code to email.
    """
    normalized_email = payload.email.strip().lower()
    if not EMAIL_REGEX.match(normalized_email):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid email address format.", "code": "INVALID_EMAIL"}
        )

    cleaned_phone = re.sub(r"[\s\-\(\)\.]", "", payload.phone.strip())
    digits_only = re.sub(r"\D", "", cleaned_phone)
    if len(digits_only) < 10:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid phone number format. Must contain at least 10 digits.", "code": "INVALID_PHONE"}
        )

    if len(payload.password) < PASSWORD_MIN_LENGTH:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": f"Password must be at least {PASSWORD_MIN_LENGTH} characters long.", "code": "PASSWORD_TOO_SHORT"}
        )

    if len(payload.password) > PASSWORD_MAX_LENGTH:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": f"Password must not exceed {PASSWORD_MAX_LENGTH} characters.", "code": "PASSWORD_TOO_LONG"}
        )

    if not payload.name.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Name is required.", "code": "INVALID_NAME"}
        )

    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "An account with this email already exists in the database. Please sign in instead.",
                "code": "ACCOUNT_EXISTS"
            }
        )

    pw_score, pw_max, pw_grade, pw_rating, pw_reasons = check_password_strength(payload.password)
    if pw_rating in ("TOO WEAK", "WEAK"):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": "Password is too weak. " + " ".join(pw_reasons),
                "code": "PASSWORD_TOO_WEAK",
                "password_strength": {
                    "score": pw_score,
                    "max_score": pw_max,
                    "grade": pw_grade,
                    "rating": pw_rating,
                    "reasons": pw_reasons,
                }
            }
        )

    # Abuse prevention caps: global daily cap and per-target-email sliding window
    # Security limitation: Limits are in-memory (single instance) and a client who calls
    # the Render URL directly can spoof X-Forwarded-For, which is why the per-email and global caps exist.
    if daily_email_tracker.is_exceeded(settings.EMAIL_DAILY_CAP):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Daily email dispatch limit reached.", "code": "EMAIL_CAP"}
        )

    allowed, retry_after = email_rate_limiter.check_and_record(normalized_email)
    if not allowed:
        resp = JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": f"Too many verification requests for {normalized_email}. Please wait before requesting another.",
                "code": "RATE_LIMITED"
            }
        )
        resp.headers["Retry-After"] = str(retry_after)
        return resp

    db.query(UserVerification).filter(UserVerification.email == normalized_email).delete()

    normalized_phone = normalize_phone(payload.phone)
    email_otp = f"{secrets.randbelow(900000) + 100000:06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    verification = UserVerification(
        email=normalized_email,
        phone=normalized_phone,
        name=payload.name.strip(),
        password_hash=hash_password(payload.password),
        role=payload.role or "Investigator",
        organization=payload.organization.strip() if payload.organization else "",
        email_otp=email_otp,
        expires_at=expires_at,
        attempts=0
    )
    db.add(verification)
    db.commit()

    import time
    _last_resend_timestamps[normalized_email] = time.time()

    email_sent = notification_service.send_email_otp(
        to_email=normalized_email,
        otp_code=email_otp,
        user_name=payload.name.strip()
    )
    daily_email_tracker.record_send()

    return {
        "status": "initiated",
        "message": f"Verification code sent to {normalized_email}.",
        "email": normalized_email,
        "delivery": {
            "email": email_sent
        }
    }


@router.post("/register/verify")
def register_verify(payload: RegisterVerifyRequest, db: Session = Depends(get_db)):
    """
    Verifies the email OTP. On success, creates user account and returns access token.
    """
    normalized_email = payload.email.strip().lower()

    verification = db.query(UserVerification).filter(UserVerification.email == normalized_email).first()

    if not verification:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": "No pending registration found for this email. Please initiate registration first.",
                "code": "NO_PENDING_REGISTRATION"
            }
        )

    now = datetime.now(timezone.utc)
    exp = verification.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)

    if now > exp:
        db.query(UserVerification).filter(UserVerification.email == normalized_email).delete()
        db.commit()
        return JSONResponse(
            status_code=status.HTTP_410_GONE,
            content={
                "detail": "Verification code has expired. Please request a new code.",
                "code": "OTP_EXPIRED"
            }
        )

    if verification.attempts >= 5:
        db.query(UserVerification).filter(UserVerification.email == normalized_email).delete()
        db.commit()
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Too many failed attempts. Registration reset. Please register again.",
                "code": "TOO_MANY_ATTEMPTS"
            }
        )

    if not hmac.compare_digest(payload.email_otp.strip(), verification.email_otp):
        verification.attempts += 1
        db.commit()
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": f"Invalid verification code. {5 - verification.attempts} attempts remaining.",
                "code": "INVALID_OTP",
                "attempts_remaining": 5 - verification.attempts
            }
        )

    new_user = User(
        email=verification.email,
        phone=verification.phone,
        name=verification.name,
        password_hash=verification.password_hash,
        role=verification.role,
        organization=verification.organization,
        is_verified_email=True,
        is_verified_phone=True,
        is_active=True
    )
    db.add(new_user)
    db.query(UserVerification).filter(UserVerification.email == normalized_email).delete()
    db.commit()
    db.refresh(new_user)

    user_dict = new_user.to_dict()
    token = create_access_token(user_dict)

    return {
        "status": "verified",
        "message": "Account created successfully.",
        "user": user_dict,
        "access_token": token,
        "token_type": "bearer"
    }


@router.post("/register/resend")
@limiter.limit("3/hour")
def register_resend(request: Request, payload: ResendOTPRequest, db: Session = Depends(get_db)):
    """
    Resends verification code if pending registration exists and 30s cooldown passed.
    """
    normalized_email = payload.email.strip().lower()

    # Abuse prevention caps: global daily cap and per-target-email sliding window
    # Security limitation: Limits are in-memory (single instance) and a client who calls
    # the Render URL directly can spoof X-Forwarded-For, which is why the per-email and global caps exist.
    if daily_email_tracker.is_exceeded(settings.EMAIL_DAILY_CAP):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Daily email dispatch limit reached.", "code": "EMAIL_CAP"}
        )

    import time
    last_time = _last_resend_timestamps.get(normalized_email, 0)
    elapsed = time.time() - last_time
    if elapsed < 30:
        remaining = int(30 - elapsed)
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": f"Please wait {remaining} seconds before requesting another code.",
                "code": "COOLDOWN_ACTIVE",
                "retry_after_seconds": remaining
            }
        )

    allowed, retry_after = email_rate_limiter.check_and_record(normalized_email)
    if not allowed:
        resp = JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": f"Too many verification requests for {normalized_email}. Please wait before requesting another.",
                "code": "RATE_LIMITED"
            }
        )
        resp.headers["Retry-After"] = str(retry_after)
        return resp

    verification = db.query(UserVerification).filter(UserVerification.email == normalized_email).first()

    if not verification:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": "No pending registration found for this email.",
                "code": "NO_PENDING_REGISTRATION"
            }
        )

    new_email_otp = f"{secrets.randbelow(900000) + 100000:06d}"
    verification.email_otp = new_email_otp
    verification.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    # Note: Do NOT reset verification.attempts on resend to prevent brute-force abuse
    db.commit()

    _last_resend_timestamps[normalized_email] = time.time()

    email_result = notification_service.send_email_otp(
        to_email=verification.email,
        otp_code=new_email_otp,
        user_name=verification.name
    )
    daily_email_tracker.record_send()

    return {
        "status": "resent",
        "message": "Fresh verification code generated and sent.",
        "email": verification.email,
        "delivery": {
            "email": email_result
        }
    }


@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates an investigator via email and password.
    Returns identical 401 response for non-existent email and wrong password.
    """
    normalized_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()

    auth_failed_response = JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "detail": "Invalid email or password.",
            "code": "INVALID_CREDENTIALS"
        }
    )

    if not user:
        return auth_failed_response

    if not verify_password(payload.password, user.password_hash):
        return auth_failed_response

    if not getattr(user, "is_active", True):
        return auth_failed_response

    token = create_access_token(user.to_dict())

    return {
        "status": "authenticated",
        "user": user.to_dict(),
        "access_token": token,
        "token_type": "bearer"
    }


# ---------------------------------------------------------
# Existing Profile & Token Verification Endpoints
# ---------------------------------------------------------

@router.get("/config", response_model=AuthConfigResponse)
def get_auth_config():
    """
    Returns public configuration parameters.
    """
    return {
        "supabase_url": settings.SUPABASE_URL,
        "supabase_anon_key": settings.SUPABASE_ANON_KEY,
        "configured": auth_service.is_configured(),
        "auth_required": True,
    }


@router.get("/me")
def get_authenticated_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns the current authenticated investigator's profile.
    """
    return {
        "status": "authenticated",
        "user": current_user
    }


@router.post("/verify")
def verify_access_token(payload: TokenVerifyRequest, db: Session = Depends(get_db)):
    """
    Verifies an access token and returns decoded investigator claims.
    Returns {"valid": False} with 401 status for any bad, expired, or forged token.
    """
    try:
        user_info = auth_service.verify_token(payload.access_token, db=db)
        return {
            "valid": True,
            "user": user_info
        }
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"valid": False, "detail": "Invalid, expired, or untrusted authentication token"}
        )
