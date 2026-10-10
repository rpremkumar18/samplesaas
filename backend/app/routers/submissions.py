"""Submission endpoints."""

from typing import cast

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.submission import Submission
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.submission import SubmissionCreate, SubmissionList, SubmissionRead
from app.services import submission_service

router = APIRouter(prefix="/submissions", tags=["submissions"])


def uid(user: User) -> int:
    """Return the user's integer id."""
    return cast(int, user.id)


def sid(submission: Submission) -> int:
    """Return the submission's integer id."""
    return cast(int, submission.id)


@router.post("", response_model=SubmissionRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
def create_submission(
    request: Request,
    payload: SubmissionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SubmissionRead:
    """Create a submission and enqueue analysis."""
    submission = submission_service.create_submission(db, uid(user), payload)
    background_tasks.add_task(submission_service.run_analysis, sid(submission))
    return SubmissionRead.model_validate(submission)


@router.get("", response_model=SubmissionList)
def list_submissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SubmissionList:
    """List the current user's submissions, newest first."""
    items, total = submission_service.list_submissions(db, uid(user), skip, limit)
    return SubmissionList(items=[SubmissionRead.model_validate(s) for s in items], total=total)


@router.get("/{submission_id}", response_model=SubmissionRead)
def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SubmissionRead:
    """Get one of the current user's submissions."""
    return SubmissionRead.model_validate(
        submission_service.get_submission(db, uid(user), submission_id)
    )


@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    """Delete one of the current user's submissions."""
    submission_service.delete_submission(db, uid(user), submission_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{submission_id}/retry", response_model=SubmissionRead)
@limiter.limit("10/minute")
def retry_submission(
    request: Request,
    submission_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SubmissionRead:
    """Re-run analysis for a failed or stalled submission."""
    submission = submission_service.reset_for_retry(db, uid(user), submission_id)
    background_tasks.add_task(submission_service.run_analysis, sid(submission))
    return SubmissionRead.model_validate(submission)
