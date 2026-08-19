# Changelog

## 1.0.0 - Sprint 4 Appointment Agent

- Added persistent booking drafts with COLLECTING -> CONFIRMING -> EXECUTING/INFO flow.
- Added deterministic availability lookup and numbered slot selection.
- Added explicit confirmation gate before any AI appointment write.
- Added idempotent appointment request creation for exact lead/service/staff/start combinations.
- AI-created appointments start as REQUESTED and lead status becomes BOOKED.
- Added safe cancellation and stale-slot recovery.
- Added tenant-safe admin appointment status transitions and audit events.
- Added Alembic migration 20260819_0004 for conversation booking_draft.

## 0.9.0 - Sprint 3 Lead & CRM Reliability

- Added deterministic lead contact collection after genuine service/booking intent.
- Added phone normalization and same-clinic lead deduplication by phone.
- Added deterministic service-interest resolution for captured chatbot leads.
- Added respectful lead-capture opt-out handling.
- Hardened CRM lead updates against cross-clinic assignee/service references.
- Added lead filtering/pagination and editable CRM lead contact fields.
- Added deterministic integration tests without requiring a live LLM call.

## 0.8.1 - Sprint 2 Clinic Profile Routing Hotfix

- Added deterministic routing for public clinic profile fields such as address, Instagram, phone, email, and contact details.
- Profile questions now use `get_clinic_profile` directly instead of relying on probabilistic LLM tool selection.
- Added deterministic profile routing tests and HTTP acceptance coverage.

## 0.8.0 - Sprint 2 Informational AI Quality

- Added precise `search_services` lookup for named service questions.
- Added prompt-level tool routing for service catalogue, clinic profile, and knowledge FAQ requests.
- Added per-agent-run caching for identical read-only tool calls.
- Improved source precision for named service answers.
- Kept service/business names visible in traces while retaining customer PII redaction.
- Added Sprint 2 deterministic tests, live DB service-search validation, and release documentation.

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
