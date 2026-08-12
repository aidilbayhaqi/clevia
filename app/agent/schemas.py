from __future__ import annotations

from pydantic import BaseModel, Field

from app.db.models.enums import AgentState


class SourceReference(BaseModel):
    source_ref: str
    title: str | None = None
    document_id: str | None = None
    version: int | None = None


class HandoffResult(BaseModel):
    reason: str
    summary: str
    status: str


class AgentResult(BaseModel):
    message: str
    state: AgentState
    intent: str
    sources: list[SourceReference] = Field(default_factory=list)
    tools_used: list[dict] = Field(default_factory=list)
    handoff: HandoffResult | None = None
    trace_id: str
    prompt_id: str
    prompt_version: str
