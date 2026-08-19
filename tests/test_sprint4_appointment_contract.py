from pathlib import Path

from app.db.models.enums import AppointmentStatus
from app.schemas.appointment import AppointmentUpdate


def test_admin_appointment_update_accepts_status_and_note() -> None:
    assert "status" in AppointmentUpdate.model_fields
    assert "internal_note" in AppointmentUpdate.model_fields


def test_route_has_explicit_safe_transition_map() -> None:
    source = Path("app/api/v1/routes/appointments.py").read_text(encoding="utf-8")
    assert "ALLOWED_STATUS_TRANSITIONS" in source
    assert "AppointmentStatus.REQUESTED" in source
    assert "AppointmentStatus.CONFIRMED" in source
    assert "Invalid appointment transition" in source


def test_terminal_statuses_exist() -> None:
    assert AppointmentStatus.COMPLETED.value == "completed"
    assert AppointmentStatus.CANCELLED.value == "cancelled"
    assert AppointmentStatus.NO_SHOW.value == "no_show"


def test_prompt_states_confirmation_and_requested_boundary() -> None:
    source = Path("app/llm/prompt_registry.py").read_text(encoding="utf-8")
    assert "explicitly" in source
    assert "create_appointment_request" in source
    assert "only REQUESTED" in source
