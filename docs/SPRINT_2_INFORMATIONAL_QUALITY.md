# Sprint 2 — Informational AI Quality

Release target: **Clevia v0.8.0**

## Product goal

Make informational answers more precise and cheaper without expanding Clevia into
booking/transactional automation yet.

## Problems observed after Sprint 1

A named-service question could call `search_knowledge` more than once and then
`list_services`, which returns the complete service catalogue. The answer could be
correct while tool selection, latency, and source precision were worse than needed.

Tool traces also redacted every field named `name`, including harmless service names.

## Changes

### 1. Precise service lookup

New read-only tool:

`search_services(query)`

Use it for named/keyword service questions about:

- price;
- duration;
- category;
- public service description.

Results are scoped to the active business, active/public services, ranked with exact
name/slug matches first, and limited to five results.

### 2. Explicit tool routing

Prompt `clevia-informational` moves from `2.0.0` to `2.1.0`.

Routing contract:

- named service / price / duration -> `search_services`;
- broad catalogue -> `list_services`;
- clinic profile -> `get_clinic_profile`;
- policies / FAQs -> `search_knowledge`.

### 3. Read-only duplicate suppression

Identical read-only tool results are cached within one agent run.

Cached tools:

- `get_clinic_profile`
- `list_services`
- `search_services`
- `search_knowledge`

Side-effect tools such as `capture_lead` and `request_human_handoff` are never cached.

### 4. Better observability redaction

Generic `name` is no longer considered automatically sensitive. `full_name`, phone,
email, tokens, notes, messages, and other sensitive values remain redacted.

This keeps service/clinic names visible in traces while preserving customer PII
redaction.

## Non-goals

- autonomous appointment booking;
- payment;
- prescription/diagnosis;
- multi-clinic provisioning;
- CRM workflow expansion.

## Release gates

- baseline Git blobs match the reviewed Sprint 1 GitHub state;
- tracked worktree clean before installation;
- Python compile pass;
- targeted Sprint 2 tests pass;
- live DB service-search contract pass;
- full pytest pass;
- offline eval pass;
- Ruff pass;
- `git diff --check` pass;
- API build and Docker health pass;
- optional Gemini E2E acceptance pass.
