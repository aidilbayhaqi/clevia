from __future__ import annotations

from app.agent.router import Intent


MISSING_EVIDENCE_MESSAGE = (
    "Saya belum punya info resmi yang cukup untuk jawab itu dengan yakin. "
    "Daripada saya asal jawab, saya bisa bantu teruskan ke admin ya."
)

MEDICAL_HANDOFF_MESSAGE = (
    "Kalau menyangkut kondisi atau keamanan treatment untuk kamu secara pribadi, "
    "lebih aman dicek langsung oleh tim klinik. Saya teruskan konteksnya ke admin ya."
)

HUMAN_HANDOFF_MESSAGE = (
    "Siap, saya teruskan ke admin ya. Konteks chat ini ikut saya sertakan supaya kamu "
    "nggak perlu jelasin dari awal."
)


def requires_grounded_source(intent: Intent) -> bool:
    # Only pure informational answers are hard-gated here. For lead/booking intent
    # the agent may simply collect contact details without making a factual claim.
    return intent == Intent.INFORMATION