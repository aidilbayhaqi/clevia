from fastapi import APIRouter
from app.api.v1.routes import appointments, auth, conversations, crm, health, knowledge, public

api_router = APIRouter()
api_router.include_router(health.router,prefix="/health",tags=["health"])
api_router.include_router(auth.router,prefix="/auth",tags=["auth"])
api_router.include_router(public.router,prefix="/public",tags=["public"])
api_router.include_router(conversations.public_router,prefix="/public",tags=["public-chat"])
api_router.include_router(crm.router,prefix="/crm",tags=["crm"])
api_router.include_router(appointments.router,prefix="/appointments",tags=["appointments"])
api_router.include_router(conversations.admin_router,prefix="/conversations",tags=["conversations"])
api_router.include_router(knowledge.router,prefix="/knowledge",tags=["knowledge"])
