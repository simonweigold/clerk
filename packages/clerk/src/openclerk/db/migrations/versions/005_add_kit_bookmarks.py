"""Add user_kit_bookmarks table.

Revision ID: 005
Revises: 004
Create Date: 2026-02-22
"""

import sqlalchemy as sa
from alembic import op

revision = "005_add_kit_bookmarks"
down_revision = "004_add_execution_label"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user_kit_bookmarks table."""
    op.create_table(
        "user_kit_bookmarks",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "kit_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reasoning_kits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "kit_id", name="uq_user_kit_bookmark"),
    )


def downgrade() -> None:
    """Drop user_kit_bookmarks table."""
    op.drop_table("user_kit_bookmarks")
