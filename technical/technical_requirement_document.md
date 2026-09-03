# Technical Requirements Document

## Status and Source of Truth

This document defines constraints for the planned EchoSphere prototype. No runtime implementation exists yet. Product behavior is defined in `product/project_requirement_document.md`; planned data is in `technical/backend_schema.md`; current implementation state is in `execution/features.md`.

## Technical Overview

| Area | Requirement |
|---|---|
| Backend | Python/Flask application with transport, orchestration, policy, integration, and persistence boundaries |
| Interactive UI | React/TypeScript for caller simulator and live agent/supervisor console |
| Static shell | Jinja may supply page shell and configuration bootstrap |
| Real-time voice | Agora RTC plus Agora Conversational AI in every AI voice session |
| Persistence | SQLite for the prototype behind repositories; production database is a later decision |
| Case integration | Provider-neutral ticket adapter; local/mock adapter required |
| Authentication | Caller session capability tokens plus demo agent/supervisor accounts; production identity-provider selection is unresolved |

Exact SDK/package versions must be pinned during implementation against then-current official Agora and framework documentation.

## Architecture Invariants

1. Browsers never receive Agora App Certificates, customer API secrets, or ticket credentials.
2. A server endpoint issues short-lived, least-privilege session tokens.
3. Vendor callbacks use the authentication/integrity controls actually provided by the selected Agora event mechanism, plus event deduplication, freshness checks where timestamps exist, and schema validation. Unsupported signature guarantees must not be invented.
4. Agora-specific objects remain behind a voice gateway; conversation policy must be testable without Agora.
5. The deterministic conversation orchestrator—not an unconstrained model—owns required fields, confirmations, retry limits, and escalation state.
6. Generative output cannot mark a fact confirmed, authorize a consequential action, or bypass a safety rule.
7. Ticket failure cannot prevent human handoff; it creates a retryable integration job.
8. Confirmed, tentative, corrected, and unresolved values remain distinct.
9. Material transitions are append-only audit events.
10. Session operations and callbacks are safe under duplicate delivery.

## Logical Components

- **Flask API:** session lifecycle, token issuance, callbacks, cases, handoff, and console read models.
- **Agora voice gateway:** creates/ends RTC and Conversational AI sessions and normalizes vendor events.
- **Conversation orchestrator:** finite-state flow, prioritized slots, repair counters, language state, and response directives.
- **Safety/policy engine:** detects prohibited advice and mandatory escalation; rules override model output.
- **Confidence evaluator:** combines speech, intent, field, contradiction, repair, and policy signals; returns score bands plus reason codes.
- **Transcript service:** stores ordered finalized turns and optional ephemeral partials.
- **Handoff service:** freezes a context snapshot before routing and tracks transfer lifecycle.
- **Ticket adapter:** maps canonical case data to an external system using an idempotency key.
- **React console/caller simulator:** consumes API plus a server-sent events or WebSocket event stream; Agora media stays on the supported client channel.

## Conversation State Machine

```text
CREATED -> CONNECTING -> DISCLOSURE -> COLLECTING <-> CONFIRMING
                              |             |             |
                              +-------------+-------------+
                                            |
                         COMPLETING or ESCALATING
                                            |
                        TRANSFERRING -> HUMAN_CONNECTED
                                            |
                                   ENDED / FAILED
```

Hard safety and human-request transitions may enter `ESCALATING` from any active conversational state. Once escalating, only transfer-critical dialogue is permitted.

## Confidence Contract

Each evaluated caller turn returns:

```json
{
  "overall_band": "high|medium|low",
  "speech_score": 0.0,
  "intent_score": 0.0,
  "field_scores": {"intent": 0.0},
  "audio_quality": "good|degraded|poor|unknown",
  "reason_codes": ["BACKGROUND_SPEECH", "AMBIGUOUS_INTENT"],
  "hard_escalation": false
}
```

- Scores are optional when a provider does not supply them; missing is not treated as high confidence.
- Hard rules override scores.
- Critical values require explicit confirmation regardless of score.
- Two failed focused repairs for the same critical need cause escalation.
- Configuration owns thresholds and is versioned with the session policy.

## Interruption and Audio Requirements

- Enable Agora-supported voice activity/turn detection and interruption behavior.
- On detected caller speech during playback, stop or duck generated audio promptly and cancel obsolete response generation where supported.
- Preserve the caller audio/turn and do not commit text from cancelled AI output as spoken.
- Ignore or down-rank non-primary/background speech when detectable; ask for repetition instead of guessing.
- Measure time-to-first-audio, barge-in stop latency, packet loss/jitter where exposed, and repair frequency.
- Offer text/status fallback in the demo console when media fails, but never represent it as a completed voice interaction.

