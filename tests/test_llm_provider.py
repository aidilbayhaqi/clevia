from app.core.config import settings
from app.llm.gemini_adapter import GeminiGenerateContentAdapter


def test_gemini_tool_call_id_round_trip():
    call_id = "gemini::0::capture_lead"
    assert GeminiGenerateContentAdapter._call_name(call_id) == "capture_lead"


def test_gemini_plain_call_name_fallback():
    assert GeminiGenerateContentAdapter._call_name("search_knowledge") == "search_knowledge"


def test_tool_output_json_parsing():
    assert GeminiGenerateContentAdapter._parse_tool_output('{"status":"ok"}') == {
        "status": "ok"
    }


def test_tool_output_text_fallback():
    assert GeminiGenerateContentAdapter._parse_tool_output("plain text") == {
        "result": "plain text"
    }


def test_provider_config_has_active_model():
    assert isinstance(settings.active_llm_model, str)
    assert settings.active_llm_model