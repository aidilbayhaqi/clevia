from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings
from app.llm.base import LLMFunctionCall, LLMTurn


class OpenAIResponsesAdapter:
    provider = "openai"

    def _get_client(self) -> AsyncOpenAI:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. Set it in .env and restart the API container."
            )
        return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def respond(
        self,
        *,
        instructions: str,
        input_items: list[Any],
        tools: list[dict],
    ) -> LLMTurn:
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": settings.OPENAI_MODEL,
            "reasoning": {"effort": settings.OPENAI_REASONING_EFFORT},
            "instructions": instructions,
            "input": input_items,
            "parallel_tool_calls": False,
        }
        if tools:
            kwargs["tools"] = tools

        response = await client.responses.create(**kwargs)
        function_calls = [
            LLMFunctionCall(
                call_id=item.call_id,
                name=item.name,
                arguments_json=item.arguments,
            )
            for item in response.output
            if getattr(item, "type", None) == "function_call"
        ]
        usage = getattr(response, "usage", None)
        return LLMTurn(
            text=getattr(response, "output_text", "") or "",
            function_calls=function_calls,
            continuation_items=list(response.output),
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
            provider=self.provider,
            model=settings.OPENAI_MODEL,
        )
