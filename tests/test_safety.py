from app.services.safety import classify_risk
def test_emergency_risk():
    assert classify_risk("Saya sulit bernapas setelah treatment")=="emergency"
def test_normal_risk():
    assert classify_risk("Berapa harga facial?")=="normal"
