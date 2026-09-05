# Architecture

## Status

Approved target architecture for the prototype. Phase 0 contains a partial implementation of the session/token path, Agora gateway, and caller RTC surface; the feature registry is the only authority for implementation status. This document must not be read as evidence that every component below exists.

## System Context

```text
Caller browser
  |  Agora RTC audio
  v
Agora Conversational AI <----server control/events----> Flask backend
                                                        |
                                                        +--> Orchestrator
                                                        +--> Safety + confidence
                                                        +--> SQLite repositories
                                                        +--> Ticket adapter
                                                        +--> Handoff adapter
                                                        |
Agent console <--------------authorized event stream----+
```

Agora Conversational AI is in the live media/conversation path, not used as a decorative or offline-only dependency.

## Backend Layers

```text
Routes / authenticated callbacks
              |
        Application services
   session | conversation | handoff
              |
 Domain policy and deterministic state machine
              |
 Ports: voice | ticket | transfer | repositories
              |
 Adapters: Agora | mock ticket | future vendor | SQLite
```

Domain code has no dependency on Flask, Agora SDK objects, React, or a ticket vendor.

## Primary Runtime Sequence

1. Caller simulator requests a session.
2. Backend creates session/case records and short-lived Agora join data.
3. Browser joins the Agora channel; backend starts the Conversational AI agent.
4. Normalized transcript/audio events feed the orchestrator.
5. The orchestrator updates tentative/confirmed fields and selects the next directive.
6. Safety and confidence policy can override normal collection and begin escalation.
7. Before transfer, the backend persists a context snapshot and queues an idempotent ticket update.
8. Human console receives the offer and context; acceptance updates the transfer state.
9. Session closure finalizes audit state while integration retry may continue independently.

For the browser prototype, human handoff is implemented by admitting an authorized human participant to the existing Agora RTC channel and stopping the AI only after acceptance/context delivery. This is a project design inference, not an asserted Agora contact-center feature. PSTN or external contact-center transfer requires a separately selected adapter.

## Failure Boundaries

- **Agora join/start failure:** show failure, attempt bounded recovery, then offer human/manual route.
- **Model/STT uncertainty:** focused repair, then escalation; never guess.
- **Persistence failure:** stop unsafe progression and surface operator failure.
- **Ticket outage:** queue retry and continue handoff.
- **Console disconnect:** state remains server-side and is recoverable on reconnect.
- **Transfer failure:** retain context, show queue failure, and provide configured manual fallback.

## Trust Boundaries

- Caller browser is untrusted.
- Agent console is authenticated and authorized.
- Vendor callbacks cross an external boundary and require verification.
- Generative model output is untrusted input to policy enforcement.
- Persisted confirmed facts require a caller-confirmation event, not model assertion.

## Ownership of State

| State | Authority |
|---|---|
| Media membership and realtime audio | Agora RTC/Conversational AI |
| Required questions and current phase | EchoSphere orchestrator |
| Confirmed/tentative facts | EchoSphere case service |
| Safety and escalation decision | EchoSphere policy engine |
| Human queue/acceptance | EchoSphere handoff adapter |
| External ticket identifier/status | Ticket adapter, mirrored locally |

If vendor and local session state disagree, the backend records the discrepancy, queries/reconciles when supported, and chooses the safer action: stop automation or escalate rather than silently continuing.

## Deployment Shape

The prototype may run as one Flask deployment plus a React bundle and SQLite database. Logical boundaries must remain so the production path can separate workers, relational storage, and realtime services without rewriting conversation policy.
