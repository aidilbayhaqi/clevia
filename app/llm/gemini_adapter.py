"""Gemini adapters for Clevia.

Canonical runtime:
    GeminiGenerateContentAdapter.respond()

Provider boundary rules:
- canonical Clevia tool schemas remain provider-neutral/strict;
- Gemini declarations use `parameters`;
- unsupported schema keys are removed only for Gemini;
- model Content is preserved for continuation/thought-signature integrity;
- function responses are returned as USER content for the current Gemini runtime;
- native FunctionCall IDs are preserved when the installed SDK exposes
  FunctionResponse.id;
- parallel function results are grouped into a single user Content turn.

This module intentionally avoids relying on the convenience helper
`Part.from_function_response(..., id=...)` because some google-genai 2.x builds
expose FunctionResponse.id while the helper itself does not accept an `id`
keyword.
"""
from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from typing import Any
from urllib.parse import quote, unquote

from app.core.config import settings
from app.llm.base import LLMFunctionCall, LLMTurn
from app.llm.errors import (
    LLMNotConfiguredError,
    LLMProviderError,
    LLMRateLimitedError,
    LLMTimeoutError,
)
from app.llm.gemini_provider import GeminiProvider, GeminiProviderConfig
from app.llm.provider_contract import LLMResponse


def _gemini_config_from_settings() -> GeminiProviderConfig:
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key:
        raise LLMNotConfiguredError(
            "Gemini provider is not configured. Set GEMINI_API_KEY and restart the API."
        )

    return GeminiProviderConfig(
        api_key=api_key,
        model=settings.GEMINI_MODEL,
        timeout_seconds=settings.GEMINI_TIMEOUT_SECONDS,
        max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
    )


class GeminiLLMAdapter:
    """Compatibility adapter for the secondary text-only provider contract."""

    provider_name = "gemini"

    def __init__(self, provider: GeminiProvider) -> None:
        self._provider = provider

    @classmethod
    def from_env(cls) -> "GeminiLLMAdapter":
        return cls(GeminiProvider(_gemini_config_from_settings()))

    @property
    def model(self) -> str:
        return self._provider.config.model

    async def complete(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        max_output_tokens: int | None = None,
    ) -> LLMResponse:
        result = await self._provider.generate_text(
            prompt,
            system_instruction=system_instruction,
            max_output_tokens=max_output_tokens,
        )
        return LLMResponse(
            text=result.text,
            provider=result.provider,
            model=result.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            total_tokens=result.total_tokens,
            finish_reason=result.finish_reason,
        )

    async def close(self) -> None:
        await self._provider.aclose()