## API Surface (Planned)

| Method | Route | Purpose |
|---|---|---|
| POST | `/api/sessions` | Create session and return short-lived caller join data |
| POST | `/api/sessions/{id}/start` | Start the Agora conversational agent |
| POST | `/api/sessions/{id}/end` | End session idempotently |
| GET | `/api/sessions/{id}` | Read session/case state |
| GET | `/api/sessions/{id}/events` | Authorized live event stream |
| POST | `/api/sessions/{id}/escalations` | Request/force escalation |
| POST | `/api/sessions/{id}/handoff/accept` | Human accepts handoff |
| POST | `/api/webhooks/agora` | Receive authenticated vendor events |
| POST | `/api/integration-jobs/{id}/retry` | Supervisor retries a ticket operation |
| GET | `/console` | Agent/supervisor console |
| GET | `/demo/call` | Caller simulator |

Mutation endpoints require authentication appropriate to the actor, CSRF protection for cookie sessions, validation, and idempotency where retryable.

Caller access uses a short-lived opaque capability bound to one session; it is not reusable as an agent-console credential. Agent and supervisor access are separate roles. The demo may use seeded local accounts, but it must not expose the console publicly or call that production-grade authentication.

## Security and Privacy

- TLS is required outside local development.
- Secrets come from environment/secret storage and must be redacted.
- Validate callback authentication/signatures and timestamps only through mechanisms documented for the selected Agora event API; otherwise use the strongest documented transport/authentication controls and record the limitation.
- Use opaque UUIDs; never expose sequential case IDs as authorization.
- Store only finalized transcript turns by default; partial transcripts are ephemeral unless needed for diagnostics and explicitly enabled.
- Recording is off by default. If enabled later, disclose it and document separate retention/access controls.
- Callback numbers and free-text transcripts are sensitive; restrict console access and log only redacted references.
- Retention is configuration, not hard-coded. Purge must remove or anonymize linked content consistently while retaining minimal operational audit where legally allowed.

## Reliability

- All external calls use bounded timeouts, safe retries with exponential backoff/jitter, and circuit breaking or failure isolation.
- Use idempotency keys: session UUID for Agora start/stop and `case_id:event_type:version` for ticket operations.
- Persist handoff context before initiating transfer.
- Duplicate/out-of-order events are detected through provider event IDs and monotonic sequence/timestamps.
- If AI orchestration fails, play a brief limitation message if possible and route to a human; do not loop.

## Observability

Structured events include correlation/session ID, component, event type, latency, outcome, and safe reason codes. Prohibited data includes credentials, raw tokens, and unredacted phone numbers. Metrics cover session starts, connection failures, language switches, repair attempts, safety triggers, escalations by reason, transfer success/time, ticket failures, latency, and interruption response.

## Testing

- Unit tests: state machine, question priority, confirmation/correction, confidence rules, safety rules, summaries, redaction, idempotency.
- Contract tests: Agora gateway and ticket adapters with fixtures/mocks.
- Integration tests: session-to-handoff and ticket retry flows.
- Scenario tests: Hindi, English, code-switching, background talk, barge-in, silence, contradictory facts, safety prompts, and explicit human requests.
- Manual device/network matrix: headphones/speakerphone, poor network, noisy clips, desktop/mobile.
- Safety regression corpus must assert both prohibited content avoidance and successful escalation.

## Prototype Performance Targets

| Metric | Target under healthy test conditions |
|---|---|
| End-of-turn to first AI audio | median < 1.5 s; p95 recorded |
| AI speech suppression after barge-in | < 500 ms target |
| Event propagation to console | p95 < 1 s |
| Duplicate ticket creation under retries | 0 |
| Handoff packet availability before transfer attempt | 100% scripted tests |

These are evaluation targets, not production SLAs.

## Configuration

Environment-specific values include Agora credentials/project identifiers, token TTL, supported languages, provider voice/model settings, confidence thresholds, clarification limit, queue mapping, ticket adapter, retry policy, retention, allowed origins, and feature flags. Log active non-secret configuration/policy versions per session.

## Unresolved Technical Selections

- Agora Conversational AI SDK/API integration mode and supported handoff mechanism.
- Event transport for the console (SSE is preferred for one-way updates; WebSocket if bidirectional realtime commands require it).
- External ticket vendor and human queue/telephony provider.
- Production database and job runner.
- Validated STT/TTS/model combination for Hindi-English code-switching.

See `technical/agora_integration.md`, `technical/api_contract.md`, and `technical/operations.md` for concrete integration, interface, and operating contracts.
