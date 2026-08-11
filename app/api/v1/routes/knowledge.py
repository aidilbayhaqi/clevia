import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.models.enums import KnowledgeStatus, UserRole
from app.db.models.knowledge import KnowledgeDocument
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.knowledge import KnowledgeCreate, KnowledgeRead, KnowledgeUpdate

router = APIRouter()

@router.get("", response_model=list[KnowledgeRead])
async def list_knowledge(
    user: User=Depends(require_roles(UserRole.OWNER,UserRole.MANAGER,UserRole.RECEPTIONIST)),
    db: AsyncSession=Depends(get_db),
):
    return list((await db.scalars(
        select(KnowledgeDocument).where(KnowledgeDocument.clinic_id==user.clinic_id)
        .order_by(KnowledgeDocument.updated_at.desc())
    )).all())

@router.post("", response_model=KnowledgeRead)
async def create_knowledge(
    payload: KnowledgeCreate,
    user: User=Depends(require_roles(UserRole.OWNER,UserRole.MANAGER)),
    db: AsyncSession=Depends(get_db),
):
    doc = KnowledgeDocument(
        clinic_id=user.clinic_id,title=payload.title,category=payload.category,
        content=payload.content,status=KnowledgeStatus.DRAFT,
    )
    db.add(doc); await db.commit(); await db.refresh(doc); return doc

@router.patch("/{document_id}", response_model=KnowledgeRead)
async def update_knowledge(
    document_id: uuid.UUID, payload: KnowledgeUpdate,
    user: User=Depends(require_roles(UserRole.OWNER,UserRole.MANAGER)),
    db: AsyncSession=Depends(get_db),
):
    doc = await db.get(KnowledgeDocument,document_id)
    if doc is None or doc.clinic_id != user.clinic_id:
        raise HTTPException(status_code=404,detail="Knowledge document not found")
    for key,value in payload.model_dump(exclude_unset=True).items():
        setattr(doc,key,value)
    doc.version += 1
    doc.status = KnowledgeStatus.DRAFT
    await db.commit(); await db.refresh(doc); return doc

@router.post("/{document_id}/publish", response_model=KnowledgeRead)
async def publish_knowledge(
    document_id: uuid.UUID,
    user: User=Depends(require_roles(UserRole.OWNER,UserRole.MANAGER)),
    db: AsyncSession=Depends(get_db),
):
    doc = await db.get(KnowledgeDocument,document_id)
    if doc is None or doc.clinic_id != user.clinic_id:
        raise HTTPException(status_code=404,detail="Knowledge document not found")
    doc.status = KnowledgeStatus.PUBLISHED
    await db.commit(); await db.refresh(doc); return doc
