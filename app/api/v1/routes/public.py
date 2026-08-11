import secrets
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.clinic import Clinic
from app.db.models.conversation import Conversation
from app.db.models.crm import Lead
from app.db.models.enums import AppointmentSource, LeadSource, LeadStatus
from app.db.models.service import Service
from app.db.models.staff import Staff
from app.db.session import get_db
from app.schemas.appointment import AvailabilitySlot, AppointmentRead, PublicAppointmentRequest
from app.schemas.conversation import ConversationCreateResponse
from app.schemas.public import ClinicPublic, ServicePublic, StaffPublic
from app.services.appointments import create_appointment, get_available_slots
from app.services.cache import cache_get_json, cache_key, cache_set_json


router = APIRouter()


async def active_clinic(db: AsyncSession) -> Clinic:
    clinic = await db.scalar(
        select(Clinic).where(Clinic.is_active.is_(True)).limit(1)
    )
    if clinic is None:
        raise HTTPException(status_code=404, detail="Clinic not configured")
    return clinic


@router.get("/clinic", response_model=ClinicPublic)
async def clinic_public(db: AsyncSession = Depends(get_db)):
    key = cache_key("public", "clinic")
    cached = await cache_get_json(key)
    if cached is not None:
        return cached

    clinic = await active_clinic(db)
    payload = ClinicPublic.model_validate(clinic).model_dump(mode="json")
    await cache_set_json(
        key,
        payload,
        settings.CACHE_TTL_CLINIC_SECONDS,
    )
    return payload


@router.get("/services", response_model=list[ServicePublic])
async def services_public(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    clinic = await active_clinic(db)
    key = cache_key(
        "public",
        "services",
        clinic.id,
        category or "all",
    )
    cached = await cache_get_json(key)
    if cached is not None:
        return cached

    query = select(Service).where(
        Service.clinic_id == clinic.id,
        Service.is_active.is_(True),
        Service.public_visible.is_(True),
    )
    if category:
        query = query.where(Service.category == category)

    services = list(
        (await db.scalars(query.order_by(Service.name))).all()
    )
    payload = [
        ServicePublic.model_validate(item).model_dump(mode="json")
        for item in services
    ]
    await cache_set_json(
        key,
        payload,
        settings.CACHE_TTL_SERVICES_SECONDS,
    )
    return payload


@router.get("/staff", response_model=list[StaffPublic])
async def staff_public(db: AsyncSession = Depends(get_db)):
    clinic = await active_clinic(db)
    key = cache_key("public", "staff", clinic.id)
    cached = await cache_get_json(key)
    if cached is not None:
        return cached

    staff = list(
        (
            await db.scalars(
                select(Staff)
                .where(
                    Staff.clinic_id == clinic.id,
                    Staff.is_active.is_(True),
                    Staff.public_visible.is_(True),
                )
                .order_by(Staff.full_name)
            )
        ).all()
    )
    payload = [
        StaffPublic.model_validate(item).model_dump(mode="json")
        for item in staff
    ]
    await cache_set_json(
        key,
        payload,
        settings.CACHE_TTL_STAFF_SECONDS,
    )
    return payload


@router.get("/availability", response_model=list[AvailabilitySlot])
async def availability_public(
    service_id: uuid.UUID,
    date_value: date = Query(alias="date"),
    staff_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    clinic = await active_clinic(db)
    key = cache_key(
        "availability",
        clinic.id,
        service_id,
        date_value.isoformat(),
        staff_id or "all",
    )
    cached = await cache_get_json(key)
    if cached is not None:
        return cached

    slots = await get_available_slots(
        db,
        clinic_id=clinic.id,
        service_id=service_id,
        target_date=date_value,
        timezone_name=clinic.timezone,
        staff_id=staff_id,
    )
    payload = [
        AvailabilitySlot(**slot).model_dump(mode="json")
        for slot in slots
    ]
    await cache_set_json(
        key,
        payload,
        settings.CACHE_TTL_AVAILABILITY_SECONDS,
    )
    return payload


@router.post("/appointment-requests", response_model=AppointmentRead)
async def appointment_request(
    payload: PublicAppointmentRequest,
    db: AsyncSession = Depends(get_db),
):
    clinic = await active_clinic(db)

    lead = await db.scalar(
        select(Lead).where(
            Lead.clinic_id == clinic.id,
            Lead.phone == payload.phone,
        )
    )
    if lead is None:
        lead = Lead(
            clinic_id=clinic.id,
            full_name=payload.full_name,
            phone=payload.phone,
            email=str(payload.email) if payload.email else None,
            source=LeadSource.WEBSITE,
            status=LeadStatus.BOOKED,
            interest_service_id=payload.service_id,
        )
        db.add(lead)
        await db.flush()

    appointment = await create_appointment(
        db,
        clinic_id=clinic.id,
        lead_id=lead.id,
        service_id=payload.service_id,
        staff_id=payload.staff_id,
        starts_at=payload.starts_at,
        source=AppointmentSource.WEBSITE,
        customer_note=payload.note,
    )
    await db.commit()
    await db.refresh(appointment)
    return appointment


@router.post("/conversations", response_model=ConversationCreateResponse)
async def create_conversation(db: AsyncSession = Depends(get_db)):
    clinic = await active_clinic(db)
    conversation = Conversation(
        clinic_id=clinic.id,
        public_token=secrets.token_urlsafe(40),
        channel="web",
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return ConversationCreateResponse(
        conversation_id=conversation.id,
        conversation_token=conversation.public_token,
        status=conversation.status.value,
    )
