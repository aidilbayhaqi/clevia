# Audit Canonical Agent Runtime — v0.6.1

Generated: `2026-08-12T08:02:25.755757+00:00`

## Keputusan arsitektur

- Runtime canonical: `app/agent`.
- `app/agents` diperlakukan sebagai legacy/deprecated apabila masih ada.
- Patch ini tidak menghapus legacy runtime secara otomatis.
- Import legacy baru diblokir melalui architecture test berbasis baseline.

## Ringkasan

- `app/agent` tersedia: **True**
- `app/agents` tersedia: **True**
- Import canonical ditemukan: **36**
- Import legacy ditemukan: **3**
- Import legacy dari luar folder legacy: **3**
- Import legacy dari dalam canonical runtime: **0**

## Status migrasi

Masih ada consumer yang mengimpor `app.agents`. Import tersebut dibaseline sebagai utang teknis dan **tidak dihapus otomatis**.

## Import legacy eksternal

| File | Baris | Module |
|---|---:|---|
| `.clevia-updates/backups/1.1.0-20260808-101742/app/agents/orchestrator.py` | 5 | `app.agents.prompts` |
| `.clevia-updates/backups/1.1.0-20260808-101742/app/agents/orchestrator.py` | 6 | `app.agents.tools.registry` |
| `.clevia-updates/backups/1.1.0-20260808-101742/app/api/v1/routes/conversations.py` | 7 | `app.agents.orchestrator` |

## Tindakan berikutnya

1. Review report ini.
2. Migrasikan consumer legacy satu per satu dengan test/eval evidence.
3. Jangan menambah import `app.agents` baru.
4. Setelah runtime canonical terbukti, lakukan provider factory/runtime wiring pada patch berikutnya.
5. Hapus `app/agents` hanya setelah runtime, integration test, dan smoke test membuktikan tidak ada dependency aktif.
