import html
import os
import sys
import re
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger("cyberscope.notifications")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def _is_test_mode() -> bool:
    """
    Determines if the application is running in an automated test environment
    or has mock dispatch explicitly enabled.
    """
    return (
        settings.VERIFICATION_MOCK_DISPATCH
        or "pytest" in sys.modules
        or os.environ.get("PYTEST_CURRENT_TEST") is not None
        or settings.APP_ENV in ("test", "testing")
    )


def mask_email(email: str) -> str:
    """Masks an email address for privacy and security in logs (e.g. t***7@gmail.com)."""
    if not email or "@" not in email:
        return "***"
    local, domain = email.strip().split("@", 1)
    if len(local) <= 1:
        masked_local = f"{local}***"
    elif len(local) == 2:
        masked_local = f"{local[0]}***{local[1]}"
    else:
        masked_local = f"{local[0]}***{local[-1]}"
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """Masks a phone number for logs."""
    if not phone:
        return "***"
    clean = str(phone).strip()
    if len(clean) <= 4:
        return "***"
    return f"{clean[:2]}***{clean[-2:]}"


def _sanitize_error_text(text: Any, code: Optional[str] = None) -> str:
    """Truncates provider error body to 200 chars and removes verification code."""
    if not text:
        return ""
    val = str(text)
    if code and str(code) in val:
        val = val.replace(str(code), "[REDACTED]")
    return val[:200]


def _clean_name(name: Optional[str], default: str = "Investigator") -> str:
    """Strips CR, LF, and control characters (0-31, 127) from names to prevent header injection."""
    if not name:
        return default
    cleaned = re.sub(r"[\r\n\x00-\x1f\x7f]", "", str(name)).strip()
    return cleaned if cleaned else default


GENERIC_DELIVERY_ERROR_MESSAGE = "We could not send the verification email right now. Please wait a minute and use Resend code."


class EmailDispatcher:
    """
    Handles cryptographic dispatch of verification codes and forensic notifications
    via HTTPS Email APIs (Resend, Brevo, SendGrid, Mailgun, Webhook) and enterprise SMTP,
    with fallback to an in-memory testing outbox.
    """

    def __init__(self):
        self.dispatched_emails: List[Dict[str, Any]] = []

    def _build_html_template(self, recipient_name: str, code: str) -> str:
        name = html.escape((recipient_name or "").strip(), quote=True) if (recipient_name or "").strip() else "Investigator"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CyberScope Security Verification</title>
