from __future__ import annotations

from app.core.config import settings
from app.llm.base import LLMAdapter
from app.llm.errors import LLMNotConfiguredError
from app.llm.gemini_adapter import GeminiGenerateContentAdapter
from app.llm.openai_adapter import OpenAIResponsesAdapter


def get_llm_adapter() -> LLMAdapter:
    provider = settings.normalized_llm_provider

    if provider == "gemini":
        return GeminiGenerateContentAdapter()

    if provider == "openai":
        return OpenAIResponsesAdapter()

    raise LLMNotConfiguredError(
        f"Unsupported LLM provider: {settings.LLM_PROVIDER!r}."
    )
