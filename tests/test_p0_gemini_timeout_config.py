from app.core.config import Settings


def test_gemini_timeout_is_typed_and_configurable(monkeypatch):
    monkeypatch.setenv("GEMINI_TIMEOUT_SECONDS", "120")
    settings = Settings(_env_file=None)
    assert settings.GEMINI_TIMEOUT_SECONDS == 120.0


def test_gemini_max_output_tokens_is_typed_and_configurable(monkeypatch):
    monkeypatch.setenv("GEMINI_MAX_OUTPUT_TOKENS", "2048")
    settings = Settings(_env_file=None)
    assert settings.GEMINI_MAX_OUTPUT_TOKENS == 2048
