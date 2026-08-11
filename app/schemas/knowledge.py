import uuid
from datetime import datetime
from pydantic import BaseModel
from app.db.models.enums import KnowledgeStatus

class KnowledgeCreate(BaseModel):
    title: str
    category: str
    content: str

class KnowledgeUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    content: str | None = None

class KnowledgeRead(BaseModel):
    id: uuid.UUID
    title: str
    category: str
    content: str
    status: KnowledgeStatus
    version: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
