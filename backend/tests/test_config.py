"""Production configuration validator tests (no global settings cache pollution)."""

import pytest
from pydantic import ValidationError

from app.config import Settings

GOOD_KEY = "aB3-" * 10


def build(**kw: object) -> Settings:
    """Construct Settings from explicit values, ignoring .env files."""
    base: dict[str, object] = {"DATABASE_URL": "postgresql://u:p@h/db"}
    base.update(kw)
    return Settings(_env_file=None, **base)  # type: ignore[arg-type]


def test_short_key_rejected() -> None:
    with pytest.raises(ValidationError):
        build(ENVIRONMENT="production", SECRET_KEY="short", GITHUB_TOKEN="t")


@pytest.mark.parametrize("key", ["change-me", "your-secret-key-" + "x" * 30, "secret"])
def test_placeholder_rejected(key: str) -> None:
    with pytest.raises(ValidationError):
        build(ENVIRONMENT="production", SECRET_KEY=key, GITHUB_TOKEN="t")


def test_missing_github_token_rejected() -> None:
    with pytest.raises(ValidationError):
        build(ENVIRONMENT="production", SECRET_KEY=GOOD_KEY)
    with pytest.raises(ValidationError):
        build(ENVIRONMENT="production", SECRET_KEY=GOOD_KEY, GITHUB_TOKEN="  ")


def test_good_production_accepted() -> None:
    s = build(ENVIRONMENT="production", SECRET_KEY=GOOD_KEY, GITHUB_TOKEN="ghp_fake")
    assert s.GITHUB_TOKEN == "ghp_fake"


def test_dev_with_blank_token_ok() -> None:
    s = build(ENVIRONMENT="development", SECRET_KEY="dev", GITHUB_TOKEN="")
    assert s.GITHUB_TOKEN is None


def test_cors_origins_comma_string() -> None:
    s = build(SECRET_KEY="dev", CORS_ORIGINS="http://a.test, http://b.test")
    assert s.CORS_ORIGINS == ["http://a.test", "http://b.test"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("http://localhost:3000", ["http://localhost:3000"]),
        ("http://a.test, http://b.test", ["http://a.test", "http://b.test"]),
        ('["http://a.test","http://b.test"]', ["http://a.test", "http://b.test"]),
    ],
)
def test_cors_origins_parsed_from_real_env_var(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: list[str]
) -> None:
    """Regression: pydantic-settings used to JSON-decode this env var and crash on a plain URL."""
    monkeypatch.setenv("CORS_ORIGINS", raw)
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")
    monkeypatch.setenv("SECRET_KEY", "x")
    assert Settings(_env_file=None).CORS_ORIGINS == expected  # type: ignore[call-arg]
