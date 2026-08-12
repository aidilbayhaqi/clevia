from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Type

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.clinic import Clinic
from app.db.models.conversation import Conversation
from app.db.models.crm import Lead
from app.db.models.enums import AgentState, ConversationStatus, LeadSource
from app.db.models.service import Service
from app.knowledge.retrieval import retrieval_service


class _StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EmptyInput(_StrictInput):
    pass


class ListServicesInput(_StrictInput):
    category: str | None = None


class SearchKnowledgeInput(_StrictInput):
    query: str = Field(min_length=2, max_length=500)


class HandoffInput(_StrictInput):
    reason: str = Field(min_length=2, max_length=120)
    summary: str = Field(min_length=2, max_length=2000)


class CaptureLeadInput(_StrictInput):
    full_name: str | None = Field(default=None, max_length=160)
    phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=255)
    interest: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=1200)


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    description: str
    input_model: Type[BaseModel]

    def openai_schema(self) -> dict:
        schema = self.input_model.model_json_schema()
        properties = schema.get("properties", {})
        schema["required"] = list(properties.keys())
        schema["additionalProperties"] = False
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": schema,
            "strict": True,
        }


TOOL_DEFINITIONS = {
    "get_clinic_profile": ToolDefinition(
        name="get_clinic_profile",
        description=(
            "Get the official profile and public operational information for the business "
            "configured in this single-business deployment."
        ),
        input_model=EmptyInput,
    ),
    "list_services": ToolDefinition(
        name="list_services",
        description=(
            "List active public services for this business, including allowed public price-from values."
        ),
        input_model=ListServicesInput,
    ),
    "search_knowledge": ToolDefinition(
        name="search_knowledge",
        description=(
            "Search approved and currently valid business knowledge and return source references."
        ),
        input_model=SearchKnowledgeInput,
    ),
    "capture_lead": ToolDefinition(
        name="capture_lead",
        description=(
            "Create or update the CRM lead linked to this conversation after the visitor shows "
            "genuine service, purchase, booking, or contact intent. Pass null for unknown optional "
            "fields. Do not call this tool for casual information-only visitors."
        ),
        input_model=CaptureLeadInput,
    ),
    "request_human_handoff": ToolDefinition(
        name="request_human_handoff",
        description=(
            "Place the conversation in the human staff queue with a compact reason and context summary."
        ),
        input_model=HandoffInput,
    ),
}

TOOL_SCHEMAS = [definition.openai_schema() for definition in TOOL_DEFINITIONS.values()]


async def _clinic(db: AsyncSession, clinic_id: uuid.UUID) -> Clinic:
    # `clinic_id` is retained as a compatibility key in the current DB schema.
    # P0 deployment policy is single-business: one deployment/database serves one business.
    clinic = await db.get(Clinic, clinic_id)
    if clinic is None or not clinic.is_active:
        raise ValueError("Business profile not found or inactive")
    return clinic


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = " ".join(value.strip().split())
    return value or None


def _merge_notes(existing: str | None, interest: str | None, notes: str | None) -> str | None:
    parts: list[str] = []
    if existing:
        parts.append(existing.strip())
    if interest:
        marker = f"Interest: {interest}"
        if not existing or marker.lower() not in existing.lower():
            parts.append(marker)
    if notes:
        if not existing or notes.lower() not in existing.lower():
            parts.append(notes)
    combined = "\n".join(part for part in parts if part)
    return combined[:4000] if combined else None


async def _resolve_interest_service_id(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    interest: str | None,
) -> uuid.UUID | None:
    if not interest:
        return None

    normalized = interest.strip()
    if len(normalized) < 2:
        return None

    service = await db.scalar(
        select(Service)
        .where(
            Service.clinic_id == clinic_id,
            Service.is_active.is_(True),
            Service.name.ilike(f"%{normalized}%"),
        )
        .order_by(Service.name)
        .limit(1)
    )
    return service.id if service else None


