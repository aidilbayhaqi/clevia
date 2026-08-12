from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.policies import (
    HUMAN_HANDOFF_MESSAGE,
    MEDICAL_HANDOFF_MESSAGE,
    MISSING_EVIDENCE_MESSAGE,
    requires_grounded_source,
)
from app.agent.router import Intent, route_intent
from app.agent.schemas import AgentResult, HandoffResult, SourceReference
from app.core.config import settings
from app.core.request_context import get_request_context
from app.db.models.conversation import Conversation, Message
from app.db.models.enums import AgentState, ConversationStatus
from app.llm.openai_adapter import OpenAIResponsesAdapter
from app.llm.prompt_registry import prompt_registry
from app.observability.tracing import TraceRecorder, source_refs_from_tool_result
from app.services.safety import classify_risk, emergency_response
from app.tools.registry import TOOL_SCHEMAS, execute_tool


class CleviaAgent:
    def __init__(self) -> None:
        self.llm = OpenAIResponsesAdapter()

    @staticmethod
    def _handoff_summary(history: list[Message], user_message: str) -> str:
        lines = [
            f"{message.sender_type}: {message.content[:400]}"
            for message in history[-5:]
        ]
        lines.append(f"visitor: {user_message[:600]}")
        return "\n".join(lines)[-1800:]

    @staticmethod
    def _source_objects(result: dict) -> list[SourceReference]:
        output: list[SourceReference] = []
        if isinstance(result.get("source_ref"), str):
            output.append(
                SourceReference(
                    source_ref=result["source_ref"],
                    title=result.get("name") or result.get("title"),
                )
            )
        for key in ("results", "services"):
            rows = result.get(key)
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict) or not isinstance(row.get("source_ref"), str):
                    continue
                output.append(
                    SourceReference(
                        source_ref=row["source_ref"],
                        title=row.get("title") or row.get("name"),
                        document_id=row.get("document_id"),
                        version=row.get("version"),
                    )
                )
        return output

    async def _direct_handoff(
        self,
        db: AsyncSession,
        *,
        conversation: Conversation,
        history: list[Message],
        user_message: str,
        intent: Intent,
        reason: str,
        message: str,
        trace: TraceRecorder,
    ) -> AgentResult:
        summary = self._handoff_summary(history, user_message)
        conversation.status = ConversationStatus.WAITING_HUMAN
        conversation.agent_state = AgentState.HANDOFF.value
        conversation.handoff_reason = reason
        conversation.handoff_summary = summary
        conversation.handoff_at = datetime.now(timezone.utc)
        await trace.finish(
            intent=intent.value,
            state=AgentState.HANDOFF.value,
            provider=None,
            model=None,
            input_tokens=None,
            output_tokens=None,
            outcome="handoff",
        )
        return AgentResult(
            message=message,
            state=AgentState.HANDOFF,
            intent=intent.value,
            handoff=HandoffResult(
                reason=reason,
                summary=summary,
                status=conversation.status.value,
            ),
            trace_id=trace.trace_id,
            prompt_id=trace.trace.prompt_id or "",
            prompt_version=trace.trace.prompt_version or "",
        )

    async def run(
        self,
        db: AsyncSession,
        *,
        conversation: Conversation,
        user_message: str,
        history: list[Message],
    ) -> AgentResult:
        prompt = prompt_registry.get("clevia-informational")
        context = get_request_context()
        trace = TraceRecorder(
            db,
            request_id=context.request_id,
            clinic_id=conversation.clinic_id,
            conversation_id=conversation.id,
            prompt_id=prompt.prompt_id,
            prompt_version=prompt.version,
        )

        if classify_risk(user_message) == "emergency":
            conversation.risk_level = "emergency"
            return await self._direct_handoff(
                db,
                conversation=conversation,
                history=history,
                user_message=user_message,
                intent=Intent.MEDICAL_SAFETY,
                reason="EMERGENCY_RISK",
                message=emergency_response(),
                trace=trace,
            )

        intent = route_intent(user_message)
        lead_flow_active = (
            conversation.agent_state == AgentState.COLLECTING.value
            or intent in {Intent.SERVICE_INTEREST, Intent.BOOKING_INTEREST}
        )
        if intent in {Intent.SERVICE_INTEREST, Intent.BOOKING_INTEREST}:
            conversation.agent_state = AgentState.COLLECTING.value
        if intent == Intent.GREETING:
            conversation.agent_state = AgentState.INFO.value
            await trace.finish(
                intent=intent.value,
                state=AgentState.INFO.value,
                provider=None,
                model=None,
                input_tokens=None,
                output_tokens=None,
                outcome="static_response",
            )
            return AgentResult(
                message="Hai, ada yang bisa saya bantu hari ini?",
                state=AgentState.INFO,
                intent=intent.value,
                trace_id=trace.trace_id,
                prompt_id=prompt.prompt_id,
                prompt_version=prompt.version,
            )

        if intent == Intent.HUMAN_HANDOFF:
            return await self._direct_handoff(
                db,
                conversation=conversation,
                history=history,
                user_message=user_message,
                intent=intent,
                reason="USER_REQUESTED_HUMAN",
                message=HUMAN_HANDOFF_MESSAGE,
                trace=trace,
            )

        if intent == Intent.MEDICAL_SAFETY:
            return await self._direct_handoff(
                db,
                conversation=conversation,
                history=history,
                user_message=user_message,
                intent=intent,
                reason="PERSONALIZED_MEDICAL_SUITABILITY",
                message=MEDICAL_HANDOFF_MESSAGE,
                trace=trace,
            )

        input_items: list = [
            {
                "role": "assistant" if message.role == "assistant" else "user",
                "content": message.content,
            }
            for message in history[-12:]
        ]
        input_items.append({"role": "user", "content": user_message})

        sources: list[SourceReference] = []
        tool_trace: list[dict] = []
        handoff: HandoffResult | None = None
        input_tokens = 0
        output_tokens = 0
        provider: str | None = None
        model: str | None = None

        try:
            for _ in range(settings.MAX_AGENT_STEPS):
                turn = await self.llm.respond(
                    instructions=prompt.template,
                    input_items=input_items,
                    tools=TOOL_SCHEMAS,
                )
                provider = turn.provider
                model = turn.model
                input_tokens += turn.input_tokens or 0
                output_tokens += turn.output_tokens or 0
                input_items += turn.continuation_items

                if not turn.function_calls:
                    unique_sources: dict[str, SourceReference] = {
                        item.source_ref: item for item in sources
                    }
                    sources = list(unique_sources.values())
                    if requires_grounded_source(intent) and not sources and handoff is None and not lead_flow_active:
                        reply = MISSING_EVIDENCE_MESSAGE
                        outcome = "missing_evidence"
                    else:
                        reply = turn.text or MISSING_EVIDENCE_MESSAGE
                        outcome = "answered" if sources else "completed"

                    if handoff is not None:
                        conversation.agent_state = AgentState.HANDOFF.value
                    elif lead_flow_active and conversation.lead_id is None:
                        conversation.agent_state = AgentState.COLLECTING.value
                    else:
                        conversation.agent_state = AgentState.INFO.value
                    await trace.finish(
                        intent=intent.value,
                        state=conversation.agent_state,
                        provider=provider,
                        model=model,
                        input_tokens=input_tokens or None,
                        output_tokens=output_tokens or None,
                        outcome=outcome,
                    )
                    return AgentResult(
                        message=reply,
                        state=AgentState(conversation.agent_state),
                        intent=intent.value,
                        sources=sources,
                        tools_used=tool_trace,
                        handoff=handoff,
                        trace_id=trace.trace_id,
                        prompt_id=prompt.prompt_id,
                        prompt_version=prompt.version,
                    )

                for function_call in turn.function_calls:
                    try:
                        arguments = json.loads(function_call.arguments_json)
                    except json.JSONDecodeError:
                        arguments = {}
                    started = time.perf_counter()
                    status = "success"
                    try:
                        result = await execute_tool(
                            db,
                            clinic_id=conversation.clinic_id,
                            conversation=conversation,
                            name=function_call.name,
                            arguments=arguments,
                        )
                    except Exception as exc:
                        status = "error"
                        result = {
                            "error": "TOOL_EXECUTION_FAILED",
                            "message": str(exc)[:500],
                        }
                    latency_ms = int((time.perf_counter() - started) * 1000)
                    tool_trace.append(
                        {
                            "name": function_call.name,
                            "arguments": arguments,
                            "result": result,
                            "status": status,
                        }
                    )
                    refs = source_refs_from_tool_result(result)
                    trace.add_retrieval_refs(refs)
                    sources.extend(self._source_objects(result))
                    await trace.record_tool(
                        tool_name=function_call.name,
                        input_json=arguments,
                        output_json=result,
                        status=status,
                        latency_ms=latency_ms,
                        clinic_id=conversation.clinic_id,
                        conversation_id=conversation.id,
                    )
                    if function_call.name == "request_human_handoff" and status == "success":
                        handoff = HandoffResult(
                            reason=result["reason"],
                            summary=result["summary"],
                            status=result["status"],
                        )
                    input_items.append(
                        {
                            "type": "function_call_output",
                            "call_id": function_call.call_id,
                            "output": json.dumps(result, ensure_ascii=False, default=str),
                        }
                    )

            await trace.finish(
                intent=intent.value,
                state=conversation.agent_state,
                provider=provider,
                model=model,
                input_tokens=input_tokens or None,
                output_tokens=output_tokens or None,
                outcome="error",
                error_code="MAX_AGENT_STEPS",
            )
            raise RuntimeError("Agent exceeded MAX_AGENT_STEPS")
        except Exception as exc:
            if trace.trace.outcome == "running":
                await trace.finish(
                    intent=intent.value,
                    state=conversation.agent_state,
                    provider=provider,
                    model=model,
                    input_tokens=input_tokens or None,
                    output_tokens=output_tokens or None,
                    outcome="error",
                    error_code=type(exc).__name__,
                )
            raise
