from app.agent.orchestrator import render_profile_reply, requested_profile_fields


def test_profile_fields_detect_address_and_instagram() -> None:
    assert requested_profile_fields("Alamat dan Instagram Clevia apa?") == (
        "address",
        "instagram",
    )


def test_profile_fields_detect_contact() -> None:
    fields = requested_profile_fields("Kontak Clevia yang bisa dihubungi apa?")
    assert fields == ("phone", "email")


def test_service_price_is_not_misclassified_as_profile_request() -> None:
    assert requested_profile_fields("Berapa harga Glow Facial Signature?") == ()


def test_profile_reply_uses_only_requested_fields() -> None:
    reply = render_profile_reply(
        {
            "name": "Clevia Beauty Clinic",
            "address": "Jakarta, Indonesia",
            "instagram": "@cleviabeauty",
            "phone": "+62 21 5550 2026",
        },
        ("address", "instagram"),
    )

    assert "Alamat: Jakarta, Indonesia" in reply
    assert "Instagram: @cleviabeauty" in reply
    assert "Telepon" not in reply
