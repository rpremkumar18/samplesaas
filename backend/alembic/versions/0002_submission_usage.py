"""Add append-only submission_usage ledger for quotas and the global budget

Revision ID: 0002_submission_usage
Revises: 0001_initial
Create Date: 2026-10-10
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_submission_usage"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "submission_usage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("submission_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_submission_usage_user_id", "submission_usage", ["user_id"])
    op.create_index("ix_submission_usage_created_at", "submission_usage", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_submission_usage_created_at", table_name="submission_usage")
    op.drop_index("ix_submission_usage_user_id", table_name="submission_usage")
    op.drop_table("submission_usage")
