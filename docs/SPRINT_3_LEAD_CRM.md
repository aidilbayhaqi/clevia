# Sprint 3 — Lead & CRM Reliability

Release target: **Clevia v0.9.0**

## PRD

### Problem

Sprint 2 made informational answers precise, but lead capture was still too dependent
on probabilistic LLM behavior. A visitor could show genuine service/booking interest,
yet the model might fail to ask for the right contact field, repeat a question, or
create another lead for a phone number already present in CRM.

The CRM update endpoint also accepted an arbitrary `assigned_to_user_id` without
verifying that the assignee belonged to the same clinic.

### Goal

Convert genuine service/booking interest into a CRM lead reliably while keeping the
conversation low-friction and preserving tenant isolation.

### User stories

- As a visitor, when I show real interest, Clevia helps me and asks only one missing
  contact field at a time.
- As a visitor, I can decline sharing contact details without being pressured.
- As operations staff, repeated conversations from the same phone should link to one
  lead instead of creating duplicate CRM records.
- As operations staff, chatbot leads should preserve the service interest when a
  known service is mentioned.
- As an admin, I can filter leads and safely update status/contact/assignment without
  linking records across clinics.

### Acceptance criteria

- Name + phone collection is deterministic after the first lead-intent turn.
- Phone is stored in canonical Indonesian `+62...` format.
- Same-clinic phone reuse does not create a second lead.
- Known service name in the interest text resolves to `interest_service_id`.
- Lead source is `CHATBOT`.
- Opt-out exits `COLLECTING` and stores no new lead.
- Admin assignee/service IDs are verified against the authenticated clinic.
- No autonomous appointment creation is added.

## System design

```text
Visitor
  |
  v
Public Conversation API
  |
  v
Intent Router
  |
  +---- informational/profile ----------> existing Sprint 2 flow
  |
  +---- SERVICE_INTEREST / BOOKING_INTEREST
            |
            v
      initial helpful LLM turn
            |
            +--> enforced next missing contact question
            |
            v
      AgentState.COLLECTING
            |
            v
      deterministic LeadCapture service
        - extract name
        - extract phone
        - normalize phone
        - respect opt-out
            |
            v
      capture_lead tool
        - same-clinic phone dedupe
        - resolve service interest
        - link Conversation.lead_id
            |
            v
      CRM Lead
```

No new database migration is required in Sprint 3.

## Application workflow

```text
INFO
 |
 | genuine service / booking intent
 v
COLLECTING
 |
 +-- missing name  -> ask name only
 |
 +-- missing phone -> ask WhatsApp only
 |
 +-- opt-out ------> INFO (no lead)
 |
 +-- name + phone
 v
capture_lead
 |
 +-- phone exists -> reuse + link existing lead
 |
 +-- new phone ----> create CHATBOT lead
 |
 v
INFO
```

## Business workflow

```text
Visitor interested
  -> Clevia collects minimal contact
  -> CRM lead NEW
  -> Reception/Admin reviews lead
  -> manual lifecycle:
     NEW -> CONTACTED -> QUALIFIED -> BOOKED -> WON / LOST
```

Sprint 3 does **not** automatically move lead status beyond the model default. Staff
remain responsible for CRM pipeline decisions.

## Security

- Lead lookup/dedupe always scopes by clinic.
- CRM lead fetch/update always scopes by authenticated clinic.
- Assigned user must belong to authenticated clinic.
- Interest service must belong to authenticated clinic.
- Existing trace redaction continues to redact full name, phone, email and notes.

## Non-goals

- autonomous booking;
- calendar writes from the AI;
- payment;
- marketing automation;
- cross-clinic lead sharing;
- autonomous lead scoring.

## Release gates

1. exact local v0.8.1 baseline verification;
2. source copy SHA verification;
3. Python compile;
4. Sprint 3 runtime contract;
5. Ruff safe-fix + strict gate on touched Python files;
6. targeted tests;
7. deterministic DB lead-flow/dedupe test with transaction rollback;
8. full pytest;
9. offline eval + P0 gate;
10. Docker build/recreate + health.
