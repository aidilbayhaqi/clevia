from __future__ import annotations

from google.genai import types

from app.llm.gemini_adapter import GeminiGenerateContentAdapter


def test_native_call_id_round_trip() -> None:
    encoded = GeminiGenerateContentAdapter._encode_call_id(
        index=0,
        name="list_services",
        native_id="call-123",
    )
    assert GeminiGenerateContentAdapter._call_name(encoded) == "list_services"
    assert GeminiGenerateContentAdapter._native_call_id(encoded) == "call-123"


def test_function_response_part_does_not_depend_on_helper_id_signature() -> None:
    call_id = GeminiGenerateContentAdapter._encode_call_id(
        index=0,
        name="list_services",
        native_id="call-123",
    )

    part = GeminiGenerateContentAdapter._function_response_part(
        {
            "type": "function_call_output",
            "call_id": call_id,
            "output": '{"services":[]}',
        },
        types,
    )

    response = part.function_response
    assert response is not None
    assert response.name == "list_services"
    assert response.response == {"services": []}

    if GeminiGenerateContentAdapter._model_has_field(types.FunctionResponse, "id"):
        assert response.id == "call-123"


def test_function_response_turn_uses_user_role() -> None:
    call_id = GeminiGenerateContentAdapter._encode_call_id(
        index=0,
        name="list_services",
        native_id="call-123",
    )

    contents = GeminiGenerateContentAdapter._to_contents(
        [
            {
                "type": "function_call_output",
                "call_id": call_id,
                "output": '{"services":[]}',
            }
        ],
        types,
    )

    assert len(contents) == 1
    assert contents[0].role == "user"
    assert len(contents[0].parts) == 1


def test_parallel_function_responses_are_one_user_content() -> None:
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
