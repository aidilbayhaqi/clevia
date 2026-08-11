from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Clevia Beauty Clinic API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "postgresql+asyncpg://clevia:clevia@postgres:5432/clevia"
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_SECRET: str = "change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 480
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5.6-luna"
    OPENAI_REASONING_EFFORT: str = "low"
    MAX_AGENT_STEPS: int = 6
    CACHE_TTL_CLINIC_SECONDS: int = 900
    CACHE_TTL_SERVICES_SECONDS: int = 300
    CACHE_TTL_STAFF_SECONDS: int = 300
    CACHE_TTL_AVAILABILITY_SECONDS: int = 30
    CACHE_TTL_KNOWLEDGE_SECONDS: int = 120
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
