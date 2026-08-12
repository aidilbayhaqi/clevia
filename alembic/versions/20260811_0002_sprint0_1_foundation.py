"""Sprint 0 + 1 foundation and informational MVP schema.

Revision ID: 20260811_0002
Revises: 20260808_0001
Create Date: 2026-08-11

The initial Clevia migration creates tables dynamically from current SQLAlchemy metadata.
For that reason this migration intentionally uses IF NOT EXISTS so it is safe both for
existing v0.1 databases and for fresh databases created after this update.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260811_0002"
down_revision: Union[str, Sequence[str], None] = "20260808_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # SQLAlchemy Enum persists enum member names. Add APPROVED in an autocommit block
    # before using it to migrate legacy PUBLISHED rows.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE knowledge_status ADD VALUE IF NOT EXISTS 'APPROVED'")

    op.execute(
        """
        ALTER TABLE conversations
            ADD COLUMN IF NOT EXISTS agent_state VARCHAR(30) NOT NULL DEFAULT 'INFO',
            ADD COLUMN IF NOT EXISTS handoff_reason VARCHAR(120),
            ADD COLUMN IF NOT EXISTS handoff_summary TEXT,
            ADD COLUMN IF NOT EXISTS handoff_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS assigned_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ
        """
    )
    op.execute(
        "ALTER TABLE messages ADD COLUMN IF NOT EXISTS trace_id VARCHAR(64)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_messages_trace_id ON messages(trace_id)")

    op.execute(
        """
        ALTER TABLE knowledge_documents
            ADD COLUMN IF NOT EXISTS source_uri VARCHAR(500),
            ADD COLUMN IF NOT EXISTS source_type VARCHAR(80) NOT NULL DEFAULT 'operational_faq',
            ADD COLUMN IF NOT EXISTS owner VARCHAR(120) NOT NULL DEFAULT 'operations',
            ADD COLUMN IF NOT EXISTS valid_from DATE,
            ADD COLUMN IF NOT EXISTS valid_until DATE,
            ADD COLUMN IF NOT EXISTS sensitivity VARCHAR(40) NOT NULL DEFAULT 'public',
            ADD COLUMN IF NOT EXISTS language VARCHAR(16) NOT NULL DEFAULT 'id',
            ADD COLUMN IF NOT EXISTS capabilities_json JSONB NOT NULL DEFAULT '[]'::jsonb,
            ADD COLUMN IF NOT EXISTS metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS approved_by UUID REFERENCES users(id) ON DELETE SET NULL
        """
    )
    op.execute(
        "UPDATE knowledge_documents SET status = 'APPROVED' "
        "WHERE status::text = 'PUBLISHED'"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id UUID PRIMARY KEY,
            clinic_id UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
            document_id UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            embedding vector(1536),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_kb_chunk_index UNIQUE (document_id, chunk_index)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_clinic_id ON knowledge_chunks(clinic_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_document_id ON knowledge_chunks(document_id)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_traces (
            trace_id VARCHAR(64) PRIMARY KEY,
            request_id VARCHAR(64) NOT NULL,
            clinic_id UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
            conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
            prompt_id VARCHAR(100),
            prompt_version VARCHAR(40),
            provider VARCHAR(40),
            model VARCHAR(100),
            intent VARCHAR(80),
            state VARCHAR(30),
            retrieval_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
            tool_calls_json JSONB NOT NULL DEFAULT '[]'::jsonb,
            input_tokens INTEGER,
            output_tokens INTEGER,
            latency_ms INTEGER,
            cost NUMERIC(12,6),
            outcome VARCHAR(80),
            error_code VARCHAR(120),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_agent_traces_request_id ON agent_traces(request_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_agent_traces_clinic_id ON agent_traces(clinic_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_agent_traces_conversation_id ON agent_traces(conversation_id)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tool_executions (
            id UUID PRIMARY KEY,
            trace_id VARCHAR(64) NOT NULL,
            clinic_id UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
            conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
            tool_name VARCHAR(100) NOT NULL,
            input_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            output_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            status VARCHAR(30) NOT NULL,
            idempotency_key VARCHAR(160) UNIQUE,
            latency_ms INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_tool_executions_trace_id ON tool_executions(trace_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tool_executions_clinic_id ON tool_executions(clinic_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tool_executions_conversation_id ON tool_executions(conversation_id)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_tool_executions_tool_name ON tool_executions(tool_name)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS message_feedback (
            id UUID PRIMARY KEY,
            clinic_id UUID NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
            message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
            trace_id VARCHAR(64),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            rating VARCHAR(40) NOT NULL,
            note TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_message_feedback_clinic_id ON message_feedback(clinic_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_message_feedback_message_id ON message_feedback(message_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_message_feedback_trace_id ON message_feedback(trace_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_message_feedback_user_id ON message_feedback(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_message_feedback_rating ON message_feedback(rating)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS message_feedback")
    op.execute("DROP TABLE IF EXISTS tool_executions")
    op.execute("DROP TABLE IF EXISTS agent_traces")
    op.execute("DROP TABLE IF EXISTS knowledge_chunks")

    op.execute("ALTER TABLE messages DROP COLUMN IF EXISTS trace_id")
    op.execute(
        """
        ALTER TABLE conversations
            DROP COLUMN IF EXISTS resolved_at,
            DROP COLUMN IF EXISTS assigned_user_id,
            DROP COLUMN IF EXISTS handoff_at,
            DROP COLUMN IF EXISTS handoff_summary,
            DROP COLUMN IF EXISTS handoff_reason,
            DROP COLUMN IF EXISTS agent_state
        """
    )
    op.execute(
        """
        ALTER TABLE knowledge_documents
            DROP COLUMN IF EXISTS approved_by,
            DROP COLUMN IF EXISTS approved_at,
            DROP COLUMN IF EXISTS metadata_json,
            DROP COLUMN IF EXISTS capabilities_json,
            DROP COLUMN IF EXISTS language,
            DROP COLUMN IF EXISTS sensitivity,
            DROP COLUMN IF EXISTS valid_until,
            DROP COLUMN IF EXISTS valid_from,
            DROP COLUMN IF EXISTS owner,
            DROP COLUMN IF EXISTS source_type,
            DROP COLUMN IF EXISTS source_uri
        """
    )
    # PostgreSQL does not support dropping an enum value safely in-place. APPROVED is retained.
