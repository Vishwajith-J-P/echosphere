# Feature Registry

## Status

The local implementation slice is present across the voice-only backend, browser caller, operator console, durable SQLite store, and mock ticket adapter. A feature remains `IN_PROGRESS` where live Agora evidence or production hardening is still required. The local operator console has no login or credential gate; caller and provider media/API capabilities remain separate.

Platform/account configuration and documentation readiness are tracked in the implementation plan, not marked as completed product features.

| ID | Feature | Status | Summary |
|---|---|---|---|
| F-001 | Agora voice session | IN_PROGRESS | Secure realtime caller/AI audio foundation |
| F-002 | Multilingual conversation | IN_PROGRESS | Hindi, English, Tamil, and code-switching |
| F-003 | Interruption/noise handling | PLANNED | Barge-in and focused repair |
| F-004 | Guided information collection | PLANNED | Prioritized fields and validation |
| F-005 | Confirmation/correction | PLANNED | Tentative-to-confirmed lifecycle |
| F-006 | Confidence and safety policy | PLANNED | Explainable escalation decisions |
| F-007 | Human handoff | PLANNED | Warm transfer with context |
| F-008 | Ticket integration | PLANNED | Idempotent case sync and retry |
| F-009 | Agent/supervisor console | PLANNED | Live queue and context workspace |
| F-010 | Audit, privacy, observability | PLANNED | Safe operational evidence |

## F-001 — Agora Voice Session

**Status:** IN_PROGRESS

- [x] Server issues short-lived Agora join data without exposing certificates.
- [x] Browser implementation joins bidirectional audio and backend starts/stops Agora Conversational AI through an isolated gateway; production build and mocked lifecycle pass.
- [ ] Normalized events drive session lifecycle and transcript.
- [ ] Duplicate start/end/callback operations are safe.
- [ ] Failure produces bounded recovery and human/manual fallback.

**Acceptance:** PRD FR-001, FR-002; AC-002.

**Implementation:** `backend/echosphere/api/routes.py`, `backend/echosphere/services/sessions.py`, `backend/echosphere/services/agora_gateway.py`, `frontend/src/useVoiceSession.ts`, and `frontend/src/App.tsx`.

**Verification limit:** The second checked item proves the implemented browser/server flow and provider contract, not a completed live Agora sandbox call. F-001 remains IN_PROGRESS until live two-way audio and start/stop evidence is recorded.

## F-002 — Multilingual Conversation

**Status:** PLANNED

- [ ] Hindi and English turns work in one session.
- [ ] Mid-turn/turn-boundary language switching requires no restart.
- [ ] Current/preferred language is tracked without treating inference as confirmation.
- [ ] Hindi transcript typography and language metadata are accessible.

**Acceptance:** PRD FR-003, FR-016; AC-001.

## F-003 — Interruption and Noise Handling

**Status:** PLANNED

- [ ] Caller barge-in suppresses obsolete AI audio and preserves caller speech.
- [ ] Overlap/background noise lowers confidence rather than becoming confirmed data.
- [ ] Focused repair and silence handling follow bounded policy.
- [ ] Latencies and repair reasons are measurable.

**Acceptance:** PRD FR-004, FR-009; AC-001, AC-002.

## F-004 — Guided Information Collection

**Status:** PLANNED

- [ ] Orchestrator owns prioritized field requirements.
- [ ] Facts volunteered early fill relevant tentative slots.
- [ ] One concise question is asked at a time.
- [ ] Confirmed facts are not unnecessarily re-asked.
- [ ] Optional data can be declined.

**Acceptance:** PRD FR-005–FR-007, FR-016.

## F-005 — Confirmation and Correction

**Status:** PLANNED

- [ ] Critical values require explicit confirmation.
- [ ] Corrections supersede current values but preserve audit history.
- [ ] Corrected critical values require reconfirmation.
- [ ] UI and handoff distinguish confirmed, tentative, corrected, unresolved.

**Acceptance:** PRD FR-008, FR-015; AC-004.

## F-006 — Confidence and Safety Policy

**Status:** PLANNED

- [ ] Confidence combines available speech, intent, field, contradiction, repair, audio, and policy signals.
- [ ] Decisions include safe reason codes and missing scores are not assumed high.
- [ ] Hard safety/human-request rules override scores.
- [ ] Two failed focused repairs trigger handoff.
- [ ] Safety corpus verifies prohibited authoritative advice is not produced.

**Acceptance:** PRD FR-009, FR-010, FR-015; AC-003, AC-005.

## F-007 — Human Handoff

**Status:** PLANNED

- [ ] Escalation can start from any active state.
- [ ] Context snapshot exists before transfer attempt.
- [ ] Human sees reason, language, summary, facts by status, open questions, and transcript.
- [ ] Caller hears transfer state and confirmed context is retained.
- [ ] Transfer failure has a safe configured fallback.

**Acceptance:** PRD FR-011; AC-001, AC-005.

## F-008 — Ticket Integration

**Status:** PLANNED

- [ ] Canonical adapter supports create/update using idempotency keys.
- [ ] Local/mock adapter makes the demo deterministic.
- [ ] Retry/backoff does not duplicate cases.
- [ ] Ticket outage is visible but never blocks transfer.

**Acceptance:** PRD FR-012; AC-001.

## F-009 — Agent/Supervisor Console

**Status:** PLANNED

- [ ] Queue and session workspace update live.
- [ ] Agents accept handoffs with context visible first.
- [ ] Confidence explanation uses bands/reason codes.
- [ ] Supervisors can retry permitted integration jobs.
- [ ] Responsive and keyboard-accessible states meet the UI brief.

**Acceptance:** PRD FR-013, FR-015.

## F-010 — Audit, Privacy, and Observability

**Status:** PLANNED

- [ ] Append-only material events support reconstruction.
- [ ] Logs redact credentials and configured sensitive values.
- [ ] Retention and recording behavior are configurable; recording defaults off.
- [ ] Metrics cover latency, repairs, escalation, transfer, and ticket sync.
- [ ] Correlation IDs link safe diagnostics across components.

**Acceptance:** PRD FR-014 and non-functional requirements.

## Verification Baseline

The [limitation remediation plan](implementation_plan.md#limitation-remediation-plan) defines the six delivery gates for these features. Documenting a fix does not change its implementation status or check its acceptance boxes.

Research update (2026-09-05): [Voice gap resolution](../technical/gap_resolution.md) maps official starters and optional RNNoise/Silero references to remaining features. No dependency was installed and no feature status advanced. Managed voice availability, trusted events, policy-before-speech control, and human media continuity still require evidence.

No capability may be checked or marked COMPLETE until its automated tests pass and relevant live/manual validation is recorded. Agora-dependent behavior requires a sandbox integration test in addition to mocked contracts.

Detailed verification is defined in `docs/execution/test_plan.md`; requirement coverage is mapped in `docs/execution/traceability.md`. Planned architecture or schema documentation must not be mistaken for implemented capability.
