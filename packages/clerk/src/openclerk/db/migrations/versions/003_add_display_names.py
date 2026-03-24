"""Add display_name to resources and workflow_steps.

Revision ID: 003
Revises: 002
Create Date: 2026-02-17
"""

import sqlalchemy as sa
from alembic import op

revision = "003_add_display_names"
down_revision = "002_add_resource_is_dynamic"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add display_name columns."""
    op.add_column(
        "resources", sa.Column("display_name", sa.String(255), nullable=True)
    )
    op.add_column(
        "workflow_steps", sa.Column("display_name", sa.String(255), nullable=True)
    )


def downgrade() -> None:
    """Remove display_name columns."""
    op.drop_column("workflow_steps", "display_name")
    op.drop_column("resources", "display_name")
