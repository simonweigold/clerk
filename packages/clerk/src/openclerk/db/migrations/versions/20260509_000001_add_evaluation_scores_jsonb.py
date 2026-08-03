"""Add evaluation_scores JSONB column to step_executions

Revision ID: f3a1c8e92d74
Revises: ac8ba97f2c5d
Create Date: 2026-05-09 00:00:01.000000+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f3a1c8e92d74"
down_revision: Union[str, None] = "ac8ba97f2c5d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "step_executions",
        sa.Column(
            "evaluation_scores",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("step_executions", "evaluation_scores")
