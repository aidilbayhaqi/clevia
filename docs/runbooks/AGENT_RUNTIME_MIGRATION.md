# Runbook — Migrasi Canonical Agent Runtime

## Target

Semua production flow menggunakan `app/agent`. Folder `app/agents` hanya boleh bersifat legacy sementara sampai seluruh dependency aktif dipindahkan dan diuji.

## Jangan lakukan

- Jangan menghapus `app/agents` hanya karena tidak terlihat dipakai pada satu file.
- Jangan mass replace import tanpa unit/integration test.
- Jangan mengubah orchestrator dan provider sekaligus bila failure source belum dapat dibedakan.
- Jangan memindahkan policy/tenant/tool permission ke prompt.

## Flow migrasi

1. Jalankan audit:

```powershell
python scripts\audit_agent_runtime.py `
  --write-baseline `
  --report-md docs\audits\agent-runtime-audit-v0.6.1.md `
  --report-json docs\audits\agent-runtime-audit-v0.6.1.json
```

2. Baca `external_legacy_imports`.
3. Pilih satu consumer legacy.
4. Pastikan contract/module canonical equivalent tersedia.
5. Migrasikan import + behavior.
6. Jalankan unit/integration/eval terkait.
7. Regenerate baseline setelah import legacy berhasil dikurangi.
8. Ulangi sampai baseline kosong.
9. Cari dynamic/string reference `app.agents`.
10. Jalankan smoke/E2E critical chat flow.
11. Baru hapus/deactivate legacy directory.

## Gate sebelum legacy deletion

- [ ] `external_legacy_import_count == 0`
- [ ] `canonical_imports_legacy_count == 0`
- [ ] tidak ada dynamic reference aktif ke `app.agents`
- [ ] unit test lulus
- [ ] integration test lulus
- [ ] agent eval lulus
- [ ] chat smoke test lulus
- [ ] rollback path tersedia

## Hasil patch v0.6.1

Patch ini sengaja berhenti pada audit + guard. Wiring Gemini/provider factory dilakukan setelah hasil audit menunjukkan entrypoint canonical yang sebenarnya.
