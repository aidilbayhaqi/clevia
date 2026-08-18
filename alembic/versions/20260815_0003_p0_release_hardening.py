"""P0 release hardening.

Revision ID: 20260815_0003
Revises: 20260811_0002
Create Date: 2026-08-15
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260815_0003"
down_revision: Union[str, Sequence[str], None] = "20260811_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE tool_executions "
        "ADD COLUMN IF NOT EXISTS error_code VARCHAR(120)"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE tool_executions "
        "DROP COLUMN IF EXISTS error_code"
    )
