import uuid
from datetime import datetime
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

class PublicMessageResponse(BaseModel):
    message: str
    conversation_status: str
    tools_used: list[ToolTrace]

class ConversationRead(BaseModel):
    id: uuid.UUID
    channel: str
    status: str
    risk_level: str
    lead_id: uuid.UUID | None
    client_id: uuid.UUID | None
    created_at: datetime
    model_config = {"from_attributes": True}