</head>
<body style="margin: 0; padding: 0; background-color: #080d1a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #e2e8f0;">
  <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #080d1a; padding: 40px 10px;">
    <tr>
      <td align="center">
        <!-- Main Container -->
        <table role="presentation" width="100%" max-width="600" style="max-width: 600px; background: linear-gradient(180deg, #0f172a 0%, #0a0f1d 100%); border: 1px solid #1e293b; border-radius: 12px; overflow: hidden; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);">
          
          <!-- Top Neon Accent Header Bar -->
          <tr>
            <td style="height: 4px; background: linear-gradient(90deg, #00f0ff 0%, #00ff9d 50%, #3b82f6 100%);"></td>
          </tr>

          <!-- Brand Header -->
          <tr>
            <td style="padding: 32px 36px 20px; text-align: left;">
              <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0">
                <tr>
                  <td>
                    <div style="font-size: 24px; font-weight: 800; letter-spacing: 2px; color: #00f0ff; text-transform: uppercase;">
                      CYBERSCOPE
                    </div>
                    <div style="font-size: 11px; font-weight: 600; letter-spacing: 1.5px; color: #64748b; text-transform: uppercase; margin-top: 4px;">
                      Financial Forensics &amp; Threat Intelligence
                    </div>
                  </td>
                  <td align="right" valign="top">
                    <span style="display: inline-block; padding: 4px 10px; font-size: 10px; font-weight: 700; letter-spacing: 1px; color: #00ff9d; background: rgba(0, 255, 157, 0.1); border: 1px solid rgba(0, 255, 157, 0.3); border-radius: 4px; text-transform: uppercase;">
                      SECURITY NOTIFICATION
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Content Body -->
          <tr>
            <td style="padding: 10px 36px 24px;">
              <p style="font-size: 15px; line-height: 1.6; color: #cbd5e1; margin: 0 0 16px;">
                Hello <strong style="color: #f8fafc;">{name}</strong>,
              </p>
              <p style="font-size: 14px; line-height: 1.6; color: #94a3b8; margin: 0 0 24px;">
                A request has been initiated to verify your investigator identity on the CyberScope Intelligence Platform. Use the one-time security authentication code below to finalize your registration:
              </p>

              <!-- Prominent Monospace Code Box -->
              <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="margin: 28px 0;">
                <tr>
                  <td align="center" style="background: rgba(0, 240, 255, 0.04); border: 1px dashed rgba(0, 240, 255, 0.4); border-radius: 8px; padding: 24px 20px;">
                    <div style="font-size: 11px; font-weight: 700; letter-spacing: 2px; color: #38bdf8; text-transform: uppercase; margin-bottom: 8px;">
                      Authentication Security Code
                    </div>
                    <div style="font-family: 'Courier New', Courier, monospace; font-size: 40px; font-weight: 800; letter-spacing: 14px; color: #00f0ff; text-align: center; text-indent: 14px;">
                      {code}
                    </div>
                    <div style="font-size: 11px; color: #64748b; margin-top: 10px;">
                      6-Digit Cryptographic Verification PIN
                    </div>
                  </td>
                </tr>
              </table>

              <!-- Expiry Alert -->
              <div style="background: rgba(245, 158, 11, 0.08); border-left: 3px solid #f59e0b; border-radius: 4px; padding: 12px 16px; margin-bottom: 24px;">
                <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #fbbf24;">
                  <strong>Expiration Notice:</strong> This authentication code is valid for exactly <strong>10 minutes</strong>. After expiration, a new code must be generated.
                </p>
              </div>

              <!-- Security Advice -->
              <div style="background: #111827; border: 1px solid #1f2937; border-radius: 6px; padding: 14px 18px; margin-bottom: 20px;">
                <p style="margin: 0; font-size: 12px; line-height: 1.6; color: #94a3b8;">
                  <strong style="color: #cbd5e1;">Security Protocol:</strong> CyberScope officers and automated systems will never request your verification PIN or password via phone, email, or direct messaging. Never share this code with anyone.
                </p>
              </div>

              <p style="font-size: 12px; line-height: 1.5; color: #64748b; margin: 0;">
                If you did not initiate this registration request, no action is required; the code will expire automatically. You may report unauthorized attempts to your agency security administrator.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 24px 36px 32px; border-top: 1px solid #1e293b; background-color: #090e1a;">
              <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0">
                <tr>
                  <td style="font-size: 11px; color: #475569; line-height: 1.5;">
                    &copy; 2026 CyberScope Intelligence Network. All rights reserved.<br>
                    Autonomous Forensic Dispatch Engine &bull; Zero Trust Identity Verification
                  </td>
                </tr>
              </table>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    def _build_plain_text(self, recipient_name: str, code: str) -> str:
        name = _clean_name(recipient_name, default="Investigator")
        return f"""=======================================================
CYBERSCOPE INTELLIGENCE PLATFORM
OFFICIAL IDENTITY VERIFICATION DISPATCH
=======================================================

Hello {name},

A registration request was submitted to access the CyberScope
Forensics & Financial Crime Intelligence Platform.

Your 6-digit verification code is:

    >>> {code} <<<

SECURITY NOTICE:
- Valid for exactly 10 minutes.
- CyberScope personnel will NEVER ask you for this code.
- Do not disclose this code to anyone.

If you did not initiate this request, no action is needed;
the verification code will expire automatically.

=======================================================
CyberScope Security Operations
https://cyberscope.io
=======================================================
"""

    def _detect_provider(self) -> str:
        """
        Determines the effective email provider based on configuration.
        Auto-detection prioritizes HTTPS Email APIs over port 443 (ideal for Render/Vercel)
        before falling back to legacy SMTP.
        """
        explicit = (getattr(settings, "EMAIL_PROVIDER", "") or "auto").strip().lower()
        if explicit and explicit != "auto":
            return explicit

        if getattr(settings, "RESEND_API_KEY", "").strip():
            return "resend"
        if getattr(settings, "BREVO_API_KEY", "").strip() or os.environ.get("SENDINBLUE_API_KEY", "").strip():
            return "brevo"
        if getattr(settings, "SENDGRID_API_KEY", "").strip():
            return "sendgrid"
        if getattr(settings, "MAILGUN_API_KEY", "").strip() and getattr(settings, "MAILGUN_DOMAIN", "").strip():
            return "mailgun"
        if getattr(settings, "EMAIL_WEBHOOK_URL", "").strip():
            return "webhook"
        if getattr(settings, "SMTP_HOST", "").strip() and getattr(settings, "SMTP_USER", "").strip() and getattr(settings, "SMTP_PASSWORD", "").strip():
            return "smtp"
        return "unconfigured"

    def _get_from_identity(self, provider: str) -> tuple:
        """
        Extracts display name and from-email address tailored for the given provider.
        """
        from_name = (
            getattr(settings, "EMAIL_FROM_NAME", "")
            or getattr(settings, "SMTP_FROM_NAME", "")
            or "CyberScope Security"
        )
        from_name = _clean_name(from_name, default="CyberScope Security")
        from_email = (
            getattr(settings, "EMAIL_FROM_EMAIL", "")
            or getattr(settings, "SMTP_FROM_EMAIL", "")
            or getattr(settings, "SMTP_USER", "")
            or "security@cyberscope.io"
        ).strip()

        if provider == "resend":
            resend_from = getattr(settings, "RESEND_FROM_EMAIL", "").strip()
            if resend_from:
                from_email = resend_from
            elif not from_email or from_email.lower().endswith("@gmail.com") or from_email.lower().endswith("@yahoo.com") or from_email.lower() in ("security@cyberscope.io", "noreply@cyberscope.io"):
                # Resend testing sandbox requires onboarding@resend.dev unless a custom domain is verified
                from_email = "onboarding@resend.dev"

        return from_name, from_email

    def _dispatch_resend(self, to_email: str, recipient_name: str, subject: str, html_content: str, plain_text: str, code: str) -> Dict[str, Any]:
        api_key = getattr(settings, "RESEND_API_KEY", "").strip()
        if not api_key:
            return {"success": False, "provider": "resend", "message": "RESEND_API_KEY is not configured in environment."}

        from_name, from_email = self._get_from_identity("resend")
        clean_recipient_name = _clean_name(recipient_name, default="Investigator")
        from_header = f"{from_name} <{from_email}>" if from_name else from_email
        to_header = f"{clean_recipient_name} <{to_email}>" if clean_recipient_name else to_email
        payload = {
            "from": from_header,
            "to": [to_header],
            "subject": subject,
            "html": html_content,
            "text": plain_text,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        timeout = float(getattr(settings, "EMAIL_HTTP_TIMEOUT_SECONDS", 10.0))
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post("https://api.resend.com/emails", headers=headers, json=payload)
                if resp.status_code in (200, 201):
                    msg_id = resp.json().get("id", "")
                    logger.info(f"[EmailDispatcher:Resend] Verification email dispatched to {mask_email(to_email)} (ID: {msg_id})")
                    return {
                        "success": True,
                        "provider": "resend",
                        "message": f"Verification email dispatched via Resend to {to_email}."
                    }
                err_text = _sanitize_error_text(resp.text, code)
                try:
                    err_json = resp.json()
                    err_text = _sanitize_error_text(err_json.get("message", resp.text), code)
                except Exception:
                    pass
                logger.error(f"[EmailDispatcher:Resend] HTTP {resp.status_code}: {err_text}")
                return {
                    "success": False,
                    "provider": "resend",
                    "message": f"Resend delivery failed (HTTP {resp.status_code}): {err_text}"
                }
        except Exception as exc:
            safe_exc = _sanitize_error_text(exc, code)
            logger.error(f"[EmailDispatcher:Resend] Exception: {safe_exc}")
            return {
                "success": False,
                "provider": "resend",
                "message": f"Resend request error: {safe_exc}"
            }

    def _dispatch_brevo(self, to_email: str, recipient_name: str, subject: str, html_content: str, plain_text: str, code: str) -> Dict[str, Any]:
        api_key = (getattr(settings, "BREVO_API_KEY", "") or os.environ.get("SENDINBLUE_API_KEY", "")).strip()
        if not api_key:
            return {"success": False, "provider": "brevo", "message": "BREVO_API_KEY is not configured in environment."}

        from_name, from_email = self._get_from_identity("brevo")
        clean_recipient_name = _clean_name(recipient_name, default="Investigator")
        payload = {
            "sender": {"name": from_name, "email": from_email},
            "to": [{"email": to_email, "name": clean_recipient_name}],
            "subject": subject,
            "htmlContent": html_content,
            "textContent": plain_text,
        }
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        timeout = float(getattr(settings, "EMAIL_HTTP_TIMEOUT_SECONDS", 10.0))
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post("https://api.brevo.com/v3/smtp/email", headers=headers, json=payload)
                if resp.status_code in (200, 201, 202):
                    msg_id = resp.json().get("messageId", "")
                    logger.info(f"[EmailDispatcher:Brevo] Verification email dispatched to {mask_email(to_email)} (ID: {msg_id})")
                    return {
                        "success": True,
                        "provider": "brevo",
                        "message": f"Verification email dispatched via Brevo to {to_email}."
                    }
                err_text = _sanitize_error_text(resp.text, code)
                try:
                    err_json = resp.json()
                    err_text = _sanitize_error_text(err_json.get("message", resp.text), code)
                except Exception:
                    pass
                logger.error(f"[EmailDispatcher:Brevo] HTTP {resp.status_code}: {err_text}")
                return {
                    "success": False,
                    "provider": "brevo",
                    "message": f"Brevo delivery failed (HTTP {resp.status_code}): {err_text}"
                }
        except Exception as exc:
            safe_exc = _sanitize_error_text(exc, code)
            logger.error(f"[EmailDispatcher:Brevo] Exception: {safe_exc}")
            return {
                "success": False,
                "provider": "brevo",
                "message": f"Brevo request error: {safe_exc}"
            }

    def _dispatch_sendgrid(self, to_email: str, recipient_name: str, subject: str, html_content: str, plain_text: str, code: str) -> Dict[str, Any]:
        api_key = getattr(settings, "SENDGRID_API_KEY", "").strip()
        if not api_key:
            return {"success": False, "provider": "sendgrid", "message": "SENDGRID_API_KEY is not configured in environment."}

        from_name, from_email = self._get_from_identity("sendgrid")
        clean_recipient_name = _clean_name(recipient_name, default="Investigator")
        payload = {
            "personalizations": [{"to": [{"email": to_email, "name": clean_recipient_name}]}],
            "from": {"email": from_email, "name": from_name},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": plain_text},
                {"type": "text/html", "value": html_content}
            ]
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        timeout = float(getattr(settings, "EMAIL_HTTP_TIMEOUT_SECONDS", 10.0))
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post("https://api.sendgrid.com/v3/mail/send", headers=headers, json=payload)
                if resp.status_code in (200, 201, 202):
                    logger.info(f"[EmailDispatcher:SendGrid] Verification email dispatched to {mask_email(to_email)}")
                    return {
                        "success": True,
                        "provider": "sendgrid",
                        "message": f"Verification email dispatched via SendGrid to {to_email}."
                    }
                err_text = _sanitize_error_text(resp.text, code)
                try:
                    err_json = resp.json()
                    errs = err_json.get("errors", [])
                    if errs and isinstance(errs, list):
                        err_text = _sanitize_error_text(errs[0].get("message", resp.text), code)
                except Exception:
                    pass
                logger.error(f"[EmailDispatcher:SendGrid] HTTP {resp.status_code}: {err_text}")
                return {
                    "success": False,
                    "provider": "sendgrid",
                    "message": f"SendGrid delivery failed (HTTP {resp.status_code}): {err_text}"
                }
        except Exception as exc:
            safe_exc = _sanitize_error_text(exc, code)
            logger.error(f"[EmailDispatcher:SendGrid] Exception: {safe_exc}")
            return {
                "success": False,
                "provider": "sendgrid",
                "message": f"SendGrid request error: {safe_exc}"
            }

    def _dispatch_mailgun(self, to_email: str, recipient_name: str, subject: str, html_content: str, plain_text: str, code: str) -> Dict[str, Any]:
        api_key = getattr(settings, "MAILGUN_API_KEY", "").strip()
        domain = getattr(settings, "MAILGUN_DOMAIN", "").strip()
        if not (api_key and domain):
            return {"success": False, "provider": "mailgun", "message": "MAILGUN_API_KEY and MAILGUN_DOMAIN are required."}

        from_name, from_email = self._get_from_identity("mailgun")
        clean_recipient_name = _clean_name(recipient_name, default="Investigator")
        from_header = f"{from_name} <{from_email}>" if from_name else from_email
        to_header = f"{clean_recipient_name} <{to_email}>" if clean_recipient_name else to_email
        data = {
            "from": from_header,
            "to": [to_header],
            "subject": subject,
            "text": plain_text,
            "html": html_content
        }
        timeout = float(getattr(settings, "EMAIL_HTTP_TIMEOUT_SECONDS", 10.0))
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(
                    f"https://api.mailgun.net/v3/{domain}/messages",
                    auth=("api", api_key),
                    data=data
                )
                if resp.status_code == 200:
                    logger.info(f"[EmailDispatcher:Mailgun] Verification email dispatched to {mask_email(to_email)}")
                    return {
                        "success": True,
                        "provider": "mailgun",
                        "message": f"Verification email dispatched via Mailgun to {to_email}."
                    }
                err_text = _sanitize_error_text(resp.text, code)
                logger.error(f"[EmailDispatcher:Mailgun] HTTP {resp.status_code}: {err_text}")
                return {
                    "success": False,
                    "provider": "mailgun",
                    "message": f"Mailgun delivery failed (HTTP {resp.status_code}): {err_text}"
                }
        except Exception as exc:
            safe_exc = _sanitize_error_text(exc, code)
            logger.error(f"[EmailDispatcher:Mailgun] Exception: {safe_exc}")
            return {
                "success": False,
                "provider": "mailgun",
                "message": f"Mailgun request error: {safe_exc}"
            }

    def _dispatch_webhook(self, to_email: str, recipient_name: str, subject: str, html_content: str, plain_text: str, code: str) -> Dict[str, Any]:
        url = getattr(settings, "EMAIL_WEBHOOK_URL", "").strip()
        if not url:
            return {"success": False, "provider": "webhook", "message": "EMAIL_WEBHOOK_URL is not configured."}

        clean_recipient_name = _clean_name(recipient_name, default="Investigator")
        payload = {
            "to": to_email,
            "recipient_name": clean_recipient_name,
            "code": code,
            "subject": subject,
            "text": plain_text,
            "html": html_content
        }
        timeout = float(getattr(settings, "EMAIL_HTTP_TIMEOUT_SECONDS", 10.0))
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(url, json=payload)
                if resp.status_code in (200, 201, 202, 204):
                    logger.info(f"[EmailDispatcher:Webhook] Verification payload dispatched via webhook for {mask_email(to_email)}")
                    return {
                        "success": True,
                        "provider": "webhook",
                        "message": f"Verification email payload dispatched via Webhook to {to_email}."
                    }
                err_text = _sanitize_error_text(resp.text, code)
                logger.error(f"[EmailDispatcher:Webhook] HTTP {resp.status_code}: {err_text}")
                return {
                    "success": False,
                    "provider": "webhook",
                    "message": f"Webhook delivery failed (HTTP {resp.status_code}): {err_text}"
                }
        except Exception as exc:
            safe_exc = _sanitize_error_text(exc, code)
            logger.error(f"[EmailDispatcher:Webhook] Exception: {safe_exc}")
            return {
                "success": False,
                "provider": "webhook",
                "message": f"Webhook request error: {safe_exc}"
            }

    def _dispatch_smtp(self, to_email: str, recipient_name: str, subject: str, html_content: str, plain_text: str, code: str) -> Dict[str, Any]:
        if not (settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD):
            logger.warning(f"[EmailDispatcher:unconfigured] SMTP is not configured in .env. Email to {mask_email(to_email)} could not be sent.")
            return {
                "success": False,
                "provider": "unconfigured_smtp",
                "message": (
                    "SMTP credentials not configured in .env. "
                    "Note: Render free tier blocks outbound SMTP ports 25, 465, and 587. "
                    "Use an HTTPS email API (e.g. RESEND_API_KEY or BREVO_API_KEY) to send via port 443."
                )
            }

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        from_name, from_email = self._get_from_identity("smtp")
        clean_recipient_name = _clean_name(recipient_name, default="")
        sender_header = f"{from_name} <{from_email}>" if from_name else from_email
        msg["From"] = sender_header
        msg["To"] = f"{clean_recipient_name} <{to_email}>" if clean_recipient_name else to_email

        msg.attach(MIMEText(plain_text, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        timeout = min(getattr(settings, "SMTP_TIMEOUT_SECONDS", 10), 8)
        try:
            if settings.SMTP_USE_SSL:
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout)
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout)
                if settings.SMTP_USE_TLS:
                    server.starttls()

            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

            server.send_message(msg)
            server.quit()
            logger.info(f"[EmailDispatcher:SMTP] Real verification email successfully sent to {mask_email(to_email)}")
            return {
                "success": True,
                "provider": "smtp",
                "message": f"Verification email dispatched to {to_email}."
            }
        except Exception as exc:
            err_text = _sanitize_error_text(str(exc), code)
            logger.error(f"[EmailDispatcher:SMTP] Failed to send email to {mask_email(to_email)}: {err_text}")
            is_blocked = any(k in err_text.lower() for k in ["timed out", "connection refused", "errno 110", "errno 111", "network is unreachable"])
            if is_blocked:
                msg_out = (
                    f"SMTP connection to {settings.SMTP_HOST}:{settings.SMTP_PORT} failed ({err_text}). "
                    "Render free web services block outbound SMTP ports 25, 465, and 587. "
                    "Please set RESEND_API_KEY or BREVO_API_KEY in Render environment variables to send emails over HTTPS (port 443)."
                )
            else:
                msg_out = f"SMTP dispatch failed: {err_text}"
            return {
                "success": False,
                "provider": "smtp",
                "message": msg_out
            }

    def send_verification_email(self, to_email: str, recipient_name: str, code: str) -> Dict[str, Any]:
        """
        Constructs and dispatches a verification email.
        Supports HTTPS Email APIs (Resend, Brevo, SendGrid, Mailgun, Webhook) over port 443
        as well as enterprise SMTP, with fallback to an in-memory test outbox.
        """
        to_email = to_email.strip().lower()
        subject = f"CyberScope Verification Code: {code}"
        plain_text = self._build_plain_text(recipient_name, code)
        html_content = self._build_html_template(recipient_name, code)
        is_prod = getattr(settings, "APP_ENV", "").strip().lower() == "production"

        if is_prod:
            if getattr(settings, "VERIFICATION_MOCK_DISPATCH", False):
                raise RuntimeError("VERIFICATION_MOCK_DISPATCH is refused in production mode")
            webhook_url = getattr(settings, "EMAIL_WEBHOOK_URL", "").strip()
            if webhook_url and not webhook_url.startswith("https://"):
                raise RuntimeError("EMAIL_WEBHOOK_URL must start with https:// in production mode")

        # Check if automated test mode (unless explicitly forced via _FORCE_LIVE_SMTP or _FORCE_LIVE_EMAIL)
        is_test = _is_test_mode() and not getattr(settings, "_FORCE_LIVE_SMTP", False) and not getattr(settings, "_FORCE_LIVE_EMAIL", False) and not is_prod
        if is_test:
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "to_email": to_email,
                "recipient_name": recipient_name,
                "code": code,
                "subject": subject,
                "plain_text": plain_text,
                "html_content": html_content
            }
            self.dispatched_emails.append(record)
            logger.info(f"[EmailDispatcher:mock] Verification email recorded in test outbox for {mask_email(to_email)}")
            return {
                "success": True,
                "provider": "mock",
                "message": f"Verification email recorded in test outbox for {to_email}."
            }

        provider = self._detect_provider()

        if is_prod and provider == "mock":
            raise RuntimeError("EMAIL_PROVIDER='mock' is refused in production mode")

        if getattr(settings, "APP_ENV", "") == "development":
            logger.info(f"[DEV ONLY] Verification code for {mask_email(to_email)}: {code}")

        if provider == "resend":
            result = self._dispatch_resend(to_email, recipient_name, subject, html_content, plain_text, code)
        elif provider == "brevo":
            result = self._dispatch_brevo(to_email, recipient_name, subject, html_content, plain_text, code)
        elif provider == "sendgrid":
            result = self._dispatch_sendgrid(to_email, recipient_name, subject, html_content, plain_text, code)
        elif provider == "mailgun":
            result = self._dispatch_mailgun(to_email, recipient_name, subject, html_content, plain_text, code)
        elif provider == "webhook":
            result = self._dispatch_webhook(to_email, recipient_name, subject, html_content, plain_text, code)
        elif provider == "smtp":
            result = self._dispatch_smtp(to_email, recipient_name, subject, html_content, plain_text, code)
        elif provider == "mock":
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "to_email": to_email,
                "recipient_name": recipient_name,
                "code": code,
                "subject": subject,
                "plain_text": plain_text,
                "html_content": html_content
            }
            self.dispatched_emails.append(record)
            result = {
                "success": True,
                "provider": "mock",
                "message": f"Verification email recorded in mock outbox for {to_email}."
            }
        else:
            missing_vars = []
            if not getattr(settings, "RESEND_API_KEY", ""):
                missing_vars.append("RESEND_API_KEY")
            if not getattr(settings, "BREVO_API_KEY", ""):
                missing_vars.append("BREVO_API_KEY")
            if not getattr(settings, "SENDGRID_API_KEY", ""):
                missing_vars.append("SENDGRID_API_KEY")
            if not getattr(settings, "MAILGUN_API_KEY", ""):
                missing_vars.append("MAILGUN_API_KEY")
            if not getattr(settings, "SMTP_HOST", ""):
                missing_vars.append("SMTP_HOST")
            missing_str = ", ".join(missing_vars)
            logger.warning(
                f"[EmailDispatcher:unconfigured] Missing email configuration for {mask_email(to_email)}. "
                f"Missing variables: {missing_str}"
            )
            result = {
                "success": False,
                "provider": "unconfigured",
                "message": (
                    "Email provider not configured. Render free tier blocks outbound SMTP ports 25, 465, and 587. "
                    "Please set RESEND_API_KEY or BREVO_API_KEY in Render environment variables to send over HTTPS (port 443)."
                )
            }

        if not result.get("success") and is_prod:
            result["message"] = GENERIC_DELIVERY_ERROR_MESSAGE

        return result


