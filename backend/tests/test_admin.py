import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import ImprovementTip, Roast, Submission, SubmissionStatus, User
from tests.conftest import make_user

API = "/api/v1/admin"


def _sub(db: Session, user: User, status: SubmissionStatus, score: int | None = None) -> Submission:
    sub = Submission(user_id=user.id, repo_url="https://github.com/o/r", repo_owner="o",
                     repo_name="r", status=status)
    db.add(sub)
    db.flush()
    if score is not None:
        roast = Roast(submission_id=sub.id, roast_text="r", summary="s", score=score)
        roast.tips = [ImprovementTip(category="bugs", title="t", description="d")]  # type: ignore[arg-type]
        db.add(roast)
    db.commit()
    return sub


def test_unauthenticated_401(client: TestClient) -> None:
    for path in ("/users", "/submissions", "/stats"):
        assert client.get(f"{API}{path}").status_code == 401
    assert client.put(f"{API}/users/1", json={}).status_code == 401


def test_non_admin_403(client: TestClient, auth_headers: dict[str, str]) -> None:
    for path in ("/users", "/submissions", "/stats"):
        assert client.get(f"{API}{path}", headers=auth_headers).status_code == 403
    assert client.put(f"{API}/users/1", json={}, headers=auth_headers).status_code == 403


def test_list_users_and_search(
    client: TestClient, db: Session, admin_headers: dict[str, str]
) -> None:
    make_user(db, "alice@example.com")
    make_user(db, "bob_under@example.com")
    r = client.get(f"{API}/users", headers=admin_headers).json()
    assert r["total"] == 3
    r = client.get(f"{API}/users", params={"search": "ALICE"}, headers=admin_headers).json()
    assert [u["email"] for u in r["items"]] == ["alice@example.com"]
    # underscore is escaped, not a wildcard
    r = client.get(f"{API}/users", params={"search": "bob_"}, headers=admin_headers).json()
    assert r["total"] == 1
    r = client.get(f"{API}/users", params={"search": "b_b"}, headers=admin_headers).json()
    assert r["total"] == 0
    r = client.get(f"{API}/users", params={"search": "%"}, headers=admin_headers).json()
    assert r["total"] == 0
    r = client.get(f"{API}/users", params={"limit": 1, "skip": 1}, headers=admin_headers).json()
    assert len(r["items"]) == 1 and r["total"] == 3
    assert client.get(f"{API}/users", params={"limit": 101}, headers=admin_headers).status_code == 422


def test_update_user(client: TestClient, db: Session, admin_headers: dict[str, str]) -> None:
    target = make_user(db, "t@example.com")
    r = client.put(f"{API}/users/{target.id}", json={"is_active": False}, headers=admin_headers)
    assert r.status_code == 200 and r.json()["is_active"] is False
    r = client.put(f"{API}/users/{target.id}", json={"is_admin": True}, headers=admin_headers)
    assert r.json()["is_admin"] is True and r.json()["is_active"] is False
    assert client.put(f"{API}/users/{target.id}", json={}, headers=admin_headers).status_code == 200
    assert client.put(f"{API}/users/9999", json={}, headers=admin_headers).status_code == 404


def test_self_demote_and_deactivate_409(
    client: TestClient, admin: User, admin_headers: dict[str, str]
) -> None:
    r = client.put(f"{API}/users/{admin.id}", json={"is_admin": False}, headers=admin_headers)
    assert r.status_code == 409
    r = client.put(f"{API}/users/{admin.id}", json={"is_active": False}, headers=admin_headers)
    assert r.status_code == 409
    r = client.put(f"{API}/users/{admin.id}", json={"is_admin": True}, headers=admin_headers)
    assert r.status_code == 200


