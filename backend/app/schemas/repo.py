"""Pydantic schemas for the repo picker."""

from pydantic import BaseModel


class RepoRead(BaseModel):
    """A public GitHub repository the user can choose to roast."""

    name: str
    html_url: str
    description: str | None = None
    language: str | None = None
    pushed_at: str | None = None
