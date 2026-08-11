import uuid
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models.appointment import Appointment
from app.db.models.clinic import Clinic
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.appointment import AppointmentCreate, AppointmentRead, AvailabilitySlot
from app.services.appointments import create_appointment, get_available_slots

router = APIRouter()

@router.get("", response_model=list[AppointmentRead])
async def list_appointments(user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return list((await db.scalars(
        select(Appointment).where(Appointment.clinic_id==user.clinic_id)
        .order_by(Appointment.starts_at.desc()).limit(500)
    )).all())

@router.get("/availability", response_model=list[AvailabilitySlot])
async def availability(
    service_id: uuid.UUID, target_date: date=Query(alias="date"),
    staff_id: uuid.UUID|None=None, user: User=Depends(get_current_user),
    db: AsyncSession=Depends(get_db),
):
    clinic = await db.get(Clinic,user.clinic_id)
    return await get_available_slots(
        db, clinic_id=user.clinic_id, service_id=service_id,
        target_date=target_date, timezone_name=clinic.timezone, staff_id=staff_id,
    )

@router.post("", response_model=AppointmentRead)
async def create(payload: AppointmentCreate, user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    appt = await create_appointment(
        db, clinic_id=user.clinic_id, client_id=payload.client_id, lead_id=payload.lead_id,
        service_id=payload.service_id, staff_id=payload.staff_id,
        starts_at=payload.starts_at, source=payload.source,
        customer_note=payload.customer_note, internal_note=payload.internal_note,
    )
    await db.commit(); await db.refresh(appt); return appt
