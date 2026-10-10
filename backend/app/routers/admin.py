"""Admin endpoints (admin only); plain def so sync DB work runs in the threadpool."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_admin
from app.models.submission import SubmissionStatus
from app.models.user import User
from app.schemas.admin import (
    AdminStats,
    AdminSubmissionList,
    AdminUser,
    AdminUserList,
    AdminUserUpdate,
)
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=AdminUserList)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=100),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> AdminUserList:
    """List users with pagination and optional search."""
    return admin_service.list_users(db, skip, limit, search)


@router.put("/users/{user_id}", response_model=AdminUser)
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> AdminUser:
    """Activate/deactivate a user or change their admin role."""
    return admin_service.update_user(db, admin, user_id, payload)


@router.get("/submissions", response_model=AdminSubmissionList)
def list_submissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: SubmissionStatus | None = Query(None),
    user_id: int | None = Query(None),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> AdminSubmissionList:
    """List all submissions with owner email and score."""
    return admin_service.list_submissions(db, skip, limit, status, user_id)


@router.get("/stats", response_model=AdminStats)
def get_stats(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> AdminStats:
    """Return platform-wide statistics."""
    return admin_service.get_stats(db)
