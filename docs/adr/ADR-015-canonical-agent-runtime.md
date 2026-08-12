# ADR-015 — Canonical Agent Runtime Clevia

**Status:** Diterima untuk Sprint C0  
**Patch:** `clevia-p0-canonical-agent-runtime-v0.6.1`  
**Tanggal:** 12 Agustus 2026

## Konteks

Repository Clevia pernah memiliki `app/agent/` dan `app/agents/` secara bersamaan. Dua jalur runtime menciptakan risiko developer memodifikasi orchestrator yang bukan jalur production, regression sulit dilacak, dan provider/tool/trace dapat terpasang pada boundary yang salah.

## Keputusan

1. `app/agent/` ditetapkan sebagai **canonical agent runtime**.
2. `app/agents/` diperlakukan sebagai legacy/deprecated apabila masih ada.
3. Legacy runtime **tidak dihapus otomatis** pada patch ini.
4. Semua consumer legacy dipetakan menggunakan AST audit.
5. Import legacy yang sudah ada dibaseline sebagai utang teknis terukur.
6. Import baru ke `app.agents` dilarang melalui architecture test.
7. `app/agent` tidak diperbolehkan bergantung kembali pada `app/agents`.
8. Penghapusan legacy hanya dilakukan setelah import, dynamic reference, integration test, smoke test, dan critical flow tervalidasi.

## Alasan

Hard-delete tanpa mengetahui dependency runtime dapat memutus route/chat flow secara diam-diam. Sebaliknya, membiarkan dua runtime tanpa guard akan memperbesar technical debt. Baseline + architecture guard memberikan jalur migrasi incremental yang aman.

## Konsekuensi

- Tim mempunyai satu target arsitektur yang eksplisit.
- Technical debt lama tetap dapat hidup sementara, tetapi tidak boleh bertambah.
- Report audit menjadi input patch runtime/provider wiring berikutnya.
- Penghapusan `app/agents` menjadi keputusan berbasis evidence, bukan asumsi.

## Follow-up

1. Migrasikan consumer legacy per module.
2. Wire LLM provider selection hanya ke canonical runtime.
3. Tambahkan tenant isolation + trace integration tests.
4. Hapus legacy runtime setelah seluruh gate lulus.
