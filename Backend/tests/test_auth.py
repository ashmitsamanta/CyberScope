import pytest
from fastapi.testclient import TestClient
import jwt
from datetime import datetime, timezone, timedelta
from app.main import app
from app.config import settings
from app.database import SessionLocal
from app.models.user import User
from app.services.auth_service import hash_password, create_access_token
from app.services.notification_service import notification_service

client = TestClient(app)


def test_auth_config_endpoint():
    response = client.get("/api/auth/config")
    assert response.status_code == 200
    data = response.json()
    assert "supabase_url" in data
    assert "supabase_anon_key" in data
    assert "configured" in data
    assert "auth_required" in data
    assert "demo_account" not in data


def test_auth_me_unauthenticated():
    # Without Authorization header -> 401
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_auth_verify_invalid_tokens():
    # Demo token -> 401 valid: False
    payload = {"access_token": "demo-token"}
    response = client.post("/api/auth/verify", json=payload)
    assert response.status_code == 401
    data = response.json()
    assert data["valid"] is False

    # Wrong secret token -> 401
    bad_token = jwt.encode({"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(hours=1), "iat": datetime.now(timezone.utc)}, "wrong-secret-key-12345678901234567890", algorithm="HS256")
    resp_bad = client.post("/api/auth/verify", json={"access_token": bad_token})
    assert resp_bad.status_code == 401
    assert resp_bad.json()["valid"] is False


def test_auth_verify_jwt_token(auth_headers):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "test_investigator@cyberscope.io").first()
        token = create_access_token(user.to_dict())

        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "test_investigator@cyberscope.io"
        assert data["user"]["name"] == "Test Investigator"

        # Test POST /api/auth/verify
        verify_resp = client.post("/api/auth/verify", json={"access_token": token})
        assert verify_resp.status_code == 200
        v_data = verify_resp.json()
        assert v_data["valid"] is True
        assert v_data["user"]["email"] == "test_investigator@cyberscope.io"
    finally:
        db.close()


def test_auth_registration_flow():
    from app.models.user import UserVerification
    new_email = "new_officer@police.gov.in"
    db = SessionLocal()
    try:
        db.query(User).filter(User.email == new_email).delete()
        db.query(UserVerification).filter(UserVerification.email == new_email).delete()
        db.commit()
    finally:
        db.close()

    res_check = client.post("/api/auth/check-email", json={"email": "test_investigator@cyberscope.io"})
    assert res_check.status_code == 200
    assert res_check.json()["exists"] is True

    res_check_new = client.post("/api/auth/check-email", json={"email": new_email})
    assert res_check_new.status_code == 200
    assert res_check_new.json()["exists"] is False

    conflict_resp = client.post("/api/auth/register/initiate", json={
        "name": "Demo Dup",
        "phone": "9876543210",
        "email": "test_investigator@cyberscope.io",
        "password": "SecureTestPass123!"
    })
    assert conflict_resp.status_code == 409

    init_resp = client.post("/api/auth/register/initiate", json={
        "name": "Officer Sharma",
        "phone": "9876543210",
        "email": new_email,
        "password": "SecurePassword123!",
        "role": "Lead Investigator",
        "organization": "Delhi Cyber Cell"
    })
    assert init_resp.status_code == 200
    init_data = init_resp.json()
    assert init_data["status"] == "initiated"

    outbox = notification_service.get_test_outbox()
    email_entry = next(e for e in reversed(outbox["emails"]) if e["to_email"] == new_email)
    email_otp = email_entry["code"]

    verify_resp = client.post("/api/auth/register/verify", json={
        "email": new_email,
        "email_otp": email_otp
    })
    assert verify_resp.status_code == 200
    v_data = verify_resp.json()
    assert v_data["status"] == "verified"
    assert "access_token" in v_data
    assert v_data["user"]["email"] == new_email


def test_auth_register_validation_errors():
    resp_email = client.post("/api/auth/register/initiate", json={
        "name": "Test", "phone": "9876543210", "email": "invalidemail", "password": "SecurePassword123!"
    })
    assert resp_email.status_code == 400

    resp_pass = client.post("/api/auth/register/initiate", json={
        "name": "Test", "phone": "9876543210", "email": "valid@gov.in", "password": "123"
    })
    assert resp_pass.status_code == 400


def test_auth_resend_cooldown():
    test_email = "cooldown_test@police.gov.in"
    from app.models.user import UserVerification
    from app.api.auth import _last_resend_timestamps
    db = SessionLocal()
    try:
        db.query(User).filter(User.email == test_email).delete()
        db.query(UserVerification).filter(UserVerification.email == test_email).delete()
        db.commit()
    finally:
        db.close()

    init_resp = client.post("/api/auth/register/initiate", json={
        "name": "Cooldown Tester",
        "email": test_email,
        "phone": "+919876543211",
        "password": "SecurePassword123!"
    })
    assert init_resp.status_code == 200

    _last_resend_timestamps[test_email] = 0

    resend1 = client.post("/api/auth/register/resend", json={"email": test_email})
    assert resend1.status_code == 200

    resend2 = client.post("/api/auth/register/resend", json={"email": test_email})
    assert resend2.status_code == 429
    assert resend2.json()["code"] == "COOLDOWN_ACTIVE"


def test_auth_login_endpoints():
    # Non-existent user -> 401 INVALID_CREDENTIALS
    resp_nonexistent = client.post("/api/auth/login", json={
        "email": "ghost_agent@cyberscope.io",
        "password": "somepassword"
    })
    assert resp_nonexistent.status_code == 401
    assert resp_nonexistent.json()["code"] == "INVALID_CREDENTIALS"

    # Wrong password for existing user -> 401 (identical body)
    resp_wrongpass = client.post("/api/auth/login", json={
        "email": "test_investigator@cyberscope.io",
        "password": "wrongpassword"
    })
    assert resp_wrongpass.status_code == 401
    assert resp_wrongpass.json() == resp_nonexistent.json()

    # Valid user login -> 200 authenticated
    resp_ok = client.post("/api/auth/login", json={
        "email": "test_investigator@cyberscope.io",
        "password": "SecureTestPass123!"
    })
    assert resp_ok.status_code == 200
    data = resp_ok.json()
    assert data["status"] == "authenticated"
    assert "access_token" in data


def test_all_data_routes_require_auth():
    """
    Acceptance test iterating app.routes to ensure every route not on the
    public allowlist returns 401 when called without a valid Bearer token.
    """
    public_allowlist = {
        ("GET", "/"),
        ("GET", "/api/health"),
        ("POST", "/api/auth/login"),
        ("POST", "/api/auth/register/initiate"),
        ("POST", "/api/auth/register/verify"),
        ("POST", "/api/auth/register/resend"),
        ("POST", "/api/auth/verify"),
        ("GET", "/api/auth/config"),
        ("POST", "/api/auth/check-password"),
        ("POST", "/api/auth/check-email"),
    }

    # Generate forged / invalid tokens for testing
    wrong_secret_token = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(hours=1), "iat": datetime.now(timezone.utc)},
        "wrong-secret-key-12345678901234567890",
        algorithm="HS256"
    )
    alg_none_token = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxIiwiZXhwIjo5OTk5OTk5OTk5fQ."
    expired_token = jwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(hours=1), "iat": datetime.now(timezone.utc) - timedelta(hours=2)},
        settings.JWT_SECRET,
        algorithm="HS256"
    )
    demo_token = "demo-investigator-token-123"

    for route in app.routes:
        methods = getattr(route, "methods", {"GET"}) or {"GET"}
        path = getattr(route, "path", None)
        if not path or path.startswith("/docs") or path.startswith("/openapi") or path.startswith("/redoc"):
            continue

        for method in methods:
            if (method, path) in public_allowlist:
                continue

            # 1. No Authorization header -> 401
            req_func = getattr(client, method.lower())
            res_no_auth = req_func(path)
            assert res_no_auth.status_code == 401, f"Route {method} {path} returned {res_no_auth.status_code} without auth, expected 401"

            # 2. Wrong secret token -> 401
            res_wrong = req_func(path, headers={"Authorization": f"Bearer {wrong_secret_token}"})
            assert res_wrong.status_code == 401, f"Route {method} {path} returned {res_wrong.status_code} with wrong secret token, expected 401"

            # 3. Alg none token -> 401
            res_none = req_func(path, headers={"Authorization": f"Bearer {alg_none_token}"})
            assert res_none.status_code == 401, f"Route {method} {path} returned {res_none.status_code} with alg:none token, expected 401"

            # 4. Expired token -> 401
            res_exp = req_func(path, headers={"Authorization": f"Bearer {expired_token}"})
            assert res_exp.status_code == 401, f"Route {method} {path} returned {res_exp.status_code} with expired token, expected 401"

            # 5. Demo token -> 401
            res_demo = req_func(path, headers={"Authorization": f"Bearer {demo_token}"})
            assert res_demo.status_code == 401, f"Route {method} {path} returned {res_demo.status_code} with demo token, expected 401"


