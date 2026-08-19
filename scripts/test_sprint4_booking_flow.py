from __future__ import annotations

import asyncio
import uuid
from datetime import timedelta

from sqlalchemy import func, select

from app.agent.orchestrator import CleviaAgent
from app.core.config import settings
from app.db.models.appointment import Appointment
from app.db.models.clinic import Clinic
from app.db.models.conversation import Conversation
from app.db.models.crm import Client, Lead
from app.db.models.enums import (
    AgentState,
    AppointmentSource,
    AppointmentStatus,
    ConversationStatus,
    LeadSource,
    LeadStatus,
)
from app.db.models.observability import AgentTrace, MessageFeedback, ToolExecution
from app.db.models.service import Service
from app.db.models.staff import Staff
from app.db.models.user import User
from app.db.session import AsyncSessionLocal
from app.services.booking_flow import clinic_today
from app.tools.registry import execute_tool


async def main() -> None:
    # Register FK target tables used by the standalone ORM transaction.
    assert User.__tablename__ == "users"
    assert Client.__tablename__ == "clients"
    assert Staff.__tablename__ == "staff"
    assert "users" in User.metadata.tables
    assert AgentTrace.__tablename__ == "agent_traces"
    assert ToolExecution.__tablename__ == "tool_executions"
    assert MessageFeedback.__tablename__ == "message_feedback"

    if not settings.AGENT_TRANSACTIONAL_TOOLS_ENABLED:
        raise RuntimeError(
            "AGENT_TRANSACTIONAL_TOOLS_ENABLED must be true for Sprint 4 acceptance."
        )

    async with AsyncSessionLocal() as db:
        clinic = await db.scalar(
            select(Clinic).where(Clinic.slug == settings.DEFAULT_CLINIC_SLUG)
        )
        if clinic is None:
            raise RuntimeError("Default clinic is not seeded.")

        service = await db.scalar(
            select(Service).where(
                Service.clinic_id == clinic.id,
                Service.name == "Glow Facial Signature",
            )
        )
        if service is None:
            raise RuntimeError("Glow Facial Signature is not seeded.")

        lead = Lead(
            clinic_id=clinic.id,
            full_name="Sprint Four QA",
            phone=f"+62877{str(uuid.uuid4().int)[-8:]}",
            source=LeadSource.CHATBOT,
            status=LeadStatus.NEW,
            interest_service_id=service.id,
        )
        db.add(lead)
        await db.flush()

        conversation = Conversation(
            clinic_id=clinic.id,
            lead_id=lead.id,
            channel="web",
            status=ConversationStatus.AI_ACTIVE,
            agent_state=AgentState.INFO.value,
            risk_level="normal",
            public_token=f"sprint4-{uuid.uuid4().hex}",
            booking_draft={},
        )
        db.add(conversation)
        await db.flush()

        agent = CleviaAgent.__new__(CleviaAgent)

        start = await agent.run(
            db,
            conversation=conversation,
            user_message="mau booking",
            history=[],
        )
        assert start.state == AgentState.COLLECTING
        assert conversation.booking_draft["step"] == "date"
        assert service.name in start.message

        today = await clinic_today(db, clinic_id=clinic.id)
        target = today + timedelta(days=1)
        # Seed schedule is Monday-Saturday. Move forward if target is Sunday.
        if target.weekday() == 6:
            target += timedelta(days=1)

        date_turn = await agent.run(
            db,
            conversation=conversation,
            user_message=target.strftime("%d/%m/%Y"),
            history=[],
        )
        assert date_turn.state == AgentState.COLLECTING
        assert conversation.booking_draft["step"] == "slot"
        assert conversation.booking_draft["slots"]
        assert any(tool["name"] == "get_availability" for tool in date_turn.tools_used)

        slot_turn = await agent.run(
            db,
            conversation=conversation,
            user_message="1",
            history=[],
        )
        assert slot_turn.state == AgentState.CONFIRMING
        assert conversation.booking_draft["step"] == "confirm"
        assert "Balas YA" in slot_turn.message

        selected_draft = dict(conversation.booking_draft)
        confirm_turn = await agent.run(
            db,
            conversation=conversation,
            user_message="YA",
            history=[],
        )
        assert confirm_turn.state == AgentState.INFO
        assert conversation.booking_draft == {}
        assert any(
            tool["name"] == "create_appointment_request"
            for tool in confirm_turn.tools_used
        )

        appointment = await db.scalar(
            select(Appointment)
            .where(
                Appointment.clinic_id == clinic.id,
                Appointment.lead_id == lead.id,
            )
            .order_by(Appointment.created_at.desc())
        )
        assert appointment is not None
        assert appointment.status == AppointmentStatus.REQUESTED
        assert appointment.source == AppointmentSource.CHATBOT
        assert lead.status == LeadStatus.BOOKED

        # Explicit idempotency regression: restore the exact confirmed draft and
        # replay the write tool. It must reuse the appointment instead of creating
        # a second row.
        conversation.booking_draft = selected_draft
        conversation.agent_state = AgentState.CONFIRMING.value
        selected = selected_draft["selected_slot"]

        replay = await execute_tool(
            db,
            clinic_id=clinic.id,
            conversation=conversation,
            name="create_appointment_request",
            arguments={
                "service_id": selected_draft["service_id"],
                "staff_id": selected["staff_id"],
                "starts_at": selected["starts_at"],
                "customer_note": None,
            },
        )
        assert replay["reused"] is True

        count = await db.scalar(
            select(func.count(Appointment.id)).where(
                Appointment.clinic_id == clinic.id,
                Appointment.lead_id == lead.id,
                Appointment.service_id == service.id,
                Appointment.starts_at == appointment.starts_at,
            )
        )
        assert count == 1

        print("SPRINT4_BOOKING_FLOW_OK")
        print("appointment_id =", appointment.id)
        print("status =", appointment.status.value)
        print("source =", appointment.source.value)
        print("confirmation_gate = PASS")
        print("idempotency = PASS")

        await db.rollback()


if __name__ == "__main__":
    asyncio.run(main())
