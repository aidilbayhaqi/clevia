from app.db.models.conversation import Message
from app.services.lead_capture import (
    ensure_lead_collection_question,
    extract_lead_name,
    extract_lead_phone,
    lead_capture_opt_out,
    next_lead_question,
    normalize_phone_number,
)


def _message(role: str, content: str) -> Message:
    return Message(
        conversation_id="00000000-0000-0000-0000-000000000001",
        role=role,
        sender_type="ai" if role == "assistant" else "visitor",
        content=content,
    )


def test_phone_normalization() -> None:
    assert normalize_phone_number("0812-3456-7890") == "+6281234567890"
    assert normalize_phone_number("+62 812 3456 7890") == "+6281234567890"
    assert normalize_phone_number("abc") is None


def test_extract_name_from_prompted_plain_reply() -> None:
    history = [
        _message("user", "Saya tertarik Glow Facial Signature"),
        _message("assistant", "Boleh tahu nama kamu?"),
    ]
    assert extract_lead_name(history, "Sarah Putri") == "Sarah Putri"


def test_extract_name_from_explicit_sentence() -> None:
    assert extract_lead_name([], "Nama saya Sarah Putri") == "Sarah Putri"


def test_extract_phone_from_current_turn() -> None:
    assert extract_lead_phone([], "WA saya 0812-3456-7890") == "+6281234567890"


def test_next_question_is_one_field_at_a_time() -> None:
    assert next_lead_question(full_name=None, phone=None)[0] == "full_name"
    assert next_lead_question(full_name="Sarah", phone=None)[0] == "phone"
    assert next_lead_question(full_name="Sarah", phone="+6281234567890") == (None, None)


def test_collection_question_is_not_duplicated() -> None:
    reply = "Glow Facial tersedia. Boleh tahu nama kamu?"
    assert ensure_lead_collection_question(reply, "full_name") == reply


def test_opt_out_is_respected() -> None:
    assert lead_capture_opt_out("Saya tidak mau kasih nomor WhatsApp")
