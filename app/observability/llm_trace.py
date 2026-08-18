"""Trace metadata vendor-neutral untuk panggilan LLM Clevia.

Trace ini sengaja tidak menyimpan prompt/system instruction mentah. Tujuannya adalah
observability operasional tanpa menambah risiko kebocoran PII/PHI lewat telemetry.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class LLMCallContext:
    trace_id: str | None = None
    request_id: str | None = None
    clinic_id: str | None = None
    conversation_id: str | None = None
    prompt_version: str | None = None


@dataclass(frozen=True, slots=True)
class LLMTraceEvent:
    provider: str
    model: str
    outcome: str
    latency_ms: float
    started_at: str
    finished_at: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    finish_reason: str | None = None
    error_type: str | None = None
    trace_id: str | None = None
    request_id: str | None = None
    clinic_id: str | None = None
    conversation_id: str | None = None
    prompt_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
