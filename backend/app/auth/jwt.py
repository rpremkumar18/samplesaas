"""JWT creation/verification and password hashing helpers."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.config import get_settings
from app.exceptions import UnauthorizedError

ACCESS = "access"
REFRESH = "refresh"
OAUTH_STATE = "oauth_state"


BCRYPT_MAX_BYTES = 72


def _password_bytes(password: str) -> bytes:
    """Encode a password, truncated to bcrypt's 72-byte limit (bcrypt 5 raises above it)."""
    return password.encode("utf-8")[:BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    """Hash a plain password with bcrypt."""
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Check a plain password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(_password_bytes(password), hashed.encode("utf-8"))
    except ValueError:
        return False


def _encode(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra: dict[str, Any] | None = None,
) -> tuple[str, datetime]:
    settings = get_settings()
    expires_at = datetime.now(UTC) + expires_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "exp": expires_at,
        "iat": datetime.now(UTC),
        "jti": secrets.token_urlsafe(16),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM), expires_at


def create_access_token(user_id: int) -> str:
    """Create a short-lived access token."""
    delta = timedelta(minutes=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES)
    return _encode(str(user_id), ACCESS, delta)[0]


def create_refresh_token(user_id: int) -> tuple[str, datetime]:
    """Create a refresh token; returns (token, expires_at)."""
    delta = timedelta(days=get_settings().REFRESH_TOKEN_EXPIRE_DAYS)
    return _encode(str(user_id), REFRESH, delta)


def create_state_token(nonce: str) -> str:
    """Create a signed OAuth state token (10 minute lifetime)."""
    return _encode("oauth", OAUTH_STATE, timedelta(minutes=10), {"nonce": nonce})[0]


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """Decode and validate a token of the expected type; raise 401 otherwise."""
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub", "type"]},
        )
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc
    if payload.get("type") != expected_type or not payload.get("sub"):
        raise UnauthorizedError("Invalid token type")
    return payload


def hash_token(token: str) -> str:
    """SHA-256 digest used to store refresh tokens at rest."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
