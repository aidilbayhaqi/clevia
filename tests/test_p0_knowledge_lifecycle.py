import inspect

from app.api.v1.routes import knowledge
from app.db.models.enums import KnowledgeStatus
from app.knowledge import retrieval


def test_production_retrieval_requires_approved() -> None:
    source = inspect.getsource(retrieval.RetrievalService.search)
    assert "KnowledgeStatus.APPROVED" in source


def test_legacy_publish_is_approval_alias() -> None:
    source = inspect.getsource(knowledge.publish_knowledge_legacy)
    assert "_approve(" in source


def test_required_states_exist() -> None:
    assert KnowledgeStatus.DRAFT.value == "draft"
    assert KnowledgeStatus.APPROVED.value == "approved"
    assert KnowledgeStatus.ARCHIVED.value == "archived"
