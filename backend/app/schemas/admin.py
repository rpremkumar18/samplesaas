"""Pydantic schemas for the admin module."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.submission import SubmissionStatus


class AdminUser(BaseModel):
    """User as seen by administrators."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str | None = None
    is_active: bool
    is_verified: bool
    is_admin: bool
    oauth_provider: str | None = None
    created_at: datetime


class AdminUserUpdate(BaseModel):
    """Partial update of a user's flags."""

    is_active: bool | None = None
    is_admin: bool | None = None


class AdminUserList(BaseModel):
    """Paginated users."""

    items: list[AdminUser]
    total: int


class AdminSubmission(BaseModel):
    """Submission with owner email and roast score."""

    id: int
    user_id: int
    repo_url: str
    repo_owner: str
    repo_name: str
    assignment_title: str | None = None
    status: SubmissionStatus
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    user_email: str
    score: int | None = None


class AdminSubmissionList(BaseModel):
    """Paginated submissions."""

    items: list[AdminSubmission]
    total: int


class AdminStats(BaseModel):
    """Platform-wide aggregate statistics."""

    total_users: int
    active_users: int
    total_submissions: int
    completed_submissions: int
    failed_submissions: int
    average_score: float | None = None
