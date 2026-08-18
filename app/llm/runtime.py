"""Runtime LLM canonical Clevia.

Boundary ini berada di antara Agent dan provider factory. Runtime bertanggung jawab
atas normalisasi hasil, latency/token metadata, dan trace hook. Business rules,
tenant authorization, CRM rule, retrieval policy, serta tool permission tetap berada
di layer masing-masing dan tidak dipindahkan ke sini.
"""
from __future__ import annotations

import inspect
import time
from dataclasses import dataclass
from typing import Awaitable, Callable

from app.llm.provider_contract import LLMProvider, LLMResponse
from app.llm.provider_factory import create_llm_provider
from app.observability.llm_trace import LLMCallContext, LLMTraceEvent, utc_now_iso


TraceSink = Callable[[LLMTraceEvent], None | Awaitable[None]]


class LLMRuntimeError(RuntimeError):
    """Panggilan provider gagal setelah trace metadata dibentuk."""

    def __init__(self, message: str, *, trace_event: LLMTraceEvent) -> None:
        super().__init__(message)
        self.trace_event = trace_event


@dataclass(frozen=True, slots=True)
class LLMRuntimeResult:
    response: LLMResponse
    trace_event: LLMTraceEvent

    @property
    def text(self) -> str:
        return self.response.text


class LLMRuntime:
    def __init__(
        self,
        provider: LLMProvider | None = None,
        *,
        trace_sink: TraceSink | None = None,
    ) -> None:
        self._provider = provider or create_llm_provider()
        self._trace_sink = trace_sink

    @property
    def provider_name(self) -> str:
        return self._provider.provider_name

    async def _emit_trace(self, event: LLMTraceEvent) -> None:
        if self._trace_sink is None:
            return
        result = self._trace_sink(event)
        if inspect.isawaitable(result):
            await result

    async def complete(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        max_output_tokens: int | None = None,
        context: LLMCallContext | None = None,
    ) -> LLMRuntimeResult:
        ctx = context or LLMCallContext()
        started_at = utc_now_iso()
        start = time.perf_counter()

        try:
            response = await self._provider.complete(
                prompt,
                system_instruction=system_instruction,
                max_output_tokens=max_output_tokens,
            )
        except Exception as exc:
            finished_at = utc_now_iso()
            latency_ms = round((time.perf_counter() - start) * 1000, 3)
            model = getattr(self._provider, "model", "unknown")
            event = LLMTraceEvent(
                provider=self._provider.provider_name,
                model=str(model),
                outcome="error",
                latency_ms=latency_ms,
                started_at=started_at,
                finished_at=finished_at,
                error_type=type(exc).__name__,
                trace_id=ctx.trace_id,
                request_id=ctx.request_id,
                clinic_id=ctx.clinic_id,
                conversation_id=ctx.conversation_id,
                prompt_version=ctx.prompt_version,
            )
            await self._emit_trace(event)
            raise LLMRuntimeError(
                f"LLM provider '{self._provider.provider_name}' gagal: {type(exc).__name__}",
                trace_event=event,
            ) from exc

        finished_at = utc_now_iso()
        latency_ms = round((time.perf_counter() - start) * 1000, 3)
        event = LLMTraceEvent(
            provider=response.provider,
            model=response.model,
            outcome="success",
            latency_ms=latency_ms,
            started_at=started_at,
            finished_at=finished_at,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            total_tokens=response.total_tokens,
            finish_reason=response.finish_reason,
            trace_id=ctx.trace_id,
            request_id=ctx.request_id,
            clinic_id=ctx.clinic_id,
            conversation_id=ctx.conversation_id,
            prompt_version=ctx.prompt_version,
        )
        await self._emit_trace(event)
        return LLMRuntimeResult(response=response, trace_event=event)

    async def close(self) -> None:
        await self._provider.close()
