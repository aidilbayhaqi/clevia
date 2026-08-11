import asyncio
from datetime import time
from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.clinic import Clinic
from app.db.models.enums import StaffType, UserRole, KnowledgeStatus
from app.db.models.knowledge import KnowledgeDocument
from app.db.models.service import Service
from app.db.models.staff import Staff, StaffAvailability, staff_services
from app.db.models.user import User
from app.db.session import AsyncSessionLocal

async def seed():
    async with AsyncSessionLocal() as db:
        clinic = await db.scalar(select(Clinic).where(Clinic.slug=="clevia"))
        if clinic is None:
            clinic = Clinic(
                name="Clevia Beauty Clinic", slug="clevia",
                tagline="Confidence, refined.",
                description="Beauty clinic modern dengan pendekatan personal, elegan, dan berorientasi pada pengalaman pelanggan.",
                timezone="Asia/Jakarta", phone="+62 21 5550 2026",
                email="hello@clevia.example", address="Jakarta, Indonesia",
                instagram="@cleviabeauty",
                brand_primary="#C85A91", brand_secondary="#7B8DEB", brand_accent="#F2B35D",
            )
            db.add(clinic); await db.flush()

        owner = await db.scalar(select(User).where(User.email=="owner@clevia.local"))
        if owner is None:
            db.add(User(
                clinic_id=clinic.id, full_name="Clevia Owner",
                email="owner@clevia.local", password_hash=hash_password("ChangeMe123!"),
                role=UserRole.OWNER,
            ))
            await db.flush()

        specs = [
            ("Glow Facial Signature","glow-facial-signature","facial","Facial premium untuk membantu menjaga tampilan kulit tetap segar dan terawat.",60,650000),
            ("Acne Care Consultation","acne-care-consultation","skin","Konsultasi dan assessment oleh practitioner sebelum rekomendasi treatment.",45,350000),
            ("Laser Rejuvenation","laser-rejuvenation","laser","Treatment berbasis laser yang memerlukan assessment kesesuaian terlebih dahulu.",60,1500000),
        ]
        services=[]
        for name,slug,category,desc,duration,price in specs:
            s = await db.scalar(select(Service).where(Service.clinic_id==clinic.id,Service.slug==slug))
            if s is None:
                s=Service(
                    clinic_id=clinic.id,name=name,slug=slug,category=category,
                    short_description=desc,description=desc,duration_minutes=duration,price_from=price,
                )
                db.add(s); await db.flush()
            services.append(s)

        staff = await db.scalar(select(Staff).where(Staff.clinic_id==clinic.id,Staff.slug=="dr-alina-pratama"))
        if staff is None:
            staff=Staff(
                clinic_id=clinic.id,full_name="dr. Alina Pratama",slug="dr-alina-pratama",
                staff_type=StaffType.DOCTOR,title="Aesthetic Doctor",specialty="Aesthetic Medicine",
                bio="Berfokus pada konsultasi personal dan treatment plan yang terukur.",
            )
            db.add(staff); await db.flush()
            for s in services:
                await db.execute(staff_services.insert().values(staff_id=staff.id,service_id=s.id))
            for weekday in range(6):
                db.add(StaffAvailability(
                    staff_id=staff.id,weekday=weekday,start_time=time(9,0),end_time=time(18,0)
                ))

        knowledge = [
            ("Appointment Policy","appointment","Appointment Clevia dari website atau chatbot berstatus REQUESTED sampai dikonfirmasi oleh tim Clevia. Untuk perubahan jadwal, hubungi tim klinik."),
            ("Treatment Safety","safety","Kesesuaian treatment beauty bersifat personal dan dapat memerlukan konsultasi dengan practitioner. Chatbot tidak memberikan diagnosis, resep, atau jaminan hasil treatment."),
            ("Payment FAQ","payment","Harga yang tampil sebagai 'mulai dari' adalah estimasi awal. Harga final dapat bergantung pada assessment dan treatment plan."),
        ]
        for title,category,content in knowledge:
            exists = await db.scalar(select(KnowledgeDocument).where(
                KnowledgeDocument.clinic_id==clinic.id,KnowledgeDocument.title==title
            ))
            if exists is None:
                db.add(KnowledgeDocument(
                    clinic_id=clinic.id,title=title,category=category,
                    content=content,status=KnowledgeStatus.PUBLISHED
                ))

        await db.commit()
        print("Seed complete")
        print("Login: owner@clevia.local / ChangeMe123!")
        print("Change the password before real deployment.")

if __name__=="__main__":
    asyncio.run(seed())
