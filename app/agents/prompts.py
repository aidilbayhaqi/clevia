"""Compatibility prompt export. New code should use app.llm.prompt_registry."""

from app.llm.prompt_registry import prompt_registry

SYSTEM_PROMPT = prompt_registry.get("clevia-informational").template
