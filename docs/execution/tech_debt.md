# Technical Debt Register

## Status

The Phase 0 spike intentionally carries the bounded compromises below. None is acceptable for production deployment.

| ID | Area | Summary | Severity | Status |
|---|---|---|---|---|
| TD-001 | Persistence | Prototype now persists sessions/capabilities in SQLite, but schema normalization, backup, and multi-process locking are not production-ready | High | OPEN |
| TD-002 | Agora client | RTM transcript/toolkit dependencies are deferred because tested peer requirements conflict with RTC 4.24.3 | High | OPEN |
| TD-003 | Frontend performance | Agora RTC is bundled eagerly, producing a 1.73 MB minified initial chunk | Medium | OPEN |
| TD-004 | Vendor compatibility | `agora-agents` emits Pydantic v2 deprecation/config warnings under the pinned environment | Low | OPEN |

## Remediation

- TD-001: add migrations/backup/operational locking and normalize transcript/case records before production recovery claims.
- TD-002: validate a mutually supported RTC/RTM/toolkit matrix in IP-004; do not use `--force` or `--legacy-peer-deps` as the resolution.
- TD-003: lazy-load the RTC session module and measure the post-split caller startup path in Phase 2.
- TD-004: track an upstream-compatible Agora Agents release or pin a supported Pydantic range after contract tests.

## Planning Risks (Not Yet Debt)

- Quantitative confidence thresholds need representative Hindi/English/Tamil noisy-call calibration.
- Agora managed model/voice/language and transfer capabilities need live validation.
- Production ticket, identity, routing, database, job-runner, retention, consent, and residency choices are unresolved.
- SQLite remains the approved prototype persistence choice under D-005.
