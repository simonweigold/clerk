"""add paused status to execution run

Revision ID: f85b989ecee5
Revises: 7a9829621a7c
Create Date: 2026-02-22 20:02:26.357775+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f85b989ecee5'
down_revision: Union[str, None] = '7a9829621a7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.drop_constraint('ck_status', 'execution_runs', type_='check')
    op.create_check_constraint(
        'ck_status',
        'execution_runs',
        sa.text("status IN ('running', 'paused', 'completed', 'failed')")
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_constraint('ck_status', 'execution_runs', type_='check')
    op.create_check_constraint(
        'ck_status',
        'execution_runs',
        sa.text("status IN ('running', 'completed', 'failed')")
    )
