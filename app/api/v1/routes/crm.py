import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.models.crm import Client, Lead
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.crm import ClientCreate, ClientRead, LeadCreate, LeadRead, LeadUpdate

router = APIRouter()

@router.get("/leads", response_model=list[LeadRead])
async def list_leads(user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return list((await db.scalars(
        select(Lead).where(Lead.clinic_id==user.clinic_id).order_by(Lead.created_at.desc())
    )).all())

@router.post("/leads", response_model=LeadRead)
async def create_lead(payload: LeadCreate, user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    lead = Lead(
        clinic_id=user.clinic_id, full_name=payload.full_name, phone=payload.phone,
        email=str(payload.email) if payload.email else None, source=payload.source,
        interest_service_id=payload.interest_service_id, notes=payload.notes,
    )
    db.add(lead); await db.commit(); await db.refresh(lead); return lead

@router.patch("/leads/{lead_id}", response_model=LeadRead)
async def update_lead(lead_id: uuid.UUID, payload: LeadUpdate, user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    lead = await db.get(Lead, lead_id)
    if lead is None or lead.clinic_id != user.clinic_id:
        raise HTTPException(status_code=404, detail="Lead not found")
    for key,value in payload.model_dump(exclude_unset=True).items():
        setattr(lead,key,value)
    await db.commit(); await db.refresh(lead); return lead

@router.get("/clients", response_model=list[ClientRead])
async def list_clients(user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    return list((await db.scalars(
        select(Client).where(Client.clinic_id==user.clinic_id).order_by(Client.created_at.desc())
    )).all())

@router.post("/clients", response_model=ClientRead)
async def create_client(payload: ClientCreate, user: User=Depends(get_current_user), db: AsyncSession=Depends(get_db)):
    client = Client(
        clinic_id=user.clinic_id, full_name=payload.full_name, phone=payload.phone,
        email=str(payload.email) if payload.email else None, birth_date=payload.birth_date,
        tags=payload.tags, administrative_notes=payload.administrative_notes,
    )
    db.add(client); await db.commit(); await db.refresh(client); return client
