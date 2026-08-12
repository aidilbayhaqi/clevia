from app.agent.router import Intent, route_intent


def test_greeting_route():
    assert route_intent("Halo") == Intent.GREETING


def test_human_route():
    assert route_intent("Saya mau bicara dengan admin") == Intent.HUMAN_HANDOFF


def test_medical_suitability_route():
    assert route_intent("Treatment ini aman untuk saya saat hamil?") == Intent.MEDICAL_SAFETY


def test_default_information_route():
    assert route_intent("Jam buka klinik hari Sabtu?") == Intent.INFORMATION
