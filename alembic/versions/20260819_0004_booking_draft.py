"""Sprint 4 persistent booking draft.

Revision ID: 20260819_0004
Revises: 20260815_0003
Create Date: 2026-08-19
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260819_0004"
down_revision: str | Sequence[str] | None = "20260815_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE conversations "
        "ADD COLUMN IF NOT EXISTS booking_draft JSONB NOT NULL "
        "DEFAULT '{}'::jsonb"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE conversations "
        "DROP COLUMN IF EXISTS booking_draft"
    )
