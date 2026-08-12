# ADR-003 — pgvector

Status: Accepted

Use PostgreSQL + pgvector for the initial knowledge index to keep operational complexity low. Canonical knowledge remains relational source data; vectors are derived and rebuildable. Embeddings are opt-in in v0.3.0.