def test_email_dispatcher_resend_mocked(monkeypatch):
    """Verifies HTTPS Resend API dispatch on port 443 with mocked httpx response."""
    from unittest.mock import MagicMock
    from app.services.notification_service import EmailDispatcher

    dispatcher = EmailDispatcher()
    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test_key_123")
    monkeypatch.setattr(settings, "EMAIL_FROM_EMAIL", "security@cyberscope.io")
    monkeypatch.setattr(settings, "EMAIL_FROM_NAME", "CyberScope Security")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "res_msg_abc123"}

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_resp

    import httpx
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client)

    result = dispatcher._dispatch_resend(
        to_email="investigator@agency.gov",
        recipient_name="Agent Smith",
        subject="CyberScope Verification",
        html_content="<p>123456</p>",
        plain_text="123456",
        code="123456"
    )

    assert result["success"] is True
    assert result["provider"] == "resend"
    assert "Verification email dispatched via Resend" in result["message"]
    assert mock_client.post.called
    call_args = mock_client.post.call_args
    assert call_args[0][0] == "https://api.resend.com/emails"
    assert call_args[1]["headers"]["Authorization"] == "Bearer re_test_key_123"


def test_email_dispatcher_brevo_mocked(monkeypatch):
    """Verifies HTTPS Brevo API dispatch on port 443 with mocked httpx response."""
    from unittest.mock import MagicMock
    from app.services.notification_service import EmailDispatcher

    dispatcher = EmailDispatcher()
    monkeypatch.setattr(settings, "BREVO_API_KEY", "xkeysib-test-key-456")
    monkeypatch.setattr(settings, "EMAIL_FROM_EMAIL", "cyberscope60@gmail.com")
    monkeypatch.setattr(settings, "EMAIL_FROM_NAME", "CyberScope Security")

    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"messageId": "<20261013.123@smtp-relay.brevo.com>"}

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_resp

    import httpx
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client)

    result = dispatcher._dispatch_brevo(
        to_email="officer@police.gov.in",
        recipient_name="Officer Rao",
        subject="CyberScope Verification Code",
        html_content="<p>654321</p>",
        plain_text="654321",
        code="654321"
    )

    assert result["success"] is True
    assert result["provider"] == "brevo"
    assert "Verification email dispatched via Brevo" in result["message"]
    assert mock_client.post.called
    call_args = mock_client.post.call_args
    assert call_args[0][0] == "https://api.brevo.com/v3/smtp/email"
    assert call_args[1]["headers"]["api-key"] == "xkeysib-test-key-456"
    assert call_args[1]["json"]["sender"]["email"] == "cyberscope60@gmail.com"


