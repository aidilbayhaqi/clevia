from __future__ import annotations

from app.core.config import settings
from app.llm.base import LLMAdapter
from app.llm.gemini_adapter import GeminiGenerateContentAdapter
from app.llm.openai_adapter import OpenAIResponsesAdapter
from app.llm.gemini_adapter import GeminiLLMAdapter


def get_llm_adapter() -> LLMAdapter:
    provider = settings.normalized_llm_provider

    if provider == "gemini":
        return GeminiLLMAdapter.from_env()

    if provider == "openai":
        return OpenAIResponsesAdapter()

    raise RuntimeError(
        f"Unsupported LLM_PROVIDER={settings.LLM_PROVIDER!r}. "
        "Supported providers: gemini, openai."
    )