from __future__ import annotations

import json
from pathlib import Path

from app.agent.router import route_intent
from app.observability.redaction import redact_for_trace
from app.services.safety import classify_risk

ROOT = Path(__file__).resolve().parents[1]

CASES = [
    ("greeting", "Halo", "GREETING", "normal"),
    ("info", "Jam buka klinik hari Sabtu?", "INFORMATION", "normal"),
    ("human", "Saya mau bicara sama admin", "HUMAN_HANDOFF", "normal"),
    ("complaint", "Saya tidak puas hasilnya", "HUMAN_HANDOFF", "normal"),
    ("booking", "Saya ingin reservasi hari Sabtu", "BOOKING_INTEREST", "normal"),
    ("interest", "Saya tertarik layanan acne", "SERVICE_INTEREST", "normal"),
    ("medical", "Apakah treatment aman untuk saya saat hamil?", "MEDICAL_SAFETY", "normal"),
    ("emergency", "Saya kejang setelah treatment", "INFORMATION", "emergency"),
]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def main() -> int:
    failures: list[dict] = []

    for case_id, message, expected_intent, expected_risk in CASES:
        actual_intent = route_intent(message).value
        actual_risk = classify_risk(message)

        if actual_intent != expected_intent or actual_risk != expected_risk:
            failures.append(
                {
                    "case": case_id,
                    "expected": {
                        "intent": expected_intent,
                        "risk": expected_risk,
                    },
                    "actual": {
                        "intent": actual_intent,
                        "risk": actual_risk,
                    },
                }
            )

    retrieval = read("app/knowledge/retrieval.py")
    for needle in (
        "KnowledgeDocument.clinic_id == clinic_id",
        "KnowledgeDocument.status == KnowledgeStatus.APPROVED",
        "KnowledgeChunk.clinic_id == clinic_id",
        "KnowledgeDocument.valid_from",
        "KnowledgeDocument.valid_until",
    ):
        if needle not in retrieval:
            failures.append({"contract": "retrieval", "missing": needle})

    knowledge = read("app/api/v1/routes/knowledge.py")
    if "KnowledgeDocument.clinic_id == clinic_id" not in knowledge:
        failures.append({"contract": "knowledge_tenant"})

    conversations = read("app/api/v1/routes/conversations.py")
    if "Conversation.clinic_id == clinic_id" not in conversations:
        failures.append({"contract": "conversation_tenant"})
    if "\nagent = CleviaAgent()\n" in conversations:
        failures.append({"contract": "eager_agent_initialization"})
    if "def get_agent() -> CleviaAgent:" not in conversations:
        failures.append({"contract": "lazy_agent_factory_missing"})
    if "await get_agent().run(" not in conversations:
        failures.append({"contract": "lazy_agent_not_used"})

    provider = read("app/llm/provider.py")
    if "return GeminiGenerateContentAdapter()" not in provider:
        failures.append({"contract": "wrong_gemini_runtime_adapter"})

    adapter = read("app/llm/gemini_adapter.py")
    for needle in (
        "class GeminiGenerateContentAdapter:",
        "async def respond(",
        "def _call_name(",
        "def _parse_tool_output(",
    ):
        if needle not in adapter:
            failures.append({"contract": "gemini_runtime", "missing": needle})

    prompt = read("app/llm/prompt_registry.py")
    if 'version="2.0.0"' not in prompt:
        failures.append({"contract": "prompt_version_2"})

    clean = redact_for_trace(
        {
            "full_name": "Budi",
            "phone": "+628123456789",
            "email": "budi@example.com",
        }
    )
    if any(clean[key] != "[REDACTED]" for key in ("full_name", "phone", "email")):
        failures.append({"contract": "trace_privacy"})

    result = {
        "gate": "P0_REPAIR_V066",
        "passed": not failures,
        "routing_cases": len(CASES),
        "failures": failures,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
