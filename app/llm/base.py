from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class LLMFunctionCall:
    call_id: str
    name: str
    arguments_json: str


@dataclass(slots=True)
class LLMTurn:
    text: str
    function_calls: list[LLMFunctionCall] = field(default_factory=list)
    continuation_items: list[Any] = field(default_factory=list)
    input_tokens: int | None = None
    output_tokens: int | None = None
    provider: str = "unknown"
    model: str = "unknown"


class LLMAdapter(Protocol):
    async def respond(
        self,
        *,
        instructions: str,
        input_items: list[Any],
        tools: list[dict],
    ) -> LLMTurn: ...
