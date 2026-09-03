# EchoSphere Project Blueprint

## Product Summary

EchoSphere is a real-time Hindi-English voice AI prototype for customer assistance, public information, and non-clinical support intake. It is designed for callers who may be stressed, interrupted, in a noisy environment, unable to explain an issue linearly, or naturally switching languages.

The assistant identifies itself as AI, gathers only the minimum useful information, treats extracted values as tentative, explicitly confirms critical details, and transfers to a human whenever the caller asks, safety rules apply, or confidence remains insufficient after bounded clarification.

## Goals and Boundaries

### The system will

- provide low-latency voice interaction through Agora Conversational AI;
- support Hindi, English, and code-switching;
- handle barge-in, silence, overlap, and degraded audio;
- collect configurable information in priority order;
- distinguish tentative, confirmed, corrected, rejected, and unresolved details;
- evaluate confidence using multiple explainable signals;
- execute a context-preserving human handoff;
- synchronize one canonical case to a ticket adapter;
- provide an accessible agent/supervisor console;
- preserve safe audit and operational evidence.

### The system will not

- provide diagnosis, clinical treatment, or medical triage;
- replace emergency responders;
- give legal, financial, or emergency instructions as authoritative advice;
- make consequential eligibility, payment, enforcement, or benefit decisions;
- pretend uncertain information is confirmed;
- conceal that it is AI;
- autonomously resolve cases outside the configured bounded workflow.

## Actors and Interfaces

| Actor | Interface | Primary outcome |
|---|---|---|
| Caller | React browser voice UI | Explain need, confirm facts, reach human |
| Human agent | React console | Receive context and continue call |
| Supervisor | Console diagnostics | Monitor queue and retry ticket jobs |
| Agora | RTC, Signaling, Conversational AI | Carry audio, transcripts, agent events |
| Ticket system | Adapter API | Store/update external support case |

The prototype uses browser-to-browser Agora RTC handoff. Real phone/PSTN and contact-center routing are future adapters, not current scope.

## Technology Stack

| Layer | Selected technology | Status/rationale |
|---|---|---|
| Backend | Python + Flask | Accepted; application services and APIs |
| Frontend | React + TypeScript + Vite | Accepted for realtime caller/console UI |
| Server rendering | Jinja | Optional lightweight shell/static pages |
| Voice/media | Agora RTC | Included in Agora project |
| Voice AI runtime | Agora Conversational AI Engine | Enabled and mandatory in live voice path |
| Realtime metadata | Agora Signaling | Enabled; transcripts and client events |
| Server notifications | Agora notifications/webhooks | Enabled; exact event contract requires Phase 0 validation |
| Persistence | SQLite + SQLAlchemy/Alembic planned | Prototype choice behind repositories |
| Console updates | Server-Sent Events proposed | Simpler one-way updates; final spike decision |
| Testing | Pytest plus frontend unit/E2E tooling | Exact frontend tools pinned during scaffold |
| Ticketing | Provider-neutral adapter + local mock | External provider unresolved |
| Deployment | Single-service prototype | Production platform unresolved |

Dependency versions are not guessed in documentation. They will be pinned after scaffold/vendor validation.

## Modular Architecture

```text
Browser clients
├── Caller application
│   ├── microphone/RTC lifecycle
│   ├── transcript and language view
│   └── confirmation/human-request controls
└── Agent console
    ├── escalation queue
    ├── case/transcript workspace
    └── handoff and integration controls
            |
            v
Flask transport layer
├── session API
├── agent/console API
├── event stream
└── Agora callback/event ingress
            |
            v
Application services
├── session service
├── conversation service
├── case service
├── handoff service
└── integration-job service
            |
            v
Domain modules
├── deterministic conversation state machine
├── prioritized field policy
├── confirmation/correction rules
├── confidence evaluator
└── safety/escalation policy
            |
            v
Ports and adapters
├── Agora voice gateway
├── human handoff adapter
├── ticket adapter
├── repositories
└── telemetry
            |
            v
SQLite / external services
```

### Module rules

- Transport code validates input but contains no business policy.
- Domain modules do not import Flask, React, Agora SDK objects, or ticket-vendor types.
- Agora payloads are normalized by the voice adapter.
- Ticket-provider payloads are built by an adapter from the canonical case.
- The deterministic orchestrator owns workflow state; the LLM cannot confirm facts or bypass escalation.
- Safety rules override normal conversation and model output.
- Human transfer is independent of ticket success.
- All external operations use timeouts, bounded retries, idempotency, and safe error mapping.

## End-to-End Runtime

1. Caller requests a session.
2. Flask creates the local session/case and issues channel-bound, short-lived join material.
3. Caller joins an Agora RTC channel and publishes microphone audio.
4. Flask starts the Agora Conversational AI agent in the same channel.
5. Agora performs the configured ASR → LLM → TTS pipeline and delivers transcript/events through Signaling or the validated event interface.
6. EchoSphere normalizes finalized turns and applies field, confidence, and safety policy.
7. The agent asks the highest-priority missing question or confirms a critical tentative value.
8. A hard trigger or two failed focused repairs starts escalation.
9. EchoSphere commits a handoff snapshot before offering the call.
10. Human joins the channel, sees the context, accepts, and EchoSphere stops the AI agent.
11. Ticket synchronization proceeds idempotently and may retry without blocking the transfer.
12. Session closure finalizes state, audit events, and retention scheduling.

