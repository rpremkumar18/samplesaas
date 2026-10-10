"""Authentication endpoints."""

import logging
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import oauth
from app.auth.jwt import OAUTH_STATE, create_state_token, decode_token
from app.config import get_settings
from app.dependencies import get_current_user, get_db
from app.exceptions import AppError
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    TokenPair,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.services import auth_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

STATE_COOKIE = "oauth_state_nonce"
STATE_COOKIE_PATH = "/api/v1/auth/github"


def _is_secure() -> bool:
    return get_settings().ENVIRONMENT.lower() == "production"


def _frontend(path: str) -> str:
    return f"{get_settings().FRONTEND_URL.rstrip('/')}{path}"


def _error_redirect(code: str) -> RedirectResponse:
    """Redirect to the SPA login page with a short error code; always clears the state cookie."""
    response = RedirectResponse(_frontend(f"/login?{urlencode({'error': code})}"))
    _clear_state_cookie(response)
    return response


def _clear_state_cookie(response: Response) -> None:
    response.delete_cookie(
        STATE_COOKIE,
        path=STATE_COOKIE_PATH,
        httponly=True,
        samesite="lax",
        secure=_is_secure(),
    )


@router.post("/register", response_model=UserRead, status_code=201)
@limiter.limit("10/minute")
def register(request: Request, body: UserCreate, db: Session = Depends(get_db)) -> User:
    """Create a new account."""
    return auth_service.register_user(db, body)


@router.post("/login", response_model=TokenPair)
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    """Exchange credentials for a token pair."""
    return auth_service.login(db, body.email, body.password)


@router.post("/refresh", response_model=TokenPair)
@limiter.limit("30/minute")
def refresh(
    request: Request, body: RefreshRequest, db: Session = Depends(get_db)
) -> TokenPair:
    """Rotate a refresh token."""
    return auth_service.refresh_tokens(db, body.refresh_token)


@router.post("/logout", status_code=204)
@limiter.limit("30/minute")
def logout(request: Request, body: RefreshRequest, db: Session = Depends(get_db)) -> Response:
    """Revoke a refresh token."""
    auth_service.logout(db, body.refresh_token)
    return Response(status_code=204)


@router.get("/me", response_model=UserRead)
@limiter.limit("120/minute")
def me(request: Request, user: User = Depends(get_current_user)) -> User:
    """Return the current user."""
    return user


@router.put("/me", response_model=UserRead)
def update_me(
    body: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Update the current user's profile."""
    return auth_service.update_profile(db, user, body)


@router.get("/github")
@limiter.limit("20/minute")
def github_login(request: Request) -> RedirectResponse:
    """Redirect to GitHub's authorization screen with a signed state."""
    nonce = secrets.token_urlsafe(16)
    url = oauth.build_authorization_url(oauth.redirect_uri(), create_state_token(nonce))
    response = RedirectResponse(url)
    response.set_cookie(
        STATE_COOKIE,
        nonce,
        max_age=600,
        httponly=True,
        samesite="lax",
        secure=_is_secure(),
        path=STATE_COOKIE_PATH,
    )
    return response


@router.get("/github/callback")
@limiter.limit("20/minute")
def github_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Verify state, exchange the code, and redirect to the SPA.

    Success: ``{FRONTEND_URL}/auth/callback#access_token=...&refresh_token=...`` (URL
    fragment, never sent to servers). Any failure: ``{FRONTEND_URL}/login?error=<code>``.
    The state cookie is deleted on every path. Tokens and the URL are never logged.
    """
    if error or not code or not state:
        return _error_redirect("access_denied")
    try:
        payload = decode_token(state, OAUTH_STATE)
    except AppError:
        return _error_redirect("invalid_state")
    cookie_nonce = request.cookies.get(STATE_COOKIE)
    if not cookie_nonce or not secrets.compare_digest(
        str(payload.get("nonce", "")), cookie_nonce
    ):
        return _error_redirect("invalid_state")
    try:
        profile = oauth.fetch_profile(code, oauth.redirect_uri())
    except AppError:
        logger.warning("GitHub OAuth code exchange failed")
        return _error_redirect("github_failed")
    if not profile.email_verified:
        return _error_redirect("email_unverified")
    try:
        user = auth_service.get_or_create_github_user(
            db, profile.email, profile.full_name, profile.login
        )
    except AppError:
        return _error_redirect("account_unavailable")
    tokens = auth_service.issue_tokens(db, user)
    fragment = urlencode(
        {"access_token": tokens.access_token, "refresh_token": tokens.refresh_token}
    )
    response = RedirectResponse(_frontend(f"/auth/callback#{fragment}"))
    _clear_state_cookie(response)
    return response
