"""Adapter Gemini ke kontrak LLM canonical Clevia."""
from __future__ import annotations

from app.llm.gemini_provider import GeminiProvider
from app.llm.provider_contract import LLMResponse


class GeminiLLMAdapter:
    provider_name = "gemini"

    def __init__(self, provider: GeminiProvider) -> None:
        self._provider = provider

    @classmethod
    def from_env(cls) -> "GeminiLLMAdapter":
        return cls(GeminiProvider.from_env())

    @property
    def model(self) -> str:
        return self._provider.config.model

    async def complete(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        max_output_tokens: int | None = None,
    ) -> LLMResponse:
        result = await self._provider.generate_text(
            prompt,
            system_instruction=system_instruction,
            max_output_tokens=max_output_tokens,
        )
        return LLMResponse(
            text=result.text,
            provider=result.provider,
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            total_tokens=result.total_tokens,
            finish_reason=result.finish_reason,
        )

    async def close(self) -> None:
        await self._provider.aclose()
