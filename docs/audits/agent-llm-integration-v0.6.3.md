# Audit Integrasi Agent ↔ LLM Runtime v0.6.3

- Canonical orchestrator: `True`
- Agent LLM bridge: `True`
- LLM runtime: `True`
- File dipindai: `19`

## Titik integrasi yang ditemukan

### `app/agent/llm_bridge.py`

Import LLM:
- `app.llm.runtime.LLMRuntime`

Class: `AgentLLMBridge`, `AgentLLMResult`

- L1: `"""Bridge canonical dari Agent Clevia ke LLMRuntime.`
- L11: `from app.llm.runtime import LLMRuntime`
- L22: `def __init__(self, runtime: LLMRuntime | None = None) -> None:`
- L23: `self._runtime = runtime or LLMRuntime()`
- L33: `result = await self._runtime.complete(`
- L45: `def create_agent_llm_bridge() -> AgentLLMBridge:`

### `app/agent/orchestrator.py`

Import LLM:
- `app.llm.prompt_registry.prompt_registry`
- `app.llm.provider.get_llm_adapter`

Class: `CleviaAgent`


## Status wiring

Patch v0.6.3 memasang runtime bridge dan trace contract yang siap digunakan oleh orchestrator. Audit ini tetap read-only terhadap orchestrator agar perubahan business flow tidak dilakukan secara heuristik.

## Gate sebelum mengubah orchestrator

1. Identifikasi class/function entrypoint orchestrator aktif.
2. Identifikasi call site LLM lama dan bentuk return value-nya.
3. Ganti dependency ke `AgentLLMBridge` secara eksplisit.
4. Propagasikan `request_id`, `trace_id`, `clinic_id`, `conversation_id`, dan `prompt_version` ke `LLMCallContext`.
5. Jalankan unit + integration + agent eval sebelum menghapus provider path lama.
