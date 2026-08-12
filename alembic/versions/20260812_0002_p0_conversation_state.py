"""P0 conversation state, handoff metadata, and trace link.

Revision ID: 20260812_0002
Revises: 20260808_0001
Create Date: 2026-08-12
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260812_0002"
down_revision: Union[str, Sequence[str], None] = "20260808_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE conversations
            ADD COLUMN IF NOT EXISTS agent_state VARCHAR(30) NOT NULL DEFAULT 'INFO',
            ADD COLUMN IF NOT EXISTS assigned_user_id UUID NULL,
            ADD COLUMN IF NOT EXISTS handoff_reason VARCHAR(120) NULL,
            ADD COLUMN IF NOT EXISTS handoff_summary TEXT NULL,
            ADD COLUMN IF NOT EXISTS handoff_at TIMESTAMPTZ NULL,
            ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ NULL;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_conversations_assigned_user_id_users'
            ) THEN
                ALTER TABLE conversations
                ADD CONSTRAINT fk_conversations_assigned_user_id_users
                FOREIGN KEY (assigned_user_id)
                REFERENCES users(id)
                ON DELETE SET NULL;
            END IF;
        END
        $$;
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_conversations_assigned_user_id "
        "ON conversations (assigned_user_id)"
    )

    op.execute(
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS trace_id VARCHAR(64) NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_messages_trace_id ON messages (trace_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_messages_trace_id")
    op.execute("ALTER TABLE messages DROP COLUMN IF EXISTS trace_id")
    op.execute("DROP INDEX IF EXISTS ix_conversations_assigned_user_id")
    op.execute(
        "ALTER TABLE conversations "
        "DROP CONSTRAINT IF EXISTS fk_conversations_assigned_user_id_users"
    )
    op.execute(
        """
        ALTER TABLE conversations
            DROP COLUMN IF EXISTS resolved_at,
            DROP COLUMN IF EXISTS handoff_at,
            DROP COLUMN IF EXISTS handoff_summary,
            DROP COLUMN IF EXISTS handoff_reason,
            DROP COLUMN IF EXISTS assigned_user_id,
            DROP COLUMN IF EXISTS agent_state;
        """
    )