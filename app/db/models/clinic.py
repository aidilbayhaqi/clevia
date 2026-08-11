from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

class Clinic(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "clinics"
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    tagline: Mapped[str|None] = mapped_column(String(255))
    description: Mapped[str|None] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Jakarta", nullable=False)
    phone: Mapped[str|None] = mapped_column(String(32))
    email: Mapped[str|None] = mapped_column(String(255))
    address: Mapped[str|None] = mapped_column(Text)
    instagram: Mapped[str|None] = mapped_column(String(255))
    brand_primary: Mapped[str] = mapped_column(String(16), default="#C85A91", nullable=False)
    brand_secondary: Mapped[str] = mapped_column(String(16), default="#7B8DEB", nullable=False)
    brand_accent: Mapped[str] = mapped_column(String(16), default="#F2B35D", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
