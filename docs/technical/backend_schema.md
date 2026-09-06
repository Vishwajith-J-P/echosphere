# Backend Schema

## Status and Database

The logical contract below is approved. Migration 1 is implemented locally in SQLite behind repository/service interfaces; production storage and normalized high-volume transcript tables remain later decisions. UUID strings and UTC timestamps are used.

## Entity Registry

| ID | Entity / table | Purpose |
|---|---|---|
| E-001 | `call_sessions` | Voice/conversation lifecycle |
| E-002 | `cases` | Canonical collected support case |
| E-003 | `case_fields` | Versioned tentative/confirmed facts |
| E-004 | `transcript_turns` | Finalized caller/AI/human turns |
| E-005 | `confidence_assessments` | Explainable turn/field confidence |
| E-006 | `escalations` | Escalation reason and transfer lifecycle |
| E-007 | `handoff_snapshots` | Immutable context sent to a human |
| E-008 | `audit_events` | Append-only material event history |
| E-009 | `integration_jobs` | Idempotent ticket operations/retry |
| E-010 | `processed_webhooks` | Callback deduplication |

## Shared Conventions

- IDs are application-generated UUIDv4 strings.
- Timestamps are UTC and immutable where they describe an event.
- JSON is stored as serialized text in SQLite and validated at service boundaries.
- Enumerated values are constrained in application code and database checks where practical.
- No physical deletion API is planned for individual transcript/audit rows; retention purge is a privileged case/session operation.
- Raw audio is not stored. Recording is off by default and would require a separate approved schema.
- Partial transcripts are ephemeral; only finalized turns are persisted by default.

## E-001 — Call Session

| Field | Type | Required | Description |
|---|---|---:|---|
| `id` | UUID string | Yes | Internal correlation ID |
| `provider_session_id` | string | No | Agora session/agent identifier; unique when present |
| `channel_ref` | string | No | Non-secret provider channel reference |
| `status` | enum | Yes | Session state |
| `current_language` | string | No | Current detected BCP-47 language |
| `preferred_language` | string | No | Caller-confirmed language |
| `policy_version` | string | Yes | Rules/threshold version |
| `started_at`, `ended_at` | datetime | No | Lifecycle timestamps |
| `created_at`, `updated_at` | datetime | Yes | Record timestamps |

Index `status, created_at`; unique partial index on `provider_session_id`.

`status` values are `created|connecting|disclosure|collecting|confirming|completing|escalating|transferring|human_connected|ended|failed`. Normal transitions follow the state machine in `docs/technical/architecture.md`; terminal states are `ended` and `failed`.

## E-002 — Case

| Field | Type | Required | Description |
|---|---|---:|---|
| `id` | UUID string | Yes | Canonical case ID |
| `session_id` | UUID string | Yes | Unique FK to call session |
| `status` | enum | Yes | `open|handoff_pending|human_active|closed` |
| `intent_summary` | text | No | Neutral derived summary, never a confirmed fact |
| `external_ticket_id` | string | No | Vendor identifier |
| `created_at`, `updated_at` | datetime | Yes | Record timestamps |

Delete is restricted except through retention purge. One session has one case.

## E-003 — Case Field

Each extraction/correction creates a version; previous values are not overwritten.

| Field | Type | Required | Description |
|---|---|---:|---|
| `id` | UUID string | Yes | Field-version ID |
| `case_id` | UUID string | Yes | Owning case |
| `field_name` | enum/string | Yes | Configured slot name |
| `value_text` | text | No | Normalized value |
| `source_turn_id` | UUID string | No | Originating transcript turn |
| `state` | enum | Yes | `tentative|confirmed|corrected|rejected|unresolved` |
| `confidence_band` | enum | Yes | `high|medium|low|unknown` |
| `is_current` | boolean | Yes | One current version per case/field |
| `confirmed_at` | datetime | No | Requires explicit caller confirmation event |
| `supersedes_id` | UUID string | No | Prior version |
| `created_at` | datetime | Yes | Event time |

Unique partial constraint: one `is_current = true` row per `case_id, field_name`. Callback numbers are sensitive and must be masked in standard logs/views.

## E-004 — Transcript Turn

| Field | Type | Required | Description |
|---|---|---:|---|
| `id` | UUID string | Yes | Turn ID |
| `session_id` | UUID string | Yes | Owning session |
| `sequence_no` | integer | Yes | Stable order; unique per session |
| `speaker` | enum | Yes | `caller|ai|human|system` |
| `text` | text | Yes | Finalized transcript |
| `language_code` | string | No | Detected/declared BCP-47 language |
| `started_at`, `ended_at` | datetime | No | Media timing |
| `interrupted` | boolean | Yes | AI turn was interrupted or caller barge-in occurred |
| `provider_event_id` | string | No | Trace/dedup reference |
| `created_at` | datetime | Yes | Persistence time |

Transcript text is sensitive. Index `session_id, sequence_no`.

## E-005 — Confidence Assessment

| Field | Type | Required | Description |
|---|---|---:|---|
| `id` | UUID string | Yes | Assessment ID |
| `session_id`, `turn_id` | UUID string | Yes | Context |
| `overall_band` | enum | Yes | `high|medium|low` |
| `speech_score`, `intent_score` | decimal | No | Provider/model scores when available |
| `field_scores_json` | JSON text | Yes | Per-field scores, possibly empty |
| `audio_quality` | enum | Yes | `good|degraded|poor|unknown` |
| `reason_codes_json` | JSON text | Yes | Safe explainability codes |
| `hard_escalation` | boolean | Yes | Rule override |
| `policy_version` | string | Yes | Evaluating policy |
| `created_at` | datetime | Yes | Evaluation time |