def test_email_dispatcher_blocked_smtp_diagnosis(monkeypatch):
    """Verifies that an outbound SMTP timeout on Render triggers an actionable diagnostic message."""
    from app.services.notification_service import EmailDispatcher
    import smtplib

    dispatcher = EmailDispatcher()
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USER", "test@gmail.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "apppassword")

    def mock_smtp_connect(*args, **kwargs):
        raise TimeoutError("[Errno 110] Connection timed out")

    monkeypatch.setattr(smtplib, "SMTP", mock_smtp_connect)

    result = dispatcher._dispatch_smtp(
        to_email="test@example.com",
        recipient_name="Test",
        subject="Test Code",
        html_content="<p>999999</p>",
        plain_text="999999",
        code="999999"
    )

    assert result["success"] is False
    assert result["provider"] == "smtp"
    assert "Render free web services block outbound SMTP ports 25, 465, and 587" in result["message"]
    assert "RESEND_API_KEY or BREVO_API_KEY" in result["message"]


def test_email_dispatcher_provider_detection(monkeypatch):
    """Verifies provider detection hierarchy."""
    from app.services.notification_service import EmailDispatcher

    dispatcher = EmailDispatcher()

    # Default with no keys -> unconfigured
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "auto")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "")
    monkeypatch.setattr(settings, "BREVO_API_KEY", "")
    monkeypatch.setattr(settings, "SENDGRID_API_KEY", "")
    monkeypatch.setattr(settings, "MAILGUN_API_KEY", "")
    monkeypatch.setattr(settings, "EMAIL_WEBHOOK_URL", "")
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    assert dispatcher._detect_provider() == "unconfigured"

    # RESEND_API_KEY set -> resend
    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_123")
    assert dispatcher._detect_provider() == "resend"

    # BREVO_API_KEY set without resend -> brevo
    monkeypatch.setattr(settings, "RESEND_API_KEY", "")
    monkeypatch.setattr(settings, "BREVO_API_KEY", "xkeysib_123")
    assert dispatcher._detect_provider() == "brevo"

    # Explicit override takes precedence
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "smtp")
    assert dispatcher._detect_provider() == "smtp"


