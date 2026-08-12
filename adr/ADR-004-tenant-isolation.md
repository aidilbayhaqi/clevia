# ADR-004 — Tenant isolation

Status: Accepted

`clinic_id` is enforced in data/service queries. Public single-clinic routing resolves a configured `DEFAULT_CLINIC_SLUG`; admin routing derives the clinic from the authenticated user. Prompt instructions are not a tenant-isolation mechanism.
