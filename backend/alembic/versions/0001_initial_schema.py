"""Initial schema: users, refresh_tokens, submissions, roasts, improvement_tips

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-10
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

submission_status = sa.Enum(
    "pending", "fetching", "analyzing", "completed", "failed", name="submission_status"
)
tip_category = sa.Enum(
    "structure", "naming", "bugs", "security", "readability", "best_practices", name="tip_category"
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("oauth_provider", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(512), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_refresh_tokens_id", "refresh_tokens", ["id"])
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token", "refresh_tokens", ["token"], unique=True)

    op.create_table(
        "submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("repo_url", sa.String(500), nullable=False),
        sa.Column("repo_owner", sa.String(100), nullable=False),
        sa.Column("repo_name", sa.String(100), nullable=False),
        sa.Column("assignment_title", sa.String(200), nullable=True),
        sa.Column("status", submission_status, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_submissions_id", "submissions", ["id"])
    op.create_index("ix_submissions_user_id", "submissions", ["user_id"])
    op.create_index("ix_submissions_status", "submissions", ["status"])

    op.create_table(
        "roasts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "submission_id",
            sa.Integer(),
            sa.ForeignKey("submissions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("roast_text", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("score >= 0 AND score <= 100", name="ck_roasts_score_range"),
    )
    op.create_index("ix_roasts_id", "roasts", ["id"])

    op.create_table(
        "improvement_tips",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("roast_id", sa.Integer(), sa.ForeignKey("roasts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", tip_category, nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=True),
    )
    op.create_index("ix_improvement_tips_id", "improvement_tips", ["id"])
    op.create_index("ix_improvement_tips_roast_id", "improvement_tips", ["roast_id"])


def downgrade() -> None:
    op.drop_table("improvement_tips")
    op.drop_table("roasts")
    op.drop_table("submissions")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    tip_category.drop(op.get_bind(), checkfirst=True)
    submission_status.drop(op.get_bind(), checkfirst=True)
