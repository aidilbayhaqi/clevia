# Runbook — Wiring Provider LLM ke Canonical Agent Runtime

## Tujuan

Menghubungkan `app/agent/` dengan kontrak provider baru tanpa membuat orchestrator bergantung pada SDK Gemini.

## Gate sebelum wiring

- `app/agent/` sudah ditetapkan sebagai canonical runtime.
- `app/llm/gemini_provider.py` tersedia dari v0.6.0.
- Test `test_llm_provider_factory_v062.py` lulus di container API.
- `docs/audits/llm-runtime-wiring-v0.6.2.md` tersedia.
- Call site LLM existing telah diketahui.

## Bentuk target

```text
app/agent/orchestrator.py
        |
        v
LLMProvider (Protocol)
        |
        v
provider_factory
        |
        +--> GeminiLLMAdapter --> GeminiProvider --> google-genai
        |
        +--> provider lain di masa depan
```

## Aturan

- Orchestrator tidak mengimpor SDK vendor.
- API key tidak pernah masuk prompt atau trace.
- Trace menyimpan provider/model/usage, bukan secret.
- Timeout/retry berada di layer provider/adapter.
- Safety, tenant isolation, grounding, dan tool permission tetap berada di layer Clevia.
