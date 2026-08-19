from pathlib import Path

from app.schemas.crm import ClientCreate, LeadRead, LeadUpdate


def test_lead_read_exposes_updated_at() -> None:
    assert "updated_at" in LeadRead.model_fields


def test_lead_update_allows_admin_contact_and_interest_edits() -> None:
    fields = LeadUpdate.model_fields
    for required in (
        "full_name",
        "phone",
        "email",
        "status",
        "interest_service_id",
        "assigned_to_user_id",
        "notes",
    ):
        assert required in fields


def test_client_tags_are_not_a_shared_mutable_default() -> None:
    first = ClientCreate(full_name="A", phone="081234567890")
    second = ClientCreate(full_name="B", phone="081234567891")
    first.tags.append("vip")
    assert second.tags == []


def test_crm_route_tenant_validates_assignee_and_service() -> None:
    source = Path("app/api/v1/routes/crm.py").read_text(encoding="utf-8")
    assert "User.clinic_id == clinic_id" in source
    assert "Service.clinic_id == clinic_id" in source
    assert "Lead.clinic_id == clinic_id" in source
