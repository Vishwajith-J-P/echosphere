# Application Flow

## Actors

- **Caller:** joins a browser-simulated support call.
- **Human agent:** accepts escalations and continues the conversation.
- **Supervisor:** monitors sessions and retries failed integrations.
- **Agora service:** supplies realtime voice/conversational events.

## Route Registry

| ID | Method | Route | Rendering/Access | Purpose |
|---|---|---|---|---|
| R-001 | GET | `/` | Jinja/Public | Prototype overview and entry choices |
| R-002 | GET | `/demo/call` | React/Public demo | Caller simulator |
| R-003 | GET | `/console` | React/Agent | Live queue and session workspace |
| R-004 | POST | `/api/sessions` | API/Public demo, rate-limited | Create voice session/join data and caller capability |
| R-005 | POST | `/api/sessions/{id}/start` | API/Caller capability | Start AI agent idempotently |
| R-006 | POST | `/api/sessions/{id}/end` | API/Caller capability or agent | End call |
| R-007 | GET | `/api/sessions/{id}` | API/Authorized | Read context |
| R-008 | GET | `/api/sessions/{id}/events` | API/Authorized | Live events |
| R-009 | POST | `/api/sessions/{id}/escalations` | API/Authorized | Request escalation |
| R-010 | POST | `/api/sessions/{id}/handoff/accept` | API/Agent | Accept transfer |
| R-011 | POST | `/api/webhooks/agora` | API/Vendor | Ingest verified events |
| R-012 | POST | `/api/integration-jobs/{id}/retry` | API/Supervisor | Retry ticket sync |

Routes are planned and not implemented.

## FLOW-001 — Standard Assisted Intake

1. Caller opens the simulator, grants microphone access, and starts.
2. System establishes Agora media and introduces itself as an AI.
3. AI states it can transfer to a person and asks an open intent question.
4. Caller may answer in Hindi, English, Tamil, or code-switch among them.
5. System extracts supplied fields as tentative, selects the highest-priority missing field, and asks one short question.
6. Critical facts are read back in the caller's current language.
7. Caller confirms or corrects them. Corrections are reconfirmed.
8. If the bounded task can be completed safely, the system summarizes, creates/updates the case, and ends.
9. If human judgement or low confidence applies, FLOW-003 begins.

## FLOW-002 — Noise, Misunderstanding, and Interruption

1. If the caller speaks during AI playback, playback stops/ducks and the caller turn takes precedence.
2. If audio or interpretation is unclear, the AI identifies the uncertain part and asks a focused repair question.
3. Background or overlapping speech is never promoted to a confirmed fact solely from inference.
4. A second failed clarification for a required critical detail triggers handoff.
5. Silence gets a gentle check-in; repeated timeout triggers handoff or graceful end according to queue availability.

## FLOW-003 — Human Escalation

Triggers include explicit human request, safety boundary, unresolved contradiction, low confidence after repairs, policy requirement, or system integrity failure.

1. Stop all nonessential questions.
2. Tell the caller why a person is being brought in using neutral, non-alarming language.
3. Persist a snapshot: confirmed facts, tentative facts, unanswered questions, language, reason codes, summary, and transcript reference.
4. Start ticket sync independently.
5. Offer the transfer to the appropriate human queue. In the browser prototype this means an authorized human joins the existing Agora channel; external/PSTN transfer requires a future adapter.
6. Agent reviews context and accepts.
7. The authorized agent uses the same website's operator workspace to join the existing Agora channel with a scoped human token; the AI agent is stopped before the caller is told the human is connected.
8. Connect human and caller; mark the AI as no longer authoritative in the dialogue.
9. If transfer fails, retain context and use the configured manual fallback. Ticket failure never blocks the transfer.

## FLOW-004 — Safety Boundary

1. Policy detects a medical, legal, financial, emergency, safeguarding, or other expert-judgement request.
2. AI does not answer it as authoritative advice.
3. AI says it is not qualified to provide that guidance and initiates escalation.
4. The handoff notes the caller's own statement and the policy category without diagnosis or unsupported conclusions.

## FLOW-005 — Agent Console

1. Agent opens the authenticated console and sees queued/active calls.
2. Agent selects an escalation and sees language, reason, summary, confirmed/tentative fields, open questions, transcript, and ticket status.
3. Agent accepts the call or leaves it in queue according to permissions.
4. Supervisor may retry a failed ticket job without duplicating the case.

## FLOW-006 — Hindi-to-English Example

1. AI greets and discloses itself; caller begins in Hindi.
2. Caller switches to English while giving an incomplete issue and background speakers overlap.
3. AI follows the caller's language, preserves clear details as tentative, and asks only for the missing priority item.
4. AI repeats critical details; unclear details are explicitly identified and repaired.
5. After two failed repairs or a judgement boundary, AI transfers.
6. Agent receives a bilingual-safe concise summary, language history, confirmed facts, tentative fragments, and the next unanswered question.

## UI States and Failure Paths

- **Caller:** idle, permission request, connecting, AI speaking, listening, reconnecting, transferring, human connected, ended, error.
- **Console:** loading, empty queue, active, low confidence, safety escalation, accepted, transfer failure, ticket pending/failed/synced.
- Microphone denial provides corrective browser guidance.
- Agora failure never displays secrets or raw vendor errors.
- Unauthorized console/API access returns 401/403.
- Unknown sessions return 404 without leaking whether unrelated identifiers exist.
- Unexpected failures use a safe message and correlation ID.

## Flow Dependencies

| Flow | Depends On |
|---|---|
| FLOW-001 | Agora session, orchestration, transcript |
| FLOW-002 | Barge-in, confidence policy |
| FLOW-003 | Handoff service, context snapshot, ticket adapter |
| FLOW-004 | Safety policy, FLOW-003 |
| FLOW-005 | Access control, live event stream |

## Change Log

**2026-09-03:** Replaced template flow placeholders with the planned EchoSphere call and handoff journeys.
