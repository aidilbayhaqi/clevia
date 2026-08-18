from __future__ import annotations

import asyncio

from app.agent.llm_bridge import AgentLLMBridge
from app.llm.provider_contract import LLMResponse
from app.llm.runtime import LLMRuntime
from app.observability.llm_trace import LLMCallContext


class SmokeProvider:
    provider_name = "smoke"
    model = "smoke-model"

    async def complete(self, prompt, *, system_instruction=None, max_output_tokens=None):
        return LLMResponse(
            text="CLEVIA_AGENT_LLM_BRIDGE_OK",
            provider=self.provider_name,
            model=self.model,
            input_tokens=1,
            output_tokens=1,
            total_tokens=2,
            finish_reason="stop",
        )

    async def close(self):
        return None


async def main() -> None:
    bridge = AgentLLMBridge(LLMRuntime(SmokeProvider()))
    result = await bridge.generate(
        "offline smoke",
        context=LLMCallContext(trace_id="tr-smoke", request_id="req-smoke"),
    )
    print(f"text={result.text}")
    print(f"provider={result.trace_event.provider}")
    print(f"model={result.trace_event.model}")
    print(f"outcome={result.trace_event.outcome}")
    print("status=CLEVIA_LLM_RUNTIME_V063_OK")


if __name__ == "__main__":
    asyncio.run(main())