async def _capture_lead(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    conversation: Conversation,
    payload: CaptureLeadInput,
) -> dict:
    full_name = _clean(payload.full_name)
    phone = _clean(payload.phone)
    email = _clean(payload.email)
    interest = _clean(payload.interest)
    notes = _clean(payload.notes)

    lead: Lead | None = None
    if conversation.lead_id:
        lead = await db.get(Lead, conversation.lead_id)
        if lead is not None and lead.clinic_id != clinic_id:
            raise ValueError("Conversation lead is outside the active business scope")

    effective_name = full_name or (lead.full_name if lead else None)
    effective_phone = phone or (lead.phone if lead else None)

    missing_fields: list[str] = []
    if not effective_name:
        missing_fields.append("full_name")
    if not effective_phone:
        missing_fields.append("phone")

    if missing_fields:
        conversation.agent_state = AgentState.COLLECTING.value
        await db.flush()
        return {
            "status": "collecting",
            "lead_id": str(lead.id) if lead else None,
            "missing_fields": missing_fields,
            "message": "Collect one missing field naturally, then call capture_lead again.",
        }

    service_id = await _resolve_interest_service_id(
        db,
        clinic_id=clinic_id,
        interest=interest,
    )

    if lead is None:
        lead = Lead(
            clinic_id=clinic_id,
            full_name=effective_name,
            phone=effective_phone,
            email=email,
            source=LeadSource.CHATBOT,
            interest_service_id=service_id,
            notes=_merge_notes(None, interest, notes),
        )
        db.add(lead)
        await db.flush()
        conversation.lead_id = lead.id
    else:
        if full_name:
            lead.full_name = full_name
        if phone:
            lead.phone = phone
        if email:
            lead.email = email
        if service_id:
            lead.interest_service_id = service_id
        lead.notes = _merge_notes(lead.notes, interest, notes)

    conversation.agent_state = AgentState.INFO.value
    await db.flush()

    return {
        "status": "captured",
        "lead_id": str(lead.id),
        "full_name": lead.full_name,
        "phone": lead.phone,
        "interest": interest,
        "missing_fields": [],
    }


async def execute_tool(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    conversation: Conversation,
    name: str,
    arguments: dict[str, Any],
) -> dict:
    definition = TOOL_DEFINITIONS.get(name)
    if definition is None:
        raise ValueError(f"Unknown or disabled tool: {name}")

    try:
        payload = definition.input_model.model_validate(arguments)
    except ValidationError as exc:
        raise ValueError(f"Invalid input for {name}: {exc}") from exc

    if name == "get_clinic_profile":
        clinic = await _clinic(db, clinic_id)
        return {
            "source_ref": f"business:{clinic.id}:profile",
            "name": clinic.name,
            "tagline": clinic.tagline,
            "phone": clinic.phone,
            "email": clinic.email,
            "address": clinic.address,
            "instagram": clinic.instagram,
            "timezone": clinic.timezone,
        }

    if name == "list_services":
        query = select(Service).where(
            Service.clinic_id == clinic_id,
            Service.is_active.is_(True),
            Service.public_visible.is_(True),
        )
        if payload.category:
            query = query.where(Service.category == payload.category)

        services = list((await db.scalars(query.order_by(Service.name))).all())
        return {
            "services": [
                {
                    "source_ref": f"service:{service.id}:catalog",
                    "id": str(service.id),
                    "name": service.name,
                    "category": service.category,
                    "description": service.short_description,
                    "duration_minutes": service.duration_minutes,
                    "price_from": str(service.price_from) if service.price_from is not None else None,
                    "currency": service.currency,
                }
                for service in services
            ]
        }

    if name == "search_knowledge":
        results = await retrieval_service.search(
            db,
            clinic_id=clinic_id,
            query=payload.query,
            limit=5,
        )
        return {"results": [item.model_dump() for item in results]}

    if name == "capture_lead":
        return await _capture_lead(
            db,
            clinic_id=clinic_id,
            conversation=conversation,
            payload=payload,
        )

    if name == "request_human_handoff":
        conversation.status = ConversationStatus.WAITING_HUMAN
        conversation.agent_state = AgentState.HANDOFF.value
        conversation.handoff_reason = payload.reason
        conversation.handoff_summary = payload.summary
        conversation.handoff_at = datetime.now(timezone.utc)
        await db.flush()
        return {
            "status": conversation.status.value,
            "reason": payload.reason,
            "summary": payload.summary,
        }

    raise ValueError(f"Unhandled tool: {name}")