"""Add tools table for kit version tool assignments.

Revision ID: 007_add_tools_table
Revises: 20260222_200226_add_paused_status_to_execution_run
Create Date: 2026-02-28
"""

import sqlalchemy as sa
from alembic import op

revision = "007_add_tools_table"
down_revision = "f85b989ecee5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tools table."""
    op.create_table(
        "tools",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "version_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kit_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tool_number", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("configuration", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("version_id", "tool_number", name="uq_tool_number"),
    )


def downgrade() -> None:
    """Drop tools table."""
    op.drop_table("tools")
