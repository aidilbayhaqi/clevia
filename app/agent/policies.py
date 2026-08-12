from __future__ import annotations

from app.agent.router import Intent


MISSING_EVIDENCE_MESSAGE = (
    "Saya belum menemukan informasi resmi yang disetujui klinik untuk menjawab hal tersebut. "
    "Saya tidak ingin menebak. Jika diperlukan, percakapan ini dapat diteruskan ke tim klinik."
)

MEDICAL_HANDOFF_MESSAGE = (
    "Untuk pertanyaan yang menyangkut keamanan atau kesesuaian treatment secara personal, "
    "Clevia tidak memberikan penilaian medis melalui chatbot. Saya teruskan konteksnya ke tim "
    "klinik agar dapat ditangani oleh tenaga yang sesuai."
)

HUMAN_HANDOFF_MESSAGE = "Baik, percakapan ini saya teruskan ke tim klinik."


def requires_grounded_source(intent: Intent) -> bool:
    return intent == Intent.INFORMATION
