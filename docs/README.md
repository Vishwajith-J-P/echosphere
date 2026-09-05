# EchoSphere Documentation

## Purpose

This directory is the canonical documentation set for EchoSphere. It separates product intent, technical design, execution status, and architectural rationale so planned behavior is not confused with implemented behavior.

## Current State

- **Project phase:** Phase 0 vendor spike in progress
- **Application code:** The secure session/token slice and basic React caller RTC surface exist; the feature registry is authoritative for details
- **Feature status:** F-001 is IN_PROGRESS; all other product features remain PLANNED
- **Agora account:** Authenticated through Agora CLI 0.2.8
- **Agora project:** `echosphere`, global region
- **Enabled capabilities:** RTC included, Signaling enabled, Conversational AI enabled
- **Known readiness warning:** Agora CLI reports token capability disabled; this is non-blocking for the initial spike but must be resolved before production-style access is accepted
- **Data policy:** Synthetic demo data only; recording disabled

The current slice is not evidence of a complete live voice product. Live Hindi-English speech, code-switching, transcript events, interruption latency, and browser-channel human handoff still require Agora sandbox validation.

Never add credentials, tokens, certificates, caller data, or generated secret values to documentation.

## Start Here

1. `project_blueprint.md` — concise complete system overview.
2. `product/project_requirement_document.md` — approved behavior and acceptance criteria.
3. `technical/architecture.md` — modular architecture and runtime ownership.
4. `technical/agora_integration.md` — voice platform integration contract.
5. `execution/implementation_plan.md` — build order and current work.
6. `execution/features.md` — authoritative implementation status.

7. `execution/ai_harness_contract.md` — mandatory build rules and completion gates for an implementation agent.

## Directory Structure

```text
docs/
├── README.md
├── project_blueprint.md
├── decisions.md
├── product/
│   ├── project_requirement_document.md
│   ├── app_flow.md
│   ├── ui_ux_brief.md
│   └── safety_policy.md
├── technical/
│   ├── technical_requirement_document.md
│   ├── architecture.md
│   ├── agora_integration.md
│   ├── api_contract.md
│   ├── backend_schema.md
│   └── operations.md
└── execution/
    ├── features.md
    ├── implementation_plan.md
    ├── test_plan.md
    ├── traceability.md
    └── tech_debt.md
```

## Document Ownership

| Concern | Canonical document |
|---|---|
| Product goals, scope, requirements | `product/project_requirement_document.md` |
| User/call journeys | `product/app_flow.md` |
| Voice and screen experience | `product/ui_ux_brief.md` |
| Safety behavior and escalation | `product/safety_policy.md` |
| Technical invariants and stack | `technical/technical_requirement_document.md` |
| Modules and runtime relationships | `technical/architecture.md` |
| Agora lifecycle and boundaries | `technical/agora_integration.md` |
| HTTP and internal events | `technical/api_contract.md` |
| Persistent data | `technical/backend_schema.md` |
| Configuration, deployment, incidents | `technical/operations.md` |
| What currently exists | `execution/features.md` |
| AI implementation rules and gates | `execution/ai_harness_contract.md` |
| Work sequence | `execution/implementation_plan.md` |
| Verification | `execution/test_plan.md` |
| Requirement coverage | `execution/traceability.md` |
| Intentional compromises | `execution/tech_debt.md` |
| Why architecture choices were made | `decisions.md` |

## Status Vocabulary

- **PLANNED/TODO:** Approved but not implemented.
- **IN_PROGRESS:** Code work has begun but is not fully verified.
- **COMPLETE:** Implementation and required evidence both exist.
- **BLOCKED:** Work cannot proceed because a documented dependency is unavailable.

Architecture and schema descriptions are planned contracts until the feature registry says otherwise.

## Maintenance Rules

- Update requirements before implementing new product scope.
- Update architecture and decisions when module ownership changes.
- Update schema only alongside an implemented migration, unless clearly marked planned.
- Update feature status and verification evidence after implementation.
- Add intentional shortcuts to the debt register.
- Keep traceability synchronized with requirements, features, and tests.
- Link to source documents instead of duplicating detailed rules.

## Official Agora References

These sources inform the vendor-specific setup and remain external references rather than project requirements:

- [Agora Skills](https://docs.agora.io/en/introduction/agora-skills) — official workflow guidance for selecting starters and using the Agora CLI.
- [Conversational AI quickstart](https://docs.agora.io/en/ai/get-started/quickstart) — supported CLI initialization and local run sequence.
- [Next.js agent quickstart](https://github.com/AgoraIO-Conversational-AI/agent-quickstart-nextjs) — official browser/server starter pattern; EchoSphere currently uses React/Vite while preserving the same server-controlled agent boundary.
- [Agora CLI walkthrough](https://www.youtube.com/watch?v=YGhnI5f3bp8) — supplemental CLI orientation; written docs and command output remain the verification authority.
