import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.orchestrator import CleviaAgent
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.request_context import set_clinic_context
from app.db.models.conversation import Conversation, Message
from app.db.models.enums import AgentState, ConversationStatus
from app.db.models.observability import MessageFeedback
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.conversation import (
    ConversationRead,
    FeedbackCreate,
    FeedbackRead,
    MessageRead,
    PublicMessageCreate,
    PublicMessageResponse,
    StaffMessageCreate,
)
from app.services.audit import add_audit_event


public_router = APIRouter()
admin_router = APIRouter()
agent = CleviaAgent()


async def _tenant_conversation(
    db: AsyncSession,
    *,
    conversation_id: uuid.UUID,
    clinic_id: uuid.UUID,
) -> Conversation:
    conversation = await db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.clinic_id == clinic_id,
        )
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@public_router.post(
    "/conversations/{conversation_id}/messages",
    response_model=PublicMessageResponse,
)
async def send_public_message(
    conversation_id: uuid.UUID,
    payload: PublicMessageCreate,
    db: AsyncSession = Depends(get_db),
):
    conversation = await db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.public_token == payload.conversation_token,
        )
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    set_clinic_context(conversation.clinic_id)
    if conversation.status in {ConversationStatus.HUMAN_ACTIVE, ConversationStatus.RESOLVED}:
        raise HTTPException(
            status_code=409,
            detail="Conversation is not currently handled by the AI.",
        )

    history = list(
        (
            await db.scalars(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.created_at.asc())
            )
        ).all()
    )
    visitor_message = Message(
        conversation_id=conversation.id,
        role="user",
        sender_type="visitor",
        content=payload.message,
    )
    db.add(visitor_message)
    await db.flush()

    try:
        result = await agent.run(
            db,
            conversation=conversation,
            user_message=payload.message,
            history=history,
        )
    except RuntimeError as exc:
        if "API_KEY" in str(exc):
            await db.commit()
            raise HTTPException(
                status_code=503,
                detail=(
                    "AI chatbot is not configured yet. "
                    f"Set {settings.active_llm_key_name} in .env."
                ),
            ) from exc
        raise

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        sender_type="ai",
        content=result.message,
        model_name=(
            settings.active_llm_model
            if settings.llm_configured
            and result.intent not in {"GREETING", "HUMAN_HANDOFF", "MEDICAL_SAFETY"}
            else None
        ),
        tool_trace_json=json.dumps(result.tools_used, ensure_ascii=False, default=str),
        trace_id=result.trace_id,
    )
    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)

    return PublicMessageResponse(
        message=result.message,
        message_id=assistant_message.id,
        conversation_status=conversation.status.value,
        state=result.state.value,
        intent=result.intent,
        tools_used=result.tools_used,
        sources=[item.model_dump() for item in result.sources],
        handoff=result.handoff.model_dump() if result.handoff else None,
        trace_id=result.trace_id,
    )


@admin_router.get("", response_model=list[ConversationRead])
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return list(
        (
            await db.scalars(
                select(Conversation)
                .where(Conversation.clinic_id == user.clinic_id)
                .order_by(Conversation.updated_at.desc())
                .limit(200)
            )
        ).all()
    )


@admin_router.get("/{conversation_id}/messages", response_model=list[MessageRead])
async def conversation_messages(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversation = await _tenant_conversation(
        db, conversation_id=conversation_id, clinic_id=user.clinic_id
    )
    return list(
        (
            await db.scalars(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.created_at.asc())
            )
        ).all()
    )


