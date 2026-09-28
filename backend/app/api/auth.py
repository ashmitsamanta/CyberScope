from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from app.config import settings
from app.services.auth_service import auth_service, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class TokenVerifyRequest(BaseModel):
    access_token: str = Field(..., description="Supabase JWT access token to verify")


class AuthConfigResponse(BaseModel):
    supabase_url: str
    supabase_anon_key: str
    configured: bool
    auth_required: bool
    demo_account: Dict[str, str]


@router.get("/config", response_model=AuthConfigResponse)
def get_auth_config():
    """
    Returns public Supabase client configuration parameters.
    Allows frontend clients to dynamically initialize Supabase without
    baking credentials directly into static builds.
    """
    return {
        "supabase_url": settings.SUPABASE_URL,
        "supabase_anon_key": settings.SUPABASE_ANON_KEY,
        "configured": auth_service.is_configured(),
        "auth_required": settings.REQUIRE_AUTH,
        "demo_account": {
            "email": "investigator@cyberscope.io",
            "password": "password123",
            "name": "Investigator Demo",
            "role": "Investigator"
        }
    }


@router.get("/me")
def get_authenticated_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns the current authenticated investigator's profile.
    Extracts identity from Supabase JWT access token.
    """
    return {
        "status": "authenticated",
        "user": current_user
    }


@router.post("/verify")
def verify_access_token(payload: TokenVerifyRequest):
    """
    Verifies a Supabase access token and returns decoded investigator claims.
    """
    try:
        user_info = auth_service.verify_token(payload.access_token)
        return {
            "valid": True,
            "user": user_info
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token verification failed: {str(e)}"
        )
