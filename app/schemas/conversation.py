import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ConversationCreateResponse(BaseModel):
    conversation_id: uuid.UUID
    conversation_token: str
    status: str


class PublicMessageCreate(BaseModel):
    conversation_token: str
    message: str = Field(min_length=1, max_length=3000)


class ToolTrace(BaseModel):
    name: str
    arguments: dict
    result: dict
    status: str | None = None


class PublicMessageResponse(BaseModel):
    message: str
    message_id: uuid.UUID | None = None
    conversation_status: str
    state: str | None = None
    intent: str | None = None
    tools_used: list[ToolTrace] = Field(default_factory=list)
    sources: list[dict] = Field(default_factory=list)
    handoff: dict | None = None
    trace_id: str | None = None


class ConversationRead(BaseModel):
    id: uuid.UUID
    channel: str
    status: str
    risk_level: str
    lead_id: uuid.UUID | None
    client_id: uuid.UUID | None
    agent_state: str | None = None
    assigned_user_id: uuid.UUID | None = None
    handoff_reason: str | None = None
    handoff_summary: str | None = None
    handoff_at: datetime | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

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
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class StaffMessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=3000)


class FeedbackRating(StrEnum):
    GOOD = "good"
    WRONG = "wrong"
    MISSING_KNOWLEDGE = "missing_knowledge"


class FeedbackCreate(BaseModel):
    rating: FeedbackRating
    note: str | None = Field(default=None, max_length=2000)


class FeedbackRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    message_id: uuid.UUID
    trace_id: str | None = None
    user_id: uuid.UUID
    rating: str
    note: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}