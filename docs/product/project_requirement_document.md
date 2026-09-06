# Product Requirements Document

## Product

**Name:** EchoSphere  
**Vision:** A calm, real-time multilingual voice assistant for customer assistance, public-information, and non-clinical support lines. It collects only the minimum useful facts, confirms critical details, and hands off to a person whenever automation is unsafe or uncertain.  
**Status:** Approved prototype scope; local implementation is in progress and live Agora acceptance remains open.

## Problem

Callers may be stressed, in noisy places, unable to explain an issue in order, or may naturally switch languages mid-sentence. Conventional menus and brittle bots make these calls longer and can silently capture the wrong details. Human agents then receive a cold transfer and must restart the conversation.

EchoSphere must demonstrate useful first-contact automation without pretending to replace human judgement. Agora Conversational AI is mandatory in the live voice path.

## Users

- **Caller:** seeks assistance by voice and may be multilingual, interrupted, or distressed.
- **Human agent:** receives escalated calls and needs concise, trustworthy context.
- **Supervisor:** monitors active calls, escalations, and integration failures.
- **Administrator/integrator:** configures languages, question policy, escalation rules, and case-system connections.

## Goals

1. Sustain low-latency Hindi, English, and code-switched conversation.
2. Let callers interrupt the AI without losing conversational state.
3. Collect and validate a configurable minimum information set.
4. Explicitly confirm critical details before relying on them.
5. Detect uncertainty and safety boundaries, then escalate promptly.
6. Transfer with a summary, facts, open questions, and transcript context.
7. Create/update a case without making transfer depend on the integration.

## Non-Goals and Safety Boundaries

The prototype must not:

- diagnose, triage, prescribe, or provide clinical advice;
- replace emergency responders or delay access to them;
- provide legal, financial, or emergency instructions as authoritative advice;
- claim uncertain, inferred, or unverified information is confirmed fact;
- autonomously make eligibility, enforcement, payment, benefit, or other consequential decisions;
- impersonate a human or conceal that the caller is interacting with AI;
- continue collecting nonessential information after escalation is decided.

When expert judgement is implicated, the AI states its limitation and transfers to the configured human queue. The generic prototype does not invent jurisdiction-specific emergency instructions or numbers.

## Approved Prototype Scope

### In Scope

- Browser-based support-line simulation using Agora real-time audio and Agora Conversational AI.
- Hindi, English, and Tamil, including switching within an utterance or turn.
- Streaming transcript with speaker and language indicators.
- Noise-tolerant turn handling, clarification, repetition, and confirmation.
- Configurable prioritized questions for a generic support case.
- Confidence evaluation across speech, understanding, fields, and policy.
- Caller-requested and automatic warm handoff.
- Agent console with live context, confirmed/unconfirmed distinction, summary, and transcript.
- Case/ticket adapter plus a local/mock adapter for reliable demonstration.
- Audit events that explain confirmation and escalation decisions.

### Out of Scope

- Production PSTN procurement, emergency dispatch, or workforce routing.
- Medical, legal, financial, or emergency advisory workflows.
- Caller identity proofing, production identity-provider integration, payments, or sensitive-document upload. Basic protected demo access for the human console remains required.
- Languages beyond Hindi, English, and Tamil without additional validation.
- Training foundation speech or language models.
- Autonomous case resolution or irreversible downstream actions.
- Production compliance certification or indefinite recordings.

## Minimum Case Information

| Priority | Field | Critical | Rule |
|---|---|---:|---|
| 1 | `intent` | Yes | Capture what help is needed in the caller's words. |
| 2 | `location_or_service_area` | Conditional | Ask only when routing/service depends on place. |
| 3 | `issue_details` | Yes | Concise description plus relevant timing/context. |
| 4 | `contact_name` | No | Caller may decline. |
| 5 | `callback_number` | Conditional | Confirm digit-by-digit when follow-up is required. |
| 6 | `preferred_language` | Yes | Infer provisionally; confirm when material to handoff. |

Domain deployments may change this set but must preserve data minimization, question priority, and explicit confirmation of critical values.

## Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-001 | Disclose that the assistant is AI and offer human assistance. | Must |
| FR-002 | Establish live bidirectional audio through Agora Conversational AI. | Must |
| FR-003 | Understand/respond in Hindi, English, and Tamil with natural code-switching. | Must |
| FR-004 | Support barge-in: stop/duck AI speech promptly, preserve caller audio, and resume appropriately. | Must |
| FR-005 | Collect configured fields in priority order while accepting multiple fields supplied early. | Must |
| FR-006 | Ask one short question at a time and avoid re-asking confirmed facts. | Must |
| FR-007 | Keep extracted values tentative until validation/confirmation rules pass. | Must |
| FR-008 | Repeat and explicitly confirm critical details; corrections replace current tentative values with audit history. | Must |
| FR-009 | Detect recognition failure, ambiguity, conflict, unsupported requests, safety triggers, frustration, silence, and human requests. | Must |
| FR-010 | Escalate on hard rules or when confidence remains low after at most two focused clarifications. | Must |
| FR-011 | Preserve handoff reason, summary, confirmed/tentative facts, open questions, language, and transcript reference. | Must |
| FR-012 | Create/update a ticket idempotently with retry; an outage must not block transfer. | Must |
| FR-013 | Provide a supervisor/agent console showing live state, confidence explanations, escalation, and integration status. | Should |
| FR-014 | Keep an append-only audit trail of material state, confirmation, safety, and escalation events. | Must |
| FR-015 | Distinguish confirmed caller facts, caller statements, AI inference, and system status in speech and UI. | Must |
| FR-016 | Permit correction, repetition, language change, refusal, and human escalation at any time. | Must |

