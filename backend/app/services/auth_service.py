"""Authentication business logic."""

import logging
import threading
import time
from datetime import UTC, datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.jwt import (
    REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.exceptions import ConflictError, RateLimitError, UnauthorizedError
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import TokenPair, UserCreate, UserUpdate

logger = logging.getLogger(__name__)

# Used to equalise timing when the email is unknown.
_DUMMY_HASH = hash_password("dummy-password-for-timing")


# Per-email failed-login throttle. NOTE: in-process memory only, so it is per worker and
# resets on restart; use a shared store (e.g. Redis) for a multi-worker deployment.
MAX_LOGIN_FAILURES = 5
LOGIN_FAILURE_WINDOW_SECONDS = 15 * 60
_MAX_TRACKED_EMAILS = 10_000
_failures: dict[str, list[float]] = {}
_failures_lock = threading.Lock()


def reset_login_throttle() -> None:
    """Forget all recorded failures (used by tests)."""
    with _failures_lock:
        _failures.clear()


def _recent(key: str, now: float) -> list[float]:
    recent = [t for t in _failures.get(key, []) if now - t < LOGIN_FAILURE_WINDOW_SECONDS]
    if recent:
        _failures[key] = recent
    else:
        _failures.pop(key, None)
    return recent


def _check_throttle(key: str) -> None:
    with _failures_lock:
        if len(_recent(key, time.monotonic())) >= MAX_LOGIN_FAILURES:
            raise RateLimitError("Too many failed login attempts. Try again later.")


def _record_failure(key: str) -> None:
    now = time.monotonic()
    with _failures_lock:
        if len(_failures) >= _MAX_TRACKED_EMAILS and key not in _failures:
            for k in list(_failures):
                _recent(k, now)
            if len(_failures) >= _MAX_TRACKED_EMAILS:
                _failures.pop(next(iter(_failures)))
        _failures.setdefault(key, []).append(now)


def _clear_failures(key: str) -> None:
    with _failures_lock:
        _failures.pop(key, None)


def get_user_by_email(db: Session, email: str) -> User | None:
    """Look up a user by (case-insensitive) email."""
    return db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()


def issue_tokens(db: Session, user: User) -> TokenPair:
    """Create an access/refresh pair and persist the hashed refresh token."""
    user_id = int(user.id)
    refresh, expires_at = create_refresh_token(user_id)
    db.add(RefreshToken(user_id=user_id, token=hash_token(refresh), expires_at=expires_at))
    db.commit()
    return TokenPair(access_token=create_access_token(user_id), refresh_token=refresh)


def register_user(db: Session, data: UserCreate) -> User:
    """Create a new local user; 409 if the email exists."""
    email = data.email.lower()
    if get_user_by_email(db, email):
        raise ConflictError("Email already registered")
    user = User(
        email=email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Email already registered") from exc
    db.refresh(user)
    logger.info("User registered: id=%s", user.id)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    """Verify credentials and return the user, else 401 (429 if the email is throttled)."""
    key = email.lower()
    _check_throttle(key)
    user = get_user_by_email(db, key)
    # Accounts without a password (Google-only, or cleared by M1) take the same path and
    # run a dummy bcrypt so timing and the response are identical to wrong credentials.
    hashed = str(user.hashed_password) if user and user.hashed_password else _DUMMY_HASH
    valid = verify_password(password, hashed)
    if not user or not user.hashed_password or not valid:
        _record_failure(key)
        raise UnauthorizedError("Incorrect email or password")
    if not user.is_active:
        raise UnauthorizedError("Account is inactive")
    _clear_failures(key)
    return user


def login(db: Session, email: str, password: str) -> TokenPair:
    """Authenticate and issue tokens (also purges the user's expired refresh tokens)."""
    user = authenticate(db, email, password)
    _purge_expired(db, int(user.id))
    return issue_tokens(db, user)


def _purge_expired(db: Session, user_id: int) -> None:
    """Delete this user's expired refresh-token rows (revoked rows are kept until expiry
    so that reuse of a rotated token can still be detected)."""
    db.execute(
        delete(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.expires_at <= datetime.now(UTC)
        )
    )


def revoke_all_tokens(db: Session, user_id: int) -> None:
    """Revoke every live refresh token of a user (does not commit)."""
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
        .values(revoked=True)
    )


def refresh_tokens(db: Session, refresh_token: str) -> TokenPair:
    """Rotate a refresh token atomically.

    A single conditional UPDATE (revoked=false AND not expired) claims the token, so
    concurrent requests presenting the same token can only mint one new pair. Presenting
    a token that is already revoked is treated as theft: all of the user's refresh tokens
    are revoked and 401 is returned.
    """
    decode_token(refresh_token, REFRESH)
    token_hash = hash_token(refresh_token)
    claimed = db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.token == token_hash,
            RefreshToken.revoked.is_(False),
            RefreshToken.expires_at > func.now(),
        )
        .values(revoked=True)
        .returning(RefreshToken.user_id)
    ).first()
    if claimed is None:
        stored = db.execute(
            select(RefreshToken).where(RefreshToken.token == token_hash)
        ).scalar_one_or_none()
        if stored is not None and stored.revoked:
            revoke_all_tokens(db, int(stored.user_id))
            db.commit()
            logger.warning("Refresh token reuse detected: user_id=%s", stored.user_id)
        else:
            db.rollback()
        raise UnauthorizedError("Invalid refresh token")
    user = db.get(User, int(claimed[0]))
    if user is None or not user.is_active:
        db.commit()  # keep the revocation
        raise UnauthorizedError("Invalid refresh token")
    _purge_expired(db, int(user.id))
    return issue_tokens(db, user)


def logout(db: Session, refresh_token: str) -> None:
    """Revoke a refresh token (idempotent for unknown tokens)."""
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.token == hash_token(refresh_token), RefreshToken.revoked.is_(False))
        .values(revoked=True)
    )
    db.commit()


def update_profile(db: Session, user: User, data: UserUpdate) -> User:
    """Update mutable profile fields."""
    if data.full_name is not None:
        user.full_name = data.full_name  # type: ignore[assignment,unused-ignore]
    db.commit()
    db.refresh(user)
    return user


def get_or_create_google_user(db: Session, email: str, full_name: str | None) -> User:
    """Find or create a user for a verified Google login, linking existing accounts.

    Pre-hijack defence (M1): registration does not verify email ownership. If the existing
    password account is NOT verified, someone else may have registered it with a password
    they know, so on linking we clear ``hashed_password`` (NULL) and revoke all of its
    refresh tokens before marking it verified. Password login is then impossible for it.
    """
    user = get_user_by_email(db, email)
    if user is None:
        user = User(
            email=email,
            full_name=full_name,
            oauth_provider="google",
            is_verified=True,
        )
        db.add(user)
    else:
        if not user.is_active:
            raise UnauthorizedError("Account is inactive")
        if not user.is_verified:
            if user.hashed_password is not None:
                user.hashed_password = None  # type: ignore[assignment,unused-ignore]
            revoke_all_tokens(db, int(user.id))
        if user.oauth_provider is None:
            user.oauth_provider = "google"  # type: ignore[assignment,unused-ignore]
        user.is_verified = True  # type: ignore[assignment,unused-ignore]
    db.commit()
    db.refresh(user)
    return user
