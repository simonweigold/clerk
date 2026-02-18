"""Add label to execution_runs.

Revision ID: 004
Revises: 003
Create Date: 2026-02-18
"""

import sqlalchemy as sa
from alembic import op

revision = "004_add_execution_label"
down_revision = "003_add_display_names"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add label column to execution_runs."""
    op.add_column(
        "execution_runs", sa.Column("label", sa.String(255), nullable=True)
    )


def downgrade() -> None:
    """Remove label column."""
    op.drop_column("execution_runs", "label")