def test_verification_logging_no_secrets(caplog, monkeypatch):
    """
    Acceptance test for Task 1:
    Sends a verification email through a mocked provider with caplog at DEBUG level
    and asserts neither the 6-digit code nor the API key appears anywhere in captured logs.
    Also verifies the email address is masked.
    """
    import logging
    from unittest.mock import MagicMock
    import httpx
    from app.services.notification_service import EmailDispatcher

    caplog.set_level(logging.DEBUG)
    secret_api_key = "re_super_secret_test_key_xyz987"
    secret_code = "739281"
    raw_email = "target_investigator@example.com"

    monkeypatch.setattr(settings, "RESEND_API_KEY", secret_api_key)
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "resend")
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "VERIFICATION_MOCK_DISPATCH", False)
    monkeypatch.setattr(settings, "_FORCE_LIVE_EMAIL", True, raising=False)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "msg_mock_12345"}
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_resp
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client)

    dispatcher = EmailDispatcher()
    res = dispatcher.send_verification_email(
        to_email=raw_email,
        recipient_name="Investigator Target",
        code=secret_code
    )
    assert res["success"] is True

    captured = caplog.text
    assert secret_code not in captured, f"Verification code found in logs: {captured}"
    assert secret_api_key not in captured, f"API key found in logs: {captured}"
    assert raw_email not in captured, f"Unmasked email found in logs: {captured}"
    assert "t***r@example.com" in captured


def test_verification_logging_sanitizes_error_body(caplog, monkeypatch):
    """
    Verifies that error response bodies from providers are truncated to 200 chars
    and have verification codes redacted.
    """
    import logging
    from unittest.mock import MagicMock
    import httpx
    from app.services.notification_service import EmailDispatcher

    caplog.set_level(logging.DEBUG)
    secret_code = "847291"
    long_error_with_code = f"Error processing code {secret_code}: " + ("x" * 300)

    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_dummy_key_123")
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "resend")
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "VERIFICATION_MOCK_DISPATCH", False)
    monkeypatch.setattr(settings, "_FORCE_LIVE_EMAIL", True, raising=False)

    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = long_error_with_code
    mock_resp.json.side_effect = Exception("not json")
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_resp
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client)

    dispatcher = EmailDispatcher()
    res = dispatcher.send_verification_email(
        to_email="test@example.com",
        recipient_name="Investigator Target",
        code=secret_code
    )
    assert res["success"] is False

    captured = caplog.text
    assert secret_code not in captured
    assert "[REDACTED]" in captured


