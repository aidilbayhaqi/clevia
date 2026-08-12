# CleVIA Sprint 0 + 1 Implementation

Version: **0.3.0**

## Scope

This update turns the existing prototype into a traceable informational-agent baseline without
removing the existing website booking flow. Autonomous agent booking/lead tools are disabled from
the Sprint 1 agent runtime.

Implemented foundation:

- request correlation ID and request context;
- deterministic tenant selection using `DEFAULT_CLINIC_SLUG`;
- separated agent runtime, LLM adapter, prompt registry, retrieval, tools, and observability;
- prompt ID/version captured in `AgentTrace`;
- conversation `agent_state` separated from human/AI ownership `status`;
- KB metadata, approval lifecycle, chunk index, optional pgvector embeddings;
- approved + tenant + validity filtered retrieval;
- source references in chat API responses;
- human handoff summary/reason, transcript API, staff reply, resolve;
- AI-message feedback (`good`, `wrong`, `missing_knowledge`);
- offline golden-set baseline and CI pipeline;
- development/staging configuration separation;
- frontend demo mode defaults to off.

## Important boundaries

- The Clinic AI Agent in this release is informational + handoff only.
- Website appointment requests remain available as a normal website feature.
- `AGENT_TRANSACTIONAL_TOOLS_ENABLED=false` is intentionally the default.
- Knowledge embeddings are optional. With `KNOWLEDGE_EMBEDDINGS_ENABLED=false`, retrieval uses
  approved chunked keyword retrieval. When enabled, vector candidates are blended with keyword
  candidates.
- Clevia remains a customer-engagement/operations product, not an EMR/EHR.

## New endpoints

- `GET /api/v1/conversations/{conversation_id}/messages`
- `POST /api/v1/conversations/{conversation_id}/messages`
- `POST /api/v1/conversations/{conversation_id}/resolve`
- `POST /api/v1/conversations/{conversation_id}/messages/{message_id}/feedback`
- `POST /api/v1/knowledge/{document_id}/approve`
- `POST /api/v1/knowledge/{document_id}/archive`

The legacy `POST /knowledge/{id}/publish` route remains as a deprecated alias to `/approve`.

## Verification

```bash
ruff check app tests evals
pytest -q
python -m evals.runner --offline
alembic upgrade head
```

For local Docker:

```bash
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api python -m scripts.seed
```

## Known limitations

1. The offline eval harness validates deterministic routing/safety contracts. Full model
   groundedness evaluation still needs a controlled staging dataset and configured model key.
2. Vector embedding generation is opt-in to avoid hidden API cost during initial installation.
3. Transactional agent tools are intentionally outside the release capability gate.
4. Tenant routing is deterministic by configured slug, not yet domain/subdomain based.
