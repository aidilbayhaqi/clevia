from google.genai import types

from app.llm.gemini_adapter import GeminiGenerateContentAdapter


def _schema_dict():
    return {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
            }
        },
        "additionalProperties": False,
    }


def test_google_genai_function_declaration_accepts_parameters_field():
    declaration = types.FunctionDeclaration(
        name="list_services",
        description="List services",
        parameters=_schema_dict(),
    )

    assert declaration.parameters is not None


def test_gemini_adapter_build_tools_serializes_parameters_not_parameters_json_schema():
    built = GeminiGenerateContentAdapter._build_tools(
        [
            {
                "type": "function",
                "name": "list_services",
                "description": "List services",
                "parameters": _schema_dict(),
            }
        ],
        types,
    )

    assert len(built) == 1
    assert built[0].function_declarations
    declaration = built[0].function_declarations[0]

    payload = declaration.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=True,
    )

    assert "parameters" in payload
    assert "parameters_json_schema" not in payload
