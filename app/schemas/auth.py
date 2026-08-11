import uuid
from pydantic import BaseModel, EmailStr
from app.db.models.enums import UserRole

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserMe(BaseModel):
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: UserRole
    model_config = {"from_attributes": True}

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserMe
