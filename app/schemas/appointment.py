import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.db.models.enums import AppointmentSource, AppointmentStatus

class AvailabilitySlot(BaseModel):
    staff_id: uuid.UUID
    staff_name: str
    starts_at: datetime
    ends_at: datetime

class AppointmentCreate(BaseModel):
    client_id: uuid.UUID | None = None
    lead_id: uuid.UUID | None = None
    service_id: uuid.UUID
    staff_id: uuid.UUID
    starts_at: datetime
    source: AppointmentSource = AppointmentSource.CRM
    customer_note: str | None = None
    internal_note: str | None = None

class PublicAppointmentRequest(BaseModel):
    full_name: str
    phone: str
    email: EmailStr | None = None
    service_id: uuid.UUID
    staff_id: uuid.UUID
    starts_at: datetime
    note: str | None = None

class AppointmentRead(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID | None
    lead_id: uuid.UUID | None
    service_id: uuid.UUID
    staff_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    status: AppointmentStatus
    source: AppointmentSource
    customer_note: str | None
    internal_note: str | None
    created_at: datetime
    model_config = {"from_attributes": True}