## Conversation State

```text
created -> connecting -> disclosure -> collecting <-> confirming
                                            |
                                  completing or escalating
                                                    |
                                      transferring -> human_connected
                                                    |
                                             ended / failed
```

Safety, explicit human request, or platform failure can transition from any active state to escalation. No ordinary data collection occurs after escalation begins.

## Information Model

Default priority fields:

1. intent — critical;
2. location/service area — conditional;
3. issue details — critical;
4. contact name — optional;
5. callback number — conditional and digit-confirmed;
6. preferred language — confirmed when relevant to handoff.

Critical values require explicit caller confirmation regardless of model confidence. Corrections create a new tentative version and preserve an audit link to the superseded value.

## Confidence and Escalation

Confidence combines available ASR/audio quality, intent ambiguity, per-field extraction, contradictions, repair count, silence/overlap, safety category, and system integrity. It returns bands and reason codes rather than pretending to be universal probability.

Immediate escalation occurs for:

- explicit request for a human;
- prohibited/expert-judgement subject;
- configured harm, threat, abuse, or safeguarding category;
- unresolved critical contradiction;
- system failure that makes safe automation unreliable.

Low confidence receives no more than two focused clarification attempts for the same critical need.

## Persistent Data

Planned entities cover call sessions, canonical cases, versioned fields, finalized transcript turns, confidence assessments, escalations, versioned immutable handoff snapshots, append-only audit events, ticket integration jobs, and webhook deduplication.

Raw audio is not stored. Recording is disabled. Partial transcripts are ephemeral by default. Real-data retention and residency must be approved before production.

## API Groups

- Session creation/start/end/status.
- Authorized session event stream.
- Escalation request and handoff acceptance.
- Agora event ingress.
- Supervisor-only integration retry.
- Caller and agent RTC token issuance with separate scoped capabilities.

Detailed request, response, authorization, idempotency, and error contracts live in `technical/api_contract.md`.

## Security and Privacy

- App Certificate, REST credentials, ticket secrets, and webhook secrets stay server-side.
- `.env` is ignored; `.env.example` contains placeholders only.
- Caller capabilities are bound to one session and expire.
- Agent/supervisor roles are distinct from caller access.
- Sensitive contact details and transcripts are restricted and redacted from ordinary logs.
- Recording is opt-in only through a separately approved change.
- Synthetic data is mandatory until consent, legal basis, retention, residency, and access controls are approved.

## Reliability and Operations

The system degrades toward human assistance, never toward unguarded AI. Ticket outages queue retries; console reconnect reloads server state; duplicate/out-of-order events are reconciled; Agora/model failure stops unsafe continuation and attempts the configured fallback.

Metrics cover session/agent starts, transcript gaps, language switches, repair count, safety triggers, escalation reasons, handoff latency/failure, ticket retries, and barge-in/turn latency.

## Testing Strategy

- Unit/state-model tests enforce workflow invariants.
- Adapter contract tests validate Agora and ticket boundaries.
- Flask/SQLite integration tests cover transactions and idempotency.
- Agora sandbox tests prove media, transcripts, Hindi-English behavior, interruption, and human join.
- Safety corpus covers prohibited requests and benign controls in both languages.
- Accessibility, security, failure injection, and limited load testing complete the prototype gate.

Core completion gates include zero authoritative prohibited answers, immediate escalation for every explicit human request, no duplicate ticket under retries, and a committed handoff snapshot before every tested transfer.

## Implementation Roadmap

| Phase | Outcome |
|---|---|
| 0 — Agora spike | Verified credentials, SDK/API, media, transcript events, code-switching, barge-in, browser human handoff |
| 1 — Domain foundation | Flask foundation, schema, orchestrator, confirmation, confidence, safety |
| 2 — Caller voice UI | Secure RTC session, Agora agent, transcripts, language/noise/interruption behavior |
| 3 — Handoff and ticketing | Agent console, snapshot, transfer lifecycle, ticket adapter/retry |
| 4 — Hardening | Privacy, access, observability, accessibility, resilience, full acceptance suite |

## Current Readiness and Open Decisions

Completed setup:

- GitHub repository and `main` branch configured.
- Agora CLI 0.2.8 installed and authenticated.
- Workspace bound to Agora project `echosphere`.
- RTC included, Signaling and Conversational AI enabled.
- Required Agora environment keys present locally.
- `.env` ignored and sanitized `.env.example` prepared.

Open before or during Phase 0:

- Agora CLI continues to report token capability disabled; resolve/verify before production-style access.
- Validate exact current transcript/runtime event path and authentication guarantees.
- Select/pin ASR, LLM, and TTS configuration after Hindi-English testing.
- Decide SSE versus WebSocket after console interaction proof.
- Select production identity, ticket, telephony/handoff, database, job runner, deployment, and retention policy later.

## Authoritative References

This blueprint summarizes rather than replaces the detailed documents. In a conflict: PRD controls product scope; safety policy controls prohibited runtime behavior; TRD controls technical invariants; decisions record rationale; feature registry controls implementation status; code and test evidence determine what actually works.
