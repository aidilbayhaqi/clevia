import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.db.models.enums import LeadSource, LeadStatus


class LeadCreate(BaseModel):
    full_name: str
    phone: str
    email: EmailStr | None = None
    source: LeadSource = LeadSource.MANUAL
    interest_service_id: uuid.UUID | None = None
    notes: str | None = None


class LeadUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    status: LeadStatus | None = None
    interest_service_id: uuid.UUID | None = None
    assigned_to_user_id: uuid.UUID | None = None
    notes: str | None = None


class LeadRead(BaseModel):
    id: uuid.UUID
    full_name: str
    phone: str
    email: EmailStr | None
    source: LeadSource
    status: LeadStatus
    interest_service_id: uuid.UUID | None
    assigned_to_user_id: uuid.UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClientCreate(BaseModel):
    full_name: str
    phone: str
    email: EmailStr | None = None
    birth_date: date | None = None
    tags: list[str] = Field(default_factory=list)
    administrative_notes: str | None = None


class ClientRead(BaseModel):
    id: uuid.UUID
    full_name: str
    phone: str
    email: EmailStr | None
    birth_date: date | None
    tags: list
    administrative_notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
