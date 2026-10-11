import threading
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import database
from app.auth import oauth
from app.auth.jwt import create_state_token, hash_token
from app.exceptions import BadRequestError, UnauthorizedError
from app.models import RefreshToken, User
from app.services import auth_service
from tests.conftest import PASSWORD, make_user

API = "/api/v1/auth"


@pytest.fixture(autouse=True)
def _reset_throttle() -> None:
    auth_service.reset_login_throttle()


def _register(client: TestClient, email: str = "new@test.com") -> None:
    r = client.post(
        f"{API}/register",
        json={"email": email, "password": PASSWORD, "full_name": "New"},
    )
    assert r.status_code == 201, r.text


def _login(client: TestClient, email: str = "new@test.com") -> dict[str, str]:
    r = client.post(f"{API}/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    data: dict[str, str] = r.json()
    return data


def test_register_ok_and_hides_password(client: TestClient) -> None:
    r = client.post(
        f"{API}/register",
        json={"email": "New@Test.com", "password": PASSWORD, "full_name": "N"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "new@test.com"
    assert "password" not in body and "hashed_password" not in body


def test_register_duplicate_409(client: TestClient) -> None:
    _register(client)
    r = client.post(
        f"{API}/register",
        json={"email": "NEW@test.com", "password": PASSWORD, "full_name": "N"},
    )
    assert r.status_code == 409


def test_register_validation(client: TestClient) -> None:
    r = client.post(f"{API}/register", json={"email": "bad", "password": "x", "full_name": "N"})
    assert r.status_code == 422


def test_login_and_wrong_password(client: TestClient) -> None:
    _register(client)
    tokens = _login(client)
    assert tokens["token_type"] == "bearer"
    r = client.post(f"{API}/login", json={"email": "new@test.com", "password": "wrongpass1"})
    assert r.status_code == 401
    r = client.post(f"{API}/login", json={"email": "nobody@test.com", "password": PASSWORD})
    assert r.status_code == 401


def test_login_inactive_user(client: TestClient, db: Session) -> None:
    make_user(db, "off@test.com", active=False)
    r = client.post(f"{API}/login", json={"email": "off@test.com", "password": PASSWORD})
    assert r.status_code == 401


def test_refresh_rotation_and_reuse(client: TestClient) -> None:
    _register(client)
    first = _login(client)
    r = client.post(f"{API}/refresh", json={"refresh_token": first["refresh_token"]})
    assert r.status_code == 200
    second = r.json()
    assert second["refresh_token"] != first["refresh_token"]
    # reuse of the revoked token
    r = client.post(f"{API}/refresh", json={"refresh_token": first["refresh_token"]})
    assert r.status_code == 401
    # reuse is a compromise signal (M10): the rotated token is revoked too
    r = client.post(f"{API}/refresh", json={"refresh_token": second["refresh_token"]})
    assert r.status_code == 401


def test_refresh_rejects_access_token_and_garbage(client: TestClient) -> None:
    _register(client)
    tokens = _login(client)
    r = client.post(f"{API}/refresh", json={"refresh_token": tokens["access_token"]})
    assert r.status_code == 401
    assert client.post(f"{API}/refresh", json={"refresh_token": "garbage"}).status_code == 401


def test_logout_revokes_refresh(client: TestClient) -> None:
    _register(client)
    tokens = _login(client)
    r = client.post(f"{API}/logout", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 204
    r = client.post(f"{API}/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401
    # idempotent
    r = client.post(f"{API}/logout", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 204
    assert client.post(f"{API}/logout", json={"refresh_token": "unknown"}).status_code == 204


def test_me_requires_auth(client: TestClient) -> None:
    assert client.get(f"{API}/me").status_code == 401
    assert client.get(f"{API}/me", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_me_and_update(client: TestClient, auth_headers: dict[str, str]) -> None:
    r = client.get(f"{API}/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "user@example.com"
    r = client.put(f"{API}/me", json={"full_name": "Renamed"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["full_name"] == "Renamed"
    assert client.put(f"{API}/me", json={"full_name": ""}, headers=auth_headers).status_code == 422


def test_refresh_token_not_usable_as_access(client: TestClient) -> None:
    _register(client)
    tokens = _login(client)
    r = client.get(f"{API}/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"})
    assert r.status_code == 401


def test_inactive_user_token_rejected(
    client: TestClient, db: Session, auth_headers: dict[str, str]
) -> None:
    u = db.query(User).filter_by(email="user@example.com").one()
    u.is_active = False  # type: ignore[assignment]
    db.commit()
    assert client.get(f"{API}/me", headers=auth_headers).status_code == 401


def test_github_login_not_configured(client: TestClient) -> None:
    with patch("app.auth.oauth.get_settings") as gs:
        gs.return_value.GITHUB_CLIENT_ID = ""
        r = client.get(f"{API}/github", follow_redirects=False)
    assert _error_code(r) == "not_configured"


def test_github_login_redirect_sets_cookie(client: TestClient) -> None:
    with patch("app.auth.oauth.get_settings") as gs:
        gs.return_value.GITHUB_CLIENT_ID = "cid"
        gs.return_value.BACKEND_PUBLIC_URL = "https://api.example.com/"
        gs.return_value.SECRET_KEY = "k" * 40
        r = client.get(f"{API}/github", follow_redirects=False, headers={"Host": "evil.test"})
    assert r.status_code in (302, 307)
    assert r.headers["location"].startswith(oauth.AUTH_URL)
    cookie = r.headers["set-cookie"]
    assert "oauth_state_nonce" in cookie
    assert "Path=/api/v1/auth/github" in cookie
    # redirect_uri comes from config, never from the Host header (M9)
    redirect_uri = parse_qs(urlparse(r.headers["location"]).query)["redirect_uri"][0]
    assert redirect_uri == "https://api.example.com/api/v1/auth/github/callback"


def _error_code(r) -> str:  # type: ignore[no-untyped-def]
    assert r.status_code in (302, 307), r.text
    loc = urlparse(r.headers["location"])
    assert loc.path == "/login"
    assert "oauth_state_nonce" in r.headers["set-cookie"]  # cookie deletion header present
    assert "Path=/api/v1/auth/github" in r.headers["set-cookie"]
    return parse_qs(loc.query)["error"][0]


def _get_callback(client: TestClient, **params: str):  # type: ignore[no-untyped-def]
    return client.get(f"{API}/github/callback", params=params, follow_redirects=False)


def test_github_callback_state_mismatch(client: TestClient) -> None:
    client.cookies.set("oauth_state_nonce", "cookie-nonce")
    r = _get_callback(client, code="c", state=create_state_token("different-nonce"))
    assert _error_code(r) == "invalid_state"


def test_github_callback_missing_cookie_bad_state_and_denied(client: TestClient) -> None:
    assert _error_code(_get_callback(client, code="c", state=create_state_token("n"))) == (
        "invalid_state"
    )
    assert _error_code(_get_callback(client, code="c", state="junk")) == "invalid_state"
    assert _error_code(_get_callback(client, error="access_denied")) == "access_denied"


def test_github_callback_exchange_failure_redirects(client: TestClient) -> None:
    client.cookies.set("oauth_state_nonce", "n1")
    with patch("app.routers.auth.oauth.fetch_profile", side_effect=BadRequestError("x")):
        r = _get_callback(client, code="c", state=create_state_token("n1"))
    assert _error_code(r) == "github_failed"


def _callback(client: TestClient, profile: oauth.GitHubProfile):  # type: ignore[no-untyped-def]
    client.cookies.set("oauth_state_nonce", "n1")
    state = create_state_token("n1")
    with patch("app.routers.auth.oauth.fetch_profile", new=MagicMock(return_value=profile)):
        return client.get(
            f"{API}/github/callback", params={"code": "c", "state": state}, follow_redirects=False
        )


def test_github_callback_success_uses_fragment(client: TestClient, db: Session) -> None:
    r = _callback(client, oauth.GitHubProfile("g@example.com", "G", True, "octocat"))
    assert r.status_code in (302, 307)
    loc = urlparse(r.headers["location"])
    assert loc.path == "/auth/callback"
    assert loc.query == ""  # nothing in the query string (M2)
    frag = parse_qs(loc.fragment)
    assert frag["access_token"][0] and frag["refresh_token"][0]
    assert "Path=/api/v1/auth/github" in r.headers["set-cookie"]
    created = db.query(User).filter_by(email="g@example.com").one()
    assert created.oauth_provider == "github"
    assert created.github_login == "octocat"


def test_github_callback_unverified_email(client: TestClient) -> None:
    r = _callback(client, oauth.GitHubProfile("g@example.com", "G", False))
    assert _error_code(r) == "email_unverified"


def test_github_links_existing_verified_account_keeps_password(
    client: TestClient, user: User, db: Session
) -> None:
    user.is_verified = True  # type: ignore[assignment]
    db.commit()
    r = _callback(client, oauth.GitHubProfile("user@example.com", "G", True))
    assert r.status_code in (302, 307)
    db.refresh(user)
    assert user.oauth_provider == "github"
    assert user.hashed_password is not None


def test_github_link_unverified_account_clears_password_and_tokens(
    client: TestClient, db: Session
) -> None:
    """M1: attacker pre-registers the victim's email; the GitHub link must lock them out."""
    _register(client, "victim@example.com")
    attacker = _login(client, "victim@example.com")
    r = _callback(client, oauth.GitHubProfile("victim@example.com", "V", True))
    assert r.status_code in (302, 307)
    victim = db.query(User).filter_by(email="victim@example.com").one()
    assert victim.hashed_password is None
    assert victim.is_verified is True and victim.oauth_provider == "github"
    # attacker's password no longer works, with the same generic 401 as an unknown email
    bad = client.post(f"{API}/login", json={"email": "victim@example.com", "password": PASSWORD})
    unknown = client.post(f"{API}/login", json={"email": "nobody@example.com", "password": PASSWORD})
    assert bad.status_code == 401 and bad.json() == unknown.json()
    # attacker's previously issued refresh token was revoked
    r = client.post(f"{API}/refresh", json={"refresh_token": attacker["refresh_token"]})
    assert r.status_code == 401


def test_refresh_reuse_revokes_all_user_tokens(client: TestClient, db: Session) -> None:
    _register(client)
    first = _login(client)
    second = client.post(f"{API}/refresh", json={"refresh_token": first["refresh_token"]}).json()
    other_session = _login(client)
    # replay of the rotated token is a compromise signal
    r = client.post(f"{API}/refresh", json={"refresh_token": first["refresh_token"]})
    assert r.status_code == 401
    assert db.query(RefreshToken).filter_by(revoked=False).count() == 0
    for tok in (second, other_session):
        r = client.post(f"{API}/refresh", json={"refresh_token": tok["refresh_token"]})
        assert r.status_code == 401


def test_refresh_reuse_does_not_touch_other_users(client: TestClient) -> None:
    _register(client, "a@test.com")
    _register(client, "b@test.com")
    a = _login(client, "a@test.com")
    b = _login(client, "b@test.com")
    client.post(f"{API}/refresh", json={"refresh_token": a["refresh_token"]})
    client.post(f"{API}/refresh", json={"refresh_token": a["refresh_token"]})  # reuse
    r = client.post(f"{API}/refresh", json={"refresh_token": b["refresh_token"]})
    assert r.status_code == 200


def test_concurrent_rotation_mints_single_pair(client: TestClient, db: Session) -> None:
    _register(client)
    tokens = _login(client)
    results: list[str] = []
    barrier = threading.Barrier(2)

    def worker() -> None:
        session = database.SessionLocal()
        try:
            barrier.wait()
            auth_service.refresh_tokens(session, tokens["refresh_token"])
            results.append("ok")
        except UnauthorizedError:
            results.append("denied")
        finally:
            session.close()

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results.count("ok") == 1 and results.count("denied") == 1


def test_expired_token_rejected_and_purged_on_login(client: TestClient, db: Session) -> None:
    _register(client)
    tokens = _login(client)
    row = db.query(RefreshToken).filter_by(token=hash_token(tokens["refresh_token"])).one()
    row.expires_at = datetime.now(UTC) - timedelta(hours=1)  # type: ignore[assignment]
    db.commit()
    r = client.post(f"{API}/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401
    assert db.query(RefreshToken).count() == 1
    _login(client)  # purges the expired row, adds a new one
    db.expire_all()
    assert db.query(RefreshToken).count() == 1


def test_failed_login_throttle_429_and_reset_on_success(client: TestClient) -> None:
    _register(client)
    body = {"email": "new@test.com", "password": "wrongpass1"}
    for _ in range(4):
        assert client.post(f"{API}/login", json=body).status_code == 401
    _login(client)  # a success resets the counter
    for _ in range(5):
        assert client.post(f"{API}/login", json=body).status_code == 401
    assert client.post(f"{API}/login", json=body).status_code == 429
    # even the right password is blocked while throttled
    r = client.post(f"{API}/login", json={"email": "NEW@test.com", "password": PASSWORD})
    assert r.status_code == 429
    # other emails unaffected
    r = client.post(f"{API}/login", json={"email": "other@test.com", "password": "x"})
    assert r.status_code == 401


def test_long_password_over_72_bytes_registers_and_logs_in(client: TestClient) -> None:
    password = "é" * 60  # 120 bytes, within the 128-char schema limit
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": "long@example.com", "password": password, "full_name": "Long"},
    )
    assert reg.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": "long@example.com", "password": password})
    assert login.status_code == 200


def test_token_without_exp_is_rejected() -> None:
    import jwt as pyjwt

    from app.auth.jwt import ACCESS, decode_token
    from app.config import get_settings
    from app.exceptions import UnauthorizedError

    settings = get_settings()
    token = pyjwt.encode({"sub": "1", "type": ACCESS}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    with pytest.raises(UnauthorizedError):
        decode_token(token, ACCESS)


def test_github_authorize_url_uses_pkce_and_least_privilege_scope(client: TestClient) -> None:
    with patch("app.auth.oauth.get_settings") as gs:
        gs.return_value.GITHUB_CLIENT_ID = "cid"
        gs.return_value.BACKEND_PUBLIC_URL = "https://api.example.com"
        gs.return_value.SECRET_KEY = "k" * 40
        r = client.get(f"{API}/github", follow_redirects=False)
    q = parse_qs(urlparse(r.headers["location"]).query)
    assert q["scope"] == ["user:email"]
    assert q["code_challenge_method"] == ["S256"]
    nonce = r.cookies.get("oauth_state_nonce") or ""
    assert nonce
    with patch("app.auth.oauth.get_settings") as gs:
        gs.return_value.SECRET_KEY = "k" * 40
        verifier = oauth.pkce_verifier(nonce)
    assert q["code_challenge"] == [oauth.pkce_challenge(verifier)]
    assert len(verifier) == 43
