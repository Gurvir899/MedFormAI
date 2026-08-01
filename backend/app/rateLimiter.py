"""
Simple in-memory rate limiter for auth endpoints.

Prevents brute-force attacks on login/register.
IP-based tracking with sliding window.

For production: replace with Redis-backed limiter (flask-limiter + redis).
"""

import time
from collections import defaultdict, deque
from functools import wraps
from flask import request, jsonify

# IP → list of timestamps
_loginAttempts: dict[str, deque] = defaultdict(deque)
_registerAttempts: dict[str, deque] = defaultdict(deque)

# Limits
LOGIN_MAX = 5          # max 5 attempts
LOGIN_WINDOW = 60      # per 60 seconds
REGISTER_MAX = 3       # max 3 registrations
REGISTER_WINDOW = 3600 # per hour


def _getClientIp() -> str:
    """Get client IP, accounting for proxy headers."""
    if request.headers.get("X-Forwarded-For"):
        return request.headers["X-Forwarded-For"].split(",")[0].strip()
    return request.remote_addr or "unknown"


def _checkRate(store: dict, ip: str, maxCount: int, windowSec: int) -> tuple[bool, int]:
    """
    Check if IP is within rate limit.
    Returns (allowed, retryAfterSec).
    """
    now = time.time()
    attempts = store[ip]

    # Remove expired entries
    while attempts and now - attempts[0] > windowSec:
        attempts.popleft()

    if len(attempts) >= maxCount:
        oldest = attempts[0]
        retryAfter = int(windowSec - (now - oldest)) + 1
        return False, max(1, retryAfter)

    attempts.append(now)
    return True, 0


def rateLimitLogin(fn):
    """Decorator: limit login attempts per IP."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        ip = _getClientIp()
        allowed, retryAfter = _checkRate(_loginAttempts, ip, LOGIN_MAX, LOGIN_WINDOW)
        if not allowed:
            response = jsonify({
                "status": "error",
                "message": f"Too many login attempts. Try again in {retryAfter}s."
            })
            response.status_code = 429
            response.headers["Retry-After"] = str(retryAfter)
            return response
        return fn(*args, **kwargs)
    return wrapper


def rateLimitRegister(fn):
    """Decorator: limit registration attempts per IP."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        ip = _getClientIp()
        allowed, retryAfter = _checkRate(_registerAttempts, ip, REGISTER_MAX, REGISTER_WINDOW)
        if not allowed:
            response = jsonify({
                "status": "error",
                "message": f"Too many registration attempts. Try again in {retryAfter}s."
            })
            response.status_code = 429
            response.headers["Retry-After"] = str(retryAfter)
            return response
        return fn(*args, **kwargs)
    return wrapper
