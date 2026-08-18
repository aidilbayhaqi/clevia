# Runbook — Wiring Agent ke LLM Runtime

## Target

```text
app/agent/orchestrator.py
        ↓
app/agent/llm_bridge.py
        ↓
app/llm/runtime.py
        ↓
app/llm/provider_factory.py
        ↓
Gemini / provider lain
```

## Trace minimum
Setiap call LLM harus membawa correlation metadata sejauh tersedia:
- `trace_id`
- `request_id`
- `clinic_id`
- `conversation_id`
- `prompt_version`

Trace LLM mencatat provider/model/token/latency/outcome tanpa menyimpan prompt mentah.

## Gate wiring orchestrator
Jangan mengganti call site lama sebelum:
1. Audit `docs/audits/agent-llm-integration-v0.6.3.md` ditinjau.
2. Signature call lama dipahami.
3. Return contract downstream diketahui.
4. Unit/integration test tersedia.
5. Rollback path tersedia.

## Failure policy
- Provider timeout/error → runtime melempar `LLMRuntimeError`.
- Orchestrator menentukan fallback/handoff sesuai policy capability.
- Runtime tidak boleh mengubah error menjadi jawaban sukses palsu.
