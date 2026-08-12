from __future__ import annotations

import json
from typing import Any

from google import genai
from google.genai import types

from app.core.config import settings
from app.llm.base import LLMFunctionCall, LLMTurn


class GeminiGenerateContentAdapter:
    """
    Gemini adapter for Clevia P0.

    Clevia keeps conversation and tool state locally. For that reason this
    adapter uses the fully supported generateContent API with manual function
    calling instead of delegating CRM tool execution to the SDK.
    """

    provider = "gemini"

    def __init__(self) -> None:
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. Set it in .env and restart the API container."
            )

        if self._client is None:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

        return self._client

    @staticmethod
    def _call_name(call_id: str) -> str:
        prefix = "gemini::"
        if call_id.startswith(prefix):
            parts = call_id.split("::", 2)
            if len(parts) == 3 and parts[2]:
                return parts[2]
        return call_id

    @staticmethod
    def _parse_tool_output(raw_output: Any) -> dict[str, Any]:
        if isinstance(raw_output, dict):
            return raw_output

        if isinstance(raw_output, str):
            try:
                decoded = json.loads(raw_output)
            except json.JSONDecodeError:
                return {"result": raw_output}

            if isinstance(decoded, dict):
                return decoded
            return {"result": decoded}

        return {"result": raw_output}

    @classmethod
    def _to_contents(cls, input_items: list[Any]) -> list[types.Content]:
        contents: list[types.Content] = []

        for item in input_items:
            if isinstance(item, types.Content):
                contents.append(item)
                continue

            if not isinstance(item, dict):
                continue

            if item.get("_clevia_provider") == "gemini" and item.get("kind") == "model_content":
                raw_content = item.get("content")
                if isinstance(raw_content, dict):
                    contents.append(types.Content.model_validate(raw_content))
                continue

            item_type = item.get("type")
            if item_type == "function_call_output":
                call_id = str(item.get("call_id") or "")
                function_name = cls._call_name(call_id)
                response_payload = cls._parse_tool_output(item.get("output"))

                contents.append(
                    types.Content(
                        role="tool",
                        parts=[
                            types.Part.from_function_response(
                                name=function_name,
                                response=response_payload,
                            )
                        ],
                    )
                )
                continue

            role = item.get("role")
            if role in {"user", "assistant", "model"}:
                content = item.get("content")
                if not isinstance(content, str) or not content.strip():
                    continue

                gemini_role = "model" if role in {"assistant", "model"} else "user"
                contents.append(
                    types.Content(
                        role=gemini_role,
                        parts=[types.Part.from_text(text=content)],
                    )
                )

        return contents

    @staticmethod
    def _to_tool(tools: list[dict]) -> types.Tool | None:
        declarations: list[types.FunctionDeclaration] = []

        for tool in tools:
            if not isinstance(tool, dict):
                continue
            if tool.get("type") != "function":
                continue

            name = tool.get("name")
            parameters = tool.get("parameters")
            if not isinstance(name, str) or not name:
                continue
            if not isinstance(parameters, dict):
                parameters = {"type": "object", "properties": {}}

            declarations.append(
                types.FunctionDeclaration(
                    name=name,
                    description=str(tool.get("description") or ""),
                    parameters_json_schema=parameters,
                )
            )

        if not declarations:
            return None

        return types.Tool(function_declarations=declarations)

    async def respond(
        self,
        *,
        instructions: str,
        input_items: list[Any],
        tools: list[dict],
    ) -> LLMTurn:
        client = self._get_client()
        contents = self._to_contents(input_items)
        gemini_tool = self._to_tool(tools)

        config_kwargs: dict[str, Any] = {
            "system_instruction": instructions,
            "temperature": settings.GEMINI_TEMPERATURE,
            "automatic_function_calling": types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        }

        if gemini_tool is not None:
            config_kwargs["tools"] = [gemini_tool]

        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(**config_kwargs),
        )

        raw_calls = list(response.function_calls or [])
        function_calls: list[LLMFunctionCall] = []

        for index, call in enumerate(raw_calls):
            name = str(getattr(call, "name", "") or "")
            arguments = getattr(call, "args", None) or {}
            function_calls.append(
                LLMFunctionCall(
                    call_id=f"gemini::{index}::{name}",
                    name=name,
                    arguments_json=json.dumps(
                        arguments,
                        ensure_ascii=False,
                        default=str,
                    ),
                )
            )

        continuation_items: list[Any] = []
        candidates = list(getattr(response, "candidates", None) or [])
        if candidates:
            model_content = getattr(candidates[0], "content", None)
            if model_content is not None:
                continuation_items.append(
                    {
                        "_clevia_provider": "gemini",
                        "kind": "model_content",
                        "content": model_content.model_dump(
                            exclude_none=True,
                            mode="json",
                        ),
                    }
                )

        usage = getattr(response, "usage_metadata", None)

        return LLMTurn(
            text=getattr(response, "text", "") or "",
            function_calls=function_calls,
            continuation_items=continuation_items,
            input_tokens=getattr(usage, "prompt_token_count", None),
            output_tokens=getattr(usage, "candidates_token_count", None),
            provider=self.provider,
            model=settings.GEMINI_MODEL,
        )