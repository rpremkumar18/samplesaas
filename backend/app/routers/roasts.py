"""Roast endpoints (mounted under /api/v1)."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.dependencies import get_current_user, get_db
from app.exceptions import NotFoundError
from app.models.roast import Roast
from app.models.submission import Submission
from app.schemas.roast import RoastListOut, RoastOut, TipOut

router = APIRouter(prefix="/roasts", tags=["roasts"])


def _to_out(roast: Roast) -> RoastOut:
    """Map a Roast (with submission and tips loaded) to its response schema."""
    sub = roast.submission
    return RoastOut(
        id=roast.id,
        submission_id=roast.submission_id,
        repo_url=sub.repo_url,
        assignment_title=sub.assignment_title,
        roast_text=roast.roast_text,
        summary=roast.summary,
        score=roast.score,
        created_at=roast.created_at,
        tips=[TipOut.model_validate(t) for t in roast.tips],
    )


@router.get("", response_model=RoastListOut)
def list_roasts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> RoastListOut:
    """Return the current user's roast history, newest first."""
    total = db.scalar(
        select(func.count(Roast.id))
        .join(Submission, Roast.submission_id == Submission.id)
        .where(Submission.user_id == user.id)
    )
    rows = db.scalars(
        select(Roast)
        .join(Submission, Roast.submission_id == Submission.id)
        .where(Submission.user_id == user.id)
        .options(selectinload(Roast.tips), selectinload(Roast.submission))
        .order_by(Roast.created_at.desc(), Roast.id.desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return RoastListOut(items=[_to_out(r) for r in rows], total=total or 0)


@router.get("/{submission_id}", response_model=RoastOut)
def get_roast(
    submission_id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
) -> RoastOut:
    """Return the roast for a submission owned by the current user."""
    submission = db.scalar(
        select(Submission).where(Submission.id == submission_id, Submission.user_id == user.id)
    )
    if submission is None:
        raise NotFoundError("Roast not found")
    roast = db.scalar(
        select(Roast)
        .where(Roast.submission_id == submission_id)
        .options(selectinload(Roast.tips), selectinload(Roast.submission))
    )
    if roast is None:
        raise NotFoundError("Roast not ready")
    return _to_out(roast)
