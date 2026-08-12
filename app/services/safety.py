EMERGENCY_TERMS = {
    "sulit bernapas",
    "sesak napas",
    "tidak bisa bernapas",
    "nyeri dada",
    "pingsan",
    "kejang",
    "perdarahan hebat",
    "bengkak tenggorokan",
    "bengkak di tenggorokan",
    "anafilaksis",
}


def classify_risk(message: str) -> str:
    normalized = message.lower()
    return "emergency" if any(term in normalized for term in EMERGENCY_TERMS) else "normal"


def emergency_response() -> str:
    return (
        "Keluhan yang Anda sampaikan dapat membutuhkan pertolongan medis segera. "
        "Chatbot Clevia tidak dapat menangani kondisi darurat atau memberikan diagnosis. "
        "Segera cari pertolongan medis langsung atau layanan gawat darurat terdekat."
    )
