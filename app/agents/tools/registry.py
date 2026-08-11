import uuid
from datetime import date, datetime
from typing import Any
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.clinic import Clinic
from app.db.models.conversation import Conversation
from app.db.models.crm import Lead
from app.db.models.enums import AppointmentSource, ConversationStatus, KnowledgeStatus, LeadSource, LeadStatus
from app.db.models.knowledge import KnowledgeDocument
from app.db.models.service import Service
from app.services.appointments import create_appointment, get_available_slots

TOOL_SCHEMAS = [
    {
        "type":"function","name":"get_clinic_profile",
        "description":"Get official public information about Clevia Beauty Clinic.",
        "parameters":{"type":"object","properties":{},"required":[],"additionalProperties":False},
        "strict":True,
    },
    {
        "type":"function","name":"list_services",
        "description":"List active public beauty services offered by Clevia.",
        "parameters":{
            "type":"object",
            "properties":{"category":{"type":["string","null"],"description":"Optional service category filter."}},
            "required":["category"],"additionalProperties":False,
        },"strict":True,
    },
    {
        "type":"function","name":"search_knowledge",
        "description":"Search approved Clevia knowledge for policy, preparation, aftercare, FAQ, payment, and clinic-specific information.",
        "parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"],"additionalProperties":False},
        "strict":True,
    },
    {
        "type":"function","name":"get_available_slots",
        "description":"Get live available appointment slots for a service on an exact date.",
        "parameters":{
            "type":"object",
            "properties":{
                "service_id":{"type":"string","description":"UUID from list_services."},
                "date":{"type":"string","description":"Date in YYYY-MM-DD."},
                "staff_id":{"type":["string","null"],"description":"Optional practitioner UUID."},
            },
            "required":["service_id","date","staff_id"],"additionalProperties":False,
        },"strict":True,
    },
    {
        "type":"function","name":"capture_lead",
        "description":"Create/update a CRM lead only after the visitor voluntarily provides name and phone.",
        "parameters":{
            "type":"object",
            "properties":{
                "full_name":{"type":"string"},"phone":{"type":"string"},
                "email":{"type":["string","null"]},
                "interest_service_id":{"type":["string","null"]},
            },
            "required":["full_name","phone","email","interest_service_id"],
            "additionalProperties":False,
        },"strict":True,
    },
    {
        "type":"function","name":"create_appointment_request",
        "description":"Create an appointment REQUEST after name, phone, service, staff, and exact slot are known. This does not confirm the booking.",
        "parameters":{
            "type":"object",
            "properties":{
                "full_name":{"type":"string"},"phone":{"type":"string"},
                "email":{"type":["string","null"]},"service_id":{"type":"string"},
                "staff_id":{"type":"string"},"starts_at":{"type":"string"},
                "note":{"type":["string","null"]},
            },
            "required":["full_name","phone","email","service_id","staff_id","starts_at","note"],
            "additionalProperties":False,
        },"strict":True,
    },
    {
        "type":"function","name":"request_human_handoff",
        "description":"Put this conversation in the human receptionist queue.",
        "parameters":{"type":"object","properties":{"reason":{"type":"string"}},"required":["reason"],"additionalProperties":False},
        "strict":True,
    },
]

async def _clinic(db: AsyncSession, clinic_id: uuid.UUID) -> Clinic:
    clinic = await db.get(Clinic, clinic_id)
    if clinic is None:
        raise ValueError("Clinic not found")
    return clinic

