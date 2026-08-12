# ADR-008 - Single-Business Deployment

Status: Accepted  
Version: Clevia P0 / v0.5.0

## Decision

One Clevia deployment serves exactly one business/client.

QLABS keeps one reusable Clevia codebase, but each client receives a separate runtime environment,
database, Redis instance/namespace, secrets, domain, knowledge set, users, and integration credentials.

Clevia P0 is **not** a shared multi-company tenant platform.

## Compatibility note

The current database still contains `clinic_id` on several tables because the existing v0.3.0 schema
was built around that key. During P0 it is treated only as an internal business-scope compatibility key.
The application must not expose arbitrary cross-company tenant selection.

Removing the key physically from every table is intentionally deferred to a dedicated cleanup migration,
because it is not required to prove the CRM + AI Agent prototype and would create unnecessary migration risk.

## Consequences

- Faster prototype delivery.
- Simpler security boundary.
- Easier client-specific deployment and rollback.
- No cross-company data sharing.
- Client customization must be configuration/knowledge driven, not source-code forks.