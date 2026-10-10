import threading
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.exceptions import ValidationFailedError
from app.models import Submission, SubmissionStatus, SubmissionUsage, User
from app.routers import submissions as submissions_router
from app.services import submission_service
from app.services.submission_service import parse_github_repo_url

API = "/api/v1/submissions"
URL = "https://github.com/octocat/hello-world"


@pytest.fixture(autouse=True)
def _no_analysis() -> Iterator[MagicMock]:
    with patch("app.services.submission_service.run_analysis") as m:
        yield m


@pytest.fixture(autouse=True)
def _loose_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default to generous in-flight/global limits; individual tests tighten them."""
    settings = get_settings()
    monkeypatch.setattr(settings, "MAX_IN_FLIGHT_PER_USER", 1000)
    monkeypatch.setattr(settings, "DAILY_ANALYSIS_BUDGET", 100000)
    monkeypatch.setattr(settings, "MAX_SUBMISSIONS_PER_DAY", 20)
    monkeypatch.setattr(settings, "STALE_SUBMISSION_MINUTES", 15)


def _age(db: Session, sid: int, minutes: int, status: SubmissionStatus | None = None) -> None:
    """Backdate a submission's updated_at (and optionally set its status)."""
    values: dict[str, Any] = {"updated_at": datetime.now(UTC) - timedelta(minutes=minutes)}
    if status is not None:
        values["status"] = status
    db.execute(update(Submission).where(Submission.id == sid).values(**values))
    db.commit()


def _create(client: TestClient, headers: dict[str, str], url: str = URL, **extra: Any) -> Any:
    return client.post(API, json={"repo_url": url, **extra}, headers=headers)


def test_requires_auth(client: TestClient) -> None:
    assert client.post(API, json={"repo_url": URL}).status_code == 401
    assert client.get(API).status_code == 401


def test_create_valid_triggers_analysis(
    client: TestClient, auth_headers: dict[str, str], _no_analysis: MagicMock
) -> None:
    r = _create(client, auth_headers, assignment_title="HW1")
    assert r.status_code == 201
    body = r.json()
    assert body["repo_owner"] == "octocat"
    assert body["repo_name"] == "hello-world"
    assert body["assignment_title"] == "HW1"
    assert body["status"] == "pending"
    _no_analysis.assert_called_once_with(body["id"])


