# ADR-014 — Gemini sebagai Provider LLM Tambahan

**Status:** Diterima untuk foundation P0  
**Patch:** `clevia-p0-gemini-provider-v0.6.0`  
**Tanggal:** 12 Agustus 2026

## Konteks

Clevia membutuhkan abstraction layer agar agent runtime tidak terkunci ke satu vendor/model. Produk tetap menempatkan LLM sebagai provider, bukan business logic. Business rule, tenant isolation, knowledge approval, tool permission, confirmation, dan audit tetap ditegakkan oleh service/policy Clevia.

## Keputusan

1. Tambahkan provider Gemini yang terisolasi pada `app/llm/gemini_provider.py`.
2. Gunakan official `google-genai` SDK.
3. Default model provider Gemini adalah stable `gemini-3.6-flash`.
4. Gunakan API v1.
5. API key hanya dibaca dari `GEMINI_API_KEY` dan tidak ditulis ke source/trace.
6. Patch ini **tidak otomatis mengganti provider runtime yang sedang aktif**. Wiring runtime dilakukan secara eksplisit setelah contract provider existing tervalidasi.
7. Jangan memindahkan business rule Clevia ke prompt/model provider.

## Konsekuensi

- Clevia mempunyai fondasi provider Gemini yang dapat diuji secara independen.
- Model/provider dapat diganti tanpa mengubah CRM/knowledge/tool domain.
- Diperlukan patch lanjutan untuk menyatukan provider selection dengan canonical orchestrator setelah active runtime contract selesai diaudit.

## Guardrail

- Jangan commit `GEMINI_API_KEY`.
- Jangan log raw credential.
- Provider error dinormalisasi agar secret tidak bocor dalam exception message.
- Sampling parameter `temperature`, `top_p`, dan `top_k` tidak dipakai pada default Gemini 3.6 path.
