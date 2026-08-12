"""Factory provider LLM untuk Clevia.

Pemilihan provider berada di layer infrastructure/config, bukan di orchestrator.
Business logic cukup bergantung pada kontrak LLMProvider.
"""
from __future__ import annotations

import os
from collections.abc import Callable

from app.llm.gemini_adapter import GeminiLLMAdapter
from app.llm.provider_contract import LLMProvider


DEFAULT_LLM_PROVIDER = "gemini"


class LLMProviderFactoryError(RuntimeError):
    """Konfigurasi provider tidak valid atau provider belum diregistrasikan."""


ProviderBuilder = Callable[[], LLMProvider]
_REGISTRY: dict[str, ProviderBuilder] = {}
_ALIASES = {"google": "gemini", "google-gemini": "gemini"}


def normalize_provider_name(name: str | None) -> str:
    raw = (name or os.getenv("LLM_PROVIDER", DEFAULT_LLM_PROVIDER)).strip().lower()
    if not raw:
        raw = DEFAULT_LLM_PROVIDER
    return _ALIASES.get(raw, raw)


def register_llm_provider(
    name: str,
    builder: ProviderBuilder,
    *,
    replace: bool = False,
) -> None:
    normalized = normalize_provider_name(name)
    if normalized in _REGISTRY and not replace:
        raise LLMProviderFactoryError(f"Provider '{normalized}' sudah diregistrasikan.")
    _REGISTRY[normalized] = builder


def available_llm_providers() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))


def create_llm_provider(name: str | None = None) -> LLMProvider:
    normalized = normalize_provider_name(name)
    builder = _REGISTRY.get(normalized)
    if builder is None:
        available = ", ".join(available_llm_providers()) or "(kosong)"
        raise LLMProviderFactoryError(
            f"LLM provider '{normalized}' belum tersedia. Provider tersedia: {available}."
        )
    return builder()


def _build_gemini() -> LLMProvider:
    return GeminiLLMAdapter.from_env()


register_llm_provider("gemini", _build_gemini)