def test_title_defaults_to_repo_and_git_suffix(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    r = _create(client, auth_headers, url=URL + ".git")
    assert r.status_code == 201
    assert r.json()["repo_url"] == URL
    assert r.json()["assignment_title"] == "hello-world"


@pytest.mark.parametrize(
    "bad",
    [
        "http://github.com/o/r",
        "https://gitlab.com/o/r",
        "https://github.com:8080/o/r",
        "https://user@github.com/o/r",
        "https://user:pw@github.com/o/r",
        "https://github.com/o/r?x=1",
        "https://github.com/o/r#frag",
        "https://github.com/o/r/tree/main",
        "https://github.com/o",
        "https://github.com/../r",
        "https://github.com/o/..",
        "https://github.com/./r",
        "https://github.com/o/r\n",
        "https://github.com/o/r\nhttps://evil.com",
        "https://github.com/o/r with space",
        "https://github.com.evil.com/o/r",
        "https://evil.com/https://github.com/o/r",
        " https://github.com/o/r",
        "ftp://github.com/o/r",
        "file:///etc/passwd",
        "javascript:alert(1)",
        "https://github.com//r",
        "https://github.com/o/r%2f..",
    ],
)
def test_invalid_urls_rejected(bad: str) -> None:
    with pytest.raises(ValidationFailedError):
        parse_github_repo_url(bad)


def test_valid_url_variants() -> None:
    assert parse_github_repo_url("https://github.com/a-b/c.d_e") == ("a-b", "c.d_e")
    assert parse_github_repo_url("https://github.com/a/b/") == ("a", "b")


def test_invalid_url_returns_422(client: TestClient, auth_headers: dict[str, str]) -> None:
    assert _create(client, auth_headers, url="https://evil.com/a/b").status_code == 422
    assert _create(client, auth_headers, url="").status_code == 422
    assert _create(client, auth_headers, url=URL + "\n").status_code == 422


def test_ownership_isolation(
    client: TestClient, auth_headers: dict[str, str], other_headers: dict[str, str]
) -> None:
    sid = _create(client, auth_headers).json()["id"]
    assert client.get(f"{API}/{sid}", headers=other_headers).status_code == 404
    assert client.delete(f"{API}/{sid}", headers=other_headers).status_code == 404
    assert client.post(f"{API}/{sid}/retry", headers=other_headers).status_code == 404
    assert client.get(API, headers=other_headers).json() == {"items": [], "total": 0}
    assert client.get(f"{API}/{sid}", headers=auth_headers).status_code == 200


def test_list_pagination(client: TestClient, auth_headers: dict[str, str]) -> None:
    ids = [
        _create(client, auth_headers, url=f"https://github.com/o/r{i}").json()["id"]
        for i in range(5)
    ]
    r = client.get(API, params={"skip": 0, "limit": 2}, headers=auth_headers).json()
    assert r["total"] == 5
    assert [s["id"] for s in r["items"]] == ids[::-1][:2]
    r = client.get(API, params={"skip": 4, "limit": 2}, headers=auth_headers).json()
    assert [s["id"] for s in r["items"]] == [ids[0]]
    assert client.get(API, params={"limit": 0}, headers=auth_headers).status_code == 422
    assert client.get(API, params={"skip": -1}, headers=auth_headers).status_code == 422


def test_delete(client: TestClient, auth_headers: dict[str, str]) -> None:
    sid = _create(client, auth_headers).json()["id"]
    assert client.delete(f"{API}/{sid}", headers=auth_headers).status_code == 204
    assert client.get(f"{API}/{sid}", headers=auth_headers).status_code == 404


def test_retry_only_failed(
    client: TestClient, db: Session, auth_headers: dict[str, str], _no_analysis: MagicMock
) -> None:
    sid = _create(client, auth_headers).json()["id"]
    assert client.post(f"{API}/{sid}/retry", headers=auth_headers).status_code == 409
    sub = db.get(Submission, sid)
    assert sub is not None
    sub.status = SubmissionStatus.failed  # type: ignore[assignment]
    sub.error_message = "boom"  # type: ignore[assignment]
    db.commit()
    _no_analysis.reset_mock()
    r = client.post(f"{API}/{sid}/retry", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "pending"
    assert r.json()["error_message"] is None
    _no_analysis.assert_called_once_with(sid)


def test_daily_limit_429(client: TestClient, auth_headers: dict[str, str]) -> None:
    for i in range(get_settings().MAX_SUBMISSIONS_PER_DAY):
        r = _create(client, auth_headers, url=f"https://github.com/o/r{i}")
        assert r.status_code == 201
    assert _create(client, auth_headers, url="https://github.com/o/extra").status_code == 429


def test_daily_limit_is_per_user(
    client: TestClient, auth_headers: dict[str, str], other_headers: dict[str, str]
) -> None:
    for i in range(get_settings().MAX_SUBMISSIONS_PER_DAY):
        _create(client, auth_headers, url=f"https://github.com/o/r{i}")
    assert _create(client, other_headers).status_code == 201


def test_usage_row_written_on_create_and_retry(
    client: TestClient, db: Session, auth_headers: dict[str, str]
) -> None:
    sid = _create(client, auth_headers).json()["id"]
    assert db.scalar(select(func.count()).select_from(SubmissionUsage)) == 1
    _age(db, sid, 0, SubmissionStatus.failed)
    assert client.post(f"{API}/{sid}/retry", headers=auth_headers).status_code == 200
    rows = db.execute(select(SubmissionUsage)).scalars().all()
    assert len(rows) == 2
    assert {r.submission_id for r in rows} == {sid}


def test_quota_survives_delete_and_resubmit(
    client: TestClient, db: Session, auth_headers: dict[str, str]
) -> None:
    for i in range(get_settings().MAX_SUBMISSIONS_PER_DAY):
        r = _create(client, auth_headers, url=f"https://github.com/o/r{i}")
        assert r.status_code == 201
        assert client.delete(f"{API}/{r.json()['id']}", headers=auth_headers).status_code == 204
    assert _create(client, auth_headers, url="https://github.com/o/again").status_code == 429
    assert db.scalar(select(func.count()).select_from(SubmissionUsage)) == 20


def test_old_usage_does_not_count(
    client: TestClient, db: Session, user: User, auth_headers: dict[str, str]
) -> None:
    for _ in range(get_settings().MAX_SUBMISSIONS_PER_DAY):
        db.add(SubmissionUsage(user_id=user.id, created_at=datetime.now(UTC) - timedelta(hours=25)))
    db.commit()
    assert _create(client, auth_headers).status_code == 201


def test_in_flight_cap(
    client: TestClient,
    db: Session,
    auth_headers: dict[str, str],
    other_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(get_settings(), "MAX_IN_FLIGHT_PER_USER", 2)
    first = _create(client, auth_headers, url="https://github.com/o/a").json()["id"]
    _create(client, auth_headers, url="https://github.com/o/b")
    r = _create(client, auth_headers, url="https://github.com/o/c")
    assert r.status_code == 429
    assert "in progress" in r.text
    # another user is unaffected, and finishing one frees a slot
    assert _create(client, other_headers).status_code == 201
    _age(db, first, 0, SubmissionStatus.completed)
    assert _create(client, auth_headers, url="https://github.com/o/c").status_code == 201


def test_retry_obeys_in_flight_cap(
    client: TestClient, db: Session, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "MAX_IN_FLIGHT_PER_USER", 1)
    failed = _create(client, auth_headers, url="https://github.com/o/a").json()["id"]
    _age(db, failed, 0, SubmissionStatus.failed)
    _create(client, auth_headers, url="https://github.com/o/b")  # occupies the only slot
    assert client.post(f"{API}/{failed}/retry", headers=auth_headers).status_code == 429


def test_global_budget_kill_switch(
    client: TestClient,
    auth_headers: dict[str, str],
    other_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(get_settings(), "DAILY_ANALYSIS_BUDGET", 2)
    assert _create(client, auth_headers, url="https://github.com/o/a").status_code == 201
    assert _create(client, other_headers, url="https://github.com/o/b").status_code == 201
    r = _create(client, auth_headers, url="https://github.com/o/c")
    assert r.status_code == 429
    assert "capacity" in r.text


def test_sweeper_marks_only_stale_active_rows(
    client: TestClient, db: Session, auth_headers: dict[str, str]
) -> None:
    names = ("stale_pending", "stale_fetch", "stale_analyze", "fresh", "done", "failed")
    ids = {
        n: _create(client, auth_headers, url=f"https://github.com/o/{n}").json()["id"] for n in names
    }
    _age(db, ids["stale_pending"], 60)
    _age(db, ids["stale_fetch"], 60, SubmissionStatus.fetching)
    _age(db, ids["stale_analyze"], 60, SubmissionStatus.analyzing)
    _age(db, ids["done"], 60, SubmissionStatus.completed)
    _age(db, ids["failed"], 60, SubmissionStatus.failed)
    assert submission_service.sweep_stale_submissions() == 3
    db.expire_all()
    for name in ("stale_pending", "stale_fetch", "stale_analyze"):
        sub = db.get(Submission, ids[name])
        assert sub is not None
        assert sub.status == SubmissionStatus.failed
        assert sub.error_message == "Analysis was interrupted. Please retry."
    fresh = db.get(Submission, ids["fresh"])
    done = db.get(Submission, ids["done"])
    assert fresh is not None and fresh.status == SubmissionStatus.pending
    assert done is not None and done.status == SubmissionStatus.completed
    assert submission_service.sweep_stale_submissions() == 0


def test_sweeper_never_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom() -> None:
        raise RuntimeError("db down")

    monkeypatch.setattr(submission_service, "SessionLocal", boom)
    assert submission_service.sweep_stale_submissions() == 0


def test_status_change_bumps_updated_at(
    client: TestClient, db: Session, auth_headers: dict[str, str]
) -> None:
    sid = _create(client, auth_headers).json()["id"]
    _age(db, sid, 60)
    sub = db.get(Submission, sid)
    assert sub is not None
    old = sub.updated_at
    sub.status = SubmissionStatus.fetching  # type: ignore[assignment]
    db.commit()
    db.refresh(sub)
    assert sub.updated_at > old


def test_retry_stale_allowed_fresh_in_flight_409(
    client: TestClient, db: Session, auth_headers: dict[str, str], _no_analysis: MagicMock
) -> None:
    sid = _create(client, auth_headers).json()["id"]
    _age(db, sid, 1, SubmissionStatus.analyzing)
    assert client.post(f"{API}/{sid}/retry", headers=auth_headers).status_code == 409
    _age(db, sid, 60, SubmissionStatus.analyzing)
    _no_analysis.reset_mock()
    r = client.post(f"{API}/{sid}/retry", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "pending"
    _no_analysis.assert_called_once_with(sid)
    # completed is never retryable
    _age(db, sid, 60, SubmissionStatus.completed)
    assert client.post(f"{API}/{sid}/retry", headers=auth_headers).status_code == 409


def test_concurrent_double_retry_wins_once(
    client: TestClient, db: Session, user: User, auth_headers: dict[str, str]
) -> None:
    sid = _create(client, auth_headers).json()["id"]
    _age(db, sid, 0, SubmissionStatus.failed)
    user_id = int(user.id)
    barrier = threading.Barrier(2)
    outcomes: list[str] = []

    def attempt() -> None:
        session = SessionLocal()
        try:
            barrier.wait()
            submission_service.reset_for_retry(session, user_id, sid)
            outcomes.append("ok")
        except Exception as exc:  # noqa: BLE001
            outcomes.append(type(exc).__name__)
        finally:
            session.close()

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(outcomes) == ["ConflictError", "ok"]
    assert db.scalar(select(func.count()).select_from(SubmissionUsage)) == 2  # create + 1 retry


def test_rate_limit_decorators_registered() -> None:
    from app.rate_limit import limiter

    for fn in (submissions_router.create_submission, submissions_router.retry_submission):
        assert f"{fn.__module__}.{fn.__name__}" in limiter._route_limits  # noqa: SLF001
