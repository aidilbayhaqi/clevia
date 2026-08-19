from app.llm.prompt_registry import prompt_registry


def test_prompt_is_versioned_and_current():
    prompt = prompt_registry.get("clevia-informational")

    assert prompt.prompt_id == "clevia-informational"
    assert prompt.version == "2.2.0"

    for required_section in (
        "PRIMARY GOAL",
        "GROUNDING",
        "TOOL ROUTING",
        "LEAD BEHAVIOR",
        "HANDOFF",
        "MEDICAL BOUNDARY",
        "TOOL DISCIPLINE",
    ):
        assert required_section in prompt.template
