from enum import StrEnum


class Intent(StrEnum):
    GREETING = "GREETING"
    INFORMATION = "INFORMATION"
    HUMAN_HANDOFF = "HUMAN_HANDOFF"
    MEDICAL_SAFETY = "MEDICAL_SAFETY"


_GREETING = {
    "halo",
    "hai",
    "hi",
    "hello",
    "pagi",
    "siang",
    "sore",
    "malam",
    "terima kasih",
    "makasih",
}

_HUMAN_PHRASES = (
    "bicara dengan admin",
    "bicara sama admin",
    "hubungi admin",
    "mau admin",
    "petugas manusia",
    "customer service",
    "receptionist",
    "resepsionis",
    "staf klinik",
)

_MEDICAL_TERMS = (
    "hamil",
    "kehamilan",
    "menyusui",
    "kontraindikasi",
    "komplikasi",
    "alergi parah",
    "aman untuk saya",
    "cocok untuk saya",
    "obat yang saya minum",
    "diagnosis",
    "diagnosa",
    "resep",
    "dosis obat",
)


def route_intent(message: str) -> Intent:
    normalized = " ".join(message.lower().strip().split())
    if normalized in _GREETING:
        return Intent.GREETING
    if any(phrase in normalized for phrase in _HUMAN_PHRASES):
        return Intent.HUMAN_HANDOFF
    if any(term in normalized for term in _MEDICAL_TERMS):
        return Intent.MEDICAL_SAFETY
    return Intent.INFORMATION
