"""Kontrak provider LLM canonical untuk Clevia.

Patch: clevia-p0-llm-provider-factory-v0.6.2

Modul ini sengaja tidak mengetahui business rule, CRM, knowledge base, tenant,
atau policy Clevia. Semua provider harus mengembalikan bentuk response yang sama
agar orchestrator tidak terikat langsung pada SDK vendor.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class LLMResponse:
    text: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    finish_reason: str | None = None


@runtime_checkable
class LLMProvider(Protocol):
    provider_name: str

    async def complete(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        max_output_tokens: int | None = None,
    ) -> LLMResponse:
        """Menghasilkan text completion dalam kontrak vendor-neutral."""
        ...

    async def close(self) -> None:
        """Menutup resource provider bila ada."""
        ...
