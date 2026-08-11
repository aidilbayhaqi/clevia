import uuid
from datetime import time
from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, Table, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.models.enums import StaffType

staff_services = Table(
    "staff_services", Base.metadata,
    Column("staff_id", UUID(as_uuid=True), ForeignKey("staff.id", ondelete="CASCADE"), primary_key=True),
    Column("service_id", UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
)

class Staff(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "staff"
    clinic_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    staff_type: Mapped[StaffType] = mapped_column(Enum(StaffType, name="staff_type"), nullable=False)
    title: Mapped[str|None] = mapped_column(String(160))
    specialty: Mapped[str|None] = mapped_column(String(160))
    bio: Mapped[str|None] = mapped_column(String(1000))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    public_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

class StaffAvailability(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "staff_availability"
    __table_args__ = (UniqueConstraint("staff_id","weekday","start_time","end_time", name="uq_staff_availability_window"),)
    staff_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("staff.id", ondelete="CASCADE"), index=True)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