def test_deactivated_user_loses_access(
    client: TestClient, db: Session, user: User, auth_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    client.put(f"{API}/users/{user.id}", json={"is_active": False}, headers=admin_headers)
    assert client.get("/api/v1/auth/me", headers=auth_headers).status_code == 401


def test_stats_math(client: TestClient, db: Session, user: User, admin_headers: dict[str, str]) -> None:
    empty = client.get(f"{API}/stats", headers=admin_headers).json()
    assert empty["total_submissions"] == 0 and empty["average_score"] is None
    make_user(db, "off@example.com", active=False)
    _sub(db, user, SubmissionStatus.completed, 80)
    _sub(db, user, SubmissionStatus.completed, 51)
    _sub(db, user, SubmissionStatus.failed)
    _sub(db, user, SubmissionStatus.pending)
    s = client.get(f"{API}/stats", headers=admin_headers).json()
    assert s == {
        "total_users": 3,  # admin, user, off
        "active_users": 2,
        "total_submissions": 4,
        "completed_submissions": 2,
        "failed_submissions": 1,
        "average_score": 65.5,
    }


def test_submissions_filters(
    client: TestClient, db: Session, user: User, other_user: User, admin_headers: dict[str, str]
) -> None:
    _sub(db, user, SubmissionStatus.completed, 70)
    _sub(db, user, SubmissionStatus.failed)
    _sub(db, other_user, SubmissionStatus.completed, 40)
    r = client.get(f"{API}/submissions", headers=admin_headers).json()
    assert r["total"] == 3
    r = client.get(f"{API}/submissions", params={"status": "failed"}, headers=admin_headers).json()
    assert r["total"] == 1 and r["items"][0]["score"] is None
    assert r["items"][0]["user_email"] == "user@example.com"
    r = client.get(f"{API}/submissions", params={"user_id": other_user.id}, headers=admin_headers).json()
    assert r["total"] == 1 and r["items"][0]["score"] == 40
    r = client.get(
        f"{API}/submissions",
        params={"user_id": user.id, "status": "completed"},
        headers=admin_headers,
    ).json()
    assert r["total"] == 1 and r["items"][0]["score"] == 70
    r = client.get(f"{API}/submissions", params={"limit": 2}, headers=admin_headers).json()
    assert len(r["items"]) == 2 and r["total"] == 3
    assert client.get(f"{API}/submissions", params={"status": "bogus"}, headers=admin_headers).status_code == 422


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "healthy"}


def test_unhandled_error_hidden(client: TestClient) -> None:
    from unittest.mock import patch

    with patch("app.routers.admin.admin_service.get_stats", side_effect=RuntimeError("boom")):
        c = TestClient(client.app, raise_server_exceptions=False)
        admin_user_headers = None
        # need an admin token; create inline
        from app.auth.jwt import create_access_token
        from app.database import SessionLocal

        s = SessionLocal()
        try:
            adm = make_user(s, "adm2@example.com", admin=True)
            admin_user_headers = {"Authorization": f"Bearer {create_access_token(int(adm.id))}"}
        finally:
            s.close()
        r = c.get(f"{API}/stats", headers=admin_user_headers)
    assert r.status_code == 500
    assert r.json() == {"detail": "Internal server error"}


def test_last_active_admin_cannot_be_removed(db: Session, admin: User) -> None:
    """A deactivated admin acting on the only active admin is refused (409)."""
    from app.exceptions import ConflictError
    from app.schemas.admin import AdminUserUpdate
    from app.services import admin_service

    ghost = make_user(db, "ghost@example.com", admin=True, active=False)
    with pytest.raises(ConflictError):
        admin_service.update_user(db, ghost, int(admin.id), AdminUserUpdate(is_admin=False))
    with pytest.raises(ConflictError):
        admin_service.update_user(db, ghost, int(admin.id), AdminUserUpdate(is_active=False))
    make_user(db, "second@example.com", admin=True)
    result = admin_service.update_user(db, ghost, int(admin.id), AdminUserUpdate(is_admin=False))
    assert result.is_admin is False


def test_admin_update_logs_diff(
    client: TestClient,
    db: Session,
    admin_headers: dict[str, str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    target = make_user(db, "log@example.com")
    with caplog.at_level(logging.INFO, logger="app.services.admin_service"):
        client.put(f"{API}/users/{target.id}", json={"is_active": False}, headers=admin_headers)
    assert any(
        "before={'is_active': True}" in m and "after={'is_active': False}" in m
        for m in caplog.messages
    )
