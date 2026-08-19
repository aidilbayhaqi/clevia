from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import func, select

from app.agent.orchestrator import CleviaAgent
from app.core.config import settings
from app.db.models.clinic import Clinic
from app.db.models.conversation import Conversation, Message
from app.db.models.crm import Lead
from app.db.models.enums import AgentState, ConversationStatus, LeadSource
from app.db.models.service import Service
from app.db.models.user import User
from app.db.session import AsyncSessionLocal
from app.services.lead_capture import normalize_phone_number


def message(conversation_id, role: str, content: str) -> Message:
    return Message(
        conversation_id=conversation_id,
        role=role,
        sender_type="ai" if role == "assistant" else "visitor",
        content=content,
    )


async def main() -> None:
    # Conversation and Lead both reference users.id. Importing User above registers
    # the users table in the shared SQLAlchemy metadata used during ORM flush.
    assert User.__tablename__ == "users"
    assert "users" in User.metadata.tables

    async with AsyncSessionLocal() as db:
        clinic = await db.scalar(
            select(Clinic).where(Clinic.slug == settings.DEFAULT_CLINIC_SLUG)
        )
        if clinic is None:
            raise RuntimeError("Default clinic is not seeded.")

        glow = await db.scalar(
            select(Service).where(
                Service.clinic_id == clinic.id,
                Service.name == "Glow Facial Signature",
            )
        )
        if glow is None:
            raise RuntimeError("Glow Facial Signature is not seeded.")

        unique_suffix = str(uuid.uuid4().int)[-9:]
        raw_phone = f"08{unique_suffix}"
        normalized_phone = normalize_phone_number(raw_phone)
        if normalized_phone is None:
            raise RuntimeError("Generated test phone did not normalize.")

        agent = CleviaAgent.__new__(CleviaAgent)

        conversation = Conversation(
            clinic_id=clinic.id,
            channel="web",
            status=ConversationStatus.AI_ACTIVE,
            agent_state=AgentState.COLLECTING.value,
            risk_level="normal",
            public_token=f"sprint3-{uuid.uuid4().hex}",
        )
        db.add(conversation)
        await db.flush()

        history = [
            message(conversation.id, "user", "Saya tertarik Glow Facial Signature"),
            message(conversation.id, "assistant", "Boleh tahu nama kamu?"),
        ]

        name_turn = await agent.run(
            db,
            conversation=conversation,
            user_message="Sarah Putri",
            history=history,
        )

        assert name_turn.state == AgentState.COLLECTING
        assert "WhatsApp" in name_turn.message
        assert conversation.lead_id is None

        history.extend(
            [
                message(conversation.id, "user", "Sarah Putri"),
                message(conversation.id, "assistant", name_turn.message),
            ]
        )

        phone_turn = await agent.run(
            db,
            conversation=conversation,
            user_message=raw_phone,
            history=history,
        )

        assert phone_turn.state == AgentState.INFO
        assert conversation.lead_id is not None
        assert any(tool["name"] == "capture_lead" for tool in phone_turn.tools_used)

        lead = await db.get(Lead, conversation.lead_id)
        assert lead is not None
        assert lead.full_name == "Sarah Putri"
        assert lead.phone == normalized_phone
        assert lead.source == LeadSource.CHATBOT
        assert lead.interest_service_id == glow.id

        second = Conversation(
            clinic_id=clinic.id,
            channel="web",
            status=ConversationStatus.AI_ACTIVE,
            agent_state=AgentState.COLLECTING.value,
            risk_level="normal",
            public_token=f"sprint3-{uuid.uuid4().hex}",
        )
        db.add(second)
        await db.flush()

        second_history = [
            message(second.id, "user", "Saya tertarik Glow Facial Signature"),
            message(second.id, "assistant", "Boleh tahu nama kamu?"),
            message(second.id, "user", "Sarah Putri"),
            message(
                second.id,
                "assistant",
                "Nomor WhatsApp yang bisa dihubungi tim Clevia berapa?",
            ),
        ]

        second_turn = await agent.run(
            db,
            conversation=second,
            user_message=raw_phone,
            history=second_history,
        )

        assert second.lead_id == lead.id
        assert second_turn.state == AgentState.INFO

        phone_digits = normalized_phone.replace("+", "")
        stored_digits = func.regexp_replace(Lead.phone, r"[^0-9]", "", "g")
        count = await db.scalar(
            select(func.count(Lead.id)).where(
                Lead.clinic_id == clinic.id,
                stored_digits == phone_digits,
            )
        )
        assert count == 1

        print("SPRINT3_LEAD_FLOW_OK")
        print("lead_id =", lead.id)
        print("normalized_phone =", normalized_phone)
        print("service =", glow.name)
        print("dedupe =", "PASS")

        # This is a release test: do not persist its conversations, traces, or lead.
        await db.rollback()


if __name__ == "__main__":
    asyncio.run(main())
