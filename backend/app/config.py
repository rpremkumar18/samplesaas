"""Application settings loaded from environment variables."""

import json
from functools import lru_cache
from typing import Annotated

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. No secrets are hardcoded; set via env or .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Assignment Roaster"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    # Where the SPA is served (OAuth redirects go here) and the public base URL of this API
    # (used to build the Google redirect_uri instead of trusting the Host header).
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_PUBLIC_URL: str = "http://localhost:8000"

    OPENAI_API_KEY: str = ""
    # Check https://developers.openai.com/api/docs/models for current model ids.
    OPENAI_MODEL: str = "gpt-6.1-sol"
    GITHUB_TOKEN: str | None = None

    # Cost / abuse controls
    MAX_SUBMISSIONS_PER_DAY: int = 20  # per user, counted on an append-only usage table
    MAX_IN_FLIGHT_PER_USER: int = 2  # concurrent pending/fetching/analyzing submissions
    DAILY_ANALYSIS_BUDGET: int = 500  # global analyses per rolling 24h (kill switch)
    STALE_SUBMISSION_MINUTES: int = 15  # non-terminal submissions older than this are failed
    PIPELINE_TIMEOUT_SECONDS: int = 300  # overall fetch + LLM deadline per analysis
    OPENAI_TIMEOUT_SECONDS: float = 90.0
    OPENAI_MAX_RETRIES: int = 1

    # Comma-separated in env, e.g. "http://localhost:5173,http://localhost:3000"
    # NoDecode: pydantic-settings must not JSON-parse the env value before split_origins runs.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    @model_validator(mode="after")
    def check_production_safety(self) -> "Settings":
        """Reject unsafe configuration when ENVIRONMENT=production."""
        if self.ENVIRONMENT.lower() != "production":
            return self
        placeholders = {"change-me", "changeme", "secret"}
        key = self.SECRET_KEY.strip()
        if len(key) < 32 or key.lower() in placeholders or key.lower().startswith("your-"):
            raise ValueError("SECRET_KEY must be a random value of at least 32 characters")
        if not (self.GITHUB_TOKEN or "").strip():
            raise ValueError("GITHUB_TOKEN is required in production (GitHub rate limits)")
        return self

    @field_validator("GITHUB_TOKEN", mode="before")
    @classmethod
    def blank_token_is_none(cls, value: object) -> object:
        """Treat an empty GITHUB_TOKEN= line as unset."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        """Accept CORS_ORIGINS as a comma-separated string or a JSON list string."""
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                return json.loads(text)
            return [o.strip() for o in text.split(",") if o.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Return the cached Settings instance."""
    return Settings()  # type: ignore[call-arg,unused-ignore]