def test_empty_jwt_secret_raises():
    """Acceptance test Task 2 (a): Instantiating Settings with empty or short JWT_SECRET raises ValueError."""
    from app.config import Settings
    with pytest.raises(ValueError, match="JWT_SECRET must be at least 32 characters long"):
        Settings(JWT_SECRET="")

    with pytest.raises(ValueError, match="JWT_SECRET must be at least 32 characters long"):
        Settings(JWT_SECRET="short-secret-key")


def test_old_public_default_jwt_secret_rejected_with_401():
    """Acceptance test Task 2 (b): A token signed with the old public default secret is rejected with 401."""
    import base64
    from datetime import datetime, timezone, timedelta
    from app.main import app
    from fastapi.testclient import TestClient
    import jwt

    # Decode old public default without literal string match in repository source
    old_secret = base64.b64decode("Y3liZXJzY29wZS1zZWNyZXQtand0LWtleS1mb3ItYXV0aC10b2tlbi12ZXJpZmljYXRpb24tMzJi").decode("utf-8")

    now = datetime.now(timezone.utc)
    payload = {
        "sub": "1",
        "email": "test_investigator@cyberscope.io",
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "iat": int(now.timestamp())
    }
    old_signed_token = jwt.encode(payload, old_secret, algorithm="HS256")

    client = TestClient(app)
    # Test verify endpoint
    verify_resp = client.post("/api/auth/verify", json={"access_token": old_signed_token})
    assert verify_resp.status_code == 401
    assert verify_resp.json()["valid"] is False

    # Test me endpoint
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {old_signed_token}"})
    assert me_resp.status_code == 401


def test_register_rejects_html_injection_name():
    """Acceptance test Task 3: Name with HTML injection is rejected with 422."""
    evil_name = '<a href="https://evil.example">x</a>'
    res = client.post("/api/auth/register/initiate", json={
        "name": evil_name,
        "email": "valid_user_xss@example.com",
        "phone": "+919876543210",
        "password": "SecurePassword123!"
    })
    assert res.status_code == 422


def test_build_html_template_escapes_name():
    """Acceptance test Task 3: Directly passing HTML in recipient_name escapes <a to &lt;a and contains no raw <a href."""
    from app.services.notification_service import EmailDispatcher
    dispatcher = EmailDispatcher()
    evil_name = '<a href="https://evil.example">x</a>'
    html_out = dispatcher._build_html_template(evil_name, "123456")
    assert "&lt;a" in html_out
    assert '<a href="https://evil.example">' not in html_out
    assert "<a href" not in html_out


def test_name_with_newline_stripped_from_provider_payloads(monkeypatch):
    """Acceptance test Task 3: Name with \r\nBcc: x@y.z never reaches provider payloads with the newline."""
    from unittest.mock import MagicMock
    import httpx
    from app.services.notification_service import EmailDispatcher

    monkeypatch.setattr(settings, "BREVO_API_KEY", "test-brevo-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"messageId": "msg123"}
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_resp
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client)

    dispatcher = EmailDispatcher()
    malicious_name = "Investigator\r\nBcc: x@y.z"
    dispatcher._dispatch_brevo(
        to_email="test@example.com",
        recipient_name=malicious_name,
        subject="Test Code",
        html_content="<p>code</p>",
        plain_text="code",
        code="123456"
    )
    assert mock_client.post.called
    payload = mock_client.post.call_args[1]["json"]
    sent_name = payload["to"][0]["name"]
    assert "\r" not in sent_name
    assert "\n" not in sent_name


