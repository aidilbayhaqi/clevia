from __future__ import annotations

import time
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.observability import AgentTrace, ToolExecution


class TraceRecorder:
    def __init__(
        self,
        db: AsyncSession,
        *,
        request_id: str,
        clinic_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
        prompt_id: str,
        prompt_version: str,
    ) -> None:
        self.db = db
        self.started = time.perf_counter()
        self.trace = AgentTrace(
            trace_id=f"tr_{uuid.uuid4().hex}",
            request_id=request_id,
            clinic_id=clinic_id,
            conversation_id=conversation_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            retrieval_refs=[],
            tool_calls_json=[],
            outcome="running",
        )
        db.add(self.trace)

    @property
    def trace_id(self) -> str:
        return self.trace.trace_id

    async def record_tool(
        self,
        *,
        tool_name: str,
        input_json: dict,
        output_json: dict,
        status: str,
        latency_ms: int,
        clinic_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
        idempotency_key: str | None = None,
    ) -> None:
        self.trace.tool_calls_json = [
            *self.trace.tool_calls_json,
            {"tool_name": tool_name, "status": status, "latency_ms": latency_ms},
        ]
        self.db.add(
            ToolExecution(
                trace_id=self.trace_id,
                clinic_id=clinic_id,
                conversation_id=conversation_id,
                tool_name=tool_name,
                input_json=input_json,
                output_json=output_json,
                status=status,
                idempotency_key=idempotency_key,
                latency_ms=latency_ms,
            )
        )
        await self.db.flush()

    def add_retrieval_refs(self, refs: list[str]) -> None:
        current = list(self.trace.retrieval_refs)
        for ref in refs:
            if ref not in current:
                current.append(ref)
        self.trace.retrieval_refs = current

    async def finish(
        self,
        *,
        intent: str,
        state: str,
        provider: str | None,
        model: str | None,
        input_tokens: int | None,
        output_tokens: int | None,
        outcome: str,
        error_code: str | None = None,
    ) -> None:
        self.trace.intent = intent
        self.trace.state = state
        self.trace.provider = provider
        self.trace.model = model
        self.trace.input_tokens = input_tokens
        self.trace.output_tokens = output_tokens
        self.trace.latency_ms = int((time.perf_counter() - self.started) * 1000)
        self.trace.outcome = outcome
        self.trace.error_code = error_code
        await self.db.flush()


def source_refs_from_tool_result(result: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(result, dict):
        ref = result.get("source_ref")
        if isinstance(ref, str):
            refs.append(ref)
        for key in ("results", "services"):
            rows = result.get(key)
            if isinstance(rows, list):
                for row in rows:
                    if isinstance(row, dict) and isinstance(row.get("source_ref"), str):
                        refs.append(row["source_ref"])
    return refs
