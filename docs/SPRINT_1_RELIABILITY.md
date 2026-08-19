# Sprint 1 — Reliability Closure & Baseline Consolidation

Target release: **Clevia v0.7.0**

## Sprint Goal

A fresh Clevia environment must be able to build, boot, run tests, and execute the
Gemini tool-calling path without replaying historical hotfix installers.

## Scope

1. Consolidate the canonical Gemini agent adapter.
2. Normalize `.env` and remove duplicate keys.
3. Make Gemini timeout/output settings typed.
4. Pin the exact `google-genai` version already running successfully in the local
   API container.
5. Remove eager `CleviaAgent()` construction from route import time.
6. Normalize provider timeout/rate/provider errors.
7. Return a controlled public fallback instead of HTTP 500 for controlled LLM
   runtime failures.
8. Add regression tests and runtime smoke tools.
9. Verify `.env` is not tracked by Git.
10. Update release metadata/documentation.

## Release Gate

- `docker compose config --quiet`
- API build succeeds
- Postgres/Redis/API healthy
- no duplicate `.env` keys
- exact `google-genai==x.y.z` pin
- pytest passes
- offline eval passes
- P0 release gate passes when present
- `pip check` passes
- `git diff --check` passes
- `.env` is not tracked
- optional live Gemini direct smoke passes
- optional live Clevia acceptance passes

## Not in this sprint

Booking, payments, new transactional tools, multi-clinic features, and AI tool
selection optimization remain outside Sprint 1.
