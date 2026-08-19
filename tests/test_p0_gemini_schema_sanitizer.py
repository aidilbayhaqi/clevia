from __future__ import annotations

from typing import Any

from google.genai import types

from app.llm.gemini_adapter import GeminiGenerateContentAdapter
from app.tools.registry import TOOL_SCHEMAS

FORBIDDEN_KEYS = {"additionalProperties", "additional_properties"}


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def test_schema_sanitizer_removes_additional_properties_recursively() -> None:
    original = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "payload": {
                "type": "object",
                "additional_properties": False,
                "properties": {"name": {"type": "string"}},
            }
        },
    }

    cleaned = GeminiGenerateContentAdapter._sanitize_schema_for_gemini(original)

    for node in _walk(cleaned):
        assert not (FORBIDDEN_KEYS & set(node))


def test_build_tools_has_no_forbidden_schema_keys_for_real_clevia_tools() -> None:
    built = GeminiGenerateContentAdapter._build_tools(TOOL_SCHEMAS, types)

    assert built
    declarations = built[0].function_declarations
    assert declarations

    for declaration in declarations:
        payload = declaration.model_dump(mode="json", by_alias=True, exclude_none=True)
        for node in _walk(payload):
            assert not (FORBIDDEN_KEYS & set(node))
