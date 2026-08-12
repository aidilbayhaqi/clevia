from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Clevia Beauty Clinic API"
    APP_VERSION: str = "0.6.0"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://clevia:clevia@postgres:5432/clevia"
    REDIS_URL: str = "redis://redis:6379/0"

    JWT_SECRET: str = "change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 480

    DEFAULT_CLINIC_SLUG: str = "clevia"

    LLM_PROVIDER: str = "gemini"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"
    GEMINI_TEMPERATURE: float = 0.7
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5.6-luna"
    OPENAI_REASONING_EFFORT: str = "low"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    MAX_AGENT_STEPS: int = 6

    AGENT_TRANSACTIONAL_TOOLS_ENABLED: bool = False
    KNOWLEDGE_EMBEDDINGS_ENABLED: bool = False
    KNOWLEDGE_CHUNK_MAX_CHARS: int = 1200

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

    @property
    def normalized_llm_provider(self) -> str:
        return self.LLM_PROVIDER.strip().lower()

    @property
    def llm_configured(self) -> bool:
        provider = self.normalized_llm_provider
        if provider == "gemini":
            return bool(self.GEMINI_API_KEY.strip())
        if provider == "openai":
            return bool(self.OPENAI_API_KEY.strip())
        return False

    @property
    def active_llm_model(self) -> str:
        provider = self.normalized_llm_provider
        if provider == "gemini":
            return self.GEMINI_MODEL
        if provider == "openai":
            return self.OPENAI_MODEL
        return "unknown"

    @property
    def active_llm_key_name(self) -> str:
        provider = self.normalized_llm_provider
        if provider == "gemini":
            return "GEMINI_API_KEY"
        if provider == "openai":
            return "OPENAI_API_KEY"
        return "LLM_API_KEY"
    @property
    def is_non_dev(self) -> bool:
        return self.ENVIRONMENT.lower() in {"staging", "production"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
