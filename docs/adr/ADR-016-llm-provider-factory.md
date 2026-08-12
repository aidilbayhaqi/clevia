# ADR-016 — Kontrak dan Factory Provider LLM

**Status:** Accepted  
**Patch:** `clevia-p0-llm-provider-factory-v0.6.2`

## Konteks

Clevia harus dapat mengganti provider/model tanpa memindahkan business rule ke SDK vendor. Provider Gemini v0.6.0 sudah tersedia, tetapi orchestrator belum boleh bergantung langsung pada implementasi `GeminiProvider`.

## Keputusan

1. `app/llm/provider_contract.py` menjadi kontrak vendor-neutral.
2. Setiap vendor diadaptasikan ke `LLMResponse` yang sama.
3. `app/llm/provider_factory.py` bertanggung jawab memilih provider dari konfigurasi.
4. Default factory adalah `gemini`, tetapi `.env` production tetap menjadi sumber konfigurasi deployment.
5. Factory tidak boleh menyimpan policy klinik, routing intent, tenant rule, CRM rule, atau retrieval rule.
6. Runtime orchestrator hanya boleh di-wire setelah titik pemanggilan LLM existing teridentifikasi dari audit, bukan melalui patch heuristik.

## Konsekuensi

- Pergantian provider menjadi configuration concern.
- Trace nantinya dapat merekam `provider` dan `model` dengan format konsisten.
- Provider baru dapat diregistrasikan tanpa memodifikasi orchestrator.
- Ada satu tahap migrasi eksplisit untuk mengganti call site LLM lama ke kontrak baru.
