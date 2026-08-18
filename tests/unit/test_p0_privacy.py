from app.observability.redaction import REDACTED, redact_for_trace


def test_redacts_named_pii_and_secrets() -> None:
    clean = redact_for_trace(
        {
            "tool_name": "capture_lead",
            "arguments": {
                "full_name": "Budi Santoso",
                "phone": "+628123456789",
                "email": "budi@example.com",
                "service_id": "svc_123",
                "notes": "private note",
                "api_key": "secret",
            },
            "result": {"lead_id": "lead_123", "status": "created"},
        }
    )

    assert clean["tool_name"] == "capture_lead"
    assert clean["arguments"]["service_id"] == "svc_123"
    assert clean["arguments"]["full_name"] == REDACTED
    assert clean["arguments"]["phone"] == REDACTED
    assert clean["arguments"]["email"] == REDACTED
    assert clean["arguments"]["notes"] == REDACTED
    assert clean["arguments"]["api_key"] == REDACTED
    assert clean["result"]["lead_id"] == "lead_123"


def test_redacts_patterns_inside_non_sensitive_strings() -> None:
    clean = redact_for_trace(
        {
            "error_detail": "provider rejected budi@example.com / +628123456789",
            "header": "Bearer abcdefghijklmnop",
            "provider_detail": "invalid sk-abcdefghijklmnop",
        }
    )

    assert "budi@example.com" not in clean["error_detail"]
    assert "+628123456789" not in clean["error_detail"]
    assert "abcdefghijklmnop" not in clean["header"]
    assert "sk-abcdefghijklmnop" not in clean["provider_detail"]


def test_operational_ids_are_preserved() -> None:
    raw = {
        "clinic_id": "clinic-1",
        "trace_id": "trace-1",
        "service_id": "service-1",
        "status": "success",
        "latency_ms": 25,
    }
    assert redact_for_trace(raw) == raw