class SmsDispatcher:
    """
    Handles SMS verification dispatch with multi-provider failover:
    Supports Twilio, Fast2SMS, custom Webhook, and in-memory test recording.
    """

    def __init__(self):
        self.dispatched_sms: List[Dict[str, Any]] = []

    def send_verification_sms(self, to_phone: str, code: str) -> Dict[str, Any]:
        """
        Dispatches a 6-digit OTP code to the recipient's phone number.
        """
        to_phone = to_phone.strip()
        message = f"Your CyberScope verification code is: {code}. Valid for 10 minutes. Do not share this code."
        provider = settings.SMS_PROVIDER.lower() if settings.SMS_PROVIDER else "twilio"

        # Check if automated test mode (unless explicitly forced via _FORCE_LIVE_SMS)
        is_test = _is_test_mode() and not getattr(settings, "_FORCE_LIVE_SMS", False)
        if is_test:
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "to_phone": to_phone,
                "code": code,
                "message": message,
                "provider": "mock"
            }
            self.dispatched_sms.append(record)
            logger.info(f"[SmsDispatcher:mock] Verification SMS recorded in test outbox for {mask_phone(to_phone)}")
            return {
                "success": True,
                "provider": "mock",
                "message": f"Verification SMS recorded in test outbox for {to_phone}."
            }

        # Provider: Twilio
        if provider == "twilio":
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            from_num = settings.TWILIO_FROM_NUMBER
            messaging_service_sid = settings.TWILIO_MESSAGING_SERVICE_SID

            if not (account_sid and auth_token and (from_num or messaging_service_sid)):
                logger.warning(f"[SmsDispatcher:unconfigured] Twilio SMS credentials missing in .env. SMS to {mask_phone(to_phone)} not sent.")
                return {
                    "success": False,
                    "provider": "unconfigured_twilio",
                    "message": "Twilio SMS credentials not configured in .env. Please configure TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER."
                }

            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
            data: Dict[str, str] = {
                "To": to_phone,
                "Body": message
            }
            if from_num:
                data["From"] = from_num
            elif messaging_service_sid:
                data["MessagingServiceSid"] = messaging_service_sid

            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(url, auth=(account_sid, auth_token), data=data)
                    if resp.status_code in (200, 201):
                        logger.info(f"[SmsDispatcher:Twilio] SMS dispatched to {mask_phone(to_phone)}")
                        return {
                            "success": True,
                            "provider": "twilio",
                            "message": f"Verification SMS sent via Twilio to {to_phone}."
                        }
                    safe_err = _sanitize_error_text(resp.text, code)
                    logger.error(f"[SmsDispatcher:Twilio] Twilio returned HTTP {resp.status_code}: {safe_err}")
                    return {
                        "success": False,
                        "provider": "twilio",
                        "message": f"Twilio SMS delivery failed (HTTP {resp.status_code}): {safe_err}"
                    }
            except Exception as exc:
                safe_exc = _sanitize_error_text(exc, code)
                logger.error(f"[SmsDispatcher:Twilio] Exception during dispatch: {safe_exc}")
                return {
                    "success": False,
                    "provider": "twilio",
                    "message": f"Twilio dispatch error: {safe_exc}"
                }

        # Provider: Fast2SMS
        if provider == "fast2sms":
            key = settings.FAST2SMS_API_KEY
            if not key:
                logger.warning(f"[SmsDispatcher:unconfigured] Fast2SMS API key missing in .env. SMS to {mask_phone(to_phone)} not sent.")
                return {
                    "success": False,
                    "provider": "unconfigured_fast2sms",
                    "message": "Fast2SMS API key not configured in .env. Please configure FAST2SMS_API_KEY."
                }

            # Extract clean 10-digit number for Fast2SMS Indian gateway
            phone_digits = re.sub(r"\D", "", to_phone)
            if len(phone_digits) > 10:
                phone_digits = phone_digits[-10:]

            url = "https://www.fast2sms.com/dev/bulkV2"
            headers = {
                "authorization": key,
                "Content-Type": "application/json"
            }
            payload = {
                "route": "otp",
                "variables_values": code,
                "numbers": phone_digits
            }

            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        res_data = resp.json()
                        if res_data.get("return") is True:
                            logger.info(f"[SmsDispatcher:Fast2SMS] OTP dispatched to {mask_phone(phone_digits)}")
                            return {
                                "success": True,
                                "provider": "fast2sms",
                                "message": f"Verification SMS sent via Fast2SMS to {to_phone}."
                            }
                        safe_msg = _sanitize_error_text(res_data.get('message', 'Unknown error'), code)
                        return {
                            "success": False,
                            "provider": "fast2sms",
                            "message": f"Fast2SMS rejected dispatch: {safe_msg}"
                        }
                    safe_err = _sanitize_error_text(resp.text, code)
                    logger.error(f"[SmsDispatcher:Fast2SMS] Fast2SMS returned HTTP {resp.status_code}: {safe_err}")
                    return {
                        "success": False,
                        "provider": "fast2sms",
                        "message": f"Fast2SMS returned HTTP {resp.status_code}: {safe_err}"
                    }
            except Exception as exc:
                safe_exc = _sanitize_error_text(exc, code)
                logger.error(f"[SmsDispatcher:Fast2SMS] Exception: {safe_exc}")
                return {
                    "success": False,
                    "provider": "fast2sms",
                    "message": f"Fast2SMS dispatch error: {safe_exc}"
                }

        # Provider: Webhook
        if provider == "webhook":
            url = settings.SMS_WEBHOOK_URL
            if not url:
                return {
                    "success": False,
                    "provider": "unconfigured_webhook",
                    "message": "SMS Webhook URL not configured in .env. Please configure SMS_WEBHOOK_URL."
                }
            payload = {
                "to": to_phone,
                "code": code,
                "message": message
            }
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code in (200, 201, 202, 204):
                        logger.info(f"[SmsDispatcher:Webhook] Dispatched SMS payload via webhook for {mask_phone(to_phone)}")
                        return {
                            "success": True,
                            "provider": "webhook",
                            "message": f"Verification SMS dispatched via Webhook to {to_phone}."
                        }
                    safe_err = _sanitize_error_text(resp.text, code)
                    logger.error(f"[SmsDispatcher:Webhook] Webhook returned HTTP {resp.status_code}: {safe_err}")
                    return {
                        "success": False,
                        "provider": "webhook",
                        "message": f"Webhook returned HTTP {resp.status_code}: {safe_err}"
                    }
            except Exception as exc:
                safe_exc = _sanitize_error_text(exc, code)
                logger.error(f"[SmsDispatcher:Webhook] Exception: {safe_exc}")
                return {
                    "success": False,
                    "provider": "webhook",
                    "message": f"Webhook dispatch error: {safe_exc}"
                }

        # Unconfigured / Mock outside test environment
        logger.warning(f"[SmsDispatcher:unconfigured] SMS provider '{provider}' credentials are not configured in .env.")
        return {
            "success": False,
            "provider": f"unconfigured_{provider}",
            "message": f"SMS provider '{provider}' credentials are not configured in .env. Please set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER or FAST2SMS_API_KEY."
        }


