# Operations, Configuration, and Failure Runbook

## Environments

- **Local:** synthetic data, mock ticket/handoff allowed, Agora sandbox credentials.
- **Test/CI:** no real caller data; provider contracts mocked, optional sandbox smoke test.
- **Demo:** synthetic/demo data only, real Agora sandbox/project, protected console.
- **Production:** not approved until identity, providers, retention, consent/legal basis, residency, security review, and operational ownership are resolved.

## Configuration Inventory

| Category | Examples | Secret |
|---|---|---:|
| Agora | App ID, App Certificate, REST Customer ID/Secret, region, token TTL | Mixed |
| Models | ASR/LLM/TTS vendor, model, language, voice, credentials | Mixed |
| Policy | supported languages, confidence thresholds, repair limit, policy version | No |
| Handoff | queue mapping, wait timeout, fallback adapter | Mixed |
| Ticket | adapter, base URL, credentials, timeout/retry | Mixed |
| Data | database URL, retention periods, recording flag | Mixed |
| Web | allowed origins, secure-cookie/CSRF settings, rate limits | Mixed |
| Observability | log level, metrics endpoint, tracing exporter | Mixed |

Startup fails closed when required secrets or safe policy settings are missing. Logs print non-secret effective configuration and policy version only.

## Health

- `/health/live`: process event loop/responding; no dependency calls.
- `/health/ready`: schema current, database writable, mandatory local services ready; external provider degradation is reported separately rather than causing restart loops.
- Restricted diagnostics report Agora/ticket/handoff circuit state and last safe error category.

## Metrics and Alerts

Track session creation/start success, Agora connection/start latency, turn latency, barge-in suppression, transcript gaps, language switches, repair count, escalations by reason, handoff offer/accept/connect latency, transfer failures, ticket retries/dead letters, callback rejection/duplicates, and active sessions.

Alert candidates:

- safety-policy execution failure: immediate critical;
- handoff failures above threshold: urgent;
- Agora start/connect failures or transcript gaps above baseline: urgent;
- ticket backlog oldest age beyond target: operational;
- repeated callback authentication failures: security;
- storage/migration/retention failure: urgent.

Thresholds require load and sandbox baselines and must not be invented before measurement.

## Incident Priorities

1. Prevent unsafe AI continuation.
2. Preserve or restore human-transfer ability.
3. Preserve confirmed context and audit integrity.
4. Restore Agora/media operation.
5. Reconcile tickets and noncritical analytics.

### Agora Degradation

Stop new AI sessions when the circuit is open; do not create retry storms. Existing calls get bounded reconnect/reconciliation and then configured human/manual fallback. Record safe reason codes.

### Policy/Orchestrator Failure

Stop generated responses, communicate a brief limitation if possible, and escalate. Never fall back to an unguarded model.

### Ticket Failure

Continue handoff, persist retry job, expose “ticket pending,” retry with bounded exponential backoff/jitter, and move exhausted jobs to operator-visible failed state.

### Handoff Failure

Keep the context snapshot and caller informed without promising a connection. Use only configured fallback. The generic prototype must not invent phone numbers or emergency instructions.

### Database Failure

Do not continue collecting facts that cannot be safely persisted/confirmed. Attempt safe transfer with the minimal available ephemeral context only if the approved adapter supports it; otherwise end with a clear limitation.

## Deployment and Migration

- Apply migrations before marking the new application ready.
- Back up before destructive migrations and test rollback/forward recovery.
- Use one process for SQLite write-heavy prototype operation unless concurrency testing supports more; production scale requires revisiting D-005.
- Deploy policy/config changes with explicit version and rollback.
- Rotate secrets without committing them or exposing them to the browser.

## Privacy Operations

Before any non-synthetic data:

- approve consent/disclosure copy and legal basis;
- set transcript/case/integration/audit retention;
- document data processors and residency;
- configure role access and access review;
- test export/deletion/purge consistency;
- confirm recording remains off unless separately approved.

## Demo Readiness Checklist

- Agora project doctor passes and pinned versions are recorded.
- Synthetic Hindi/English scenario succeeds.
- Explicit human request and safety boundary tests pass.
- Human console is protected and accepts a browser-channel handoff.
- Ticket outage/retry demo creates one case only.
- No secrets or unmasked callback details appear in logs.
- Failure messages and correlation IDs are visible.
