"""Add is_dynamic column to resources table.

Revision ID: 002
Revises: 001_initial_schema
Create Date: 2026-02-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_add_resource_is_dynamic"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_dynamic boolean column to resources table."""
    op.add_column(
        "resources",
        sa.Column(
            "is_dynamic", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )


def downgrade() -> None:
    """Remove is_dynamic column from resources table."""
    op.drop_column("resources", "is_dynamic")