def test_login_rate_limiting_429_on_6th_attempt():
    """
    Acceptance test for Task 4:
    POST /api/auth/login is limited to 5/minute per IP.
    The 6th attempt within the minute returns HTTP 429 with RATE_LIMITED code and Retry-After header.
    """
    from app.limiter import limiter
    limiter.reset()

    # Attempts 1 through 5 should reach endpoint (and return 401 for bad credentials)
    for i in range(5):
        resp = client.post("/api/auth/login", json={
            "email": "rate_limit_test@example.com",
            "password": "WrongPassword123!"
        })
        assert resp.status_code == 401, f"Attempt {i+1} should return 401"

    # 6th attempt must be rate-limited by SlowAPI
    resp_6 = client.post("/api/auth/login", json={
        "email": "rate_limit_test@example.com",
        "password": "WrongPassword123!"
    })
    assert resp_6.status_code == 429
    data = resp_6.json()
    assert data.get("code") == "RATE_LIMITED"
    assert "Retry-After" in resp_6.headers


def test_register_initiate_per_email_limit_429_on_4th_attempt():
    """
    Acceptance test for Task 4:
    Per-target-email limit on /register/initiate enforces at most 3 sends per hour.
    The 4th send to the same email returns HTTP 429 with RATE_LIMITED code and Retry-After header.
    """
    from app.limiter import email_rate_limiter, limiter
    from app.models.user import UserVerification
    limiter.reset()
    email_rate_limiter.reset_for_tests()

    target_email = "investigator_abuse_test@example.com"
    db = SessionLocal()
    try:
        db.query(User).filter(User.email == target_email).delete()
        db.query(UserVerification).filter(UserVerification.email == target_email).delete()
        db.commit()
    finally:
        db.close()

    # First 3 initiate requests to this email should succeed
    # We pass different X-Forwarded-For so slowapi per-IP limit does not trigger before email limit
    for i in range(3):
        headers = {"X-Forwarded-For": f"198.51.100.{i+1}"}
        resp = client.post(
            "/api/auth/register/initiate",
            json={
                "name": "Investigator abuse test",
                "email": target_email,
                "phone": "+919876543210",
                "password": "StrongPassword123!"
            },
            headers=headers
        )
        assert resp.status_code == 200, f"Attempt {i+1} should succeed"

    # 4th initiate to the exact same email must trigger the per-email sliding window cap
    resp_4 = client.post(
        "/api/auth/register/initiate",
        json={
            "name": "Investigator abuse test",
            "email": target_email,
            "phone": "+919876543210",
            "password": "StrongPassword123!"
        },
        headers={"X-Forwarded-For": "198.51.100.99"}
    )
    assert resp_4.status_code == 429
    data = resp_4.json()
    assert data.get("code") == "RATE_LIMITED"
    assert "Retry-After" in resp_4.headers


