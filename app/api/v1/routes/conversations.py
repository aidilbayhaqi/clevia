import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import CleviaAgent
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.models.conversation import Conversation, Message
from app.db.models.enums import ConversationStatus
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.conversation import ConversationRead, PublicMessageCreate, PublicMessageResponse

public_router = APIRouter()
admin_router = APIRouter()
agent = CleviaAgent()

@public_router.post("/conversations/{conversation_id}/messages", response_model=PublicMessageResponse)
async def send_public_message(
    conversation_id: uuid.UUID,
    payload: PublicMessageCreate,
    db: AsyncSession=Depends(get_db),
):
    conversation = await db.scalar(select(Conversation).where(
        Conversation.id==conversation_id,
        Conversation.public_token==payload.conversation_token,
    ))
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.status == ConversationStatus.HUMAN_ACTIVE:
        raise HTTPException(status_code=409, detail="Conversation is handled by clinic staff.")
    history = list((await db.scalars(
        select(Message).where(Message.conversation_id==conversation.id).order_by(Message.created_at.asc())
    )).all())

    db.add(Message(
        conversation_id=conversation.id, role="user",
        sender_type="visitor", content=payload.message,
    ))

    try:
        result = await agent.run(
            db,
            conversation=conversation,
            user_message=payload.message,
            history=history,
        )
    except RuntimeError as exc:
        if "OPENAI_API_KEY" in str(exc):
            raise HTTPException(
                status_code=503,
                detail=(
                    "AI chatbot is not configured yet. "
                    "Set OPENAI_API_KEY in .env."
                ),
            ) from exc
        raise
    db.add(Message(
        conversation_id=conversation.id, role="assistant", sender_type="ai",
        content=result["message"], model_name=settings.OPENAI_MODEL,
        tool_trace_json=json.dumps(result["tools_used"],ensure_ascii=False,default=str),
    ))
    await db.commit()

    return PublicMessageResponse(
        message=result["message"],
        conversation_status=conversation.status.value,
        tools_used=result["tools_used"],
    )

@admin_router.get("", response_model=list[ConversationRead])
async def list_conversations(user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return list((await db.scalars(
        select(Conversation)
        .where(Conversation.clinic_id==user.clinic_id)
        .order_by(Conversation.created_at.desc()).limit(200)
    )).all())

@admin_router.post("/{conversation_id}/takeover")
async def takeover(conversation_id: uuid.UUID, user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    c = await db.get(Conversation, conversation_id)
    if c is None or c.clinic_id != user.clinic_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    c.status = ConversationStatus.HUMAN_ACTIVE
    await db.commit()
    return {"status":c.status.value}

@admin_router.post("/{conversation_id}/release")
async def release(conversation_id: uuid.UUID, user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    c = await db.get(Conversation, conversation_id)
    if c is None or c.clinic_id != user.clinic_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    c.status = ConversationStatus.AI_ACTIVE
    await db.commit()
    return {"status":c.status.value}

