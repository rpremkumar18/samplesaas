"""Business logic for submissions."""

import logging
import re
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy import CursorResult, and_, func, or_, select, update
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.exceptions import ConflictError, NotFoundError, RateLimitError, ValidationFailedError
from app.models.submission import Submission, SubmissionStatus, SubmissionUsage
from app.models.user import User
from app.schemas.submission import SubmissionCreate

logger = logging.getLogger(__name__)

_GITHUB_URL_RE = re.compile(
    r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?"
)
_INVALID_URL_MESSAGE = "Repository URL must look like https://github.com/{owner}/{repo}"


def parse_github_repo_url(url: str) -> tuple[str, str]:
    """Validate a GitHub repo URL strictly and return (owner, repo)."""
    match = _GITHUB_URL_RE.fullmatch(url)
    if match is None:
        raise ValidationFailedError(_INVALID_URL_MESSAGE)
    owner, repo = match.group(1), match.group(2)
    if owner in {".", ".."} or repo in {".", ".."}:
        raise ValidationFailedError(_INVALID_URL_MESSAGE)
    return owner, repo


_ACTIVE_STATUSES = (
    SubmissionStatus.pending,
    SubmissionStatus.fetching,
    SubmissionStatus.analyzing,
)
INTERRUPTED_MESSAGE = "Analysis was interrupted. Please retry."


def _since_24h() -> datetime:
    """Start of the rolling 24-hour window."""
    return datetime.now(UTC) - timedelta(days=1)


def _stale_cutoff() -> datetime:
    """Non-terminal submissions last updated before this instant are considered stuck."""
    return datetime.now(UTC) - timedelta(minutes=get_settings().STALE_SUBMISSION_MINUTES)


def _enforce_quotas(db: Session, user_id: int, exclude_submission_id: int | None = None) -> None:
    """Raise RateLimitError if the user or the whole service is over its analysis budget.

    The user row is locked (FOR UPDATE) so concurrent requests by the same user serialize
    their check-then-insert; the lock is released when the caller commits.
    """
    settings = get_settings()
    db.execute(select(User.id).where(User.id == user_id).with_for_update()).first()
    since = _since_24h()

    global_used = int(
        db.execute(
            select(func.count())
            .select_from(SubmissionUsage)
            .where(SubmissionUsage.created_at >= since)
        ).scalar_one()
    )
    if global_used >= settings.DAILY_ANALYSIS_BUDGET:
        logger.warning("Global daily analysis budget exhausted (%d)", global_used)
        raise RateLimitError("The service is temporarily at capacity. Please try again later.")

    used = int(
        db.execute(
            select(func.count())
            .select_from(SubmissionUsage)
            .where(SubmissionUsage.user_id == user_id, SubmissionUsage.created_at >= since)
        ).scalar_one()
    )
    if used >= settings.MAX_SUBMISSIONS_PER_DAY:
        raise RateLimitError(f"Daily limit of {settings.MAX_SUBMISSIONS_PER_DAY} analyses reached")

    in_flight_stmt = (
        select(func.count())
        .select_from(Submission)
        .where(Submission.user_id == user_id, Submission.status.in_(_ACTIVE_STATUSES))
    )
    if exclude_submission_id is not None:
        in_flight_stmt = in_flight_stmt.where(Submission.id != exclude_submission_id)
    if int(db.execute(in_flight_stmt).scalar_one()) >= settings.MAX_IN_FLIGHT_PER_USER:
        raise RateLimitError(
            f"You already have {settings.MAX_IN_FLIGHT_PER_USER} analyses in progress. "
            "Wait for one to finish before starting another."
        )


def create_submission(db: Session, user_id: int, data: SubmissionCreate) -> Submission:
    """Validate, enforce quotas, and persist a new pending submission plus a usage row."""
    owner, repo = parse_github_repo_url(data.repo_url)
    _enforce_quotas(db, user_id)
    title = (data.assignment_title or "").strip() or repo
    submission = Submission(
        user_id=user_id,
        repo_url=f"https://github.com/{owner}/{repo}",
        repo_owner=owner,
        repo_name=repo,
        assignment_title=title,
        status=SubmissionStatus.pending,
    )
    db.add(submission)
    db.flush()
    db.add(SubmissionUsage(user_id=user_id, submission_id=submission.id))
    db.commit()
    db.refresh(submission)
    return submission


def list_submissions(
    db: Session, user_id: int, skip: int, limit: int
) -> tuple[list[Submission], int]:
    """Return a page of the user's submissions (newest first) and the total."""
    total = int(
        db.execute(
            select(func.count()).select_from(Submission).where(Submission.user_id == user_id)
        ).scalar_one()
    )
    stmt = (
        select(Submission)
        .where(Submission.user_id == user_id)
        .order_by(Submission.created_at.desc(), Submission.id.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all()), total


def get_submission(db: Session, user_id: int, submission_id: int) -> Submission:
    """Fetch a submission owned by the user or raise NotFoundError."""
    submission = db.execute(
        select(Submission).where(Submission.id == submission_id, Submission.user_id == user_id)
    ).scalar_one_or_none()
    if submission is None:
        raise NotFoundError("Submission not found")
    return submission


def delete_submission(db: Session, user_id: int, submission_id: int) -> None:
    """Delete a submission owned by the user."""
    submission = get_submission(db, user_id, submission_id)
    db.delete(submission)
    db.commit()


def reset_for_retry(db: Session, user_id: int, submission_id: int) -> Submission:
    """Atomically reset a failed (or stale in-flight) submission to pending.

    Obeys the same quotas as creation and records a usage row. 409 if not retryable,
    including when a concurrent retry already won.
    """
    submission = get_submission(db, user_id, submission_id)
    _enforce_quotas(db, user_id, exclude_submission_id=submission_id)
    result = db.execute(
        update(Submission)
        .where(
            Submission.id == submission_id,
            Submission.user_id == user_id,
            or_(
                Submission.status == SubmissionStatus.failed,
                and_(
                    Submission.status.in_(_ACTIVE_STATUSES),
                    Submission.updated_at < _stale_cutoff(),
                ),
            ),
        )
        .values(status=SubmissionStatus.pending, error_message=None, updated_at=func.now())
        .execution_options(synchronize_session=False)
    )
    if cast(CursorResult[Any], result).rowcount != 1:
        db.rollback()
        raise ConflictError("Only failed or stalled submissions can be retried")
    db.add(SubmissionUsage(user_id=user_id, submission_id=submission_id))
    db.commit()
    db.refresh(submission)
    return submission


def sweep_stale_submissions() -> int:
    """Mark stuck pending/fetching/analyzing submissions as failed; never raises.

    Returns the number of rows swept (0 on error).
    """
    try:
        with SessionLocal() as db:
            result = db.execute(
                update(Submission)
                .where(
                    Submission.status.in_(_ACTIVE_STATUSES),
                    Submission.updated_at < _stale_cutoff(),
                )
                .values(
                    status=SubmissionStatus.failed,
                    error_message=INTERRUPTED_MESSAGE,
                    updated_at=func.now(),
                )
                .execution_options(synchronize_session=False)
            )
            db.commit()
            count = int(cast(CursorResult[Any], result).rowcount)
        if count:
            logger.warning("Marked %d stale submission(s) as failed", count)
        return count
    except Exception:
        logger.exception("Stale submission sweep failed")
        return 0


def run_analysis(submission_id: int) -> None:
    """Background entrypoint delegating to the roast service."""
    from app.services.roast_service import analyze_submission

    analyze_submission(submission_id)
