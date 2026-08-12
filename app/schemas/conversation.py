import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.enums import FeedbackRating


class ConversationCreateResponse(BaseModel):
    conversation_id: uuid.UUID
    conversation_token: str
    status: str
    agent_state: str = "INFO"


class PublicMessageCreate(BaseModel):
    conversation_token: str
    message: str = Field(min_length=1, max_length=3000)


class ToolTrace(BaseModel):
    name: str
    arguments: dict
    result: dict
    status: str = "success"


class SourceReferenceRead(BaseModel):
    source_ref: str
    title: str | None = None
    document_id: str | None = None
    version: int | None = None


class HandoffRead(BaseModel):
    reason: str
    summary: str
    status: str


class PublicMessageResponse(BaseModel):
    message: str
    conversation_status: str
    tools_used: list[ToolTrace]
    message_id: uuid.UUID | None = None
    state: str = "INFO"
    intent: str | None = None
    sources: list[SourceReferenceRead] = Field(default_factory=list)
    handoff: HandoffRead | None = None
    trace_id: str | None = None


class ConversationRead(BaseModel):
    id: uuid.UUID
    channel: str
    status: str
    agent_state: str
    risk_level: str
    lead_id: uuid.UUID | None
    client_id: uuid.UUID | None
    handoff_reason: str | None = None
    handoff_summary: str | None = None
    handoff_at: datetime | None = None
    assigned_user_id: uuid.UUID | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class MessageRead(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    sender_type: str
    content: str
    model_name: str | None = None
    trace_id: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class StaffMessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=3000)


class FeedbackCreate(BaseModel):
    rating: FeedbackRating
    note: str | None = Field(default=None, max_length=2000)


class FeedbackRead(BaseModel):
    id: uuid.UUID
    message_id: uuid.UUID
    trace_id: str | None
    rating: str
    note: str | None
    user_id: uuid.UUID
    created_at: datetime
    model_config = {"from_attributes": True}
