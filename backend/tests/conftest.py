"""Shared fixtures: real throwaway Postgres, client, users, auth headers."""

import os
from collections.abc import Generator

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:pw@localhost:55433/roaster_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-0123456789")
os.environ["OPENAI_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app import database  # noqa: E402
from app.auth.jwt import create_access_token, hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base, User  # noqa: E402
from app.rate_limit import limiter  # noqa: E402

limiter.enabled = False

PASSWORD = "password123"


@pytest.fixture(scope="session", autouse=True)
def _schema() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=database.engine)
    Base.metadata.create_all(bind=database.engine)
    yield
    Base.metadata.drop_all(bind=database.engine)


@pytest.fixture(autouse=True)
def _clean_tables(_schema: None) -> Generator[None, None, None]:
    yield
    with database.engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE improvement_tips, roasts, submissions, submission_usage, refresh_tokens, users "
                "RESTART IDENTITY CASCADE"
            )
        )


@pytest.fixture
def db() -> Generator[Session, None, None]:
    session = database.SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    def _get_db() -> Generator[Session, None, None]:
        s = database.SessionLocal()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[database.get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_user(db: Session, email: str, admin: bool = False, active: bool = True) -> User:
    user = User(
        email=email,
        hashed_password=hash_password(PASSWORD),
        full_name="Test User",
        is_admin=admin,
        is_active=active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def headers_for(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(int(user.id))}"}


@pytest.fixture
def user(db: Session) -> User:
    return make_user(db, "user@example.com")


@pytest.fixture
def other_user(db: Session) -> User:
    return make_user(db, "other@example.com")


@pytest.fixture
def admin(db: Session) -> User:
    return make_user(db, "admin@example.com", admin=True)


@pytest.fixture
def auth_headers(user: User) -> dict[str, str]:
    return headers_for(user)


@pytest.fixture
def other_headers(other_user: User) -> dict[str, str]:
    return headers_for(other_user)


@pytest.fixture
def admin_headers(admin: User) -> dict[str, str]:
    return headers_for(admin)