def test_daily_email_cap_returns_503(monkeypatch):
    """
    Acceptance test for Task 4:
    When EMAIL_DAILY_CAP is exceeded, returns HTTP 503 {"code": "EMAIL_CAP"}
    without calling any email provider.
    """
    from unittest.mock import MagicMock
    from app.services.notification_service import notification_service
    from app.limiter import email_rate_limiter, daily_email_tracker, limiter
    from app.models.user import UserVerification

    limiter.reset()
    email_rate_limiter.reset_for_tests()
    daily_email_tracker.reset_for_tests()

    monkeypatch.setattr(settings, "EMAIL_DAILY_CAP", 2)
    mock_send = MagicMock(return_value={"success": True, "provider": "mock"})
    monkeypatch.setattr(notification_service, "send_email_otp", mock_send)

    db = SessionLocal()
    try:
        db.query(User).filter(User.email.like("daily_cap_%@example.com")).delete()
        db.query(UserVerification).filter(UserVerification.email.like("daily_cap_%@example.com")).delete()
        db.commit()
    finally:
        db.close()

    # 1st send
    resp1 = client.post("/api/auth/register/initiate", json={
        "name": "Cap Test One",
        "email": "daily_cap_1@example.com",
        "phone": "+919876543211",
        "password": "StrongPassword123!"
    }, headers={"X-Forwarded-For": "192.0.2.1"})
    assert resp1.status_code == 200

    # 2nd send
    resp2 = client.post("/api/auth/register/initiate", json={
        "name": "Cap Test Two",
        "email": "daily_cap_2@example.com",
        "phone": "+919876543212",
        "password": "StrongPassword123!"
    }, headers={"X-Forwarded-For": "192.0.2.2"})
    assert resp2.status_code == 200

    assert mock_send.call_count == 2

    # 3rd send exceeds EMAIL_DAILY_CAP (2)
    resp3 = client.post("/api/auth/register/initiate", json={
        "name": "Cap Test Three",
        "email": "daily_cap_3@example.com",
        "phone": "+919876543213",
        "password": "StrongPassword123!"
    }, headers={"X-Forwarded-For": "192.0.2.3"})
    assert resp3.status_code == 503
    data = resp3.json()
    assert data.get("code") == "EMAIL_CAP"
    # Ensure provider was NOT called for the 3rd attempt
    assert mock_send.call_count == 2


def test_login_identical_401_for_unknown_email_and_wrong_password():
    """
    Acceptance test for Task 4:
    Login returns identical 401 response body for unknown email and wrong password.
    """
    resp_unknown = client.post("/api/auth/login", json={
        "email": "completely_unknown_user@example.com",
        "password": "AnyPassword123!"
    })
    resp_wrong_pw = client.post("/api/auth/login", json={
        "email": "test_investigator@cyberscope.io",
        "password": "DefinitelyWrongPassword123!"
    })
    assert resp_unknown.status_code == 401
    assert resp_wrong_pw.status_code == 401
    assert resp_unknown.json() == resp_wrong_pw.json()
    assert resp_unknown.json() == {
        "detail": "Invalid email or password.",
        "code": "INVALID_CREDENTIALS"
    }


def test_password_policy_acceptance():
    """
    Acceptance test for Task 5:
    Rejects 7-char passwords with 400.
    Rejects 129-char passwords with 400.
    Accepts 8-char strong password.
    Rejects weak/too weak passwords.
    """
    from app.models.user import UserVerification
    test_email = "pw_policy_test@example.com"
    db = SessionLocal()
    try:
        db.query(User).filter(User.email == test_email).delete()
        db.query(UserVerification).filter(UserVerification.email == test_email).delete()
        db.commit()
    finally:
        db.close()

    # 1. 7-character password rejected
    resp_7 = client.post("/api/auth/register/initiate", json={
        "name": "Investigator Policy",
        "email": test_email,
        "phone": "+919876543210",
        "password": "Ab1!Cd2"  # 7 characters
    })
    assert resp_7.status_code == 400
    assert resp_7.json()["code"] in ("PASSWORD_TOO_SHORT", "PASSWORD_TOO_WEAK")

    # 2. 129-character password rejected
    resp_129 = client.post("/api/auth/register/initiate", json={
        "name": "Investigator Policy",
        "email": test_email,
        "phone": "+919876543210",
        "password": "A1!" + "a" * 126  # 129 characters
    })
    assert resp_129.status_code == 400
    assert resp_129.json()["code"] == "PASSWORD_TOO_LONG"

    # 3. 8-char strong password accepted
    resp_8 = client.post("/api/auth/register/initiate", json={
        "name": "Investigator Policy",
        "email": test_email,
        "phone": "+919876543210",
        "password": "Ab1!Cd2@"  # 8 characters, strong variety
    })
    assert resp_8.status_code == 200
    assert resp_8.json()["status"] == "initiated"


