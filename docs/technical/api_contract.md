# Planned API and Event Contract

## Conventions

- Base path: `/api`; JSON UTF-8.
- IDs are opaque UUID strings.
- Timestamps are UTC ISO-8601.
- Every response carries `X-Correlation-ID`; clients may submit one but the server validates/replaces unsafe values.
- Error body: `{"error":{"code":"SAFE_CODE","message":"user-safe text","correlation_id":"..."}}`.
- Retryable mutations accept `Idempotency-Key`; reuse with a different body returns conflict.
- Browser cookies, if used for console authentication, require Secure, HttpOnly, SameSite and CSRF controls.
- Unknown resources return 404 without cross-tenant information.

## Roles

| Role | Authority |
|---|---|
| Public demo | Create a rate-limited synthetic-data session only |
| Caller capability | Start/end/read one bound session and request a human |
| Agent | Read queue/context, accept a handoff, join assigned channel |
| Supervisor | Agent rights plus integration retry and diagnostics |
| Agora callback | Submit only documented vendor events through verified server endpoint |

## Endpoints

### `POST /api/sessions`

Creates local session/case and returns RTC join material.

Request:

```json
{"requested_language":"hi-IN","client":{"platform":"web"}}
```

Response `201`:

```json
{
  "session_id":"uuid",
  "caller_capability":"opaque-secret",
  "rtc":{"app_id":"...","channel":"...","uid":"1002","token":"short-lived","expires_at":"..."},
  "status":"created"
}
```

The capability and RTC token are secrets and must not be persisted by browser storage beyond the active session.

### `POST /api/sessions/{id}/start`

Caller capability required. Idempotently starts the Agora agent. Returns `202` with local status; a repeated matching request returns the existing operation/session state.

### `POST /api/sessions/{id}/end`

Caller capability or agent required. Idempotently ends automation/media participation as appropriate. Returns `202` while provider reconciliation completes.

### `GET /api/sessions/{id}`

Caller receives minimal own-session status; agent/supervisor receives authorized case context. Sensitive values are masked according to role.

### `GET /api/sessions/{id}/events`

Authorized SSE stream is the default proposed console transport:

```text
id: session-sequence
event: case.field.updated
data: {"session_id":"...","sequence":17,"field":{"name":"intent","state":"confirmed"}}
```

Clients reconnect with `Last-Event-ID`; the server either replays retained safe UI events or instructs a snapshot refresh. WebSocket replaces SSE only through an accepted decision.

### `POST /api/sessions/{id}/escalations`

Caller or authorized operator requests escalation.

```json
{"trigger":"human_request"}
```

The caller may only submit `human_request`; server policy supplies all other triggers. Returns the existing active escalation on retry.

### `POST /api/sessions/{id}/handoff/accept`

Agent-only, requires handoff version:

```json
{"escalation_id":"uuid","snapshot_version":1}
```

Returns RTC join material for that authorized agent and moves the escalation atomically to accepted. A stale snapshot returns `409 STALE_HANDOFF_SNAPSHOT`.

### `POST /api/sessions/{id}/messages`

The assigned human may send an optional text fallback after the handoff is connected:

```json
{"text":"I am reviewing the details now."}
```

The message is appended to the session transcript as a human turn. Voice through Agora remains the primary channel.

### `POST /api/queue/clear`

Local supervisor-console action. Marks all pending handoffs as cancelled, keeps their session and audit history, and removes them from the active queue. Ended sessions are excluded automatically from queue reads.

### `POST /api/webhooks/agora`

Accepts only the selected Agora event format. The adapter authenticates with documented controls, validates size/schema/freshness where available, deduplicates provider event ID, stores a payload hash, and acknowledges duplicates safely. Raw payload retention is off by default.

### `POST /api/integration-jobs/{id}/retry`

Supervisor-only. Valid only for failed/retryable jobs and reuses the original idempotency key. It never directly creates a second case.

## Domain Event Vocabulary

| Event | Meaning |
|---|---|
| `session.state.changed` | Valid lifecycle transition |
| `transcript.turn.finalized` | Persisted finalized turn |
| `language.changed` | Detected conversational language changed; not necessarily preferred language |
| `case.field.proposed` | New tentative field version |
| `case.field.confirmed` | Caller explicitly confirmed current version |
| `case.field.corrected` | Prior version superseded; replacement remains tentative |
| `confidence.assessed` | Band and safe reason codes recorded |
| `safety.triggered` | Hard policy category activated |
| `escalation.requested` | Handoff workflow created |
| `handoff.snapshot.created` | Immutable transfer context version committed |
| `handoff.accepted/connected/failed` | Transfer lifecycle |
| `ticket.sync.succeeded/failed` | External integration outcome |

Events carry session ID, monotonic local sequence, event ID, timestamp, actor type, schema version, and redacted payload.

## Error Categories

`VALIDATION_ERROR`, `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `RATE_LIMITED`, `STATE_CONFLICT`, `STALE_HANDOFF_SNAPSHOT`, `AGORA_UNAVAILABLE`, `TRANSFER_UNAVAILABLE`, `INTEGRATION_RETRYABLE`, and `INTERNAL_ERROR`.

Raw provider errors are mapped to safe codes and retained only in restricted diagnostics when necessary.

## Versioning

The prototype uses an unversioned `/api` while internal. Before an external client contract is published, adopt `/api/v1`. Additive optional fields are compatible; removing/renaming fields or changing semantics requires a versioned contract and migration plan.
