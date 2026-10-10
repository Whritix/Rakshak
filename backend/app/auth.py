"""Sovereign Authentication & JWT Token Management for Project Rakshak.

Security hardening:
- JWT secret loaded from RAKSHAK_JWT_SECRET env var (falls back to a random
  per-process secret so the hardcoded default is never silently used in
  production without an env var being set).
- PBKDF2-HMAC-SHA256, 200,000 iterations (NIST 2024 recommendation).
- Constant-time comparison via hmac.compare_digest (prevents timing attacks).
- Unique jti (JWT ID) claim included for token traceability & revocation.
- str.removeprefix('Bearer ') for robust, clean token extraction.
- Backward-compatible verification fallback for legacy 100k hashes.
"""
from __future__ import annotations
import os
import sys
import hmac
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, Header, status

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ── Secret Key Configuration ───────────────────────────────────────────────
# MUST be set via RAKSHAK_JWT_SECRET environment variable in production.
# If the env var is absent, a cryptographically secure 64-byte random key is
# generated per process, with an explicit warning printed to stderr.
_ENV_SECRET = os.getenv('RAKSHAK_JWT_SECRET', '')
if _ENV_SECRET:
    SECRET_KEY = _ENV_SECRET
else:
    SECRET_KEY = secrets.token_hex(64)  # 512-bit random key
    print(
        '[RAKSHAK AUTH WARNING] RAKSHAK_JWT_SECRET env var not set. '
        'Generated a random 64-byte per-process secret. Set RAKSHAK_JWT_SECRET in .env for persistent sessions.',
        file=sys.stderr
    )

ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24-hour tactical shift
PBKDF2_ITERATIONS = 200_000            # NIST 2024 recommendation
LEGACY_PBKDF2_ITERATIONS = 100_000     # Backward compatibility fallback

# ── Login Rate Limiting (Sliding Window) ───────────────────────────────────
import time
from collections import defaultdict

_LOGIN_ATTEMPTS: dict[str, list[float]] = defaultdict(list)
_MAX_FAILED_ATTEMPTS = 5
_LOCKOUT_WINDOW_SECONDS = 60.0


def check_login_rate_limit(identifier: str) -> None:
    """Enforce rolling-window rate limiting on authentication attempts.

    Raises:
        HTTPException(429): If 5 or more failed attempts occurred in the past 60s.
    """
    now = time.time()
    attempts = [t for t in _LOGIN_ATTEMPTS[identifier] if now - t < _LOCKOUT_WINDOW_SECONDS]
    _LOGIN_ATTEMPTS[identifier] = attempts
    if len(attempts) >= _MAX_FAILED_ATTEMPTS:
        retry_after = int(_LOCKOUT_WINDOW_SECONDS - (now - attempts[0]))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Security lockout: Too many failed authentication attempts. Locked for {max(1, retry_after)} seconds.",
            headers={"Retry-After": str(max(1, retry_after))}
        )


def record_failed_login(identifier: str) -> None:
    """Record timestamp of a failed login attempt."""
    now = time.time()
    _LOGIN_ATTEMPTS[identifier].append(now)


def reset_login_attempts(identifier: str) -> None:
    """Reset attempt counter upon successful authentication."""
    if identifier in _LOGIN_ATTEMPTS:
        del _LOGIN_ATTEMPTS[identifier]


def hash_password(
    password: str,
    salt: Optional[str] = None,
    iterations: int = PBKDF2_ITERATIONS
) -> tuple[str, str]:
    """Secure PBKDF2-HMAC-SHA256 password hashing with random salt.

    Args:
        password: Plain-text password string.
        salt: Optional hex salt string. If omitted, a random 16-byte salt is generated.
        iterations: Number of PBKDF2 iterations. Defaults to 200,000 (NIST 2024).

    Returns:
        Tuple of (password_hash_hex, salt_hex).
    """
    if not salt:
        salt = os.urandom(16).hex()
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations
    ).hex()
    return pwd_hash, salt


def verify_password(plain_password: str, password_hash: str, salt: str) -> bool:
    """Constant-time password verification to prevent timing attacks.

    Verifies against current 200,000 iterations, with backward-compatible
    fallback to 100,000 iterations for pre-existing database records.

    Args:
        plain_password: Plain-text password candidate from login request.
        password_hash: Stored hex password hash.
        salt: Stored hex salt string.

    Returns:
        True if password matches, False otherwise.
    """
    # Check with current standard (200k iterations)
    computed_hash_200k, _ = hash_password(plain_password, salt, iterations=PBKDF2_ITERATIONS)
    if hmac.compare_digest(computed_hash_200k, password_hash):
        return True

    # Fallback to legacy standard (100k iterations)
    computed_hash_100k, _ = hash_password(plain_password, salt, iterations=LEGACY_PBKDF2_ITERATIONS)
    return hmac.compare_digest(computed_hash_100k, password_hash)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a cryptographically signed HS256 JWT access token.

    Embeds standard claims (exp, iat) and a unique jti (JWT ID) token identifier
    for token rotation and revocation tracking.

    Args:
        data: Custom claims payload (e.g. sub, username, role, clearance).
        expires_delta: Optional custom token expiration duration.

    Returns:
        Encoded and signed JWT string.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        'exp': expire,
        'iat': now,
        'jti': secrets.token_hex(8)  # 64-bit unique token ID
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and cryptographically validate a JWT access token.

    Args:
        token: Raw JWT string.

    Returns:
        Decoded token payload dictionary.

    Raises:
        HTTPException (401): If token is expired or has invalid signature.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Tactical authorization token has expired. Please re-authenticate.',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid security credentials. Access denied.',
            headers={'WWW-Authenticate': 'Bearer'},
        )


def get_current_user_optional(
    authorization: Optional[str] = Header(None),
) -> Optional[dict]:
    """Extract and verify the authenticated user from a Bearer Authorization header.

    Uses str.removeprefix('Bearer ') for clean token isolation. Returns None
    (does not raise) if the header is absent or invalid, allowing endpoints to
    serve public data while enriching responses for authenticated operators.

    Args:
        authorization: HTTP Authorization header value (e.g. 'Bearer <token>').

    Returns:
        Decoded operator payload dictionary if valid, or None.
    """
    if not authorization or not authorization.startswith('Bearer '):
        return None
    token = authorization.removeprefix('Bearer ').strip()
    try:
        return decode_access_token(token)
    except HTTPException:
        return None