async def execute_tool(
    db: AsyncSession, *, clinic_id: uuid.UUID, conversation: Conversation,
    name: str, arguments: dict[str, Any],
) -> dict:
    if name == "get_clinic_profile":
        c = await _clinic(db, clinic_id)
        return {"name":c.name,"tagline":c.tagline,"phone":c.phone,"email":c.email,"address":c.address,"instagram":c.instagram,"timezone":c.timezone}

    if name == "list_services":
        q = select(Service).where(
            Service.clinic_id==clinic_id,
            Service.is_active.is_(True),
            Service.public_visible.is_(True),
        )
        if arguments.get("category"):
            q = q.where(Service.category==arguments["category"])
        services = list((await db.scalars(q.order_by(Service.name))).all())
        return {"services":[{
            "id":str(s.id),"name":s.name,"category":s.category,
            "description":s.short_description,"duration_minutes":s.duration_minutes,
            "price_from":str(s.price_from) if s.price_from is not None else None,
            "currency":s.currency,
        } for s in services]}

    if name == "search_knowledge":
        words = [word for word in arguments["query"].strip().split() if len(word)>=3][:6]
        conditions = []
        for word in words:
            like = f"%{word}%"
            conditions += [
                KnowledgeDocument.title.ilike(like),
                KnowledgeDocument.content.ilike(like),
                KnowledgeDocument.category.ilike(like),
            ]
        q = select(KnowledgeDocument).where(
            KnowledgeDocument.clinic_id==clinic_id,
            KnowledgeDocument.status==KnowledgeStatus.PUBLISHED,
        )
        if conditions:
            q = q.where(or_(*conditions))
        docs = list((await db.scalars(q.limit(5))).all())
        return {"results":[{
            "id":str(d.id),"title":d.title,"category":d.category,
            "content":d.content[:1800],"version":d.version,
        } for d in docs]}

    if name == "get_available_slots":
        c = await _clinic(db, clinic_id)
        slots = await get_available_slots(
            db, clinic_id=clinic_id,
            service_id=uuid.UUID(arguments["service_id"]),
            target_date=date.fromisoformat(arguments["date"]),
            timezone_name=c.timezone,
            staff_id=uuid.UUID(arguments["staff_id"]) if arguments.get("staff_id") else None,
        )
        return {"slots":[{
            "staff_id":str(x["staff_id"]),"staff_name":x["staff_name"],
            "starts_at":x["starts_at"].isoformat(),"ends_at":x["ends_at"].isoformat(),
        } for x in slots[:20]]}

    if name == "capture_lead":
        phone = arguments["phone"].strip()
        lead = await db.scalar(select(Lead).where(Lead.clinic_id==clinic_id, Lead.phone==phone))
        if lead is None:
            lead = Lead(
                clinic_id=clinic_id, full_name=arguments["full_name"].strip(),
                phone=phone, email=arguments.get("email"), source=LeadSource.CHATBOT,
                status=LeadStatus.NEW,
                interest_service_id=uuid.UUID(arguments["interest_service_id"]) if arguments.get("interest_service_id") else None,
            )
            db.add(lead)
            await db.flush()
        conversation.lead_id = lead.id
        await db.flush()
        return {"lead_id":str(lead.id),"status":lead.status.value}

    if name == "create_appointment_request":
        phone = arguments["phone"].strip()
        lead = await db.scalar(select(Lead).where(Lead.clinic_id==clinic_id, Lead.phone==phone))
        if lead is None:
            lead = Lead(
                clinic_id=clinic_id, full_name=arguments["full_name"].strip(),
                phone=phone, email=arguments.get("email"), source=LeadSource.CHATBOT,
                status=LeadStatus.BOOKED, interest_service_id=uuid.UUID(arguments["service_id"]),
            )
            db.add(lead)
            await db.flush()
        else:
            lead.status = LeadStatus.BOOKED

        appt = await create_appointment(
            db, clinic_id=clinic_id, lead_id=lead.id,
            service_id=uuid.UUID(arguments["service_id"]),
            staff_id=uuid.UUID(arguments["staff_id"]),
            starts_at=datetime.fromisoformat(arguments["starts_at"]),
            source=AppointmentSource.CHATBOT, customer_note=arguments.get("note"),
        )
        conversation.lead_id = lead.id
        await db.flush()
        return {
            "appointment_id":str(appt.id),"status":appt.status.value,
            "starts_at":appt.starts_at.isoformat(),
            "message":"Appointment request created; clinic confirmation is still required.",
        }

    if name == "request_human_handoff":
        conversation.status = ConversationStatus.WAITING_HUMAN
        await db.flush()
        return {"status":conversation.status.value,"reason":arguments["reason"]}

    raise ValueError(f"Unknown tool: {name}")