@admin_router.post("/{conversation_id}/messages", response_model=MessageRead)
async def staff_reply(
    conversation_id: uuid.UUID,
    payload: StaffMessageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversation = await _tenant_conversation(
        db, conversation_id=conversation_id, clinic_id=user.clinic_id
    )
    if conversation.status != ConversationStatus.HUMAN_ACTIVE:
        raise HTTPException(
            status_code=409,
            detail="Take over the conversation before replying as clinic staff.",
        )
    message = Message(
        conversation_id=conversation.id,
        role="assistant",
        sender_type="staff",
        content=payload.message,
    )
    db.add(message)
    await db.flush()
    add_audit_event(
        db,
        clinic_id=user.clinic_id,
        actor_type="user",
        actor_id=user.id,
        action="conversation.staff_reply",
        resource_type="conversation",
        resource_id=conversation.id,
        metadata={"message_id": str(message.id)},
    )
    await db.commit()
    await db.refresh(message)
    return message


@admin_router.post("/{conversation_id}/takeover")
async def takeover(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversation = await _tenant_conversation(
        db, conversation_id=conversation_id, clinic_id=user.clinic_id
    )
    if conversation.status == ConversationStatus.RESOLVED:
        raise HTTPException(status_code=409, detail="Resolved conversation cannot be taken over.")
    conversation.status = ConversationStatus.HUMAN_ACTIVE
    conversation.agent_state = AgentState.HANDOFF.value
    conversation.assigned_user_id = user.id
    if conversation.handoff_at is None:
        conversation.handoff_at = datetime.now(timezone.utc)
    add_audit_event(
        db,
        clinic_id=user.clinic_id,
        actor_type="user",
        actor_id=user.id,
        action="conversation.takeover",
        resource_type="conversation",
        resource_id=conversation.id,
    )
    await db.commit()
    return {"status": conversation.status.value, "agent_state": conversation.agent_state}


@admin_router.post("/{conversation_id}/release")
async def release(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversation = await _tenant_conversation(
        db, conversation_id=conversation_id, clinic_id=user.clinic_id
    )
    if conversation.status == ConversationStatus.RESOLVED:
        raise HTTPException(status_code=409, detail="Resolved conversation cannot be released.")
    conversation.status = ConversationStatus.AI_ACTIVE
    conversation.agent_state = AgentState.INFO.value
    conversation.assigned_user_id = None
    add_audit_event(
        db,
        clinic_id=user.clinic_id,
        actor_type="user",
        actor_id=user.id,
        action="conversation.release_to_ai",
        resource_type="conversation",
        resource_id=conversation.id,
    )
    await db.commit()
    return {"status": conversation.status.value, "agent_state": conversation.agent_state}


@admin_router.post("/{conversation_id}/resolve")
async def resolve_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversation = await _tenant_conversation(
        db, conversation_id=conversation_id, clinic_id=user.clinic_id
    )
    conversation.status = ConversationStatus.RESOLVED
    conversation.agent_state = AgentState.CLOSED.value
    conversation.resolved_at = datetime.now(timezone.utc)
    conversation.assigned_user_id = user.id
    add_audit_event(
        db,
        clinic_id=user.clinic_id,
        actor_type="user",
        actor_id=user.id,
        action="conversation.resolve",
        resource_type="conversation",
        resource_id=conversation.id,
    )
    await db.commit()
    return {"status": conversation.status.value, "agent_state": conversation.agent_state}


@admin_router.post(
    "/{conversation_id}/messages/{message_id}/feedback",
    response_model=FeedbackRead,
)
async def create_message_feedback(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    payload: FeedbackCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversation = await _tenant_conversation(
        db, conversation_id=conversation_id, clinic_id=user.clinic_id
    )
    message = await db.scalar(
        select(Message).where(
            Message.id == message_id,
            Message.conversation_id == conversation.id,
        )
    )
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    if message.sender_type != "ai":
        raise HTTPException(status_code=400, detail="Feedback is only accepted for AI messages.")

    feedback = MessageFeedback(
        clinic_id=user.clinic_id,
        message_id=message.id,
        trace_id=message.trace_id,
        user_id=user.id,
        rating=payload.rating.value,
        note=payload.note,
    )
    db.add(feedback)
    add_audit_event(
        db,
        clinic_id=user.clinic_id,
        actor_type="user",
        actor_id=user.id,
        action="conversation.message_feedback",
        resource_type="message",
        resource_id=message.id,
        metadata={"rating": payload.rating.value, "trace_id": message.trace_id},
    )
    await db.commit()
    await db.refresh(feedback)
    return feedback