class NotificationService:
    """
    Singleton facade providing unified email and SMS verification dispatch
    capabilities across the CyberScope platform.
    """

    def __init__(self):
        self.email_dispatcher = EmailDispatcher()
        self.sms_dispatcher = SmsDispatcher()

    def send_verification_email(self, to_email: str, recipient_name: str, code: str) -> Dict[str, Any]:
        """
        Sends an official verification email with branded HTML and plain-text fallback.
        """
        return self.email_dispatcher.send_verification_email(to_email, recipient_name, code)

    def send_email_otp(self, to_email: str, otp_code: str, user_name: str = "") -> Dict[str, Any]:
        """
        Alias for sending email OTP.
        """
        return self.send_verification_email(to_email, user_name, otp_code)

    def send_verification_sms(self, to_phone: str, code: str) -> Dict[str, Any]:
        """
        Sends a verification SMS containing the 6-digit OTP code.
        """
        return self.sms_dispatcher.send_verification_sms(to_phone, code)

    def get_test_outbox(self) -> Dict[str, Any]:
        """
        Retrieves all dispatched emails and SMS records in the in-memory test outbox.
        Useful for automated testing and CI verification.
        """
        return {
            "emails": list(self.email_dispatcher.dispatched_emails),
            "sms": list(self.sms_dispatcher.dispatched_sms),
        }

    def clear_test_outbox(self) -> None:
        """
        Clears the in-memory test outbox.
        """
        self.email_dispatcher.dispatched_emails.clear()
        self.sms_dispatcher.dispatched_sms.clear()

    @property
    def dispatched_emails(self) -> List[Dict[str, Any]]:
        return self.email_dispatcher.dispatched_emails

    @property
    def dispatched_sms(self) -> List[Dict[str, Any]]:
        return self.sms_dispatcher.dispatched_sms


notification_service = NotificationService()
