# Canonical Agent Runtime

Folder `app/agent/` adalah runtime agent canonical Clevia berdasarkan ADR-015.

Aturan:

- orchestrator/router/policy/state baru harus ditempatkan pada boundary canonical ini;
- jangan menambahkan dependency baru ke `app.agents`;
- business rule, tenant isolation, tool permission, dan confirmation tetap deterministic;
- perubahan behavior AI harus disertai test/eval evidence;
- legacy `app/agents` dimigrasikan incremental dan tidak dihapus tanpa integration/smoke evidence.
