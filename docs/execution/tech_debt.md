# Technical Debt Register

## Status

No implementation exists, so no intentional implementation debt has been introduced.

| ID | Area | Summary | Severity | Status |
|---|---|---|---|---|
| None | — | — | — | — |

## Risks That Are Not Yet Technical Debt

These are planning risks or unresolved decisions, not debt:

- quantitative confidence thresholds need representative Hindi/English noisy-call calibration;
- Agora model/voice/language and transfer capabilities need validation against current official APIs;
- production ticket, identity, routing, database, job-runner, retention, consent, and residency choices are unresolved;
- SQLite is intentionally a prototype choice under D-005, not debt until production requirements demand otherwise.

If implementation accepts a known shortcoming—for example in-memory retries, demo-only authentication, or incomplete redaction—it must be recorded here with owner, impact, remediation, and revisit trigger.
