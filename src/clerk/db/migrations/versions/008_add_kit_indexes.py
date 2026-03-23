"""Add indexes on reasoning_kits for performance.

Revision ID: 008_add_kit_indexes
Revises: ac8ba97f2c5d
Create Date: 2026-03-19
"""

from alembic import op

revision = "008_add_kit_indexes"
down_revision = "ac8ba97f2c5d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add indexes on frequently queried columns."""
    # Index on slug for kit lookups
    op.create_index(
        "ix_reasoning_kits_slug",
        "reasoning_kits",
        ["slug"],
        unique=False,
    )

    # Index on owner_id for user's kits
    op.create_index(
        "ix_reasoning_kits_owner_id",
        "reasoning_kits",
        ["owner_id"],
        unique=False,
    )

    # Composite index on is_public + created_at for listing public kits
    op.create_index(
        "ix_reasoning_kits_is_public_created_at",
        "reasoning_kits",
        ["is_public", "created_at"],
        unique=False,
    )

    # Index on is_public + owner_id for owner-specific queries
    op.create_index(
        "ix_reasoning_kits_is_public_owner_id",
        "reasoning_kits",
        ["is_public", "owner_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove indexes."""
    op.drop_index("ix_reasoning_kits_is_public_owner_id", table_name="reasoning_kits")
    op.drop_index("ix_reasoning_kits_is_public_created_at", table_name="reasoning_kits")
    op.drop_index("ix_reasoning_kits_owner_id", table_name="reasoning_kits")
    op.drop_index("ix_reasoning_kits_slug", table_name="reasoning_kits")
