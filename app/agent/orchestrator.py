from __future__ import annotations

import json
import re
import time
from datetime import UTC, datetime

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
from app.llm.errors import LLMInvalidResponseError
from app.llm.prompt_registry import prompt_registry
from app.llm.provider import get_llm_adapter
from app.observability.redaction import redact_for_trace
from app.observability.tracing import TraceRecorder, source_refs_from_tool_result
from app.services.booking_flow import (
    apply_service_to_draft,
    clinic_today,
    format_confirmation,
    format_slot_options,
    is_booking_cancel,
    is_confirmation,
    is_rejection,
    parse_slot_choice,
    parse_target_date,
    serialize_slots,
    start_booking_draft,
)
from app.services.lead_capture import (
    ensure_lead_collection_question,
    extract_lead_name,
    extract_lead_phone,
    lead_capture_opt_out,
    lead_interest_text,
    next_lead_question,
)
from app.services.safety import classify_risk, emergency_response
from app.tools.registry import TOOL_SCHEMAS, execute_tool

READ_ONLY_TOOL_NAMES = frozenset(
    {
        "get_clinic_profile",
        "list_services",
        "search_services",
        "search_knowledge",
        "get_availability",
    }
)


def read_tool_cache_key(name: str, arguments: dict) -> str | None:
    if name not in READ_ONLY_TOOL_NAMES:
        return None
    serialized = json.dumps(
        arguments,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return f"{name}:{serialized}"


PROFILE_FIELD_PATTERNS = {
    "address": re.compile(r"\b(alamat|lokasi|address)\b|di\s*mana\s+klinik|dimana\s+klinik", re.I),
    "instagram": re.compile(r"\b(instagram|ig)\b", re.I),
    "phone": re.compile(
        r"\b(telepon|telp|telephone|phone|whatsapp|wa)\b|nomor\s+(wa|telepon|telp)",
        re.I,
    ),
    "email": re.compile(r"\b(email|e-mail)\b", re.I),
    "profile": re.compile(r"\b(profil|profile)\b", re.I),
    "contact": re.compile(r"\b(kontak|contact)\b", re.I),
}


def requested_profile_fields(message: str) -> tuple[str, ...]:
    text = " ".join(message.strip().split())
    fields: list[str] = []

    if PROFILE_FIELD_PATTERNS["profile"].search(text):
        return ("name", "tagline", "address", "phone", "email", "instagram")

    for field in ("address", "instagram", "phone", "email"):
        if PROFILE_FIELD_PATTERNS[field].search(text):
            fields.append(field)

    if PROFILE_FIELD_PATTERNS["contact"].search(text):
        for field in ("phone", "email"):
            if field not in fields:
                fields.append(field)

    return tuple(fields)


def render_profile_reply(profile: dict, fields: tuple[str, ...]) -> str:
    if not fields:
        return MISSING_EVIDENCE_MESSAGE

    labels = {
        "name": "Nama",
        "tagline": "Tagline",
        "address": "Alamat",
        "phone": "Telepon/WhatsApp",
        "email": "Email",
        "instagram": "Instagram",
    }

    parts: list[str] = []
    for field in fields:
        value = profile.get(field)
        if value:
            parts.append(f"{labels[field]}: {value}")

    if not parts:
        return MISSING_EVIDENCE_MESSAGE

    return ". ".join(parts) + "."


class CleviaAgent:
    def __init__(self) -> None:
        self.llm = get_llm_adapter()

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
        conversation.handoff_at = datetime.now(UTC)
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

    async def _direct_profile_info(
        self,
        db: AsyncSession,
        *,
        conversation: Conversation,
        intent: Intent,
        fields: tuple[str, ...],
        trace: TraceRecorder,
        prompt_id: str,
        prompt_version: str,
    ) -> AgentResult:
        started = time.perf_counter()
        status = "success"
        error_code: str | None = None

        try:
            result = await execute_tool(
                db,
                clinic_id=conversation.clinic_id,
                conversation=conversation,
                name="get_clinic_profile",
                arguments={},
            )
        except Exception as exc:
            status = "error"
            error_code = type(exc).__name__
            result = {
                "error": "TOOL_EXECUTION_FAILED",
                "message": "Clinic profile lookup failed.",
            }

        latency_ms = int((time.perf_counter() - started) * 1000)
        tool_entry = {
            "name": "get_clinic_profile",
            "arguments": {},
            "result": redact_for_trace(result),
            "status": status,
        }

        await trace.record_tool(
            tool_name="get_clinic_profile",
            input_json={},
            output_json=result,
            status=status,
            latency_ms=latency_ms,
            clinic_id=conversation.clinic_id,
            conversation_id=conversation.id,
            error_code=error_code,
        )

        if status == "success":
            refs = source_refs_from_tool_result(result)
            trace.add_retrieval_refs(refs)
            sources = self._source_objects(result)
            reply = render_profile_reply(result, fields)
            outcome = "answered"
        else:
            sources = []
            reply = MISSING_EVIDENCE_MESSAGE
            outcome = "missing_evidence"

        conversation.agent_state = AgentState.INFO.value
        await trace.finish(
            intent=intent.value,
            state=AgentState.INFO.value,
            provider=None,
            model=None,
            input_tokens=None,
            output_tokens=None,
            outcome=outcome,
            error_code=error_code,
        )

        return AgentResult(
            message=reply,
            state=AgentState.INFO,
            intent=intent.value,
            sources=sources,
            tools_used=[tool_entry],
            trace_id=trace.trace_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
        )

    async def _direct_lead_collection(
        self,
        db: AsyncSession,
        *,
        conversation: Conversation,
        history: list[Message],
        user_message: str,
        intent: Intent,
        trace: TraceRecorder,
        prompt_id: str,
        prompt_version: str,
    ) -> AgentResult:
        if lead_capture_opt_out(user_message):
            conversation.agent_state = AgentState.INFO.value
            await trace.finish(
                intent=intent.value,
                state=AgentState.INFO.value,
                provider=None,
                model=None,
                input_tokens=None,
                output_tokens=None,
                outcome="lead_opt_out",
            )
            return AgentResult(
                message=(
                    "Oke, tidak masalah. Kita lanjut tanpa menyimpan kontak kamu. "
                    "Ada informasi lain yang ingin ditanyakan?"
                ),
                state=AgentState.INFO,
                intent=intent.value,
                trace_id=trace.trace_id,
                prompt_id=prompt_id,
                prompt_version=prompt_version,
            )

        full_name = extract_lead_name(history, user_message)
        phone = extract_lead_phone(history, user_message)
        missing_field, question = next_lead_question(
            full_name=full_name,
            phone=phone,
        )

        if missing_field:
            conversation.agent_state = AgentState.COLLECTING.value
            await trace.finish(
                intent=intent.value,
                state=AgentState.COLLECTING.value,
                provider=None,
                model=None,
                input_tokens=None,
                output_tokens=None,
                outcome="collecting_lead",
            )
            return AgentResult(
                message=question or "Boleh lanjutkan detail kontaknya?",
                state=AgentState.COLLECTING,
                intent=intent.value,
                trace_id=trace.trace_id,
                prompt_id=prompt_id,
                prompt_version=prompt_version,
            )

        arguments = {
            "full_name": full_name,
            "phone": phone,
            "email": None,
            "interest": lead_interest_text(history, user_message),
            "notes": None,
        }

        started = time.perf_counter()
        status = "success"
        error_code: str | None = None
        try:
            result = await execute_tool(
                db,
                clinic_id=conversation.clinic_id,
                conversation=conversation,
                name="capture_lead",
                arguments=arguments,
            )
        except Exception as exc:
            status = "error"
            error_code = type(exc).__name__
            result = {
                "error": "TOOL_EXECUTION_FAILED",
                "message": "Lead capture failed.",
            }

        latency_ms = int((time.perf_counter() - started) * 1000)
        await trace.record_tool(
            tool_name="capture_lead",
            input_json=arguments,
            output_json=result,
            status=status,
            latency_ms=latency_ms,
            clinic_id=conversation.clinic_id,
            conversation_id=conversation.id,
            error_code=error_code,
        )

        tool_entry = {
            "name": "capture_lead",
            "arguments": redact_for_trace(arguments),
            "result": redact_for_trace(result),
            "status": status,
        }

        if status != "success" or result.get("status") != "captured":
            conversation.agent_state = AgentState.COLLECTING.value
            await trace.finish(
                intent=intent.value,
                state=AgentState.COLLECTING.value,
                provider=None,
                model=None,
                input_tokens=None,
                output_tokens=None,
                outcome="lead_capture_error",
                error_code=error_code or "LEAD_CAPTURE_FAILED",
            )
            return AgentResult(
                message=(
                    "Kontaknya belum berhasil saya simpan. "
                    "Boleh kirim ulang nomor WhatsApp yang aktif?"
                ),
                state=AgentState.COLLECTING,
                intent=intent.value,
                tools_used=[tool_entry],
                trace_id=trace.trace_id,
                prompt_id=prompt_id,
                prompt_version=prompt_version,
            )

        conversation.agent_state = AgentState.INFO.value
        first_name = (full_name or "").split()[0] if full_name else ""
        await trace.finish(
            intent=intent.value,
            state=AgentState.INFO.value,
            provider=None,
            model=None,
            input_tokens=None,
            output_tokens=None,
            outcome="lead_captured",
        )
        return AgentResult(
            message=(
                f"Makasih, {first_name}. Data kontak kamu sudah saya catat. "
                "Kalau kamu ingin lanjut pilih jadwal, ketik 'mau booking'."
            ).strip(),
            state=AgentState.INFO,
            intent=intent.value,
            tools_used=[tool_entry],
            trace_id=trace.trace_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
        )

    async def _record_direct_tool(
        self,
        db: AsyncSession,
        *,
        conversation: Conversation,
        trace: TraceRecorder,
        name: str,
        arguments: dict,
    ) -> tuple[dict, dict]:
        started = time.perf_counter()
        status = "success"
        error_code: str | None = None

        try:
            result = await execute_tool(
                db,
                clinic_id=conversation.clinic_id,
                conversation=conversation,
                name=name,
                arguments=arguments,
            )
        except Exception as exc:
            status = "error"
            error_code = type(exc).__name__
            result = {
                "error": error_code,
                "message": str(exc),
            }

        latency_ms = int((time.perf_counter() - started) * 1000)
        await trace.record_tool(
            tool_name=name,
            input_json=arguments,
            output_json=result,
            status=status,
            latency_ms=latency_ms,
            clinic_id=conversation.clinic_id,
            conversation_id=conversation.id,
            error_code=error_code,
        )

        entry = {
            "name": name,
            "arguments": redact_for_trace(arguments),
            "result": redact_for_trace(result),
            "status": status,
        }
        return result, entry

    async def _direct_booking_flow(
        self,
        db: AsyncSession,
        *,
        conversation: Conversation,
        user_message: str,
        trace: TraceRecorder,
        prompt_id: str,
        prompt_version: str,
    ) -> AgentResult:
        intent = Intent.BOOKING_INTEREST
        tools_used: list[dict] = []

        if not settings.AGENT_TRANSACTIONAL_TOOLS_ENABLED:
            conversation.booking_draft = {}
            conversation.agent_state = AgentState.INFO.value
            await trace.finish(
                intent=intent.value,
                state=AgentState.INFO.value,
                provider=None,
                model=None,
                input_tokens=None,
                output_tokens=None,
                outcome="transactional_tools_disabled",
            )
            return AgentResult(
                message=(
                    "Booking lewat AI belum diaktifkan. Kamu tetap bisa memakai halaman booking "
                    "website atau minta bantuan tim Clevia."
                ),
                state=AgentState.INFO,
                intent=intent.value,
                trace_id=trace.trace_id,
                prompt_id=prompt_id,
                prompt_version=prompt_version,
            )

        if is_booking_cancel(user_message):
            conversation.booking_draft = {}
            conversation.agent_state = AgentState.INFO.value
            await trace.finish(
                intent=intent.value,
                state=AgentState.INFO.value,
                provider=None,
                model=None,
                input_tokens=None,
                output_tokens=None,
                outcome="booking_cancelled",
            )
            return AgentResult(
                message="Oke, proses booking dibatalkan. Tidak ada appointment yang dibuat.",
                state=AgentState.INFO,
                intent=intent.value,
                trace_id=trace.trace_id,
                prompt_id=prompt_id,
                prompt_version=prompt_version,
            )

        draft = dict(conversation.booking_draft or {})

        if not draft:
            if conversation.lead_id is None:
                conversation.agent_state = AgentState.COLLECTING.value
                await trace.finish(
                    intent=intent.value,
                    state=AgentState.COLLECTING.value,
                    provider=None,
                    model=None,
                    input_tokens=None,
                    output_tokens=None,
                    outcome="booking_requires_lead",
                )
                return AgentResult(
                    message=(
                        "Sebelum lanjut booking, saya perlu mencatat nama dan nomor WhatsApp kamu dulu."
                    ),
                    state=AgentState.COLLECTING,
                    intent=intent.value,
                    trace_id=trace.trace_id,
                    prompt_id=prompt_id,
                    prompt_version=prompt_version,
                )

            draft = await start_booking_draft(
                db,
                clinic_id=conversation.clinic_id,
                lead_id=conversation.lead_id,
                user_message=user_message,
            )
            conversation.booking_draft = draft

        step = draft.get("step")

        if step == "lead_missing":
            conversation.booking_draft = {}
            conversation.agent_state = AgentState.COLLECTING.value
            await trace.finish(
                intent=intent.value,
                state=AgentState.COLLECTING.value,
                provider=None,
                model=None,
                input_tokens=None,
                output_tokens=None,
                outcome="booking_lead_missing",
            )
            return AgentResult(
                message="Data lead tidak ditemukan. Boleh kirim ulang nama dan nomor WhatsApp kamu?",
                state=AgentState.COLLECTING,
                intent=intent.value,
                trace_id=trace.trace_id,
                prompt_id=prompt_id,
                prompt_version=prompt_version,
            )

        if step == "service":
            updated = await apply_service_to_draft(
                db,
                clinic_id=conversation.clinic_id,
                draft=draft,
                user_message=user_message,
            )
            if updated is None:
                conversation.agent_state = AgentState.COLLECTING.value
                await trace.finish(
                    intent=intent.value,
                    state=AgentState.COLLECTING.value,
                    provider=None,
                    model=None,
                    input_tokens=None,
                    output_tokens=None,
                    outcome="booking_collect_service",
                )
                return AgentResult(
                    message=(
                        "Treatment apa yang ingin kamu booking? "
                        "Contoh: Glow Facial Signature."
                    ),
                    state=AgentState.COLLECTING,
                    intent=intent.value,
                    trace_id=trace.trace_id,
                    prompt_id=prompt_id,
                    prompt_version=prompt_version,
                )
            draft = updated
            conversation.booking_draft = draft
            step = "date"

        if step == "date":
            today = await clinic_today(
                db,
                clinic_id=conversation.clinic_id,
            )
            target_date = parse_target_date(user_message, today=today)

            # On the first booking turn, service can be resolved but the user has
            # not necessarily supplied a date yet.
            if target_date is None:
                conversation.agent_state = AgentState.COLLECTING.value
                await trace.finish(
                    intent=intent.value,
                    state=AgentState.COLLECTING.value,
                    provider=None,
                    model=None,
                    input_tokens=None,
                    output_tokens=None,
                    outcome="booking_collect_date",
                )
                return AgentResult(
                    message=(
                        f"Oke, {draft['service_name']}. Tanggal berapa kamu ingin datang? "
                        "Kamu bisa tulis BESOK atau tanggal seperti 21/08/2026."
                    ),
                    state=AgentState.COLLECTING,
                    intent=intent.value,
                    trace_id=trace.trace_id,
                    prompt_id=prompt_id,
                    prompt_version=prompt_version,
                )

            if target_date < today:
                conversation.agent_state = AgentState.COLLECTING.value
                await trace.finish(
                    intent=intent.value,
                    state=AgentState.COLLECTING.value,
                    provider=None,
                    model=None,
                    input_tokens=None,
                    output_tokens=None,
                    outcome="booking_past_date",
                )
                return AgentResult(
                    message="Tanggal itu sudah lewat. Pilih tanggal hari ini atau setelahnya.",
                    state=AgentState.COLLECTING,
                    intent=intent.value,
                    trace_id=trace.trace_id,
                    prompt_id=prompt_id,
                    prompt_version=prompt_version,
                )

            arguments = {
                "service_id": draft["service_id"],
                "target_date": target_date.isoformat(),
                "staff_id": None,
            }
            availability, tool_entry = await self._record_direct_tool(
                db,
                conversation=conversation,
                trace=trace,
                name="get_availability",
                arguments=arguments,
            )
            tools_used.append(tool_entry)

            if tool_entry["status"] != "success":
                conversation.agent_state = AgentState.COLLECTING.value
                await trace.finish(
                    intent=intent.value,
                    state=AgentState.COLLECTING.value,
                    provider=None,
                    model=None,
                    input_tokens=None,
                    output_tokens=None,
                    outcome="availability_error",
                    error_code="AVAILABILITY_FAILED",
                )
                return AgentResult(
                    message="Jadwal belum bisa dicek sekarang. Coba pilih tanggal lain atau hubungi tim Clevia.",
                    state=AgentState.COLLECTING,
                    intent=intent.value,
                    tools_used=tools_used,
                    trace_id=trace.trace_id,
                    prompt_id=prompt_id,
                    prompt_version=prompt_version,
                )

            slots = serialize_slots(availability.get("slots", []))
            if not slots:
                draft["target_date"] = target_date.isoformat()
                conversation.booking_draft = draft
                conversation.agent_state = AgentState.COLLECTING.value
                await trace.finish(
                    intent=intent.value,
                    state=AgentState.COLLECTING.value,
                    provider=None,
                    model=None,
                    input_tokens=None,
                    output_tokens=None,
                    outcome="no_availability",
                )
                return AgentResult(
                    message=(
                        f"Belum ada slot tersedia untuk {target_date:%d/%m/%Y}. "
                        "Coba pilih tanggal lain."
                    ),
                    state=AgentState.COLLECTING,
                    intent=intent.value,
                    tools_used=tools_used,
                    trace_id=trace.trace_id,
                    prompt_id=prompt_id,
                    prompt_version=prompt_version,
                )

            draft.update(
                {
                    "step": "slot",
                    "target_date": target_date.isoformat(),
                    "slots": slots,
                }
            )
            conversation.booking_draft = draft
            conversation.agent_state = AgentState.COLLECTING.value
            await trace.finish(
                intent=intent.value,
                state=AgentState.COLLECTING.value,
                provider=None,
                model=None,
                input_tokens=None,
                output_tokens=None,
                outcome="booking_choose_slot",
            )
            return AgentResult(
                message=(
                    "Slot yang tersedia:\n"
                    f"{format_slot_options(slots)}\n"
                    "Balas nomor 1-5 untuk memilih jadwal."
                ),
                state=AgentState.COLLECTING,
                intent=intent.value,
                tools_used=tools_used,
                trace_id=trace.trace_id,
                prompt_id=prompt_id,
                prompt_version=prompt_version,
            )

        if step == "slot":
            slots = draft.get("slots") or []
            choice = parse_slot_choice(user_message, len(slots))
            if choice is None:
                conversation.agent_state = AgentState.COLLECTING.value
                await trace.finish(
                    intent=intent.value,
                    state=AgentState.COLLECTING.value,
                    provider=None,
                    model=None,
                    input_tokens=None,
                    output_tokens=None,
                    outcome="booking_invalid_slot",
                )
                return AgentResult(
                    message=(
                        "Pilih salah satu nomor slot yang tersedia, misalnya 1."
                    ),
                    state=AgentState.COLLECTING,
                    intent=intent.value,
                    trace_id=trace.trace_id,
                    prompt_id=prompt_id,
                    prompt_version=prompt_version,
                )

            draft.update(
                {
                    "step": "confirm",
                    "selected_slot": slots[choice],
                }
            )
            conversation.booking_draft = draft
            conversation.agent_state = AgentState.CONFIRMING.value
            await trace.finish(
                intent=intent.value,
                state=AgentState.CONFIRMING.value,
                provider=None,
                model=None,
                input_tokens=None,
                output_tokens=None,
                outcome="booking_confirmation_required",
            )
            return AgentResult(
                message=format_confirmation(draft),
                state=AgentState.CONFIRMING,
                intent=intent.value,
                trace_id=trace.trace_id,
                prompt_id=prompt_id,
                prompt_version=prompt_version,
            )

        if step == "confirm":
            if is_rejection(user_message):
                conversation.booking_draft = {}
                conversation.agent_state = AgentState.INFO.value
                await trace.finish(
                    intent=intent.value,
                    state=AgentState.INFO.value,
                    provider=None,
                    model=None,
                    input_tokens=None,
                    output_tokens=None,
                    outcome="booking_rejected",
                )
                return AgentResult(
                    message="Oke, appointment tidak dibuat. Proses booking dibatalkan.",
                    state=AgentState.INFO,
                    intent=intent.value,
                    trace_id=trace.trace_id,
                    prompt_id=prompt_id,
                    prompt_version=prompt_version,
                )

            if not is_confirmation(user_message):
                conversation.agent_state = AgentState.CONFIRMING.value
                await trace.finish(
                    intent=intent.value,
                    state=AgentState.CONFIRMING.value,
                    provider=None,
                    model=None,
                    input_tokens=None,
                    output_tokens=None,
                    outcome="booking_confirmation_ambiguous",
                )
                return AgentResult(
                    message=(
                        f"{format_confirmation(draft)}"
                    ),
                    state=AgentState.CONFIRMING,
                    intent=intent.value,
                    trace_id=trace.trace_id,
                    prompt_id=prompt_id,
                    prompt_version=prompt_version,
                )

            selected = draft["selected_slot"]
            arguments = {
                "service_id": draft["service_id"],
                "staff_id": selected["staff_id"],
                "starts_at": selected["starts_at"],
                "customer_note": None,
            }
            result, tool_entry = await self._record_direct_tool(
                db,
                conversation=conversation,
                trace=trace,
                name="create_appointment_request",
                arguments=arguments,
            )
            tools_used.append(tool_entry)

            if tool_entry["status"] != "success":
                draft["step"] = "date"
                draft.pop("slots", None)
                draft.pop("selected_slot", None)
                conversation.booking_draft = draft
                conversation.agent_state = AgentState.COLLECTING.value
                await trace.finish(
                    intent=intent.value,
                    state=AgentState.COLLECTING.value,
                    provider=None,
                    model=None,
                    input_tokens=None,
                    output_tokens=None,
                    outcome="booking_write_failed",
                    error_code="APPOINTMENT_WRITE_FAILED",
                )
                return AgentResult(
                    message=(
                        "Slot tersebut tidak berhasil dibooking atau sudah berubah. "
                        "Pilih tanggal lagi supaya saya cek ketersediaan terbaru."
                    ),
                    state=AgentState.COLLECTING,
                    intent=intent.value,
                    tools_used=tools_used,
                    trace_id=trace.trace_id,
                    prompt_id=prompt_id,
                    prompt_version=prompt_version,
                )

            conversation.agent_state = AgentState.INFO.value
            await trace.finish(
                intent=intent.value,
                state=AgentState.INFO.value,
                provider=None,
                model=None,
                input_tokens=None,
                output_tokens=None,
                outcome="appointment_requested",
            )
            return AgentResult(
                message=(
                    "Appointment request berhasil dibuat. Statusnya REQUESTED dan masih perlu "
                    "dikonfirmasi oleh tim Clevia. ID appointment: "
                    f"{result['appointment_id']}."
                ),
                state=AgentState.INFO,
                intent=intent.value,
                tools_used=tools_used,
                trace_id=trace.trace_id,
                prompt_id=prompt_id,
                prompt_version=prompt_version,
            )

        conversation.booking_draft = {}
        conversation.agent_state = AgentState.INFO.value
        await trace.finish(
            intent=intent.value,
            state=AgentState.INFO.value,
            provider=None,
            model=None,
            input_tokens=None,
            output_tokens=None,
            outcome="booking_draft_reset",
        )
        return AgentResult(
            message="Draft booking tidak valid dan sudah direset. Ketik 'mau booking' untuk mulai lagi.",
            state=AgentState.INFO,
            intent=intent.value,
            trace_id=trace.trace_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
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
        booking_active = bool(conversation.booking_draft)
        was_collecting_lead = (
            conversation.agent_state == AgentState.COLLECTING.value
            and conversation.lead_id is None
            and not booking_active
        )
        lead_flow_active = (
            was_collecting_lead
            or intent in {Intent.SERVICE_INTEREST, Intent.BOOKING_INTEREST}
        )
        if intent == Intent.SERVICE_INTEREST:
            conversation.agent_state = AgentState.COLLECTING.value
        elif intent == Intent.BOOKING_INTEREST and conversation.lead_id is None:
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

        profile_fields = requested_profile_fields(user_message)
        if intent == Intent.INFORMATION and profile_fields:
            return await self._direct_profile_info(
                db,
                conversation=conversation,
                intent=intent,
                fields=profile_fields,
                trace=trace,
                prompt_id=prompt.prompt_id,
                prompt_version=prompt.version,
            )

        if was_collecting_lead:
            return await self._direct_lead_collection(
                db,
                conversation=conversation,
                history=history,
                user_message=user_message,
                intent=intent,
                trace=trace,
                prompt_id=prompt.prompt_id,
                prompt_version=prompt.version,
            )

        if booking_active or (
            intent == Intent.BOOKING_INTEREST
            and conversation.lead_id is not None
        ):
            return await self._direct_booking_flow(
                db,
                conversation=conversation,
                user_message=user_message,
                trace=trace,
                prompt_id=prompt.prompt_id,
                prompt_version=prompt.version,
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
        read_tool_cache: dict[str, dict] = {}

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
                    if (
                        requires_grounded_source(intent)
                        and not sources
                        and handoff is None
                        and not lead_flow_active
                    ):
                        reply = MISSING_EVIDENCE_MESSAGE
                        outcome = "missing_evidence"
                    else:
                        reply = turn.text or MISSING_EVIDENCE_MESSAGE
                        outcome = "answered" if sources else "completed"

                    if lead_flow_active and conversation.lead_id is None:
                        full_name = extract_lead_name(history, user_message)
                        phone = extract_lead_phone(history, user_message)
                        missing_field, _ = next_lead_question(
                            full_name=full_name,
                            phone=phone,
                        )
                        reply = ensure_lead_collection_question(
                            reply,
                            missing_field,
                        )
                        outcome = "collecting_lead"

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
                    tool_error_code: str | None = None
                    cache_key = read_tool_cache_key(function_call.name, arguments)

                    if cache_key is not None and cache_key in read_tool_cache:
                        result = read_tool_cache[cache_key]
                        status = "cached"
                    else:
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
                            tool_error_code = type(exc).__name__
                            result = {
                                "error": "TOOL_EXECUTION_FAILED",
                                "message": "Tool execution failed. Use fallback or handoff.",
                            }

                        if cache_key is not None and status == "success":
                            read_tool_cache[cache_key] = result

                    latency_ms = int((time.perf_counter() - started) * 1000)
                    tool_trace.append(
                        {
                            "name": function_call.name,
                            "arguments": redact_for_trace(arguments),
                            "result": redact_for_trace(result),
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
                        error_code=tool_error_code,
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
            raise LLMInvalidResponseError("Agent exceeded MAX_AGENT_STEPS")
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
