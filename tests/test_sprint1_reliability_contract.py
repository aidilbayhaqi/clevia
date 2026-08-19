from __future__ import annotations

from pathlib import Path

from google.genai import types

from app.core.config import settings
from app.llm.errors import (
    LLMProviderError,
    LLMRateLimitedError,
    LLMTimeoutError,
)
from app.llm.gemini_adapter import GeminiGenerateContentAdapter
from app.llm.provider import get_llm_adapter
from app.tools.registry import TOOL_SCHEMAS


class _StatusError(Exception):
    def __init__(self, status_code: int):
        self.status_code = status_code


def test_gemini_is_canonical_agent_adapter(monkeypatch) -> None:
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    adapter = get_llm_adapter()
    assert isinstance(adapter, GeminiGenerateContentAdapter)


def test_gemini_timeout_and_rate_limit_are_normalized() -> None:
    assert isinstance(
        GeminiGenerateContentAdapter._normalize_provider_exception(_StatusError(504)),
        LLMTimeoutError,
    )
    assert isinstance(
        GeminiGenerateContentAdapter._normalize_provider_exception(_StatusError(429)),
        LLMRateLimitedError,
    )
    assert isinstance(
        GeminiGenerateContentAdapter._normalize_provider_exception(_StatusError(500)),
        LLMProviderError,
    )


def test_real_tool_schemas_are_gemini_safe() -> None:
    built = GeminiGenerateContentAdapter._build_tools(TOOL_SCHEMAS, types)
    assert built

    rendered = str(
        [
            declaration.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
            )
            for declaration in built[0].function_declarations
        ]
    )
    assert "additionalProperties" not in rendered
    assert "additional_properties" not in rendered


def test_function_outputs_are_grouped_into_user_turn() -> None:
    first = GeminiGenerateContentAdapter._encode_call_id(
        index=0, name="list_services", native_id="A"
    )
    second = GeminiGenerateContentAdapter._encode_call_id(
        index=1, name="search_knowledge", native_id="B"
    )

    contents = GeminiGenerateContentAdapter._to_contents(
        [
            {
                "type": "function_call_output",
                "call_id": first,
                "output": '{"services":[]}',
            },
            {
                "type": "function_call_output",
                "call_id": second,
                "output": '{"results":[]}',
            },
        ],
        types,
    )

    assert len(contents) == 1
    assert contents[0].role == "user"
    assert len(contents[0].parts) == 2


def test_public_conversation_route_has_no_eager_agent() -> None:
    source = Path("app/api/v1/routes/conversations.py").read_text(encoding="utf-8")
    assert "\nagent = CleviaAgent()\n" not in source
    assert "def get_agent()" in source


def test_public_route_has_controlled_system_fallback() -> None:
    source = Path("app/api/v1/routes/conversations.py").read_text(encoding="utf-8")
    assert "except LLMRuntimeError" in source
    assert 'intent="SYSTEM_FALLBACK"' in source
