from __future__ import annotations

from app.core.config import Settings


def test_sprint1_version_and_gemini_runtime_defaults(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("GEMINI_MAX_OUTPUT_TOKENS", raising=False)

    settings = Settings(_env_file=None)

    assert settings.APP_VERSION == "0.7.0"
    assert settings.GEMINI_TIMEOUT_SECONDS == 120.0
    assert settings.GEMINI_MAX_OUTPUT_TOKENS == 2048


def test_timeout_is_overridable(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_TIMEOUT_SECONDS", "180")
    settings = Settings(_env_file=None)
    assert settings.GEMINI_TIMEOUT_SECONDS == 180.0
