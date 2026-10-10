"""GitHub OAuth helpers (login only; the user's GitHub token is never stored)."""

import logging
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from app.config import get_settings
from app.exceptions import BadRequestError, ExternalServiceError

logger = logging.getLogger(__name__)

AUTH_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"  # noqa: S105
USER_URL = "https://api.github.com/user"
EMAILS_URL = "https://api.github.com/user/emails"


@dataclass
class GitHubProfile:
    """Verified GitHub profile data."""

    email: str
    full_name: str | None
    email_verified: bool
    login: str = ""


def redirect_uri() -> str:
    """Build the callback URL from configured BACKEND_PUBLIC_URL (never from the Host header)."""
    base = str(get_settings().BACKEND_PUBLIC_URL).rstrip("/")
    return f"{base}/api/v1/auth/github/callback"


def build_authorization_url(callback_url: str, state: str) -> str:
    """Return the GitHub consent URL."""
    settings = get_settings()
    if not settings.GITHUB_CLIENT_ID:
        raise BadRequestError("GitHub login is not configured")
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": callback_url,
        "scope": "read:user user:email",
        "state": state,
        "allow_signup": "true",
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def _pick_email(emails: object) -> tuple[str, bool] | None:
    """Return (email, verified) for the primary address, else any verified one."""
    if not isinstance(emails, list):
        return None
    rows = [e for e in emails if isinstance(e, dict) and e.get("email")]
    for row in rows:
        if row.get("primary") and row.get("verified"):
            return str(row["email"]).lower(), True
    for row in rows:
        if row.get("verified"):
            return str(row["email"]).lower(), True
    if rows:
        return str(rows[0]["email"]).lower(), False
    return None


def fetch_profile(code: str, callback_url: str) -> GitHubProfile:
    """Exchange an authorization code and fetch the user's profile (sync; run in threadpool)."""
    settings = get_settings()
    try:
        with httpx.Client(timeout=10.0) as client:
            token_resp = client.post(
                TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "code": code,
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "redirect_uri": callback_url,
                },
            )
            if token_resp.status_code != 200:
                raise BadRequestError("GitHub authorization failed")
            gh_token = str(token_resp.json().get("access_token", ""))
            if not gh_token:
                raise BadRequestError("GitHub authorization failed")
            headers = {
                "Authorization": f"Bearer {gh_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            user_resp = client.get(USER_URL, headers=headers)
            if user_resp.status_code != 200:
                raise ExternalServiceError("Could not fetch GitHub profile")
            info = user_resp.json()
            emails_resp = client.get(EMAILS_URL, headers=headers)
            picked = _pick_email(emails_resp.json()) if emails_resp.status_code == 200 else None
    except httpx.HTTPError as exc:
        logger.warning("GitHub OAuth request failed: %s", type(exc).__name__)
        raise ExternalServiceError("GitHub service unavailable") from exc
    except ValueError as exc:
        raise ExternalServiceError("GitHub returned an unexpected response") from exc
    login = str(info.get("login") or "")
    if not login:
        raise BadRequestError("GitHub account has no username")
    if picked is None:
        raise BadRequestError("GitHub account has no email")
    email, verified = picked
    return GitHubProfile(
        email=email,
        full_name=(info.get("name") or login),
        email_verified=verified,
        login=login,
    )