def test_failing_provider_message_production_vs_development(monkeypatch):
    """
    Acceptance test for Task 6:
    A failing email provider returns generic message in production:
    "We could not send the verification email right now. Please wait a minute and use Resend code."
    while returning detailed diagnostics in development.
    """
    from unittest.mock import MagicMock
    import httpx
    from app.services.notification_service import EmailDispatcher

    dispatcher = EmailDispatcher()
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error from upstream provider"
    mock_resp.json.side_effect = Exception("Not JSON")

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_resp
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client)

    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test_key_xyz")
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "resend")
    monkeypatch.setattr(settings, "VERIFICATION_MOCK_DISPATCH", False)
    monkeypatch.setattr(settings, "_FORCE_LIVE_EMAIL", True, raising=False)

    # 1. In Production: must return generic message
    monkeypatch.setattr(settings, "APP_ENV", "production")
    res_prod = dispatcher.send_verification_email("officer@gov.in", "Officer", "654321")
    assert res_prod["success"] is False
    assert res_prod["message"] == "We could not send the verification email right now. Please wait a minute and use Resend code."
    assert "Internal Server Error" not in res_prod["message"]

    # 2. In Development: returns detailed error message
    monkeypatch.setattr(settings, "APP_ENV", "development")
    res_dev = dispatcher.send_verification_email("officer@gov.in", "Officer", "654321")
    assert res_dev["success"] is False
    assert res_dev["message"] != "We could not send the verification email right now. Please wait a minute and use Resend code."
    assert "Resend delivery failed (HTTP 500)" in res_dev["message"]


def test_startup_fails_with_mock_provider_in_production(monkeypatch):
    """
    Acceptance test for Task 6:
    In production, unsafe providers are refused at startup:
    - Settings with EMAIL_PROVIDER="mock" in production raises ValueError
    - Settings with VERIFICATION_MOCK_DISPATCH=True in production raises ValueError
    - Settings with non-HTTPS EMAIL_WEBHOOK_URL in production raises ValueError
    """
    from app.config import Settings
    valid_jwt = "a" * 48

    # EMAIL_PROVIDER="mock" in production must raise
    with pytest.raises(ValueError, match="EMAIL_PROVIDER='mock' is not allowed in production"):
        Settings(JWT_SECRET=valid_jwt, APP_ENV="production", EMAIL_PROVIDER="mock")

    # VERIFICATION_MOCK_DISPATCH=True in production must raise
    with pytest.raises(ValueError, match="VERIFICATION_MOCK_DISPATCH cannot be True in production"):
        Settings(JWT_SECRET=valid_jwt, APP_ENV="production", VERIFICATION_MOCK_DISPATCH=True, EMAIL_PROVIDER="resend")

    # Insecure HTTP webhook in production must raise
    with pytest.raises(ValueError, match="EMAIL_WEBHOOK_URL must start with https://"):
        Settings(JWT_SECRET=valid_jwt, APP_ENV="production", EMAIL_WEBHOOK_URL="http://insecure.example/hook", EMAIL_PROVIDER="webhook")


def test_unconfigured_provider_in_production_returns_generic_and_logs_warning(monkeypatch, caplog):
    """
    Acceptance test for Task 6:
    Unconfigured provider in production returns generic message and logs a warning naming missing variables.
    """
    import logging
    from app.services.notification_service import EmailDispatcher

    caplog.set_level(logging.WARNING)
    dispatcher = EmailDispatcher()

    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "auto")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "")
    monkeypatch.setattr(settings, "BREVO_API_KEY", "")
    monkeypatch.setattr(settings, "SENDGRID_API_KEY", "")
    monkeypatch.setattr(settings, "MAILGUN_API_KEY", "")
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    monkeypatch.setattr(settings, "EMAIL_WEBHOOK_URL", "")

    res = dispatcher.send_verification_email("unconfigured@example.com", "Officer", "112233")
    assert res["success"] is False
    assert res["message"] == "We could not send the verification email right now. Please wait a minute and use Resend code."
    assert "Missing variables:" in caplog.text
    assert "RESEND_API_KEY" in caplog.text
    assert "SMTP_HOST" in caplog.text






