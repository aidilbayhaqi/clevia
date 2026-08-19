# Changelog

## 0.7.0 - Sprint 1 Reliability Closure

- Consolidated the working Gemini GenerateContent tool-calling adapter.
- Added controlled LLM timeout/rate/provider error normalization.
- Added public system fallback for controlled LLM runtime failures.
- Removed eager agent construction from route import time.
- Normalized duplicate local environment keys and typed Gemini timeout configuration.
- Pinned `google-genai==2.18.1` to the verified working runtime.
- Added Sprint 1 regression and acceptance tooling.

All notable changes to CleVIA are documented here.

## [0.3.0] - 2026-08-11

### Added
- Request correlation ID and tenant-aware request context.
- Structured request logging and persistent `AgentTrace` / `ToolExecution` telemetry.
- LLM provider adapter and versioned prompt registry.
- Explicit informational-agent state and deterministic intent/safety routing.
- Knowledge metadata, approval lifecycle, semantic chunking, optional pgvector embeddings, and tenant/approval/validity-filtered retrieval.
- Source references in public chat responses.
- Human handoff reason/summary, transcript API, staff takeover/reply/release/resolve flow.
- Staff feedback labels: `good`, `wrong`, and `missing_knowledge`.
- Baseline offline golden-set evaluation and GitHub CI workflow.
- Development/staging configuration split and production frontend container.
- Architecture Decision Records for the Sprint 0 foundation.

### Changed
- Informational agent tools are now separated from the legacy agent package.
- Public clinic resolution uses `DEFAULT_CLINIC_SLUG` instead of selecting the first active clinic.
- Frontend demo mode defaults to disabled.
- Legacy knowledge `publish` remains as a deprecated alias for the new approval flow.

### Safety / Scope
- Autonomous agent transactional tools remain disabled by default.
- Existing website appointment-request flow remains available and is not treated as an autonomous agent action.
- CleVIA remains a customer-engagement/operations product, not an EMR/EHR or diagnostic system.

### Migration
- Alembic revision `20260811_0002` upgrades legacy published knowledge to approved knowledge and adds Sprint 0/1 trace, chunk, handoff, and feedback schema.
