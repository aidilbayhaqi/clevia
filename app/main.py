from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME, version=settings.APP_VERSION,
        docs_url="/docs" if settings.ENVIRONMENT!="production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT!="production" else None,
    )
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
    )
    app.include_router(api_router,prefix=settings.API_V1_PREFIX)

    @app.get("/")
    async def root():
        return {
            "service":settings.APP_NAME,"version":settings.APP_VERSION,
            "brand":"Clevia Beauty Clinic",
            "docs":"/docs" if settings.ENVIRONMENT!="production" else None,
        }
    return app

app = create_app()
