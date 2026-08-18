import inspect

from app.api.v1.routes import conversations, knowledge
from app.knowledge import retrieval


def test_knowledge_document_lookup_is_tenant_scoped() -> None:
    source = inspect.getsource(knowledge._tenant_document)
    assert "KnowledgeDocument.id == document_id" in source
    assert "KnowledgeDocument.clinic_id == clinic_id" in source


def test_conversation_lookup_is_tenant_scoped() -> None:
    source = inspect.getsource(conversations._tenant_conversation)
    assert "Conversation.id == conversation_id" in source
    assert "Conversation.clinic_id == clinic_id" in source


def test_retrieval_is_tenant_approved_validity_scoped() -> None:
    source = inspect.getsource(retrieval.RetrievalService.search)
    assert "KnowledgeDocument.clinic_id == clinic_id" in source
    assert "KnowledgeDocument.status == KnowledgeStatus.APPROVED" in source
    assert "KnowledgeChunk.clinic_id == clinic_id" in source
    assert "KnowledgeDocument.valid_from" in source
    assert "KnowledgeDocument.valid_until" in source
