"""Admin business logic: user management, submission listing, statistics."""

import logging

from sqlalchemy import case, func, or_, select, update
from sqlalchemy.orm import Session

from app.exceptions import ConflictError, NotFoundError
from app.models.roast import Roast
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User
from app.schemas.admin import (
    AdminStats,
    AdminSubmission,
    AdminSubmissionList,
    AdminUser,
    AdminUserList,
    AdminUserUpdate,
)

logger = logging.getLogger(__name__)


def _escape_like(term: str) -> str:
    """Escape LIKE wildcards in user-supplied search text."""
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def list_users(db: Session, skip: int, limit: int, search: str | None) -> AdminUserList:
    """Return a page of users, optionally filtered by email or name."""
    conditions = []
    if search and search.strip():
        pattern = f"%{_escape_like(search.strip())}%"
        conditions.append(
            or_(User.email.ilike(pattern, escape="\\"), User.full_name.ilike(pattern, escape="\\"))
        )

    total: int = db.scalar(select(func.count(User.id)).where(*conditions)) or 0
    users = db.scalars(
        select(User)
        .where(*conditions)
        .order_by(User.created_at.desc(), User.id.desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return AdminUserList(items=[AdminUser.model_validate(u) for u in users], total=total)


def update_user(db: Session, admin: User, user_id: int, data: AdminUserUpdate) -> AdminUser:
    """Update a user's is_active / is_admin flags; admins cannot lock themselves out."""
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found")

    if user.id == admin.id:
        if data.is_active is False:
            raise ConflictError("Admins cannot deactivate themselves")
        if data.is_admin is False:
            raise ConflictError("Admins cannot remove their own admin role")

    removing_admin = (
        user.is_admin and user.is_active and (data.is_admin is False or data.is_active is False)
    )
    if removing_admin:
        others = db.scalar(
            select(func.count(User.id)).where(
                User.id != user.id, User.is_admin.is_(True), User.is_active.is_(True)
            )
        )
        if not others:
            raise ConflictError("Cannot demote or deactivate the last active admin")

    changes = data.model_dump(exclude_none=True)
    before = {k: getattr(user, k) for k in changes}
    if changes:
        db.execute(update(User).where(User.id == user_id).values(**changes))
    db.commit()
    db.refresh(user)
    after = {k: getattr(user, k) for k in changes}
    logger.info("Admin %s updated user %s: before=%s after=%s", admin.id, user.id, before, after)
    return AdminUser.model_validate(user)


def list_submissions(
    db: Session,
    skip: int,
    limit: int,
    status: SubmissionStatus | None,
    user_id: int | None,
) -> AdminSubmissionList:
    """Return a page of submissions with owner email and score in a single query."""
    conditions = []
    if status is not None:
        conditions.append(Submission.status == status)
    if user_id is not None:
        conditions.append(Submission.user_id == user_id)

    total: int = db.scalar(select(func.count(Submission.id)).where(*conditions)) or 0
    rows = db.execute(
        select(
            Submission.id,
            Submission.user_id,
            Submission.repo_url,
            Submission.repo_owner,
            Submission.repo_name,
            Submission.assignment_title,
            Submission.status,
            Submission.error_message,
            Submission.created_at,
            Submission.updated_at,
            User.email.label("user_email"),
            Roast.score.label("score"),
        )
        .join(User, User.id == Submission.user_id)
        .outerjoin(Roast, Roast.submission_id == Submission.id)
        .where(*conditions)
        .order_by(Submission.created_at.desc(), Submission.id.desc())
        .offset(skip)
        .limit(limit)
    ).all()
    items = [AdminSubmission.model_validate(dict(row._mapping)) for row in rows]
    return AdminSubmissionList(items=items, total=total)


def get_stats(db: Session) -> AdminStats:
    """Compute platform statistics with aggregate queries."""
    user_row = db.execute(
        select(
            func.count(User.id),
            func.coalesce(func.sum(case((User.is_active.is_(True), 1), else_=0)), 0),
        )
    ).one()
    sub_row = db.execute(
        select(
            func.count(Submission.id),
            func.coalesce(
                func.sum(case((Submission.status == SubmissionStatus.completed, 1), else_=0)), 0
            ),
            func.coalesce(
                func.sum(case((Submission.status == SubmissionStatus.failed, 1), else_=0)), 0
            ),
        )
    ).one()
    avg_score = db.scalar(select(func.avg(Roast.score)))

    return AdminStats(
        total_users=int(user_row[0]),
        active_users=int(user_row[1]),
        total_submissions=int(sub_row[0]),
        completed_submissions=int(sub_row[1]),
        failed_submissions=int(sub_row[2]),
        average_score=round(float(avg_score), 2) if avg_score is not None else None,
    )
