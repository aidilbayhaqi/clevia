# ADR-009 — P0 Release Hardening

Status: Accepted  
Date: 2026-08-15

## Decision

- Production knowledge retrieval remains `clinic_id + APPROVED + validity window`.
- Tool observability data is redacted before persistent storage.
- Raw tool exception text is not exposed through tool traces; exception class is kept as `error_code`.
- Tenant isolation is a data/service-layer contract, never a prompt-only rule.
- Applied Alembic migration history is not rewritten destructively in this P0 patch.
- A forward migration is used for P0 schema additions.
- Frozen migration baseline work is separated until deployed-environment inventory and restore rehearsal are complete.

## Reason

The repository already contains an historical dynamic initial migration. Rewriting an already-applied
revision can create a higher operational risk than a forward-only P0 hardening patch.

## Follow-up

Before production scale:
1. inventory Alembic revision in every environment;
2. test backup/restore;
3. generate and review a frozen baseline;
4. rehearse upgrade in staging;
5. only then adopt/squash the baseline.
