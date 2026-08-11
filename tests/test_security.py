import uuid
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password

def test_password_hashing():
    hashed=hash_password("secret123")
    assert hashed!="secret123"
    assert verify_password("secret123",hashed)

def test_jwt_round_trip():
    user_id=uuid.uuid4()
    token=create_access_token(user_id,"owner")
    assert decode_access_token(token)["sub"]==str(user_id)
