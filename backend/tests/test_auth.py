import pytest
from fastapi.testclient import TestClient
import jwt
from app.main import app
from app.config import settings
from app.services.auth_service import DEMO_USER

client = TestClient(app)


def test_auth_config_endpoint():
    response = client.get("/api/auth/config")
    assert response.status_code == 200
    data = response.json()
    assert "supabase_url" in data
    assert "supabase_anon_key" in data
    assert "configured" in data
    assert "auth_required" in data
    assert "demo_account" in data
    assert data["demo_account"]["email"] == "investigator@cyberscope.io"


def test_auth_me_demo_fallback():
    # Without Authorization header when REQUIRE_AUTH=False
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "authenticated"
    assert data["user"]["email"] == DEMO_USER["email"]
    assert data["user"]["name"] == DEMO_USER["name"]


def test_auth_verify_demo_token():
    payload = {"access_token": "demo-token"}
    response = client.post("/api/auth/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["user"]["email"] == DEMO_USER["email"]


def test_auth_verify_jwt_token():
    # Create a synthetic signed JWT
    secret = "test-supabase-secret-12345"
    settings.SUPABASE_JWT_SECRET = secret

    token_payload = {
        "sub": "user-uuid-12345",
        "email": "analyst@cyberscope.io",
        "role": "authenticated",
        "user_metadata": {
            "name": "Special Agent Ray",
            "role": "Lead Analyst",
            "organization": "National Cyber Crime Unit"
        }
    }
    token = jwt.encode(token_payload, secret, algorithm="HS256")

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "analyst@cyberscope.io"
    assert data["user"]["name"] == "Special Agent Ray"
    assert data["user"]["role"] == "Lead Analyst"

    # Also test POST /api/auth/verify
    verify_resp = client.post("/api/auth/verify", json={"access_token": token})
    assert verify_resp.status_code == 200
    v_data = verify_resp.json()
    assert v_data["valid"] is True
    assert v_data["user"]["name"] == "Special Agent Ray"

    # Reset secret
    settings.SUPABASE_JWT_SECRET = ""
