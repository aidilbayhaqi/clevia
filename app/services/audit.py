import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit import AuditLog


def add_audit_event(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    actor_type: str,
    actor_id: uuid.UUID | None,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID | None,
    metadata: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            clinic_id=clinic_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=metadata or {},
        )
    )
