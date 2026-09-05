# AI Harness Build Contract

## Purpose

This file is an execution contract for any AI agent or developer implementing EchoSphere. It removes ambiguity between the approved design and the partial Phase 0 implementation. Follow it together with `AGENTS.md`; the more specific product safety rule wins over a generic implementation preference.

## Authority Order

When documents disagree, use this order:

1. `docs/product/safety_policy.md` for prohibited output and escalation precedence.
2. `docs/product/project_requirement_document.md` for approved product scope and acceptance criteria.
3. `docs/technical/technical_requirement_document.md` for technical invariants.
4. `docs/technical/architecture.md`, `docs/technical/agora_integration.md`, and `docs/technical/backend_schema.md` for approved design contracts.
5. `docs/execution/features.md` for what is actually implemented.
6. `docs/execution/test_plan.md` and `docs/execution/traceability.md` for required evidence.
7. `docs/decisions.md` for rationale and unresolved choices.

If code conflicts with a higher-authority document, stop and record the discrepancy. Do not silently reinterpret the requirement.

## Non-negotiable Scope

- Build a browser-simulated support intake line for synthetic data.
- Use Agora RTC and Agora Conversational AI for every AI voice session.
- Support Hindi, English, and code-switching only after provider validation.
- Collect minimum case fields, keep extracted values tentative, and explicitly confirm critical values.
- Escalate immediately for a human request, safety/expert-judgement need, or unsafe system failure.
- Escalate after at most two focused repairs for one unresolved critical need.
- Preserve a handoff snapshot before transfer; ticket synchronization must never block transfer.
- Keep confirmed, tentative, corrected, rejected, and unresolved values distinct.

Do not add PSTN, emergency dispatch, medical/legal/financial advice, identity proofing, payments, autonomous case resolution, production compliance claims, or unapproved languages.

## Current Implementation Boundary

Treat F-001 as `IN_PROGRESS`. The existing slice proves only the server-issued session/token flow, Agora gateway lifecycle contract, and basic caller RTC surface. It does not prove live speech, transcript delivery, Hindi-English quality, barge-in, noise resilience, human handoff, ticketing, or console behavior. Do not mark those capabilities complete based on mocked tests or documentation alone.

## Required Build Sequence

1. Read all files listed in `AGENTS.md` before changing a feature.
2. Inspect `docs/execution/features.md` and the current code before selecting work; do not duplicate an existing slice.
3. Resolve any `PROPOSED`, `UNRESOLVED`, or vendor-dependent choice in `docs/decisions.md` before coding against it.
4. Implement one feature at a time behind the boundaries in the architecture document.
5. Add deterministic tests for policy and state before relying on a live model/provider.
6. Run the mapped checks in `docs/execution/test_plan.md`.
7. Record evidence, update `features.md`, and update traceability. Mark `COMPLETE` only when required automated and live/manual evidence exists.
8. Update schema, decisions, or technical debt only when the corresponding contract or intentional compromise changed.

## Safety Stop Conditions

Stop ordinary collection and escalate when any of these occurs: explicit human request; medical, legal, financial, emergency, safeguarding, threat, self-harm, or other trained-judgement content; unresolved critical contradiction; provider/session failure that makes safe continuation unreliable; or the second failed focused repair. Never provide substantive authoritative advice before transfer.

## Data and Security Rules

- Synthetic data only until retention, consent, residency, and access governance are approved.
- Never place App Certificates, REST credentials, ticket secrets, raw tokens, or unredacted callback numbers in browser code, logs, tests, or documentation.
- Persist finalized transcript turns only; partials are ephemeral by default and recording is off.
- A model proposal is untrusted input. Only the deterministic orchestrator can change workflow state; only an explicit caller confirmation can confirm a critical field.
- All external mutations are bounded, idempotent, and safe under duplicate delivery.

## Completion Checklist

Before claiming a feature is complete, verify: acceptance criteria mapped; tests pass; safety regression passes; failure behavior is bounded; required evidence is linked; docs are updated; and the implementation status agrees with the actual code. If any item is missing, leave the feature `PLANNED` or `IN_PROGRESS` and state the gap.
