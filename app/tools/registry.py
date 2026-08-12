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
from app.db.models.enums import AgentState, ConversationStatus
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
        description="Get the official profile and public operational information of the active clinic.",
        input_model=EmptyInput,
    ),
    "list_services": ToolDefinition(
        name="list_services",
        description="List active public services for the active clinic, including allowed public price-from values.",
        input_model=ListServicesInput,
    ),
    "search_knowledge": ToolDefinition(
        name="search_knowledge",
        description="Search approved, valid, tenant-filtered clinic knowledge and return source references.",
        input_model=SearchKnowledgeInput,
    ),
    "request_human_handoff": ToolDefinition(
        name="request_human_handoff",
        description="Place the conversation in the clinic human queue with a reason and compact context summary.",
        input_model=HandoffInput,
    ),
}

TOOL_SCHEMAS = [definition.openai_schema() for definition in TOOL_DEFINITIONS.values()]


async def _clinic(db: AsyncSession, clinic_id: uuid.UUID) -> Clinic:
    clinic = await db.get(Clinic, clinic_id)
    if clinic is None or not clinic.is_active:
        raise ValueError("Clinic not found or inactive")
    return clinic


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
            "source_ref": f"clinic:{clinic.id}:profile",
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
