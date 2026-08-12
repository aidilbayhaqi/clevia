import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.db.models.enums import KnowledgeStatus


class KnowledgeCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    category: str = Field(min_length=2, max_length=80)
    content: str = Field(min_length=2)
    source_uri: str | None = Field(default=None, max_length=500)
    source_type: str = Field(default="operational_faq", max_length=80)
    owner: str = Field(default="operations", max_length=120)
    valid_from: date | None = None
    valid_until: date | None = None
    sensitivity: str = Field(default="public", max_length=40)
    language: str = Field(default="id", max_length=16)
    capabilities: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class KnowledgeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    category: str | None = Field(default=None, min_length=2, max_length=80)
    content: str | None = Field(default=None, min_length=2)
    source_uri: str | None = Field(default=None, max_length=500)
    source_type: str | None = Field(default=None, max_length=80)
    owner: str | None = Field(default=None, max_length=120)
    valid_from: date | None = None
    valid_until: date | None = None
    sensitivity: str | None = Field(default=None, max_length=40)
    language: str | None = Field(default=None, max_length=16)
    capabilities: list[str] | None = None
    metadata: dict | None = None


class KnowledgeRead(BaseModel):
    id: uuid.UUID
    title: str
    category: str
    content: str
    status: KnowledgeStatus
    version: int
    source_uri: str | None
    source_type: str
    owner: str
    valid_from: date | None
    valid_until: date | None
    sensitivity: str
    language: str
    capabilities_json: list
    metadata_json: dict
    approved_at: datetime | None
    approved_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
