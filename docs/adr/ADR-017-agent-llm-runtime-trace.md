# ADR-017 — Agent LLM Runtime dan Trace Boundary

## Status
Accepted untuk prototype Clevia v0.6.3.

## Konteks
Clevia telah memiliki provider contract dan provider factory. Tahap berikutnya membutuhkan boundary yang membuat Agent tidak berinteraksi langsung dengan SDK vendor sekaligus menghasilkan metadata observability yang konsisten.

## Keputusan
1. `app/llm/runtime.py` menjadi boundary eksekusi provider vendor-neutral.
2. `app/agent/llm_bridge.py` menjadi dependency yang boleh digunakan Agent/Orchestrator.
3. Trace LLM hanya menyimpan metadata operasional: provider, model, latency, token usage, outcome, correlation id, dan prompt version.
4. Prompt mentah dan system instruction tidak disimpan oleh trace layer ini.
5. Runtime tidak memiliki business rule CRM, retrieval, tenant authorization, atau tool permission.
6. Provider exception dipropagasikan sebagai `LLMRuntimeError`; failure tidak boleh silent.

## Konsekuensi
- Provider dapat diganti tanpa mengganti business logic Agent.
- Trace lebih mudah dikorelasikan end-to-end.
- Wiring orchestrator harus dilakukan eksplisit setelah call site lama diketahui; tidak menggunakan regex replacement yang spekulatif.
