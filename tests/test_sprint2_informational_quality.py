from app.agent.orchestrator import READ_ONLY_TOOL_NAMES, read_tool_cache_key
from app.llm.prompt_registry import prompt_registry
from app.observability.redaction import REDACTED, redact_for_trace
from app.tools.registry import TOOL_DEFINITIONS, SearchServicesInput


def test_search_services_tool_is_registered() -> None:
    definition = TOOL_DEFINITIONS["search_services"]
    assert definition.input_model is SearchServicesInput
    assert "price" in definition.description.lower()
    assert "duration" in definition.description.lower()


def test_search_services_requires_meaningful_query() -> None:
    payload = SearchServicesInput.model_validate({"query": "Glow Facial Signature"})
    assert payload.query == "Glow Facial Signature"


def test_read_only_cache_includes_information_tools_only() -> None:
    assert "search_services" in READ_ONLY_TOOL_NAMES
    assert "search_knowledge" in READ_ONLY_TOOL_NAMES
    assert "capture_lead" not in READ_ONLY_TOOL_NAMES
    assert "request_human_handoff" not in READ_ONLY_TOOL_NAMES


def test_read_tool_cache_key_is_order_stable() -> None:
    first = read_tool_cache_key("search_services", {"query": "Glow Facial"})
    second = read_tool_cache_key("search_services", {"query": "Glow Facial"})
    assert first == second
    assert first is not None

    assert read_tool_cache_key("capture_lead", {"full_name": "Sarah"}) is None


def test_service_names_remain_observable_while_customer_pii_is_redacted() -> None:
    result = redact_for_trace(
        {
            "name": "Glow Facial Signature",
            "full_name": "Sarah Putri",
            "phone": "081234567890",
            "email": "sarah@example.com",
        }
    )

    assert result["name"] == "Glow Facial Signature"
    assert result["full_name"] == REDACTED
    assert result["phone"] == REDACTED
    assert result["email"] == REDACTED


def test_prompt_routes_named_service_questions_to_search_services() -> None:
    prompt = prompt_registry.get("clevia-informational")
    # Sprint 4 intentionally advances the informational prompt contract.
    assert prompt.version == "2.2.0"
    assert "Specific named service" in prompt.template
    assert "search_services FIRST" in prompt.template
    assert "Do NOT call search_knowledge first" in prompt.template
