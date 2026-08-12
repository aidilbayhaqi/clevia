from enum import StrEnum


class Intent(StrEnum):
    GREETING = "GREETING"
    INFORMATION = "INFORMATION"
    SERVICE_INTEREST = "SERVICE_INTEREST"
    BOOKING_INTEREST = "BOOKING_INTEREST"
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
    "thanks",
}

_HUMAN_PHRASES = (
    "bicara dengan admin",
    "bicara sama admin",
    "hubungi admin",
    "mau admin",
    "minta admin",
    "petugas manusia",
    "customer service",
    "receptionist",
    "resepsionis",
    "staf klinik",
    "orangnya langsung",
)

_COMPLAINT_PHRASES = (
    "komplain",
    "complaint",
    "kecewa",
    "tidak puas",
    "ga puas",
    "gak puas",
    "buruk sekali",
    "mau mengeluh",
    "saya protes",
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

_BOOKING_PHRASES = (
    "mau booking",
    "ingin booking",
    "mau reservasi",
    "ingin reservasi",
    "buat jadwal",
    "ambil jadwal",
    "mau jadwal",
    "ingin jadwal",
    "bisa sabtu",
    "bisa minggu",
    "ada slot",
    "ada jadwal",
    "kapan bisa datang",
)

_INTEREST_PHRASES = (
    "saya tertarik",
    "aku tertarik",
    "tertarik treatment",
    "tertarik layanan",
    "mau treatment",
    "ingin treatment",
    "mau facial",
    "ingin facial",
    "mau coba",
    "ingin coba",
    "mau ambil",
    "ingin ambil",
)


def route_intent(message: str) -> Intent:
    normalized = " ".join(message.lower().strip().split())

    if normalized in _GREETING:
        return Intent.GREETING

    if any(term in normalized for term in _MEDICAL_TERMS):
        return Intent.MEDICAL_SAFETY

    if any(phrase in normalized for phrase in _HUMAN_PHRASES):
        return Intent.HUMAN_HANDOFF

    if any(phrase in normalized for phrase in _COMPLAINT_PHRASES):
        return Intent.HUMAN_HANDOFF

    if any(phrase in normalized for phrase in _BOOKING_PHRASES):
        return Intent.BOOKING_INTEREST

    if any(phrase in normalized for phrase in _INTEREST_PHRASES):
        return Intent.SERVICE_INTEREST

    return Intent.INFORMATION