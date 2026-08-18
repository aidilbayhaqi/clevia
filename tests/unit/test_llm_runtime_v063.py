from __future__ import annotations

import asyncio
import unittest

from app.agent.llm_bridge import AgentLLMBridge
from app.llm.provider_contract import LLMResponse
from app.llm.runtime import LLMRuntime, LLMRuntimeError
from app.observability.llm_trace import LLMCallContext


class FakeProvider:
    provider_name = "fake"
    model = "fake-model"

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.closed = False

    async def complete(self, prompt, *, system_instruction=None, max_output_tokens=None):
        if self.fail:
            raise TimeoutError("simulated timeout")
        return LLMResponse(
            text="CLEVIA_RUNTIME_OK",
            provider=self.provider_name,
            model=self.model,
            input_tokens=3,
            output_tokens=2,
            total_tokens=5,
            finish_reason="stop",
        )

    async def close(self):
        self.closed = True


class LLMRuntimeV063Test(unittest.TestCase):
    def test_success_builds_trace_metadata(self):
        events = []
        runtime = LLMRuntime(FakeProvider(), trace_sink=events.append)
        result = asyncio.run(
            runtime.complete(
                "hello",
                context=LLMCallContext(
                    trace_id="tr-test",
                    request_id="req-test",
                    clinic_id="clinic-test",
                    prompt_version="pv-test",
                ),
            )
        )
        self.assertEqual(result.text, "CLEVIA_RUNTIME_OK")
        self.assertEqual(result.trace_event.provider, "fake")
        self.assertEqual(result.trace_event.model, "fake-model")
        self.assertEqual(result.trace_event.total_tokens, 5)
        self.assertEqual(result.trace_event.trace_id, "tr-test")
        self.assertEqual(result.trace_event.clinic_id, "clinic-test")
        self.assertEqual(result.trace_event.outcome, "success")
        self.assertGreaterEqual(result.trace_event.latency_ms, 0)
        self.assertEqual(len(events), 1)

    def test_trace_does_not_store_prompt(self):
        runtime = LLMRuntime(FakeProvider())
        result = asyncio.run(runtime.complete("RAHASIA-PROMPT"))
        data = result.trace_event.to_dict()
        serialized = repr(data)
        self.assertNotIn("RAHASIA-PROMPT", serialized)
        self.assertNotIn("prompt", data)
        self.assertNotIn("system_instruction", data)

    def test_failure_is_fail_loud_and_traced(self):
        events = []
        runtime = LLMRuntime(FakeProvider(fail=True), trace_sink=events.append)
        with self.assertRaises(LLMRuntimeError) as ctx:
            asyncio.run(runtime.complete("hello"))
        self.assertEqual(ctx.exception.trace_event.outcome, "error")
        self.assertEqual(ctx.exception.trace_event.error_type, "TimeoutError")
        self.assertEqual(len(events), 1)

    def test_agent_bridge_uses_runtime_contract(self):
        runtime = LLMRuntime(FakeProvider())
        bridge = AgentLLMBridge(runtime)
        result = asyncio.run(bridge.generate("hello"))
        self.assertEqual(result.text, "CLEVIA_RUNTIME_OK")
        self.assertEqual(result.trace_event.provider, "fake")


if __name__ == "__main__":
    unittest.main(verbosity=2)
