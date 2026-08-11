import uuid
from decimal import Decimal
from pydantic import BaseModel

class ClinicPublic(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    tagline: str | None
    description: str | None
    timezone: str
    phone: str | None
    email: str | None
    address: str | None
    instagram: str | None
    brand_primary: str
    brand_secondary: str
    brand_accent: str
    model_config = {"from_attributes": True}

class ServicePublic(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    category: str
    short_description: str | None
    description: str | None
    duration_minutes: int
    price_from: Decimal | None
    currency: str
    model_config = {"from_attributes": True}

class StaffPublic(BaseModel):
    id: uuid.UUID
    full_name: str
    slug: str
    staff_type: str
    title: str | None
    specialty: str | None
    bio: str | None
    model_config = {"from_attributes": True}
