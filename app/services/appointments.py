import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.appointment import Appointment
from app.db.models.enums import AppointmentSource, AppointmentStatus
from app.db.models.service import Service
from app.db.models.staff import Staff, StaffAvailability, staff_services
from app.services.cache import cache_delete_pattern, cache_key

BLOCKING_STATUSES = {
    AppointmentStatus.REQUESTED,
    AppointmentStatus.CONFIRMED,
    AppointmentStatus.CHECKED_IN,
}


async def get_service(db: AsyncSession, service_id: uuid.UUID) -> Service:
    service = await db.scalar(
        select(Service).where(
            Service.id == service_id,
            Service.is_active.is_(True),
        )
    )
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


async def _validate_booking_rules(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    service: Service,
    staff_id: uuid.UUID,
    starts_at: datetime,
) -> Staff:
    if starts_at.tzinfo is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="starts_at must contain timezone information.",
        )

    staff = await db.scalar(
        select(Staff)
        .join(staff_services, staff_services.c.staff_id == Staff.id)
        .where(
            Staff.id == staff_id,
            Staff.clinic_id == clinic_id,
            Staff.is_active.is_(True),
            staff_services.c.service_id == service.id,
        )
    )
    if staff is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Selected practitioner does not provide this service.",
        )

    local_start = starts_at.astimezone(ZoneInfo("Asia/Jakarta"))
    local_end = local_start + timedelta(minutes=service.duration_minutes)

    windows = list(
        (
            await db.scalars(
                select(StaffAvailability).where(
                    StaffAvailability.staff_id == staff.id,
                    StaffAvailability.weekday == local_start.weekday(),
                )
            )
        ).all()
    )

    inside_working_window = any(
        local_start.time().replace(tzinfo=None) >= window.start_time
        and local_end.time().replace(tzinfo=None) <= window.end_time
        for window in windows
    )
    if not inside_working_window:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Selected time is outside practitioner availability.",
        )

    return staff


async def create_appointment(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    service_id: uuid.UUID,
    staff_id: uuid.UUID,
    starts_at: datetime,
    source: AppointmentSource,
    client_id: uuid.UUID | None = None,
    lead_id: uuid.UUID | None = None,
    customer_note: str | None = None,
    internal_note: str | None = None,
) -> Appointment:
    service = await get_service(db, service_id)

    if service.clinic_id != clinic_id:
        raise HTTPException(status_code=404, detail="Service not found")

    await _validate_booking_rules(
        db,
        clinic_id=clinic_id,
        service=service,
        staff_id=staff_id,
        starts_at=starts_at,
    )

    advisory_key = int.from_bytes(staff_id.bytes[:8], "big", signed=True)
    await db.execute(select(func.pg_advisory_xact_lock(advisory_key)))

    ends_at = starts_at + timedelta(minutes=service.duration_minutes)

    conflict = await db.scalar(
        select(Appointment.id)
        .where(
            Appointment.clinic_id == clinic_id,
            Appointment.staff_id == staff_id,
            Appointment.status.in_(BLOCKING_STATUSES),
            Appointment.starts_at < ends_at,
            Appointment.ends_at > starts_at,
        )
        .limit(1)
    )
    if conflict is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Selected slot is no longer available.",
        )

    appointment = Appointment(
        clinic_id=clinic_id,
        client_id=client_id,
        lead_id=lead_id,
        service_id=service_id,
        staff_id=staff_id,
        starts_at=starts_at,
        ends_at=ends_at,
        status=AppointmentStatus.REQUESTED,
        source=source,
        customer_note=customer_note,
        internal_note=internal_note,
    )
    db.add(appointment)
    await db.flush()

    await cache_delete_pattern(cache_key("availability", clinic_id, "*"))
    return appointment


async def find_exact_active_appointment(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    lead_id: uuid.UUID,
    service_id: uuid.UUID,
    staff_id: uuid.UUID,
    starts_at: datetime,
) -> Appointment | None:
    return await db.scalar(
        select(Appointment)
        .where(
            Appointment.clinic_id == clinic_id,
            Appointment.lead_id == lead_id,
            Appointment.service_id == service_id,
            Appointment.staff_id == staff_id,
            Appointment.starts_at == starts_at,
            Appointment.status.in_(BLOCKING_STATUSES),
        )
        .order_by(Appointment.created_at.desc())
        .limit(1)
    )


async def create_appointment_idempotent(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    lead_id: uuid.UUID,
    service_id: uuid.UUID,
    staff_id: uuid.UUID,
    starts_at: datetime,
    source: AppointmentSource,
    customer_note: str | None = None,
) -> tuple[Appointment, bool]:
    existing = await find_exact_active_appointment(
        db,
        clinic_id=clinic_id,
        lead_id=lead_id,
        service_id=service_id,
        staff_id=staff_id,
        starts_at=starts_at,
    )
    if existing is not None:
        return existing, True

    appointment = await create_appointment(
        db,
        clinic_id=clinic_id,
        lead_id=lead_id,
        service_id=service_id,
        staff_id=staff_id,
        starts_at=starts_at,
        source=source,
        customer_note=customer_note,
    )
    return appointment, False


async def get_available_slots(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    service_id: uuid.UUID,
    target_date: date,
    timezone_name: str,
    staff_id: uuid.UUID | None = None,
) -> list[dict]:
    service = await get_service(db, service_id)
    if service.clinic_id != clinic_id:
        raise HTTPException(status_code=404, detail="Service not found")

    weekday = target_date.weekday()

    query = (
        select(Staff)
        .join(staff_services, staff_services.c.staff_id == Staff.id)
        .where(
            Staff.clinic_id == clinic_id,
            Staff.is_active.is_(True),
            staff_services.c.service_id == service_id,
        )
    )
    if staff_id:
        query = query.where(Staff.id == staff_id)

    staff_members = list((await db.scalars(query)).all())
    if not staff_members:
        return []

    tz = ZoneInfo(timezone_name)
    duration = timedelta(minutes=service.duration_minutes)
    slots: list[dict] = []

    for staff in staff_members:
        windows = list(
            (
                await db.scalars(
                    select(StaffAvailability).where(
                        StaffAvailability.staff_id == staff.id,
                        StaffAvailability.weekday == weekday,
                    )
                )
            ).all()
        )

        for window in windows:
            cursor = datetime.combine(target_date, window.start_time, tzinfo=tz)
            window_end = datetime.combine(target_date, window.end_time, tzinfo=tz)

            while cursor + duration <= window_end:
                end = cursor + duration
                conflict = await db.scalar(
                    select(Appointment.id)
                    .where(
                        Appointment.staff_id == staff.id,
                        Appointment.status.in_(BLOCKING_STATUSES),
                        Appointment.starts_at < end,
                        Appointment.ends_at > cursor,
                    )
                    .limit(1)
                )
                if conflict is None:
                    slots.append(
                        {
                            "staff_id": staff.id,
                            "staff_name": staff.full_name,
                            "starts_at": cursor,
                            "ends_at": end,
                        }
                    )
                cursor += duration

    return sorted(slots, key=lambda item: item["starts_at"])
