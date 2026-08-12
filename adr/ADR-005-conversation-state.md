# ADR-005 — Conversation state persistence

Status: Accepted

Keep `Conversation.status` for ownership/control (`AI_ACTIVE`, `WAITING_HUMAN`, `HUMAN_ACTIVE`, `RESOLVED`) and add `agent_state` for workflow state (`INFO`, `COLLECTING`, `CONFIRMING`, `EXECUTING`, `HANDOFF`, `CLOSED`).