## Conversation Policy

- Use the caller's current language; do not force a language-selection restart.
- Keep responses brief, calm, and non-judgmental.
- Acknowledge distress without claiming expertise or certainty.
- Prefer already-provided information over a rigid questionnaire.
- Never infer a missing critical detail and label it confirmed.
- For unclear audio, say what was and was not understood, then ask narrowly.
- Allow two clarification attempts per critical item, then hand off.
- On interruption, yield and process the caller's new turn before continuing.

## Confidence and Escalation

The orchestrator evaluates speech confidence/audio quality, intent ambiguity, per-field validation, contradictions, repair attempts, silence/interruptions/frustration, safety classification, and integration health.

**Hard triggers:** explicit human request; safety/expert-judgement need; abusive or threatening content requiring policy handling; unresolved critical contradiction; session integrity failure.

**Soft trigger:** required understanding stays below the configured threshold after no more than two clarification attempts. Thresholds are configurable and must be calibrated; they are not universal accuracy claims.

## Handoff Context Contract

Before or alongside transfer, the human receives session/case IDs, reason, current language, a neutral 3–5 sentence summary, confirmed fields with timestamps, clearly labeled tentative fields, unanswered priority questions, observational safety flags, transcript/timeline reference, and ticket status.

The caller hears that transfer is occurring and should not need to repeat confirmed information unless the human elects to verify it.

## Non-Functional Requirements

- **Latency:** prototype target median end-of-turn to first audio under 1.5 seconds; barge-in suppression under 500 ms in a healthy test environment.
- **Resilience:** transcript/ticket degradation must not trap callers; safe transfer remains available.
- **Privacy:** minimize data, encrypt transport, keep secrets server-side, redact configured sensitive values in logs, and configure recording/transcript retention.
- **Accessibility:** console supports keyboard navigation, visible focus, captions, non-color-only status, and responsive layouts.
- **Observability:** correlate events by session without logging credentials or unnecessary personal data.
- **Testability:** policy, confidence decisions, confirmation, handoff payloads, and adapters work under automated tests without live Agora.

## Acceptance Criteria

### AC-001 — Hindi/English/Tamil noisy-call scenario

Given a caller starts in Hindi, switches to English, supplies incomplete details, and background speech causes a low-confidence segment, the system continues one session, avoids confirming background speech, collects minimum required facts, confirms critical fields, escalates at the repair limit or judgement boundary, supplies a concise handoff packet, and creates/updates one idempotent case (or records retryable failure without blocking transfer).

### AC-002 — Interruption

Caller speech interrupts AI playback, is captured as a new turn, and changes the next response without loss of confirmed state.

### AC-003 — Safety boundary

For medical, legal, financial, or emergency-advice prompts, the AI avoids authoritative instruction, states its limitation, and routes according to policy.

### AC-004 — Correction

A corrected critical detail remains tentative until reconfirmed; the old value is no longer current and the change is auditable.

### AC-005 — Human request

An explicit request for a person bypasses nonessential questions and starts handoff.

## Success Measures

- All scripted critical fields are confirmed or labeled unresolved before handoff.
- All scripted safety calls avoid prohibited authoritative advice.
- All explicit human requests initiate escalation without persuasion loops.
- Tested retries create no duplicate ticket.
- Evaluators can identify why every scripted low-confidence escalation occurred.

## Assumptions and Open Decisions

- This is generic support intake, not a domain authority.
- Hindi, English, and Tamil are validation languages.
- A browser caller simulator and human console are sufficient for the demo.
- Ticket vendor, production queue provider, retention duration, and final consent copy remain deployment decisions.
- Confidence thresholds require representative-audio calibration.

## Requirement Precedence

Safety boundaries and explicit human requests take precedence over information collection, confirmation, completion, and ticket synchronization. Human transfer takes precedence over ticket availability. Confirmed caller facts take precedence over AI inference; a correction invalidates the prior current value until the replacement is reconfirmed.

Detailed safety behavior is defined in `docs/product/safety_policy.md`. Requirement-to-feature/test coverage is maintained in `docs/execution/traceability.md`.

## Requirement Change Log

### RC-001 — Replace reusable template scope

**Date:** 2026-09-03  
**Change:** Replaced the generic Flask-template PRD with the EchoSphere prototype brief.  
**Reason:** User-provided project problem statement.
