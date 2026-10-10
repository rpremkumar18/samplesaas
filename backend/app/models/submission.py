import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base, TimestampMixin


class SubmissionStatus(str, enum.Enum):
    pending = "pending"
    fetching = "fetching"
    analyzing = "analyzing"
    completed = "completed"
    failed = "failed"


class Submission(Base, TimestampMixin):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    repo_url = Column(String(500), nullable=False)
    repo_owner = Column(String(100), nullable=False)
    repo_name = Column(String(100), nullable=False)
    assignment_title = Column(String(200), nullable=True)
    status: Column[SubmissionStatus] = Column(
        Enum(SubmissionStatus, name="submission_status"),
        default=SubmissionStatus.pending,
        nullable=False,
    )
    error_message = Column(Text, nullable=True)

    user = relationship("User", back_populates="submissions")
    roast = relationship("Roast", back_populates="submission", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_submissions_user_id", "user_id"),
        Index("ix_submissions_status", "status"),
    )


class SubmissionUsage(Base):
    """Append-only ledger: one row per analysis started (create or retry).

    Deliberately has no foreign keys so deleting a submission or user never erases usage;
    quotas and the global budget are computed from this table.
    """

    __tablename__ = "submission_usage"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    submission_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

