import logging
from typing import Dict, Any, Optional
import jwt
import httpx
from fastapi import Request, HTTPException, status
from app.config import settings

logger = logging.getLogger("cyberscope.auth")

DEMO_USER = {
    "id": "demo-investigator-001",
    "email": "investigator@cyberscope.io",
    "name": "Investigator Demo",
    "role": "Investigator",
    "phone": "+919876543210",
    "organization": "TetraByte Cyber Defense",
    "is_demo": True
}


class SupabaseAuthService:
    """
    Supabase Authentication & Token Verification Service.
    Handles JWT decoding, verification with Supabase secret or Auth REST API,
    and provides fallback handling for local evaluation and offline demo mode.
    """

    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL.rstrip("/") if settings.SUPABASE_URL else ""
        self.anon_key = settings.SUPABASE_ANON_KEY
        self.jwt_secret = settings.SUPABASE_JWT_SECRET
        self.require_auth = settings.REQUIRE_AUTH

    def is_configured(self) -> bool:
        """Returns True if Supabase project URL and anon key are configured."""
        return bool(self.supabase_url and self.anon_key)

    def extract_token_from_header(self, request: Request) -> Optional[str]:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        return None

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verifies a Supabase JWT access token.
        1. Checks for demo tokens (used in local testing/offline demo)
        2. Verifies using SUPABASE_JWT_SECRET if provided
        3. Calls Supabase /auth/v1/user endpoint if SUPABASE_URL & ANON_KEY provided
        4. Falls back to unverified payload decoding for local flexibility
        """
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Empty authentication token"
            )

        if token in ("demo-token", "demo-session-token") or token.startswith("demo-"):
            return DEMO_USER

        # Method A: Verify with JWT Secret if configured
        if self.jwt_secret:
            try:
                payload = jwt.decode(
                    token,
                    self.jwt_secret,
                    algorithms=["HS256"],
                    options={"verify_aud": False}
                )
                return self._format_user_from_jwt(payload)
            except jwt.ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token has expired"
                )
            except jwt.InvalidTokenError as e:
                logger.warning(f"JWT Secret verification failed: {e}. Trying fallback methods...")

        # Method B: Verify by querying Supabase Auth endpoint
        if self.is_configured():
            try:
                with httpx.Client(timeout=5.0) as client:
                    resp = client.get(
                        f"{self.supabase_url}/auth/v1/user",
                        headers={
                            "Authorization": f"Bearer {token}",
                            "apikey": self.anon_key
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return self._format_user_from_supabase_api(data)
                    else:
                        logger.warning(f"Supabase Auth API returned {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.warning(f"Failed to reach Supabase Auth API: {e}")

        # Method C: Local unverified decode (graceful development fallback)
        try:
            unverified_payload = jwt.decode(token, options={"verify_signature": False})
            logger.info("Token decoded without signature verification (local development mode)")
            return self._format_user_from_jwt(unverified_payload)
        except Exception as e:
            logger.error(f"Failed to decode token claims: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format or corrupt payload"
            )

    def _format_user_from_jwt(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        metadata = payload.get("user_metadata", {}) or {}
        email = payload.get("email", "")
        name = metadata.get("name") or metadata.get("full_name") or (email.split("@")[0].capitalize() if email else "Investigator")
        return {
            "id": payload.get("sub") or payload.get("id"),
            "email": email,
            "name": name,
            "role": metadata.get("role", "Investigator"),
            "phone": metadata.get("phone", ""),
            "organization": metadata.get("organization", ""),
            "is_demo": False
        }

    def _format_user_from_supabase_api(self, data: Dict[str, Any]) -> Dict[str, Any]:
        metadata = data.get("user_metadata", {}) or {}
        email = data.get("email", "")
        name = metadata.get("name") or metadata.get("full_name") or (email.split("@")[0].capitalize() if email else "Investigator")
        return {
            "id": data.get("id"),
            "email": email,
            "name": name,
            "role": metadata.get("role", "Investigator"),
            "phone": metadata.get("phone", ""),
            "organization": metadata.get("organization", ""),
            "is_demo": False
        }

    def get_current_user(self, request: Request) -> Dict[str, Any]:
        """
        FastAPI dependency to extract and verify the current authenticated user.
        If REQUIRE_AUTH is False and no token is supplied, returns DEMO_USER.
        """
        token = self.extract_token_from_header(request)

        if not token:
            if self.require_auth:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required. Please provide a valid Bearer token.",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            return DEMO_USER

        try:
            return self.verify_token(token)
        except HTTPException:
            if self.require_auth:
                raise
            return DEMO_USER


auth_service = SupabaseAuthService()


def get_current_user(request: Request) -> Dict[str, Any]:
    """FastAPI dependency for accessing authenticated user."""
    return auth_service.get_current_user(request)
