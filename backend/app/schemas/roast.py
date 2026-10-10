"""Pydantic schemas for roasts: API responses and validated LLM output."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.roast import TipCategory


class TipOut(BaseModel):
    """An improvement tip returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category: TipCategory
    title: str
    description: str
    file_path: str | None = None


class RoastOut(BaseModel):
    """A roast with its tips and submission context."""

    id: int
    submission_id: int
    repo_url: str
    assignment_title: str | None = None
    roast_text: str
    summary: str
    score: int
    created_at: datetime
    tips: list[TipOut]


class RoastListOut(BaseModel):
    """Paginated roast history."""

    items: list[RoastOut]
    total: int


MAX_ROAST_TEXT = 4000
MAX_SUMMARY = 1500
MAX_TIP_TITLE = 200
MAX_TIP_DESCRIPTION = 1500
MAX_TIPS = 12
MAX_FILE_PATH = 500

_CONTROL_NO_NEWLINE = re.compile(
    "[" + chr(0) + "-" + chr(8) + chr(11) + "-" + chr(31) + chr(127) + "]"
)
_CONTROL_ALL = re.compile("[" + chr(0) + "-" + chr(31) + chr(127) + "]")


def clean_text(value: object, max_len: int, multiline: bool = False) -> object:
    """Strip control characters and truncate over-long model text instead of failing."""
    if not isinstance(value, str):
        return value
    pattern = _CONTROL_NO_NEWLINE if multiline else _CONTROL_ALL
    cleaned = pattern.sub(" " if not multiline else "", value).strip()
    return cleaned[:max_len].rstrip()


class LLMTip(BaseModel):
    """A tip as produced by the model."""

    category: TipCategory
    title: str = Field(min_length=1, max_length=MAX_TIP_TITLE)
    description: str = Field(min_length=1, max_length=MAX_TIP_DESCRIPTION)
    file_path: str | None = Field(default=None, max_length=MAX_FILE_PATH)

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, value: object) -> object:
        """Truncate and strip control characters."""
        return clean_text(value, MAX_TIP_TITLE)

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, value: object) -> object:
        """Truncate and strip control characters."""
        return clean_text(value, MAX_TIP_DESCRIPTION, multiline=True)

    @field_validator("file_path", mode="before")
    @classmethod
    def clean_file_path(cls, value: object) -> object:
        """Treat empty strings as no file; strip control characters."""
        cleaned = clean_text(value, MAX_FILE_PATH)
        if isinstance(cleaned, str) and not cleaned:
            return None
        return cleaned


class LLMRoast(BaseModel):
    """Strict structure the model must return."""

    roast_text: str = Field(min_length=1, max_length=MAX_ROAST_TEXT)
    summary: str = Field(min_length=1, max_length=MAX_SUMMARY)
    score: int = Field(ge=0, le=100)
    tips: list[LLMTip] = Field(min_length=3, max_length=MAX_TIPS)

    @field_validator("roast_text", mode="before")
    @classmethod
    def clean_roast(cls, value: object) -> object:
        """Truncate and strip control characters."""
        return clean_text(value, MAX_ROAST_TEXT, multiline=True)

    @field_validator("summary", mode="before")
    @classmethod
    def clean_summary(cls, value: object) -> object:
        """Truncate and strip control characters."""
        return clean_text(value, MAX_SUMMARY, multiline=True)

    @field_validator("tips", mode="before")
    @classmethod
    def cap_tips(cls, value: object) -> object:
        """Keep only the first MAX_TIPS tips rather than failing."""
        return value[:MAX_TIPS] if isinstance(value, list) else value
