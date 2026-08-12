import asyncio
from datetime import datetime, time, timezone

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.clinic import Clinic
from app.db.models.enums import KnowledgeStatus, StaffType, UserRole
from app.db.models.knowledge import KnowledgeDocument
from app.db.models.service import Service
from app.db.models.staff import Staff, StaffAvailability, staff_services
from app.db.models.user import User
from app.db.session import AsyncSessionLocal
from app.knowledge.ingestion import reindex_document


async def seed():
    async with AsyncSessionLocal() as db:
        clinic = await db.scalar(select(Clinic).where(Clinic.slug == "clevia"))
        if clinic is None:
            clinic = Clinic(
                name="Clevia Beauty Clinic",
                slug="clevia",
                tagline="Confidence, refined.",
                description=(
                    "Beauty clinic modern dengan pendekatan personal, elegan, "
                    "dan berorientasi pada pengalaman pelanggan."
                ),
                timezone="Asia/Jakarta",
                phone="+62 21 5550 2026",
                email="hello@clevia.example",
                address="Jakarta, Indonesia",
                instagram="@cleviabeauty",
                brand_primary="#C85A91",
                brand_secondary="#7B8DEB",
                brand_accent="#F2B35D",
            )
            db.add(clinic)
            await db.flush()

        owner = await db.scalar(select(User).where(User.email == "owner@clevia.local"))
        if owner is None:
            owner = User(
                clinic_id=clinic.id,
                full_name="Clevia Owner",
                email="owner@clevia.local",
                password_hash=hash_password("ChangeMe123!"),
                role=UserRole.OWNER,
            )
            db.add(owner)
            await db.flush()

        specs = [
            (
                "Glow Facial Signature",
                "glow-facial-signature",
                "facial",
                "Facial premium untuk membantu menjaga tampilan kulit tetap segar dan terawat.",
                60,
                650000,
            ),
            (
                "Acne Care Consultation",
                "acne-care-consultation",
                "skin",
                "Konsultasi dan assessment oleh practitioner sebelum rekomendasi treatment.",
                45,
                350000,
            ),
            (
                "Laser Rejuvenation",
                "laser-rejuvenation",
                "laser",
                "Treatment berbasis laser yang memerlukan assessment kesesuaian terlebih dahulu.",
                60,
                1500000,
            ),
        ]
        services = []
        for name, slug, category, desc, duration, price in specs:
            service = await db.scalar(
                select(Service).where(Service.clinic_id == clinic.id, Service.slug == slug)
            )
            if service is None:
                service = Service(
                    clinic_id=clinic.id,
                    name=name,
                    slug=slug,
                    category=category,
                    short_description=desc,
                    description=desc,
                    duration_minutes=duration,
                    price_from=price,
                )
                db.add(service)
                await db.flush()
            services.append(service)

        staff = await db.scalar(
            select(Staff).where(
                Staff.clinic_id == clinic.id,
                Staff.slug == "dr-alina-pratama",
            )
        )
        if staff is None:
            staff = Staff(
                clinic_id=clinic.id,
                full_name="dr. Alina Pratama",
                slug="dr-alina-pratama",
                staff_type=StaffType.DOCTOR,
                title="Aesthetic Doctor",
                specialty="Aesthetic Medicine",
                bio="Berfokus pada konsultasi personal dan treatment plan yang terukur.",
            )
            db.add(staff)
            await db.flush()
            for service in services:
                await db.execute(
                    staff_services.insert().values(staff_id=staff.id, service_id=service.id)
                )
            for weekday in range(6):
                db.add(
                    StaffAvailability(
                        staff_id=staff.id,
                        weekday=weekday,
                        start_time=time(9, 0),
                        end_time=time(18, 0),
                    )
                )

        knowledge = [
            (
                "Appointment Policy",
                "appointment",
                "operational_policy",
                "Appointment Clevia dari website berstatus REQUESTED sampai dikonfirmasi oleh tim "
                "Clevia. Untuk perubahan jadwal, hubungi tim klinik.",
            ),
            (
                "Treatment Safety",
                "safety",
                "operational_policy",
                "Kesesuaian treatment beauty bersifat personal dan dapat memerlukan konsultasi "
                "dengan practitioner. Chatbot tidak memberikan diagnosis, resep, atau jaminan hasil treatment.",
            ),
            (
                "Payment FAQ",
                "payment",
                "operational_faq",
                "Harga yang tampil sebagai 'mulai dari' adalah estimasi awal. Harga final dapat "
                "bergantung pada assessment dan treatment plan.",
            ),
        ]
        for title, category, source_type, content in knowledge:
            document = await db.scalar(
                select(KnowledgeDocument).where(
                    KnowledgeDocument.clinic_id == clinic.id,
                    KnowledgeDocument.title == title,
                )
            )
            if document is None:
                document = KnowledgeDocument(
                    clinic_id=clinic.id,
                    title=title,
                    category=category,
                    content=content,
                    source_type=source_type,
                    owner="operations",
                    status=KnowledgeStatus.APPROVED,
                    approved_at=datetime.now(timezone.utc),
                    approved_by=owner.id,
                )
                db.add(document)
                await db.flush()
                await reindex_document(db, document)
            elif document.status in {KnowledgeStatus.PUBLISHED, KnowledgeStatus.APPROVED}:
                document.status = KnowledgeStatus.APPROVED
                if document.approved_at is None:
                    document.approved_at = datetime.now(timezone.utc)
                    document.approved_by = owner.id
                await reindex_document(db, document)

        await db.commit()
        print("Seed complete")
        print("Login: owner@clevia.local / ChangeMe123!")
        print("Change the password before real deployment.")


if __name__ == "__main__":
    asyncio.run(seed())
