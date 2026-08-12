import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db.models.enums import KnowledgeStatus, UserRole
from app.db.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.db.models.user import User
from app.db.session import get_db
from app.knowledge.ingestion import reindex_document
from app.schemas.knowledge import KnowledgeCreate, KnowledgeRead, KnowledgeUpdate
from app.services.audit import add_audit_event


router = APIRouter()


async def _tenant_document(
    db: AsyncSession,
    *,
    document_id: uuid.UUID,
    clinic_id: uuid.UUID,
) -> KnowledgeDocument:
    document = await db.scalar(
        select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.clinic_id == clinic_id,
        )
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Knowledge document not found")
    return document


@router.get("", response_model=list[KnowledgeRead])
async def list_knowledge(
    user: User = Depends(
        require_roles(UserRole.OWNER, UserRole.MANAGER, UserRole.RECEPTIONIST)
    ),
    db: AsyncSession = Depends(get_db),
):
    return list(
        (
            await db.scalars(
                select(KnowledgeDocument)
                .where(KnowledgeDocument.clinic_id == user.clinic_id)
                .order_by(KnowledgeDocument.updated_at.desc())
            )
        ).all()
    )


@router.post("", response_model=KnowledgeRead)
async def create_knowledge(
    payload: KnowledgeCreate,
    user: User = Depends(require_roles(UserRole.OWNER, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    document = KnowledgeDocument(
        clinic_id=user.clinic_id,
        title=payload.title,
        category=payload.category,
        content=payload.content,
        status=KnowledgeStatus.DRAFT,
        source_uri=payload.source_uri,
        source_type=payload.source_type,
        owner=payload.owner,
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
        sensitivity=payload.sensitivity,
        language=payload.language,
        capabilities_json=payload.capabilities,
        metadata_json=payload.metadata,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


@router.patch("/{document_id}", response_model=KnowledgeRead)
async def update_knowledge(
    document_id: uuid.UUID,
    payload: KnowledgeUpdate,
    user: User = Depends(require_roles(UserRole.OWNER, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    document = await _tenant_document(
        db, document_id=document_id, clinic_id=user.clinic_id
    )
    values = payload.model_dump(exclude_unset=True)
    if "capabilities" in values:
        capabilities = values.pop("capabilities")
        if capabilities is not None:
            values["capabilities_json"] = capabilities
    if "metadata" in values:
        metadata = values.pop("metadata")
        if metadata is not None:
            values["metadata_json"] = metadata
    for key, value in values.items():
        setattr(document, key, value)

    document.version += 1
    document.status = KnowledgeStatus.DRAFT
    document.approved_at = None
    document.approved_by = None
    await db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document.id))
    add_audit_event(
        db,
        clinic_id=user.clinic_id,
        actor_type="user",
        actor_id=user.id,
        action="knowledge.update",
        resource_type="knowledge_document",
        resource_id=document.id,
        metadata={"version": document.version},
    )
    await db.commit()
    await db.refresh(document)
    return document


async def _approve(
    *,
    document_id: uuid.UUID,
    user: User,
    db: AsyncSession,
) -> KnowledgeDocument:
    document = await _tenant_document(
        db, document_id=document_id, clinic_id=user.clinic_id
    )
    if document.valid_until and document.valid_until < datetime.now(timezone.utc).date():
        raise HTTPException(status_code=409, detail="Cannot approve an expired knowledge source.")
    document.status = KnowledgeStatus.APPROVED
    document.approved_at = datetime.now(timezone.utc)
    document.approved_by = user.id
    try:
        chunks = await reindex_document(db, document)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not chunks:
        raise HTTPException(status_code=400, detail="Knowledge document produced no indexable content.")
    add_audit_event(
        db,
        clinic_id=user.clinic_id,
        actor_type="user",
        actor_id=user.id,
        action="knowledge.approve",
        resource_type="knowledge_document",
        resource_id=document.id,
        metadata={"version": document.version, "chunks": len(chunks)},
    )
    await db.commit()
    await db.refresh(document)
    return document


@router.post("/{document_id}/approve", response_model=KnowledgeRead)
async def approve_knowledge(
    document_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.OWNER, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    return await _approve(document_id=document_id, user=user, db=db)


@router.post("/{document_id}/publish", response_model=KnowledgeRead, deprecated=True)
async def publish_knowledge_legacy(
    document_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.OWNER, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    """Backward-compatible alias. New clients should call /approve."""
    return await _approve(document_id=document_id, user=user, db=db)


@router.post("/{document_id}/archive", response_model=KnowledgeRead)
async def archive_knowledge(
    document_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.OWNER, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    document = await _tenant_document(
        db, document_id=document_id, clinic_id=user.clinic_id
    )
    document.status = KnowledgeStatus.ARCHIVED
    await db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document.id))
    add_audit_event(
        db,
        clinic_id=user.clinic_id,
        actor_type="user",
        actor_id=user.id,
        action="knowledge.archive",
        resource_type="knowledge_document",
        resource_id=document.id,
    )
    await db.commit()
    await db.refresh(document)
    return document
