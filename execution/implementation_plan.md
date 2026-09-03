# Implementation Plan

## Status

Documentation and scope definition are complete. Application implementation has not started.

## Phase 0 — Vendor Spike and Test Harness

**Objective:** Prove the risky Agora path before building product surfaces.

| Task | Status | Outcome |
|---|---|---|
| IP-001 | TODO | Verify current Agora Conversational AI lifecycle, credentials, callbacks, Hindi-English model/voice support, barge-in controls, and transfer options against official docs/sandbox |
| IP-002 | TODO | Create deterministic provider fixtures and gateway contract tests |
| IP-003 | TODO | Record selected SDK/API versions and resolve proposed architecture decisions |
| IP-004 | TODO | Validate the selected Agora transcript/event mechanism, its authentication guarantees, ordering, redelivery behavior, and payload limits |

**Exit:** A minimal two-way browser call can be started/stopped securely; code-switch, interruption, transcript/event delivery, and browser-channel human handoff feasibility/results are documented.

## Phase 1 — Domain and Persistence Foundation

| Task | Status | Outcome |
|---|---|---|
| IP-010 | TODO | Flask factory, typed configuration, errors, logging, correlation IDs |
| IP-011 | TODO | Initial SQLite migration and repositories for planned entities |
| IP-012 | TODO | Deterministic conversation state machine and priority-field policy |
| IP-013 | TODO | Confirmation/correction lifecycle and append-only audit events |
| IP-014 | TODO | Multi-signal confidence and safety rule engine with reason codes |

**Dependencies:** IP-003 for provider-facing contracts; domain tests may start independently.

**Exit:** Domain scenario tests pass without Agora or a live model.

## Phase 2 — Live Voice and Caller Experience

| Task | Status | Outcome |
|---|---|---|
| IP-020 | TODO | Secure session/token endpoints and Agora gateway |
| IP-021 | TODO | Normalized event ingestion with the selected interface's documented authentication/integrity controls, validation, ordering handling, and deduplication |
| IP-022 | TODO | React caller simulator, microphone/connection states, transcript, and AI disclosure |
| IP-023 | TODO | Hindi/English switching, language metadata, and response policy |
| IP-024 | TODO | Barge-in cancellation, noise repair, silence/reconnection behavior, and latency telemetry |

**Dependencies:** Phase 0 and IP-010–IP-014.

**Exit:** Scripted English, Hindi, code-switched, noisy, and interrupted calls satisfy F-001–F-006 in the Agora sandbox.

## Phase 3 — Handoff, Console, and Ticketing

| Task | Status | Outcome |
|---|---|---|
| IP-030 | TODO | Context-summary builder and immutable handoff snapshot |
| IP-031 | TODO | Handoff adapter, lifecycle, failure fallback, and human acceptance |
| IP-032 | TODO | Live agent/supervisor console with accessible queue/session UI |
| IP-033 | TODO | Canonical ticket adapter plus local/mock implementation |
| IP-034 | TODO | Durable idempotent retry processing and supervisor retry action |

**Dependencies:** Phase 2; production provider tasks remain limited by vendor selections.

**Exit:** Explicit/automatic escalation preserves context, transfer continues during ticket failure, and retries create no duplicates.

## Phase 4 — Hardening and Demo Validation

| Task | Status | Outcome |
|---|---|---|
| IP-040 | TODO | Privacy/redaction/retention controls and access-control review |
| IP-041 | TODO | Metrics/dashboard-ready telemetry and failure injection |
| IP-042 | TODO | Accessibility and responsive-device review |
| IP-043 | TODO | Full acceptance scenario suite and safety red-team corpus |
| IP-044 | TODO | Demo seed/config, runbook, architecture and operator documentation |
| IP-045 | TODO | Complete requirements traceability with recorded automated/manual evidence |

**Exit:** All PRD acceptance criteria pass, no prohibited safety response appears in the regression corpus, and known compromises are recorded.

## Critical Scenario Matrix

| Scenario | Expected proof |
|---|---|
| Hindi -> English incomplete/noisy call | Same session; targeted repair; critical confirmation; contextual handoff |
| Caller interrupts AI | Playback stops; caller turn retained; obsolete response not committed |
| Corrected phone/location | Old value superseded; new value reconfirmed; audit retained |
| Explicit “human” request | Immediate escalation without additional intake |
| Medical/legal/financial/emergency advice | Boundary statement; no authoritative answer; handoff |
| Ticket API timeout/duplicate callback | Transfer proceeds; retry visible; one external case |
| Agora/console disconnect | Bounded recovery or safe fallback; server state recoverable |

## Completion Discipline

- Change a task to IN_PROGRESS before coding and COMPLETE only after its tests/evidence pass.
- Update `execution/features.md` capability boxes and implementation files after each completed task.
- Update schema only with implemented migrations.
- Record new architectural decisions and intentional compromises.
- Do not expand into production emergency response, expert advice, identity proofing, payments, or autonomous resolution.

## Current Work

**Active task:** None  
**Next recommended task:** IP-001 — Agora vendor spike.
