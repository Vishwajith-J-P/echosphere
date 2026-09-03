# Architecture Decision Record

## Decision Index

| ID | Decision | Status | Date |
|---|---|---|---|
| D-001 | Agora is the mandatory realtime voice/conversational path | ACCEPTED | 2026-09-03 |
| D-002 | Deterministic orchestration and policy guard generative behavior | ACCEPTED | 2026-09-03 |
| D-003 | Confidence is multi-signal and explainable | ACCEPTED | 2026-09-03 |
| D-004 | Warm handoff snapshot precedes transfer and ticket sync is decoupled | ACCEPTED | 2026-09-03 |
| D-005 | SQLite prototype behind repository interfaces | ACCEPTED | 2026-09-03 |
| D-006 | Finalized transcripts only; recording off by default | ACCEPTED | 2026-09-03 |
| D-007 | Flask plus React/Jinja delivery model | ACCEPTED | 2026-09-03 |
| D-008 | Canonical documentation lives under docs | ACCEPTED | 2026-09-03 |

## D-001 — Agora Voice Path

**Decision:** Use Agora RTC and Agora Conversational AI for live caller-agent audio and conversation sessions. Backend-issued short-lived tokens protect provider credentials.

**Reasoning:** Agora use is a product constraint and its realtime media/session capabilities directly demonstrate the required interaction.

**Tradeoffs/Risks:** Vendor APIs, pricing, regions, and model/language support must be verified during implementation; a gateway isolates those changes. A fake or offline-only Agora reference does not satisfy this decision.

## D-002 — Deterministic Orchestration and Guardrails

**Decision:** A domain state machine owns required fields, priority, confirmation, repair count, safety boundaries, and escalation. Model output proposes language/content but cannot bypass policy or mark a fact confirmed.

**Reasoning:** Safety and testability require predictable transitions even when model output is uncertain.

**Alternatives:** Prompt-only control was rejected because it cannot reliably enforce confirmation and escalation invariants.

**Tradeoffs:** More orchestration code and careful reconciliation with provider conversation state.

## D-003 — Explainable Multi-Signal Confidence

**Decision:** Combine available speech/audio, intent, field, contradiction, repair, and safety signals into configurable bands and reason codes. Hard rules override numeric confidence.

**Reasoning:** A single opaque threshold cannot represent noisy audio, ambiguity, policy risks, and missing provider scores.

**Tradeoffs:** Threshold calibration requires scenario data. Scores are not exposed as certainty claims to callers.

## D-004 — Handoff Before Integration

**Decision:** Persist an immutable context snapshot before attempting transfer. Ticket creation/update runs idempotently and independently; its failure never blocks transfer.

**Reasoning:** Humans need context even during downstream outages, and caller safety takes priority over CRM consistency.

**Tradeoffs:** Eventual consistency and a retry mechanism are required.

## D-005 — SQLite Prototype

**Decision:** Use SQLite for the prototype through repository interfaces and explicit migrations.

**Reasoning:** It supports a reproducible single-service demo and relational integrity with minimal operations.

**Alternatives:** MongoDB and a managed production database are deferred until scale/deployment needs are known.

**Tradeoffs:** SQLite is not the assumed production concurrency architecture.

## D-006 — Data Minimization

**Decision:** Persist finalized transcript turns only by default; keep partials ephemeral and recording off. Retention is configurable and must be decided before real-world deployment.

**Reasoning:** The demonstration needs context preservation, not maximal surveillance.

**Tradeoffs:** Some low-level audio debugging is unavailable without explicitly enabling separately governed diagnostics.

## D-007 — Flask and React/Jinja

**Decision:** Retain Flask for APIs/application services, React/TypeScript for realtime interactive views, and Jinja for lightweight shells/static pages.

**Reasoning:** This preserves the repository's stated technical foundation while matching realtime console needs.

**Tradeoffs:** Shared visual contracts are needed across rendering modes.

## D-008 — Canonical Documentation Directory

**Decision:** Store all product, technical, execution, and architectural decision documentation under `docs/`. Keep only the repository overview and agent instructions at the root.

**Reasoning:** A single canonical hierarchy makes the complete specification discoverable and prevents scattered or duplicated documentation.

**Alternatives:** Keeping the three documentation directories at the root was functional but did not provide one documentation home. Copying files was rejected because duplicate sources would drift.

**Tradeoffs:** Existing links and agent instructions must use the new paths.

## Proposed Decisions

The following must be resolved with official vendor capability validation or deployment stakeholders before the affected production work:

- Exact Agora Conversational AI integration mode, STT/TTS/model configuration, and supported transfer bridge.
- SSE versus WebSocket for console events.
- External ticket and human-routing providers.
- Production database/job queue.
- Retention duration, consent text, data residency, and access-control provider.

## Superseded Context

The repository previously contained only generic decision templates. D-001 through D-008 establish the product-specific architecture and documentation structure and supersede unstated generic-template assumptions where they conflict.
