from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.crm import Lead
from app.db.models.service import Service
from app.services.lead_capture import resolve_interest_service_id

YES_RE = re.compile(
    r"^\s*(ya|iya|yes|y|oke|ok|setuju|konfirmasi|confirm)\s*[.!]?\s*$",
    re.IGNORECASE,
)
NO_RE = re.compile(
    r"^\s*(tidak|nggak|gak|ga|no|n|batal|cancel|jangan)\s*[.!]?\s*$",
    re.IGNORECASE,
)
CANCEL_RE = re.compile(
    r"\b(batal|cancel|batalkan|jangan\s+booking|tidak\s+jadi)\b",
    re.IGNORECASE,
)
SLOT_RE = re.compile(r"^\s*(?:pilih\s*)?([1-5])\s*$", re.IGNORECASE)

MONTHS_ID = (
    "",
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "Mei",
    "Jun",
    "Jul",
    "Agu",
    "Sep",
    "Okt",
    "Nov",
    "Des",
)


def empty_booking_draft() -> dict:
    return {}


def parse_target_date(
    message: str,
    *,
    today: date,
) -> date | None:
    text = " ".join(message.lower().strip().split())

    if text in {"besok", "tomorrow"}:
        return today + timedelta(days=1)
    if text in {"lusa"}:
        return today + timedelta(days=2)

    for pattern, order in (
        (r"\b(\d{4})-(\d{2})-(\d{2})\b", "ymd"),
        (r"\b(\d{2})/(\d{2})/(\d{4})\b", "dmy"),
        (r"\b(\d{2})-(\d{2})-(\d{4})\b", "dmy"),
    ):
        match = re.search(pattern, text)
        if not match:
            continue

        first, second, third = (int(value) for value in match.groups())
        try:
            if order == "ymd":
                return date(first, second, third)
            return date(third, second, first)
        except ValueError:
            return None

    return None


def is_confirmation(message: str) -> bool:
    return bool(YES_RE.match(message))


def is_rejection(message: str) -> bool:
    return bool(NO_RE.match(message))


def is_booking_cancel(message: str) -> bool:
    return bool(CANCEL_RE.search(message))


def parse_slot_choice(message: str, slot_count: int) -> int | None:
    match = SLOT_RE.match(message)
    if not match:
        return None
    index = int(match.group(1)) - 1
    if index < 0 or index >= slot_count:
        return None
    return index


def _slot_datetime_iso(value: datetime | str) -> str:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value)
    else:
        raise TypeError(
            f"Unsupported slot datetime type: {type(value).__name__}"
        )

    if parsed.tzinfo is None:
        raise ValueError("Availability slot datetime must be timezone-aware")

    return parsed.isoformat()


def serialize_slots(slots: list[dict], *, limit: int = 5) -> list[dict]:
    serialized: list[dict] = []
    for slot in slots[:limit]:
        serialized.append(
            {
                "staff_id": str(slot["staff_id"]),
                "staff_name": slot["staff_name"],
                "starts_at": _slot_datetime_iso(slot["starts_at"]),
                "ends_at": _slot_datetime_iso(slot["ends_at"]),
            }
        )
    return serialized


def format_slot_options(slots: list[dict]) -> str:
    lines: list[str] = []
    for index, slot in enumerate(slots, start=1):
        starts_at = datetime.fromisoformat(slot["starts_at"])
        lines.append(
            f"{index}. {starts_at.day:02d} {MONTHS_ID[starts_at.month]} "
            f"{starts_at.year} pukul {starts_at:%H:%M} — {slot['staff_name']}"
        )
    return "\n".join(lines)


def format_confirmation(draft: dict) -> str:
    slot = draft["selected_slot"]
    starts_at = datetime.fromisoformat(slot["starts_at"])
    return (
        "Konfirmasi booking:\n"
        f"Treatment: {draft['service_name']}\n"
        f"Jadwal: {starts_at.day:02d} {MONTHS_ID[starts_at.month]} "
        f"{starts_at.year} pukul {starts_at:%H:%M}\n"
        f"Practitioner: {slot['staff_name']}\n"
        "Status awal akan REQUESTED sampai dikonfirmasi tim Clevia.\n"
        "Balas YA untuk membuat appointment request, atau TIDAK untuk membatalkan."
    )


async def get_lead(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    lead_id: uuid.UUID,
) -> Lead | None:
    return await db.scalar(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.clinic_id == clinic_id,
        )
    )


async def get_service_for_booking(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    service_id: uuid.UUID,
) -> Service | None:
    return await db.scalar(
        select(Service).where(
            Service.id == service_id,
            Service.clinic_id == clinic_id,
            Service.is_active.is_(True),
            Service.public_visible.is_(True),
        )
    )


async def start_booking_draft(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    lead_id: uuid.UUID,
    user_message: str,
) -> dict:
    lead = await get_lead(
        db,
        clinic_id=clinic_id,
        lead_id=lead_id,
    )
    if lead is None:
        return {"step": "lead_missing"}

    service_id = lead.interest_service_id
    if service_id is None:
        service_id = await resolve_interest_service_id(
            db,
            clinic_id=clinic_id,
            interest=user_message,
        )

    if service_id is None:
        return {
            "version": 1,
            "step": "service",
        }

    service = await get_service_for_booking(
        db,
        clinic_id=clinic_id,
        service_id=service_id,
    )
    if service is None:
        return {
            "version": 1,
            "step": "service",
        }

    return {
        "version": 1,
        "step": "date",
        "service_id": str(service.id),
        "service_name": service.name,
    }


async def apply_service_to_draft(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    draft: dict,
    user_message: str,
) -> dict | None:
    service_id = await resolve_interest_service_id(
        db,
        clinic_id=clinic_id,
        interest=user_message,
    )
    if service_id is None:
        return None

    service = await get_service_for_booking(
        db,
        clinic_id=clinic_id,
        service_id=service_id,
    )
    if service is None:
        return None

    updated = dict(draft)
    updated.update(
        {
            "step": "date",
            "service_id": str(service.id),
            "service_name": service.name,
        }
    )
    return updated


async def clinic_today(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
) -> date:
    from app.db.models.clinic import Clinic

    clinic = await db.get(Clinic, clinic_id)
    if clinic is None:
        raise ValueError("Clinic not found")
    return datetime.now(ZoneInfo(clinic.timezone)).date()
