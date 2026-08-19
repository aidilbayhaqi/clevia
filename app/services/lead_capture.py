from __future__ import annotations

import re
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.router import Intent, route_intent
from app.db.models.conversation import Message
from app.db.models.crm import Lead
from app.db.models.service import Service

PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?62|0)(?:[\s().-]*\d){8,13}(?!\d)",
    re.IGNORECASE,
)

EXPLICIT_NAME_PATTERNS = (
    re.compile(r"\bnama\s+saya\s+([^,;.!?\n]{2,80})", re.IGNORECASE),
    re.compile(r"\bnama\s*[:=-]\s*([^,;.!?\n]{2,80})", re.IGNORECASE),
    re.compile(r"\bpanggil\s+saya\s+([^,;.!?\n]{2,80})", re.IGNORECASE),
)

ASK_NAME_RE = re.compile(
    r"\b(nama|siapa\s+nama|boleh\s+tahu\s+nama|panggilan)\b",
    re.IGNORECASE,
)
ASK_PHONE_RE = re.compile(
    r"\b(whatsapp|nomor\s+wa|nomor\s+telepon|nomor\s+hp|telepon|phone)\b",
    re.IGNORECASE,
)

OPT_OUT_RE = re.compile(
    r"\b("
    r"(?:tidak|nggak|gak|ga)\s+(?:mau|ingin)\s+(?:kasih|beri|share|bagikan)"
    r"|jangan\s+hubungi"
    r"|tidak\s+usah\s+(?:hubungi|kontak)"
    r")\b",
    re.IGNORECASE,
)

NAME_REJECT_WORDS = {
    "tertarik",
    "booking",
    "reservasi",
    "jadwal",
    "facial",
    "treatment",
    "laser",
    "harga",
    "admin",
    "alamat",
    "instagram",
    "whatsapp",
}


def normalize_phone_number(value: str | None) -> str | None:
    if value is None:
        return None

    digits = re.sub(r"\D", "", value)
    if digits.startswith("00"):
        digits = digits[2:]

    if digits.startswith("0"):
        digits = "62" + digits[1:]
    elif not digits.startswith("62"):
        # Clevia currently operates in Indonesia; short local mobile input is
        # interpreted as an Indonesian number.
        if 9 <= len(digits) <= 13:
            digits = "62" + digits
        else:
            return None

    if not (10 <= len(digits) <= 15):
        return None

    return f"+{digits}"


def _looks_like_plain_name(value: str) -> bool:
    candidate = " ".join(value.strip().split())
    if not (2 <= len(candidate) <= 80):
        return False

    words = candidate.split()
    if not (1 <= len(words) <= 5):
        return False

    lowered = {word.lower().strip(".'-") for word in words}
    if lowered & NAME_REJECT_WORDS:
        return False

    if any(char.isdigit() for char in candidate):
        return False

    return all(
        all(char.isalpha() or char in ".'-" for char in word)
        for word in words
    )


def _explicit_name(text: str) -> str | None:
    for pattern in EXPLICIT_NAME_PATTERNS:
        match = pattern.search(text)
        if match:
            candidate = " ".join(match.group(1).strip().split())
            if _looks_like_plain_name(candidate):
                return candidate
    return None


def _assistant_asked_name(message: Message | None) -> bool:
    return bool(
        message
        and message.role == "assistant"
        and ASK_NAME_RE.search(message.content)
    )


def _assistant_asked_phone(message: Message | None) -> bool:
    return bool(
        message
        and message.role == "assistant"
        and ASK_PHONE_RE.search(message.content)
    )


def extract_lead_name(history: list[Message], user_message: str) -> str | None:
    for message in [*history, Message(
        conversation_id=uuid.uuid4(),
        role="user",
        sender_type="visitor",
        content=user_message,
    )]:
        if message.role != "user":
            continue
        explicit = _explicit_name(message.content)
        if explicit:
            return explicit

    for index, message in enumerate(history):
        if message.role != "user" or index == 0:
            continue
        if _assistant_asked_name(history[index - 1]) and _looks_like_plain_name(message.content):
            return " ".join(message.content.strip().split())

    previous = history[-1] if history else None
    if _assistant_asked_name(previous) and _looks_like_plain_name(user_message):
        return " ".join(user_message.strip().split())

    return None


def extract_lead_phone(history: list[Message], user_message: str) -> str | None:
    for text in [user_message, *[message.content for message in reversed(history) if message.role == "user"]]:
        match = PHONE_RE.search(text)
        if not match:
            continue
        normalized = normalize_phone_number(match.group(0))
        if normalized:
            return normalized
    return None


def lead_interest_text(history: list[Message], user_message: str) -> str | None:
    for message in history:
        if message.role != "user":
            continue
        if route_intent(message.content) in {Intent.SERVICE_INTEREST, Intent.BOOKING_INTEREST}:
            return " ".join(message.content.strip().split())[:240]

    if route_intent(user_message) in {Intent.SERVICE_INTEREST, Intent.BOOKING_INTEREST}:
        return " ".join(user_message.strip().split())[:240]

    return None


def lead_capture_opt_out(user_message: str) -> bool:
    return bool(OPT_OUT_RE.search(user_message))


def next_lead_question(
    *,
    full_name: str | None,
    phone: str | None,
) -> tuple[str | None, str | None]:
    if not full_name:
        return "full_name", "Boleh tahu nama kamu?"
    if not phone:
        return "phone", "Nomor WhatsApp yang bisa dihubungi tim Clevia berapa?"
    return None, None


def ensure_lead_collection_question(reply: str, missing_field: str | None) -> str:
    if missing_field == "full_name":
        if ASK_NAME_RE.search(reply):
            return reply
        return f"{reply.rstrip()} Boleh tahu nama kamu?".strip()

    if missing_field == "phone":
        if ASK_PHONE_RE.search(reply):
            return reply
        return (
            f"{reply.rstrip()} Nomor WhatsApp yang bisa dihubungi tim Clevia berapa?"
        ).strip()

    return reply


async def find_existing_lead_by_phone(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    phone: str,
) -> Lead | None:
    normalized = normalize_phone_number(phone)
    if normalized is None:
        return None

    canonical_digits = re.sub(r"\D", "", normalized)
    local_digits = (
        "0" + canonical_digits[2:]
        if canonical_digits.startswith("62")
        else canonical_digits
    )

    stored_digits = func.regexp_replace(Lead.phone, r"[^0-9]", "", "g")
    return await db.scalar(
        select(Lead)
        .where(
            Lead.clinic_id == clinic_id,
            or_(
                stored_digits == canonical_digits,
                stored_digits == local_digits,
            ),
        )
        .order_by(Lead.updated_at.desc(), Lead.created_at.desc())
        .limit(1)
    )


async def resolve_interest_service_id(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    interest: str | None,
) -> uuid.UUID | None:
    if not interest:
        return None

    normalized = " ".join(interest.lower().strip().split())
    services = list(
        (
            await db.scalars(
                select(Service)
                .where(
                    Service.clinic_id == clinic_id,
                    Service.is_active.is_(True),
                    Service.public_visible.is_(True),
                )
                .order_by(Service.name)
            )
        ).all()
    )

    # Prefer explicit service-name/slug mentions, longest name first.
    for service in sorted(services, key=lambda item: len(item.name), reverse=True):
        name = " ".join(service.name.lower().split())
        slug_text = service.slug.lower().replace("-", " ")
        if name in normalized or slug_text in normalized:
            return service.id

    category_matches = [
        service
        for service in services
        if service.category
        and service.category.lower() in normalized
    ]
    if len(category_matches) == 1:
        return category_matches[0].id

    return None
