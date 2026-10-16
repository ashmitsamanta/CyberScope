"""
Rate Limiting & Abuse Protection Module for CyberScope.

Security / Architecture Limitation Note:
Limits are in-memory (single instance) and a client who calls the Render URL directly
can spoof X-Forwarded-For, which is why the per-email and global caps exist.
"""

import time
import threading
from typing import Dict, List, Tuple, Optional, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded


def get_client_ip(request: Request) -> str:
    """
    Extracts the client IP address. Uses the first IP in X-Forwarded-For when present
    (e.g. behind Vercel and Render proxies), otherwise falls back to request.client.host.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # First IP in comma-separated list is the original client IP
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def get_user_id_key(request: Request) -> str:
    """
    Key function for /api/chat: limits per authenticated user id.
    Extracts user id from request.state.user or JWT payload.
    Falls back to client IP if not authenticated.
    """
    user = getattr(request.state, "user", None)
    if user and user.get("id"):
        return f"user:{user['id']}"

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        try:
            import jwt
            payload = jwt.decode(token, options={"verify_signature": False})
            sub = payload.get("sub") or payload.get("id")
            if sub:
                return f"user:{sub}"
        except Exception:
            pass

    return get_client_ip(request)


# Limiter instance wired across FastAPI endpoints
limiter = Limiter(key_func=get_client_ip, headers_enabled=False)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom exception handler for slowapi RateLimitExceeded.
    Returns HTTP 429 with JSON body {"detail": "...", "code": "RATE_LIMITED"}
    and a Retry-After header.
    """
    retry_after = "60"
    view_rate_limit = getattr(request.state, "view_rate_limit", None)
    lim = getattr(request.app.state, "limiter", None)
    if lim and view_rate_limit:
        try:
            window_stats = lim.limiter.get_window_stats(view_rate_limit[0], *view_rate_limit[1])
            reset_in = 1 + window_stats[0]
            retry_after = str(max(1, int(reset_in - time.time())))
        except Exception:
            pass

    response = JSONResponse(
        status_code=429,
        content={
            "detail": f"Rate limit exceeded: {exc.detail}",
            "code": "RATE_LIMITED"
        }
    )
    response.headers["Retry-After"] = retry_after
    return response


class EmailRateLimiter:
    """
    In-memory sliding-window rate limiter per target email address.
    Enforces at most max_sends per window_seconds (default 3 per hour).
    Maintains TTL cleanup and a hard capacity cap (max_keys) to prevent unbounded memory growth.

    Limitation Note:
    Limits are in-memory (single instance) and a client who calls the Render URL directly
    can spoof X-Forwarded-For, which is why the per-email and global caps exist.
    """

    def __init__(self, max_sends: int = 3, window_seconds: float = 3600.0, max_keys: int = 10000):
        self.max_sends = max_sends
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self._sends: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def _cleanup(self, now: float) -> None:
        cutoff = now - self.window_seconds
        expired_keys = [k for k, timestamps in self._sends.items() if not any(t > cutoff for t in timestamps)]
        for k in expired_keys:
            del self._sends[k]

        if len(self._sends) > self.max_keys:
            sorted_keys = sorted(self._sends.keys(), key=lambda k: max(self._sends[k]) if self._sends[k] else 0)
            to_remove = len(self._sends) - self.max_keys
            for k in sorted_keys[:to_remove]:
                del self._sends[k]

    def check_and_record(self, email: str) -> Tuple[bool, int]:
        now = time.time()
        cutoff = now - self.window_seconds
        normalized = email.strip().lower()

        with self._lock:
            if len(self._sends) >= self.max_keys or len(self._sends) % 100 == 0:
                self._cleanup(now)

            timestamps = [t for t in self._sends.get(normalized, []) if t > cutoff]
            if len(timestamps) >= self.max_sends:
                oldest = min(timestamps)
                retry_after = max(1, int(oldest + self.window_seconds - now))
                return False, retry_after

            timestamps.append(now)
            self._sends[normalized] = timestamps
            return True, 0

    def reset_for_tests(self) -> None:
        with self._lock:
            self._sends.clear()


class DailyEmailCapTracker:
    """
    Global daily email dispatch cap tracker.
    Prevents exceeding third-party provider quotas even if per-IP and per-email limits are bypassed.
    """

    def __init__(self):
        self._sends: List[float] = []
        self._lock = threading.Lock()

    def is_exceeded(self, cap: int) -> bool:
        if cap <= 0:
            return False
        now = time.time()
        cutoff = now - 86400.0
        with self._lock:
            self._sends = [t for t in self._sends if t > cutoff]
            return len(self._sends) >= cap

    def record_send(self) -> None:
        with self._lock:
            self._sends.append(time.time())

    def reset_for_tests(self) -> None:
        with self._lock:
            self._sends.clear()


email_rate_limiter = EmailRateLimiter(max_sends=3, window_seconds=3600.0, max_keys=10000)
daily_email_tracker = DailyEmailCapTracker()
