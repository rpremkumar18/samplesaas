"""GitHub OAuth helpers (login only; the user's GitHub token is never stored)."""

import base64
import hashlib
import hmac
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


def pkce_verifier(nonce: str) -> str:
    """Derive the PKCE code_verifier from the browser-bound nonce (HMAC with SECRET_KEY).

    The verifier is never sent over the front channel and cannot be guessed without the
    server secret, so a stolen authorization code is useless without the matching cookie.
    """
    key = get_settings().SECRET_KEY.encode("utf-8")
    digest = hmac.new(key, f"pkce:{nonce}".encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def pkce_challenge(verifier: str) -> str:
    """S256 code_challenge for a verifier."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def build_authorization_url(callback_url: str, state: str, nonce: str) -> str:
    """Return the GitHub consent URL (state + PKCE S256)."""
    settings = get_settings()
    if not settings.GITHUB_CLIENT_ID:
        raise BadRequestError("GitHub login is not configured")
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": callback_url,
        "scope": "user:email",  # least privilege: public profile needs no scope
        "state": state,
        "code_challenge": pkce_challenge(pkce_verifier(nonce)),
        "code_challenge_method": "S256",
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


def fetch_profile(code: str, callback_url: str, nonce: str) -> GitHubProfile:
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
                    "code_verifier": pkce_verifier(nonce),
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
