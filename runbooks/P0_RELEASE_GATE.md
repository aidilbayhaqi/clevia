# Clevia P0 Release Gate

## Mandatory gate

```bash
ruff check app tests evals
pytest -q
alembic heads
alembic upgrade head
python -m evals.runner --offline
python -m evals.p0_release_gate
```

## Knowledge

- DRAFT: not production retrievable.
- APPROVED: retrievable when valid.
- ARCHIVED: not production retrievable.
- Every production retrieval must retain clinic isolation.

## Privacy

Inspect sample `tool_executions` rows. These must not contain raw:
- full name;
- phone;
- email;
- notes/message/summary;
- API key;
- authorization/access tokens.

Operational identifiers may remain, for example:
- clinic_id;
- conversation_id;
- lead_id;
- service_id;
- trace_id;
- status;
- latency.

## Migration

A release fails if:
- more than one Alembic head exists;
- `alembic upgrade head` fails;
- migration produces schema/model mismatch.

## Rollback

If a P0 gate fails before production:
1. stop release;
2. retain logs;
3. run `Rollback-Clevia-P0.ps1`;
4. if a non-ephemeral database was migrated, follow the database backup/restore policy;
5. create a regression test before retry.
