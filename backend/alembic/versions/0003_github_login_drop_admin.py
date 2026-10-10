"""Add users.github_login (GitHub OAuth) and drop users.is_admin (no admin area)

Revision ID: 0003_github_login
Revises: 0002_submission_usage
Create Date: 2026-10-10
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_github_login"
down_revision: str | None = "0002_submission_usage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("github_login", sa.String(length=39), nullable=True))
    op.create_index("ix_users_github_login", "users", ["github_login"])
    op.drop_column("users", "is_admin")
    # Google sign-in is gone; those accounts keep working via GitHub with the same email.


def downgrade() -> None:
    op.add_column(
        "users", sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.drop_index("ix_users_github_login", table_name="users")
    op.drop_column("users", "github_login")
