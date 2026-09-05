# Implementation Plan

## Status

Documentation is complete and Phase 0 implementation is in progress.

## Completed Preparation

| Task | Status | Outcome |
|---|---|---|
| IP-000 | COMPLETE | Consolidated the product, technical, execution, safety, operations, and decision specification under `docs/`; protected local environment secrets |

**Evidence:** Documentation path/placeholder/fence validation and Git-ignore verification performed on 2026-09-03. This completes documentation only, not any product feature.

## Phase 0 — Vendor Spike and Test Harness

**Objective:** Prove the risky Agora path before building product surfaces.

| Task | Status | Outcome |
|---|---|---|
| IP-001 | IN_PROGRESS | Secure token/session API, Agora gateway, and RTC caller client implemented; live agent/model, Hindi-English, barge-in, and transfer validation remain |
| IP-002 | IN_PROGRESS | Fake provider gateway and five API lifecycle/authentication tests added; provider payload fixtures remain |
| IP-003 | IN_PROGRESS | Python/browser SDK versions pinned and initial runtime stack accepted; transcript package compatibility remains unresolved |
| IP-004 | TODO | Validate the selected Agora transcript/event mechanism, its authentication guarantees, ordering, redelivery behavior, and payload limits |

**Exit:** A minimal two-way browser call can be started/stopped securely; code-switch, interruption, transcript/event delivery, and browser-channel human handoff feasibility/results are documented.

## Phase 1 — Domain and Persistence Foundation

| Task | Status | Outcome |
|---|---|---|
| IP-010 | IN_PROGRESS | Flask factory, typed configuration, safe API errors, and correlation IDs implemented early in Phase 0; structured logging remains |
| IP-011 | TODO | Initial SQLite migration and repositories for planned entities |
| IP-012 | TODO | Deterministic conversation state machine and priority-field policy |
| IP-013 | TODO | Confirmation/correction lifecycle and append-only audit events |
| IP-014 | TODO | Multi-signal confidence and safety rule engine with reason codes |

**Dependencies:** IP-003 for provider-facing contracts; domain tests may start independently.

**Exit:** Domain scenario tests pass without Agora or a live model.

## Phase 2 — Live Voice and Caller Experience

| Task | Status | Outcome |
|---|---|---|
| IP-020 | IN_PROGRESS | Secure in-memory session/token endpoints and Agora gateway implemented in Phase 0; persistence and live sandbox evidence remain |
| IP-021 | TODO | Normalized event ingestion with the selected interface's documented authentication/integrity controls, validation, ordering handling, and deduplication |
| IP-022 | IN_PROGRESS | React caller simulator implements microphone/basic connection states and AI disclosure; transcript and full recovery states remain |
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
- Update `docs/execution/features.md` capability boxes and implementation files after each completed task.
- Update schema only with implemented migrations.
- Record new architectural decisions and intentional compromises.
- Do not expand into production emergency response, expert advice, identity proofing, payments, or autonomous resolution.

## Current Work

**Active task:** IP-001 — Agora vendor spike
**Next recommended task:** Run the browser/agent path in the Agora sandbox, then validate IP-004 transcript transport.

## Plan Change Log

### 2026-09-03 — Phase 0 foundation

- Created the `echosphere` Conda environment with Python 3.13 and pinned backend dependencies.
- Added a Flask application factory, safe configuration, correlation-aware errors, short-lived Agora token/session endpoints, idempotent start/end behavior, and an Agora Agents gateway.
- Added a React/Vite caller surface with AI disclosure, language selection, microphone processing, RTC join/publish/playback, and shutdown.
- Verified five mocked API tests, real-environment token issuance, a production frontend build, and a zero-vulnerability npm audit.
- Deferred transcript UI because the tested `agora-rtm` and client-toolkit versions have incompatible RTC peer requirements; this must be resolved in IP-004.

### 2026-09-03 — Documentation baseline and Agora readiness

- Established the canonical `docs/` hierarchy and project blueprint.
- Installed/authenticated Agora CLI 0.2.8 and bound the `echosphere` project.
- Verified RTC included, Signaling enabled, and Conversational AI enabled.
- Recorded the non-blocking CLI warning that token capability remains reported disabled.
- Added IP-004 to validate the actual transcript/event contract before relying on provider assumptions.
