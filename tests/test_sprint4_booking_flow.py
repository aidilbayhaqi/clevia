from datetime import date

from app.services.booking_flow import (
    format_confirmation,
    is_booking_cancel,
    is_confirmation,
    is_rejection,
    parse_slot_choice,
    parse_target_date,
    serialize_slots,
)


def test_date_parser_supports_relative_and_common_formats() -> None:
    today = date(2026, 8, 19)

    assert parse_target_date("besok", today=today) == date(2026, 8, 20)
    assert parse_target_date("lusa", today=today) == date(2026, 8, 21)
    assert parse_target_date("21/08/2026", today=today) == date(2026, 8, 21)
    assert parse_target_date("2026-08-22", today=today) == date(2026, 8, 22)


def test_confirmation_is_strict_and_cancel_is_distinct() -> None:
    assert is_confirmation("YA")
    assert is_confirmation("setuju")
    assert is_rejection("tidak")
    assert is_booking_cancel("saya batal booking")
    assert not is_confirmation("mungkin iya nanti")


def test_slot_choice_is_bounded() -> None:
    assert parse_slot_choice("1", 3) == 0
    assert parse_slot_choice("pilih 3", 3) == 2
    assert parse_slot_choice("4", 3) is None


def test_confirmation_summary_states_requested_status() -> None:
    draft = {
        "service_name": "Glow Facial Signature",
        "selected_slot": {
            "staff_name": "dr. Alina Pratama",
            "starts_at": "2026-08-20T09:00:00+07:00",
        },
    }
    message = format_confirmation(draft)
    assert "Glow Facial Signature" in message
    assert "dr. Alina Pratama" in message
    assert "REQUESTED" in message
    assert "Balas YA" in message


def test_serialize_slots_accepts_json_tool_output_strings() -> None:
    slots = [
        {
            "staff_id": "00000000-0000-0000-0000-000000000001",
            "staff_name": "dr. Alina Pratama",
            "starts_at": "2026-08-20T09:00:00+07:00",
            "ends_at": "2026-08-20T10:00:00+07:00",
        }
    ]

    serialized = serialize_slots(slots)

    assert serialized[0]["starts_at"] == "2026-08-20T09:00:00+07:00"
    assert serialized[0]["ends_at"] == "2026-08-20T10:00:00+07:00"


def test_serialize_slots_rejects_naive_datetime_string() -> None:
    slots = [
        {
            "staff_id": "00000000-0000-0000-0000-000000000001",
            "staff_name": "dr. Alina Pratama",
            "starts_at": "2026-08-20T09:00:00",
            "ends_at": "2026-08-20T10:00:00",
        }
    ]

    try:
        serialize_slots(slots)
    except ValueError as exc:
        assert "timezone-aware" in str(exc)
    else:
        raise AssertionError("Expected timezone-aware validation failure")
