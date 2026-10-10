"""Pydantic schemas for the auth module."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Registration payload."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    """Login payload."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    """Refresh / logout payload."""

    refresh_token: str = Field(min_length=1)


class UserUpdate(BaseModel):
    """Profile update payload."""

    full_name: str | None = Field(default=None, min_length=1, max_length=100)


class TokenPair(BaseModel):
    """Access and refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105


class UserRead(BaseModel):
    """Public user representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str | None
    is_active: bool
    is_verified: bool
    is_admin: bool
    oauth_provider: str | None
    created_at: datetime
