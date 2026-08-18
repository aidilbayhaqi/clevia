"""Bridge canonical dari Agent Clevia ke LLMRuntime.

Orchestrator seharusnya bergantung pada bridge/runtime contract ini, bukan pada SDK
Gemini/OpenAI secara langsung. File ini belum mengubah routing, policy, retrieval,
atau tool behavior.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.llm.runtime import LLMRuntime
from app.observability.llm_trace import LLMCallContext, LLMTraceEvent


@dataclass(frozen=True, slots=True)
class AgentLLMResult:
    text: str
    trace_event: LLMTraceEvent


class AgentLLMBridge:
    def __init__(self, runtime: LLMRuntime | None = None) -> None:
        self._runtime = runtime or LLMRuntime()

    async def generate(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        max_output_tokens: int | None = None,
        context: LLMCallContext | None = None,
    ) -> AgentLLMResult:
        result = await self._runtime.complete(
            prompt,
            system_instruction=system_instruction,
            max_output_tokens=max_output_tokens,
            context=context,
        )
        return AgentLLMResult(text=result.text, trace_event=result.trace_event)

    async def close(self) -> None:
        await self._runtime.close()


def create_agent_llm_bridge() -> AgentLLMBridge:
    return AgentLLMBridge()
