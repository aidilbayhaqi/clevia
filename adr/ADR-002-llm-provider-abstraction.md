# ADR-002 — LLM provider abstraction

Status: Accepted

The agent orchestrator depends on an LLM adapter contract. Provider-specific OpenAI Responses API code lives in `app/llm/openai_adapter.py`; business rules remain outside the provider adapter.
