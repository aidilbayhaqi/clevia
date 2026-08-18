from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

REDACTED = "[REDACTED]"

SENSITIVE_KEYS = {
    "full_name",
    "name",
    "phone",
    "phone_number",
    "mobile",
    "email",
    "address",
    "note",
    "notes",
    "customer_note",
    "message",
    "query",
    "summary",
    "password",
    "password_hash",
    "authorization",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "token",
    "secret",
}

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}", re.IGNORECASE)
SECRET_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?62|0)[\s.-]?(?:\d[\s.-]?){8,14}(?!\w)")


def redact_string(value: str) -> str:
    value = BEARER_RE.sub("Bearer [REDACTED]", value)
    value = SECRET_RE.sub(REDACTED, value)
    value = EMAIL_RE.sub(REDACTED, value)
    value = PHONE_RE.sub(REDACTED, value)
    return value


def redact_for_trace(value: Any) -> Any:
    """Sanitize common PII/secrets before observability persistence or public tool traces."""
    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        for key, item in value.items():
            normalized = str(key).strip().lower()
            if normalized in SENSITIVE_KEYS:
                output[str(key)] = REDACTED if item not in (None, "") else item
            else:
                output[str(key)] = redact_for_trace(item)
        return output

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact_for_trace(item) for item in value]

    if isinstance(value, str):
        return redact_string(value)

    return value
