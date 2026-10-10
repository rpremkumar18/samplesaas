from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth import oauth
from app.exceptions import NotFoundError
from app.models import User
from app.services.github_service import GitHubService

API = "/api/v1/repos"


def _repo(name: str, **extra: object) -> dict[str, object]:
    return {
        "name": name,
        "html_url": f"https://github.com/octocat/{name}",
        "description": "d",
        "language": "Python",
        "pushed_at": "2025-01-01T00:00:00Z",
        "private": False,
        "fork": False,
        "archived": False,
        **extra,
    }


def _service(payload: object, status: int = 200) -> GitHubService:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/users/octocat/repos"
        return httpx.Response(status, json=payload)

    client = httpx.Client(base_url="https://api.github.com", transport=httpx.MockTransport(handler))
    return GitHubService(client)


def test_list_filters_private_forks_and_archived() -> None:
    svc = _service(
        [
            _repo("keep"),
            _repo("secret", private=True),
            _repo("forked", fork=True),
            _repo("old", archived=True),
            {"name": 5},
        ]
    )
    assert [r.name for r in svc.list_public_repos("octocat")] == ["keep"]


def test_list_rejects_bad_login_and_maps_404() -> None:
    with pytest.raises(NotFoundError):
        _service([]).list_public_repos("bad/login")
    with pytest.raises(NotFoundError):
        _service({"message": "Not Found"}, 404).list_public_repos("octocat")


def test_endpoint_requires_auth(client: TestClient) -> None:
    assert client.get(API).status_code == 401


def test_endpoint_requires_github_account(client: TestClient, auth_headers: dict[str, str]) -> None:
    r = client.get(API, headers=auth_headers)
    assert r.status_code == 400
    assert "GitHub" in r.json()["detail"]


def test_endpoint_lists_repos_for_linked_user(
    client: TestClient, user: User, db: Session, auth_headers: dict[str, str]
) -> None:
    user.github_login = "octocat"  # type: ignore[assignment]
    db.commit()
    with patch.object(GitHubService, "list_public_repos", return_value=_service([_repo("a")]).list_public_repos("octocat")):
        r = client.get(API, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()[0]["name"] == "a"


def test_pick_email_prefers_primary_verified() -> None:
    emails = [
        {"email": "Other@x.com", "primary": False, "verified": True},
        {"email": "Main@x.com", "primary": True, "verified": True},
    ]
    assert oauth._pick_email(emails) == ("main@x.com", True)
    assert oauth._pick_email([{"email": "u@x.com", "primary": True, "verified": False}]) == (
        "u@x.com",
        False,
    )
    assert oauth._pick_email([]) is None
