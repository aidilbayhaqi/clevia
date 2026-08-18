from __future__ import annotations

import inspect
import json

from app.agent.router import route_intent
from app.api.v1.routes import conversations, knowledge
from app.knowledge import retrieval
from app.observability.redaction import redact_for_trace
from app.services.safety import classify_risk

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


def main() -> int:
    failures: list[dict] = []

    for case_id, message, expected_intent, expected_risk in CASES:
        actual_intent = route_intent(message).value
        actual_risk = classify_risk(message)
        if actual_intent != expected_intent or actual_risk != expected_risk:
            failures.append(
                {
                    "case": case_id,
                    "expected": {"intent": expected_intent, "risk": expected_risk},
                    "actual": {"intent": actual_intent, "risk": actual_risk},
                }
            )

    retrieval_source = inspect.getsource(retrieval.RetrievalService.search)
    for needle in (
        "KnowledgeDocument.clinic_id == clinic_id",
        "KnowledgeDocument.status == KnowledgeStatus.APPROVED",
        "KnowledgeChunk.clinic_id == clinic_id",
        "KnowledgeDocument.valid_from",
        "KnowledgeDocument.valid_until",
    ):
        if needle not in retrieval_source:
            failures.append({"contract": "retrieval", "missing": needle})

    if "KnowledgeDocument.clinic_id == clinic_id" not in inspect.getsource(
        knowledge._tenant_document
    ):
        failures.append({"contract": "knowledge_tenant"})

    if "Conversation.clinic_id == clinic_id" not in inspect.getsource(
        conversations._tenant_conversation
    ):
        failures.append({"contract": "conversation_tenant"})

    clean = redact_for_trace(
        {"full_name": "Budi", "phone": "+628123456789", "email": "budi@example.com"}
    )
    if any(clean[key] != "[REDACTED]" for key in ("full_name", "phone", "email")):
        failures.append({"contract": "trace_privacy"})

    result = {
        "gate": "P0_RELEASE_HARDENING",
        "passed": not failures,
        "routing_cases": len(CASES),
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
