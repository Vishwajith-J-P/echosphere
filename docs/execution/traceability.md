# Requirements Traceability

## Current implementation evidence (2026-09-06)

The supported language contract is `hi-IN`, `en-IN`, and `ta-IN`. Voice-provider transcripts exercise deterministic confirmation, correction, and escalation for all three; `SPEECH_PROVIDER=sarvam` selects Sarvam STT/TTS for the Indian-language voice path, while the documented Deepgram/MiniMax fallback remains available. Local browser coverage verifies the voice-only caller surface against an in-process fixture. Live Agora media, provider transcript events, interruption latency, and real browser-channel handoff remain open evidence items.

Operator-console verification covers direct local console access with no login flow; migration 2 removes legacy account storage.

## Matrix

| Requirement | Feature(s) | Flow(s) | Planned verification |
|---|---|---|---|
| FR-001 AI disclosure/human option | F-001, F-009 | FLOW-001 | TS-004, UI accessibility |
| FR-002 Agora live audio | F-001 | FLOW-001 | Agora contract + sandbox E2E |
| FR-003 Hindi/English/Tamil code-switching | F-002 | FLOW-006 | TS-001, local Tamil browser flow |
| FR-004 Barge-in | F-003 | FLOW-002 | TS-002, latency gate |
| FR-005 Prioritized collection | F-004 | FLOW-001 | Unit/state-model, TS-001 |
| FR-006 One short question/no repeats | F-004 | FLOW-001 | Policy unit tests |
| FR-007 Tentative extraction | F-004, F-005 | FLOW-001 | Core invariants 1–2 |
| FR-008 Confirmation/correction | F-005 | FLOW-001 | TS-003 |
| FR-009 Uncertainty/safety detection | F-003, F-006 | FLOW-002, FLOW-004 | TS-001, TS-005 |
| FR-010 Escalation rules | F-006, F-007 | FLOW-003, FLOW-004 | Invariants 3–5 |
| FR-011 Context-preserving handoff | F-007 | FLOW-003 | TS-001, invariant 6 |
| FR-012 Ticket adapter/idempotency | F-008 | FLOW-003, FLOW-005 | TS-006, invariant 7 |
| FR-013 Agent/supervisor console | F-009 | FLOW-005 | E2E + accessibility |
| FR-014 Audit trail | F-010 | All material flows | Integration/state reconstruction |
| FR-015 Fact/inference distinction | F-005, F-006, F-009 | FLOW-001, FLOW-003 | TS-001, TS-003, UI review |
| FR-016 Correction/language/refusal/human | F-002, F-004, F-005, F-007 | FLOW-001–003, FLOW-006 | TS-001, TS-003, TS-004 |

## Acceptance Criteria Coverage

The [limitation remediation plan](implementation_plan.md#limitation-remediation-plan) maps fixes to existing tasks/features: gates 1/3 cover FR-002–FR-004 and AC-001/002; gate 2 covers FR-005–FR-010, FR-015/016 and AC-003/004/005; gates 4/5 cover FR-011–FR-014 and AC-001/005; gate 6 validates cross-cutting non-functional requirements. These mappings supplement the matrix and do not assert passed tests.

| Acceptance criterion | Primary scenarios |
|---|---|
| AC-001 Hindi/English noisy call | TS-001, TS-006 |
| AC-002 Interruption | TS-002 |
| AC-003 Safety boundary | TS-005 |
| AC-004 Correction | TS-003 |
| AC-005 Human request | TS-004 |

## Status Rule

Implementation guidance: [Voice gap resolution](../technical/gap_resolution.md) covers FR-002/003/004/009/010/011/012 and maps delivery gates to existing IP tasks. TS-001 must explicitly cover Hindi digit normalization and uncertain speaker attribution; TS-002 must cover stale response cancellation; TS-005 must verify policy before speech; TS-006 must include competing handoff acceptance, failed human join, and ticket timeout after remote success.

This matrix records planned coverage, not proof. Evidence links are added only after implementation. Feature status remains authoritative in `docs/execution/features.md`.
