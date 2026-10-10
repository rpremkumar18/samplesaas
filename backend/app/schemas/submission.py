"""Pydantic schemas for submissions."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.submission import SubmissionStatus


class SubmissionCreate(BaseModel):
    """Payload for creating a submission."""

    repo_url: str = Field(min_length=1, max_length=500)
    assignment_title: str | None = Field(default=None, max_length=200)


class SubmissionRead(BaseModel):
    """Submission as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    repo_url: str
    repo_owner: str
    repo_name: str
    assignment_title: str | None
    status: SubmissionStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class SubmissionList(BaseModel):
    """Paginated list of submissions."""

    items: list[SubmissionRead]
    total: int
