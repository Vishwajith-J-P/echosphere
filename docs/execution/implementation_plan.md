# Implementation Plan

## Status

The documentation baseline is established and the local implementation slice is in place. Vendor feasibility and live acceptance evidence remain open; written plans do not close these gates.

## Limitation Remediation Plan

These fixes implement existing scope. All gates below are pending until evidence is recorded in the feature registry and test plan. See [technical gap resolution](../technical/gap_resolution.md) for provider references and integration details.

| Order | Limitation and fix | Existing tasks / features | Acceptance gate |
|---|---|---|---|
| 1 | Unverified live voice: prove Agora-managed STT, LLM, and TTS with the configured account; resolve SDK, model, voice, authentication, and event compatibility | IP-001–IP-004; F-001 | Actual two-way audio and repeatable start/stop; record pinned versions, redacted configuration, provider event fixtures, account usage and errors. Mock tests alone cannot pass |
| 2 | Missing conversation control: implement prioritized questions, tentative extraction, explicit version-bound confirmation, correction history, bounded repairs, and policy before speech | IP-011–IP-014; F-004–F-006, F-010 | TS-003/004/005 and core invariants pass; human request or safety rule prevents another intake question; prohibited model output cannot reach TTS, including on control failure |
| 3 | Unverified noisy multilingual interaction: measure existing audio processing, Hindi-English switching and interruption; evaluate an optional denoiser only after measured baseline failures | IP-020–IP-024; F-001–F-003 | TS-001/002 pass on quiet/noisy paired fixtures; verify critical digit read-back, caller turn preservation and stale response cancellation; report latency against existing targets |
| 4 | Missing human continuation: implement a protected console, immutable handoff context, atomic acceptance, scoped human join and verified media readiness | IP-030–IP-032 and minimum IP-040 access controls; F-007, F-009 | A second authorized browser continues the same call; context precedes acceptance; no false connected state on failed join; competing agents cannot both claim the call; AI stops/suppresses correctly |
| 5 | Volatile cases and unreliable integrations: finish durable SQLite repositories, migrations, local ticket adapter, persistent retry jobs and external-outcome reconciliation | IP-011, IP-013, IP-033/034; F-008, F-010 | Restart preserves case facts, snapshot and pending jobs; TS-006 loses a remote success response without creating a duplicate ticket; ticket failure never blocks transfer |
| 6 | Incomplete operational readiness: finish role checks, redaction, retention, reconnect recovery, observability, accessibility and full safety evaluation | IP-040–IP-045; F-001, F-009, F-010 and all-feature regression | TS-001–TS-007 plus accessibility/security checks pass; log review finds no secrets; recovery and safe fallback are demonstrated; evidence records test conditions and remaining failures |

### Dependency rules

- The order is an integration sequence, not permission to defer prerequisites. SQLite foundation belongs in Phase 1 before durable confirmation/handoff; step 5 completes ticket persistence and restart recovery.
- Agent authorization must exist before admitting a human into a caller channel. Phase 4 reviews and hardens it; it is not first added after a public console demo.
- Prove response control before declaring live conversational safety. An unconstrained managed-model connectivity spike remains synthetic and does not complete F-006.
- Independent domain and adapter tests can proceed while vendor evidence is pending. An unavailable provider blocks only the work that depends on it; preserve the existing phase ownership above.
- Each gate records test command/build, policy and provider versions, environment, results, and redacted artifacts using the test plan's evidence format. Record intentional implementation compromises in the debt register; do not mark a research candidate as installed.

### Limits that remain by design

Background-speaker overlap, unclear audio, and ambiguous facts require clarification or human help even with filtering. Report measured performance rather than perfect recognition claims. A human may be unavailable; keep context and use only a configured fallback without promising a connection. Internet/provider outages require bounded recovery and honest failure states.

Medical diagnosis, authoritative legal/financial/emergency advice, payments, and autonomous consequential decisions remain excluded. PSTN integration and production deployment require a separate scope decision after the browser prototype passes its gates; they are not remediation tasks in this plan.

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

Research prerequisite: apply [Voice gap resolution](../technical/gap_resolution.md) before continuing the vendor spike. Resolve the installed-versus-upstream model identifier/authentication differences, transcript dependency matrix, and pre-speech policy-control feasibility with redacted evidence. Reuse official starter patterns within the existing architecture; do not scaffold over the working tree.

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
