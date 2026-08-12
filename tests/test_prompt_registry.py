from app.llm.prompt_registry import prompt_registry


def test_prompt_is_versioned():
    prompt = prompt_registry.get("clevia-informational")
    assert prompt.prompt_id == "clevia-informational"
    assert prompt.version == "1.0.0"
    assert "INFORMATIONAL ONLY" in prompt.template
