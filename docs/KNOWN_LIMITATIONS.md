# CleVIA v0.3.0 — Known Limitations

This release is the Sprint 0 + Sprint 1 engineering baseline, not the final production release.

1. `DEFAULT_CLINIC_SLUG` is a transitional tenant resolver. Subdomain/domain-based multi-clinic routing is reserved for the later scale phase.
2. Vector embeddings are opt-in (`KNOWLEDGE_EMBEDDINGS_ENABLED=false` by default). Without embeddings, retrieval uses approved tenant-filtered keyword candidates and may miss semantic synonyms.
3. The baseline eval suite is deterministic and intentionally small. It is a CI foundation, not evidence that production quality thresholds have already been reached.
4. Cost calculation is not populated yet in `AgentTrace`; token counts and latency are recorded where the provider returns usage.
5. Human handoff supports web CRM takeover/reply/release/resolve. External channel delivery (for example WhatsApp) is not implemented by this release.
6. Autonomous appointment/lead write tools are disabled for the agent. Website appointment requests remain supported by the existing public flow.
7. Existing legacy repository artifacts may still appear as Git deletions after installer cleanup if they were previously committed; review `git status` before committing the update.
8. Database rollback is intentionally manual. The supplied rollback script restores code/files but does not run an Alembic downgrade automatically to avoid accidental loss of new trace/feedback data.
