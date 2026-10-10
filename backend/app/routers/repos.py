"""Repo picker endpoint: lists the signed-in user's public GitHub repositories."""

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool

from app.dependencies import get_current_user
from app.exceptions import BadRequestError
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.repo import RepoRead
from app.services.github_service import GitHubService

router = APIRouter(prefix="/repos", tags=["repos"])


@router.get("", response_model=list[RepoRead])
@limiter.limit("30/minute")
async def list_my_repos(request: Request, user: User = Depends(get_current_user)) -> list[RepoRead]:
    """List public repositories for the user's linked GitHub account."""
    login = str(user.github_login or "")
    if not login:
        raise BadRequestError("Sign in with GitHub to pick a repository.")
    repos = await run_in_threadpool(GitHubService().list_public_repos, login)
    return [RepoRead(**vars(r)) for r in repos]