Absence of a numeric score is represented as null, never zero or implicit high.

## E-006 — Escalation

| Field | Type | Required | Description |
|---|---|---:|---|
| `id`, `session_id`, `case_id` | UUID string | Yes | Identity/context |
| `trigger` | enum | Yes | `human_request|safety|low_confidence|contradiction|system_failure|policy` |
| `reason_codes_json` | JSON text | Yes | Non-speculative reasons |
| `status` | enum | Yes | `requested|offered|accepted|connected|failed|cancelled` |
| `queue_key` | string | Yes | Configured routing key |
| `requested_at`, `accepted_at`, `connected_at` | datetime | No | Lifecycle |
| `failure_code` | string | No | Safe operational code |

Index `status, requested_at`. A partial unique index prevents more than one escalation in `requested|offered|accepted` state per session. `connected`, `failed`, and `cancelled` are terminal escalation states.

## E-007 — Handoff Snapshot

| Field | Type | Required | Description |
|---|---|---:|---|
| `id`, `escalation_id` | UUID string | Yes | Identity and owning escalation |
| `version` | integer | Yes | Monotonically increases per escalation |
| `summary_text` | text | Yes | Neutral 3–5 sentence summary |
| `confirmed_fields_json` | JSON text | Yes | Facts plus confirmation timestamps |
| `tentative_fields_json` | JSON text | Yes | Clearly unconfirmed |
| `open_questions_json` | JSON text | Yes | Missing priority data |
| `language_context_json` | JSON text | Yes | Current/preferred/history |
| `safety_flags_json` | JSON text | Yes | Observational policy categories |
| `transcript_through_sequence` | integer | Yes | Snapshot boundary |
| `created_at` | datetime | Yes | Immutable snapshot time |

Snapshots are immutable. Unique constraint: `escalation_id, version`. The transfer references the highest committed version available before acceptance; later versions are allowed only before the escalation reaches `accepted`.

## E-008 — Audit Event

| Field | Type | Required | Description |
|---|---|---:|---|
| `id`, `session_id` | UUID string | Yes | Identity/context |
| `sequence_no` | integer | Yes | Unique order per session |
| `event_type` | string/enum | Yes | Material state event |
| `actor_type` | enum | Yes | `caller|ai|human|system|vendor` |
| `payload_json` | JSON text | Yes | Redacted structured metadata |
| `created_at` | datetime | Yes | Immutable event time |

Append-only. Do not store chain-of-thought, credentials, or redundant raw transcript text.

## E-009 — Integration Job

| Field | Type | Required | Description |
|---|---|---:|---|
| `id`, `case_id` | UUID string | Yes | Identity/context |
| `adapter`, `operation` | string | Yes | Provider and `create|update` |
| `idempotency_key` | string | Yes | Unique |
| `payload_json` | JSON text | Yes | Canonical payload |
| `status` | enum | Yes | `pending|running|retry_scheduled|succeeded|failed` |
| `attempt_count` | integer | Yes | Starts at 0 |
| `next_attempt_at` | datetime | No | Retry schedule |
| `last_error_code` | string | No | Safe error category |
| `created_at`, `updated_at` | datetime | Yes | Record timestamps |

Unique `idempotency_key`; index `status, next_attempt_at`.

`payload_json` may contain sensitive case data. It uses the same access and retention controls as the case and is never written to ordinary logs.

## E-010 — Processed Webhook

| Field | Type | Required | Description |
|---|---|---:|---|
| `provider`, `event_id` | string | Yes | Composite primary/unique identity |
| `event_type` | string | Yes | Provider event type |
| `payload_hash` | string | Yes | Integrity/debug reference, not payload |
| `processed_at` | datetime | Yes | Completion time |

Retention may be shorter than case retention but must cover the provider redelivery window.

## Relationships

```text
CallSession 1---1 Case 1---* CaseField
     |  \          \---* IntegrationJob
     |   \---* ConfidenceAssessment
     +---* TranscriptTurn
     +---* AuditEvent
     +---* Escalation 1---1 HandoffSnapshot
```

## Sensitive Data

| Data | Handling |
|---|---|
| Transcript and summary | Restricted access; encrypted transport; configurable retention |
| Callback number/contact name | Mask in logs/default lists; reveal only to authorized agent |
| Provider IDs/channel refs | Operationally restricted; never credentials |
| Tokens/certificates/API keys | Never persisted in these entities |
| Confidence/safety flags | Show reasons without hidden reasoning or unsupported diagnosis |

## Retention

Prototype defaults use synthetic data only. Exact real-data periods are unresolved. Configuration must support transcript/case purge, integration payload purge after terminal synchronization, callback-dedup expiry, and audit minimization. A deployment must approve retention, legal basis/consent, residency, and deletion behavior before accepting real personal data.

## Schema Change Log

Migration 1 was implemented on 2026-09-06 for the local prototype. Migration 2 removes the obsolete operator users/sessions tables. The local console has no login state; admission counters and durable session aggregates remain local SQLite state. The logical entities above remain the contract; conversation and transcript JSON stay inside the session aggregate until production normalization.
