"""Shared FastAPI dependencies."""

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.jwt import ACCESS, decode_token
from app.database import get_db
from app.exceptions import ForbiddenError, UnauthorizedError
from app.models.user import User

__all__ = ["get_db", "get_current_user", "require_admin"]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Return the authenticated, active user or raise 401."""
    if not token:
        raise UnauthorizedError("Not authenticated")
    payload = decode_token(token, ACCESS)
    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError) as exc:
        raise UnauthorizedError("Invalid token") from exc
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Invalid or inactive user")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require an admin user, else 403."""
    if not user.is_admin:
        raise ForbiddenError("Admin access required")
    return user
