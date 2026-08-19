import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models.appointment import Appointment
from app.db.models.clinic import Clinic
from app.db.models.enums import AppointmentStatus
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentRead,
    AppointmentUpdate,
    AvailabilitySlot,
)
from app.services.appointments import create_appointment, get_available_slots
from app.services.audit import add_audit_event

router = APIRouter()


ALLOWED_STATUS_TRANSITIONS = {
    AppointmentStatus.REQUESTED: {
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.CANCELLED,
    },
    AppointmentStatus.CONFIRMED: {
        AppointmentStatus.CHECKED_IN,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.CHECKED_IN: {
        AppointmentStatus.COMPLETED,
        AppointmentStatus.CANCELLED,
    },
    AppointmentStatus.COMPLETED: set(),
    AppointmentStatus.CANCELLED: set(),
    AppointmentStatus.NO_SHOW: set(),
}


async def _tenant_appointment(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
) -> Appointment:
    appointment = await db.scalar(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.clinic_id == clinic_id,
        )
    )
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.get("", response_model=list[AppointmentRead])
async def list_appointments(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return list(
        (
            await db.scalars(
                select(Appointment)
                .where(Appointment.clinic_id == user.clinic_id)
                .order_by(Appointment.starts_at.desc())
                .limit(500)
            )
        ).all()
    )


@router.get("/availability", response_model=list[AvailabilitySlot])
async def availability(
    service_id: uuid.UUID,
    target_date: date = Query(alias="date"),
    staff_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    clinic = await db.get(Clinic, user.clinic_id)
    if clinic is None:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return await get_available_slots(
        db,
        clinic_id=user.clinic_id,
        service_id=service_id,
        target_date=target_date,
        timezone_name=clinic.timezone,
        staff_id=staff_id,
    )


@router.post("", response_model=AppointmentRead)
async def create(
    payload: AppointmentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    appt = await create_appointment(
        db,
        clinic_id=user.clinic_id,
        client_id=payload.client_id,
        lead_id=payload.lead_id,
        service_id=payload.service_id,
        staff_id=payload.staff_id,
        starts_at=payload.starts_at,
        source=payload.source,
        customer_note=payload.customer_note,
        internal_note=payload.internal_note,
    )
    await db.commit()
    await db.refresh(appt)
    return appt


@router.patch("/{appointment_id}", response_model=AppointmentRead)
async def update_appointment(
    appointment_id: uuid.UUID,
    payload: AppointmentUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    appointment = await _tenant_appointment(
        db,
        clinic_id=user.clinic_id,
        appointment_id=appointment_id,
    )

    changes = payload.model_dump(exclude_unset=True)

    new_status = changes.get("status")
    if new_status is not None and new_status != appointment.status:
        allowed = ALLOWED_STATUS_TRANSITIONS[appointment.status]
        if new_status not in allowed:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Invalid appointment transition: "
                    f"{appointment.status.value} -> {new_status.value}"
                ),
            )
        appointment.status = new_status

    if "internal_note" in changes:
        appointment.internal_note = changes["internal_note"]

    add_audit_event(
        db,
        clinic_id=user.clinic_id,
        actor_type="user",
        actor_id=user.id,
        action="appointment.update",
        resource_type="appointment",
        resource_id=appointment.id,
        metadata={
            "status": appointment.status.value,
            "internal_note_updated": "internal_note" in changes,
        },
    )

    await db.commit()
    await db.refresh(appointment)
    return appointment
