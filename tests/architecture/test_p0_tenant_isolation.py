from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_knowledge_document_lookup_is_tenant_scoped() -> None:
    text = source("app/api/v1/routes/knowledge.py")
    assert "KnowledgeDocument.id == document_id" in text
    assert "KnowledgeDocument.clinic_id == clinic_id" in text


def test_conversation_lookup_is_tenant_scoped() -> None:
    text = source("app/api/v1/routes/conversations.py")
    assert "Conversation.id == conversation_id" in text
    assert "Conversation.clinic_id == clinic_id" in text


def test_retrieval_is_tenant_approved_validity_scoped() -> None:
    text = source("app/knowledge/retrieval.py")
    assert "KnowledgeDocument.clinic_id == clinic_id" in text
    assert "KnowledgeDocument.status == KnowledgeStatus.APPROVED" in text
    assert "KnowledgeChunk.clinic_id == clinic_id" in text
    assert "KnowledgeDocument.valid_from" in text
    assert "KnowledgeDocument.valid_until" in text


def test_conversation_route_is_lazy() -> None:
    text = source("app/api/v1/routes/conversations.py")

    assert "\nagent = CleviaAgent()\n" not in text
    assert "def get_agent() -> CleviaAgent:" in text
    assert "await get_agent().run(" in text
