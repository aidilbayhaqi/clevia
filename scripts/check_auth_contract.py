from app.schemas.auth import LoginRequest


payload = LoginRequest(email="owner@clevia.id", password="ChangeMe123!")
assert str(payload.email) == "owner@clevia.id"

print("AUTH_SCHEMA_CONTRACT_OK")
print("email =", payload.email)
