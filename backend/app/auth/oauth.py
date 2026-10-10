"""Google OAuth helpers."""

import logging
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from app.config import get_settings
from app.exceptions import BadRequestError, ExternalServiceError

logger = logging.getLogger(__name__)

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"  # noqa: S105
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


@dataclass
class GoogleProfile:
    """Verified Google profile data."""

    email: str
    full_name: str | None
    email_verified: bool


def redirect_uri() -> str:
    """Build the callback URL from configured BACKEND_PUBLIC_URL (never from the Host header)."""
    base = str(get_settings().BACKEND_PUBLIC_URL).rstrip("/")
    return f"{base}/api/v1/auth/google/callback"


def build_authorization_url(callback_url: str, state: str) -> str:
    """Return the Google consent URL."""
    settings = get_settings()
    if not settings.GOOGLE_CLIENT_ID:
        raise BadRequestError("Google OAuth is not configured")
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def fetch_profile(code: str, callback_url: str) -> GoogleProfile:
    """Exchange an authorization code and fetch the user's profile (sync; run in threadpool)."""
    settings = get_settings()
    try:
        with httpx.Client(timeout=10.0) as client:
            token_resp = client.post(
                TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": callback_url,
                    "grant_type": "authorization_code",
                },
            )
            if token_resp.status_code != 200:
                raise BadRequestError("Google authorization failed")
            google_token = str(token_resp.json().get("access_token", ""))
            info_resp = client.get(
                USERINFO_URL, headers={"Authorization": f"Bearer {google_token}"}
            )
            if info_resp.status_code != 200:
                raise ExternalServiceError("Could not fetch Google profile")
            info = info_resp.json()
    except httpx.HTTPError as exc:
        logger.warning("Google OAuth request failed: %s", type(exc).__name__)
        raise ExternalServiceError("Google service unavailable") from exc
    email = info.get("email")
    if not email:
        raise BadRequestError("Google account has no email")
    return GoogleProfile(
        email=str(email).lower(),
        full_name=info.get("name"),
        email_verified=bool(info.get("email_verified")),
    )
