from app.agent.router import Intent, route_intent


def test_greeting():
    assert route_intent("halo") == Intent.GREETING


def test_service_interest():
    assert route_intent("Saya tertarik treatment acne") == Intent.SERVICE_INTEREST


def test_booking_interest():
    assert route_intent("Saya mau booking untuk Sabtu") == Intent.BOOKING_INTEREST


def test_human_request():
    assert route_intent("Saya mau bicara dengan admin") == Intent.HUMAN_HANDOFF


def test_complaint_goes_to_human():
    assert route_intent("Saya kecewa dan mau komplain") == Intent.HUMAN_HANDOFF


def test_medical_safety_has_priority():
    assert route_intent("Treatment ini aman untuk saya?") == Intent.MEDICAL_SAFETY


def test_general_information():
    assert route_intent("Jam bukanya sampai jam berapa?") == Intent.INFORMATION