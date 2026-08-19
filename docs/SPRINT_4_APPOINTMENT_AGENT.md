# Sprint 4 — Appointment Agent

Release: **Clevia v1.0.0**

## PRD

### Problem

Clevia can answer questions and capture CRM leads, but an interested lead still has
to leave the conversation to choose a real appointment slot. Allowing an LLM to
directly write appointments without persistent state or explicit confirmation would
be unsafe.

### Goal

Allow a known CRM lead to request an appointment from chat with deterministic slot
selection, explicit confirmation, idempotent writes, and staff-controlled final
confirmation.

### Acceptance criteria

- Booking requires an existing CRM lead.
- Service is resolved from the lead interest or explicit service text.
- Date is collected before availability lookup.
- Slots come only from the appointment availability service.
- User selects a numbered real slot.
- No appointment write occurs before explicit `YA`.
- `TIDAK`/cancel creates no appointment.
- AI-created appointment starts as `REQUESTED`.
- Exact retry reuses the existing active appointment.
- Staff can transition appointment status only through allowed transitions.
- All booking writes remain tenant scoped.

## System design

```text
Chat
 |
 v
Intent Router
 |
 +-- BOOKING_INTEREST + no lead --> Sprint 3 lead capture
 |
 +-- BOOKING_INTEREST + lead
             |
             v
      Conversation.booking_draft
             |
       COLLECTING service/date
             |
             v
      get_availability (read-only)
             |
             v
      numbered slot selection
             |
             v
         CONFIRMING
             |
        YA / TIDAK
          /      \
       TIDAK      YA
        |          |
        v          v
      cancel   create_appointment_request
                    |
             confirmation guard
                    |
             idempotency lookup
                    |
             create_appointment
                    |
             REQUESTED + CHATBOT
                    |
             staff CRM confirmation
```

## Application state workflow

```text
INFO
 -> COLLECTING(service)
 -> COLLECTING(date)
 -> COLLECTING(slot)
 -> CONFIRMING
 -> INFO (REQUESTED created)

Cancel from any booking step -> INFO without write.
```

The `EXECUTING` concept is represented by the guarded transactional tool call; the
persistent conversational state is returned to INFO only after the write succeeds.

## Business workflow

```text
Lead NEW
 -> booking requested by chat
 -> Lead BOOKED
 -> Appointment REQUESTED
 -> staff CONFIRMED
 -> CHECKED_IN
 -> COMPLETED

Alternative staff branches:
REQUESTED -> CANCELLED
CONFIRMED -> CANCELLED / NO_SHOW
```

## Safety controls

- `AGENT_TRANSACTIONAL_TOOLS_ENABLED` feature flag.
- Default config remains false for safe production rollout.
- Local installer enables the flag for acceptance testing.
- Persistent DB booking draft.
- Exact payload must match the confirmed draft.
- Existing lead required.
- Service/staff/availability validated by backend.
- PostgreSQL advisory lock prevents concurrent slot races.
- Exact active request dedupe provides idempotency.
- Appointment starts REQUESTED, never automatically CONFIRMED.
- Staff status transitions are allow-listed and audited.

## Migration

`20260819_0004_booking_draft.py`

Adds:

```text
conversations.booking_draft JSONB NOT NULL DEFAULT '{}'
```

No patient medical data is stored in the booking draft.
