from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.llm.gemini_provider import (
    DEFAULT_GEMINI_MODEL,
    GeminiProviderConfig,
    GeminiProviderError,
)


def test_config_from_env_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("GEMINI_MAX_OUTPUT_TOKENS", raising=False)

    config = GeminiProviderConfig.from_env()

    assert config.api_key == "test-key"
    assert config.model == DEFAULT_GEMINI_MODEL
    assert config.timeout_seconds == 30.0
    assert config.max_output_tokens == 2048


def test_config_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(GeminiProviderError, match="GEMINI_API_KEY"):
        GeminiProviderConfig.from_env()


def test_config_validates_numeric_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_TIMEOUT_SECONDS", "invalid")

    with pytest.raises(GeminiProviderError, match="GEMINI_TIMEOUT_SECONDS"):
        GeminiProviderConfig.from_env()
