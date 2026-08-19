from app.llm.gemini_adapter import GeminiGenerateContentAdapter
from app.llm.provider import get_llm_adapter


def test_gemini_runtime_constructor_is_lazy() -> None:
    adapter = GeminiGenerateContentAdapter()
    assert callable(adapter.respond)


def test_provider_returns_respond_capable_adapter() -> None:
    adapter = get_llm_adapter()
    assert callable(adapter.respond)


def test_gemini_call_id_round_trip() -> None:
    assert (
        GeminiGenerateContentAdapter._call_name("gemini::2::search_knowledge")
        == "search_knowledge"
    )


def test_gemini_tool_output_json_parsing() -> None:
    assert GeminiGenerateContentAdapter._parse_tool_output('{"status":"ok"}') == {
        "status": "ok"
    }


def test_gemini_tool_output_text_fallback() -> None:
    assert GeminiGenerateContentAdapter._parse_tool_output("plain text") == {
        "result": "plain text"
    }
