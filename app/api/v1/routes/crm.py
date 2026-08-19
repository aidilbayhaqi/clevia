import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models.crm import Client, Lead
from app.db.models.enums import LeadSource, LeadStatus
from app.db.models.service import Service
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.crm import ClientCreate, ClientRead, LeadCreate, LeadRead, LeadUpdate
from app.services.lead_capture import normalize_phone_number

router = APIRouter()


async def _tenant_lead(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    lead_id: uuid.UUID,
) -> Lead:
    lead = await db.scalar(
        select(Lead).where(
            Lead.id == lead_id,
            Lead.clinic_id == clinic_id,
        )
    )
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


async def _validate_service(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    service_id: uuid.UUID | None,
) -> None:
    if service_id is None:
        return
    service = await db.scalar(
        select(Service.id).where(
            Service.id == service_id,
            Service.clinic_id == clinic_id,
        )
    )
    if service is None:
        raise HTTPException(status_code=422, detail="Invalid service for this clinic")


async def _validate_assignee(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    user_id: uuid.UUID | None,
) -> None:
    if user_id is None:
        return
    assignee = await db.scalar(
        select(User.id).where(
            User.id == user_id,
            User.clinic_id == clinic_id,
        )
    )
    if assignee is None:
        raise HTTPException(status_code=422, detail="Invalid assignee for this clinic")


@router.get("/leads", response_model=list[LeadRead])
async def list_leads(
    status: LeadStatus | None = None,
    source: LeadSource | None = None,
    service_id: uuid.UUID | None = None,
    q: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=100, ge=1, le=250),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    statement = select(Lead).where(Lead.clinic_id == user.clinic_id)

    if status is not None:
        statement = statement.where(Lead.status == status)
    if source is not None:
        statement = statement.where(Lead.source == source)
    if service_id is not None:
        statement = statement.where(Lead.interest_service_id == service_id)
    if q:
        term = f"%{q.strip()}%"
        statement = statement.where(
            or_(
                Lead.full_name.ilike(term),
                Lead.phone.ilike(term),
                Lead.email.ilike(term),
            )
        )

    statement = (
        statement
        .order_by(Lead.updated_at.desc(), Lead.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list((await db.scalars(statement)).all())


@router.post("/leads", response_model=LeadRead)
async def create_lead(
    payload: LeadCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _validate_service(
        db,
        clinic_id=user.clinic_id,
        service_id=payload.interest_service_id,
    )

    phone = normalize_phone_number(payload.phone)
    if phone is None:
        raise HTTPException(status_code=422, detail="Invalid phone number")

    lead = Lead(
        clinic_id=user.clinic_id,
        full_name=payload.full_name.strip(),
        phone=phone,
        email=str(payload.email) if payload.email else None,
        source=payload.source,
        interest_service_id=payload.interest_service_id,
        notes=payload.notes,
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead


@router.patch("/leads/{lead_id}", response_model=LeadRead)
async def update_lead(
    lead_id: uuid.UUID,
    payload: LeadUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead = await _tenant_lead(
        db,
        clinic_id=user.clinic_id,
        lead_id=lead_id,
    )
    changes = payload.model_dump(exclude_unset=True)

    if "interest_service_id" in changes:
        await _validate_service(
            db,
            clinic_id=user.clinic_id,
            service_id=changes["interest_service_id"],
        )

    if "assigned_to_user_id" in changes:
        await _validate_assignee(
            db,
            clinic_id=user.clinic_id,
            user_id=changes["assigned_to_user_id"],
        )

    if "phone" in changes:
        normalized = normalize_phone_number(changes["phone"])
        if normalized is None:
            raise HTTPException(status_code=422, detail="Invalid phone number")
        changes["phone"] = normalized

    if "email" in changes and changes["email"] is not None:
        changes["email"] = str(changes["email"])

    if "full_name" in changes and changes["full_name"] is not None:
        changes["full_name"] = changes["full_name"].strip()

    for key, value in changes.items():
        setattr(lead, key, value)

    await db.commit()
    await db.refresh(lead)
    return lead


@router.get("/clients", response_model=list[ClientRead])
async def list_clients(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return list(
        (
            await db.scalars(
                select(Client)
                .where(Client.clinic_id == user.clinic_id)
                .order_by(Client.created_at.desc())
            )
        ).all()
    )


@router.post("/clients", response_model=ClientRead)
async def create_client(
    payload: ClientCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    client = Client(
        clinic_id=user.clinic_id,
        full_name=payload.full_name,
        phone=payload.phone,
        email=str(payload.email) if payload.email else None,
        birth_date=payload.birth_date,
        tags=payload.tags,
        administrative_notes=payload.administrative_notes,
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client