class GeminiGenerateContentAdapter:
    provider = "gemini"

    def __init__(self) -> None:
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client

        config = _gemini_config_from_settings()

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError(
                "google-genai dependency is not installed. Install project dependencies first."
            ) from exc

        self._client = genai.Client(
            api_key=config.api_key,
            http_options=types.HttpOptions(
                api_version="v1",
                timeout=int(config.timeout_seconds * 1000),
            ),
        )
        return self._client

    @staticmethod
    def _encode_call_id(
        *,
        index: int,
        name: str,
        native_id: str | None,
    ) -> str:
        if native_id:
            token = "id-" + quote(str(native_id), safe="")
        else:
            token = f"idx-{index}"
        return f"gemini::{token}::{quote(name, safe='')}"

    @staticmethod
    def _call_name(call_id: str) -> str:
        if not isinstance(call_id, str):
            return str(call_id)

        parts = call_id.split("::", 2)
        if len(parts) == 3 and parts[0] == "gemini" and parts[2]:
            return unquote(parts[2])
        return call_id

    @staticmethod
    def _native_call_id(call_id: str) -> str | None:
        if not isinstance(call_id, str):
            return None

        parts = call_id.split("::", 2)
        if len(parts) != 3 or parts[0] != "gemini":
            return None

        token = parts[1]
        if token.startswith("id-"):
            return unquote(token[3:]) or None
        return None

    @staticmethod
    def _parse_tool_output(output: Any) -> dict[str, Any]:
        if isinstance(output, dict):
            return output
        if output is None:
            return {"result": None}
        if not isinstance(output, str):
            return {"result": output}

        try:
            parsed = json.loads(output)
        except json.JSONDecodeError:
            return {"result": output}

        return parsed if isinstance(parsed, dict) else {"result": parsed}

    @staticmethod
    def _usage_value(usage: Any, *names: str) -> int | None:
        if usage is None:
            return None

        for name in names:
            value = getattr(usage, name, None)
            if isinstance(value, int):
                return value
        return None

    @staticmethod
    def _model_has_field(model_type: Any, field_name: str) -> bool:
        fields = getattr(model_type, "model_fields", None)
        if isinstance(fields, dict):
            return field_name in fields

        legacy_fields = getattr(model_type, "__fields__", None)
        return isinstance(legacy_fields, dict) and field_name in legacy_fields

    @classmethod
    def _function_response_part(cls, item: dict[str, Any], types: Any) -> Any:
        """Build a FunctionResponse without depending on helper signature drift."""
        call_id = str(item.get("call_id") or "")

        response_kwargs: dict[str, Any] = {
            "name": cls._call_name(call_id),
            "response": cls._parse_tool_output(item.get("output")),
        }

        native_id = cls._native_call_id(call_id)
        if (
            native_id is not None
            and cls._model_has_field(types.FunctionResponse, "id")
        ):
            response_kwargs["id"] = native_id

        function_response = types.FunctionResponse(**response_kwargs)
        return types.Part(function_response=function_response)

    @classmethod
    def _to_content(cls, item: Any, types: Any) -> Any:
        try:
            if isinstance(item, types.Content):
                # Preserve Gemini model content verbatim, including thought signatures.
                return item
        except TypeError:
            pass

        if not isinstance(item, dict):
            return types.Content(
                role="user",
                parts=[types.Part.from_text(text=str(item))],
            )

        role = str(item.get("role") or "user").lower()
        gemini_role = "model" if role in {"assistant", "model"} else "user"

        return types.Content(
            role=gemini_role,
            parts=[
                types.Part.from_text(
                    text="" if item.get("content") is None else str(item.get("content"))
                )
            ],
        )

    @classmethod
    def _to_contents(cls, input_items: list[Any], types: Any) -> list[Any]:
        """Group consecutive function outputs into one USER turn."""
        contents: list[Any] = []
        pending_function_parts: list[Any] = []

        def flush_function_parts() -> None:
            if not pending_function_parts:
                return
            contents.append(
                types.Content(
                    role="user",
                    parts=list(pending_function_parts),
                )
            )
            pending_function_parts.clear()

        for item in input_items:
            if isinstance(item, dict) and item.get("type") == "function_call_output":
                pending_function_parts.append(cls._function_response_part(item, types))
                continue

            flush_function_parts()
            contents.append(cls._to_content(item, types))

        flush_function_parts()
        return contents

    @staticmethod
    def _sanitize_schema_for_gemini(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: GeminiGenerateContentAdapter._sanitize_schema_for_gemini(child)
                for key, child in value.items()
                if key not in {"additionalProperties", "additional_properties"}
            }
        if isinstance(value, list):
            return [
                GeminiGenerateContentAdapter._sanitize_schema_for_gemini(child)
                for child in value
            ]
        return value

    @staticmethod
    def _build_tools(tools: list[dict], types: Any) -> list[Any]:
        declarations: list[Any] = []

        for tool in tools:
            if not isinstance(tool, dict) or tool.get("type") != "function":
                continue

            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue

            parameters = tool.get("parameters")
            if not isinstance(parameters, dict):
                parameters = {"type": "object", "properties": {}}

            parameters = GeminiGenerateContentAdapter._sanitize_schema_for_gemini(
                parameters
            )

            declarations.append(
                types.FunctionDeclaration(
                    name=name,
                    description=tool.get("description") or "",
                    parameters=parameters,
                )
            )

        return [types.Tool(function_declarations=declarations)] if declarations else []


    @staticmethod
    def _normalize_provider_exception(exc: Exception) -> Exception:
        status_code = getattr(exc, "status_code", None)
        if status_code is None:
            status_code = getattr(exc, "code", None)
        try:
            status_code = int(status_code) if status_code is not None else None
        except (TypeError, ValueError):
            status_code = None

        if isinstance(exc, (TimeoutError, asyncio.TimeoutError)) or status_code in {408, 504}:
            return LLMTimeoutError("The LLM provider timed out.")
        if status_code == 429:
            return LLMRateLimitedError("The LLM provider rate limit was reached.")
        return LLMProviderError("The LLM provider request failed.")

    async def respond(
        self,
        *,
        instructions: str,
        input_items: list[Any],
        tools: list[dict],
    ) -> LLMTurn:
        client = self._get_client()

        try:
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError(
                "google-genai dependency is not installed. Install project dependencies first."
            ) from exc

        contents = self._to_contents(input_items, types)
        gemini_tools = self._build_tools(tools, types)

        config_kwargs: dict[str, Any] = {
            "system_instruction": instructions or None,
            "max_output_tokens": int(
                settings.GEMINI_MAX_OUTPUT_TOKENS
            ),
        }
        if gemini_tools:
            config_kwargs["tools"] = gemini_tools

        try:
            response = await client.aio.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(**config_kwargs),
            )
        except Exception as exc:
            normalized = self._normalize_provider_exception(exc)
            raise normalized from exc

        response_calls = list(getattr(response, "function_calls", None) or [])
        calls: list[LLMFunctionCall] = []

        for index, call in enumerate(response_calls):
            name = getattr(call, "name", None)
            if not isinstance(name, str) or not name:
                continue

            raw_args = getattr(call, "args", None) or {}
            if isinstance(raw_args, Mapping):
                raw_args = dict(raw_args)

            native_id = getattr(call, "id", None)
            if native_id is not None:
                native_id = str(native_id)

            calls.append(
                LLMFunctionCall(
                    call_id=self._encode_call_id(
                        index=index,
                        name=name,
                        native_id=native_id,
                    ),
                    name=name,
                    arguments_json=json.dumps(
                        raw_args,
                        ensure_ascii=False,
                        default=str,
                    ),
                )
            )

        continuation_items: list[Any] = []
        candidates = getattr(response, "candidates", None) or []
        if candidates:
            candidate_content = getattr(candidates[0], "content", None)
            if candidate_content is not None:
                continuation_items.append(candidate_content)

        usage = getattr(response, "usage_metadata", None)

        text = ""
        if not calls:
            text = (getattr(response, "text", None) or "").strip()

        return LLMTurn(
            text=text,
            function_calls=calls,
            continuation_items=continuation_items,
            input_tokens=self._usage_value(
                usage, "prompt_token_count", "input_token_count"
            ),
            output_tokens=self._usage_value(
                usage, "candidates_token_count", "output_token_count"
            ),
            provider=self.provider,
            model=settings.GEMINI_MODEL,
        )

    async def aclose(self) -> None:
        if self._client is None:
            return

        try:
            await self._client.aio.aclose()
        finally:
            self._client.close()
            self._client = None
