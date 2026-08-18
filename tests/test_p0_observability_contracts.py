from app.db.models.observability import AgentTrace, ToolExecution


def test_agent_trace_release_fields_exist() -> None:
    for field in (
        "trace_id",
        "request_id",
        "clinic_id",
        "prompt_version",
        "provider",
        "model",
        "input_tokens",
        "output_tokens",
        "latency_ms",
        "cost",
        "outcome",
        "error_code",
    ):
        assert hasattr(AgentTrace, field)


def test_tool_execution_failure_fields_exist() -> None:
    for field in (
        "trace_id",
        "clinic_id",
        "conversation_id",
        "tool_name",
        "input_json",
        "output_json",
        "status",
        "idempotency_key",
        "latency_ms",
        "error_code",
    ):
        assert hasattr(ToolExecution, field)
