# EchoSphere

EchoSphere is a planned real-time Hindi-English voice AI prototype for customer assistance, public information, and non-clinical support intake. It uses Agora Conversational AI in the live voice path, collects the minimum useful facts, confirms critical details, and transfers to a human whenever confidence or policy requires human judgement.

## Current Status

Documentation baseline complete; application implementation has not started. Every capability in `execution/features.md` remains `PLANNED`.

## Documentation Map

| Document | Authority |
|---|---|
| `product/project_requirement_document.md` | Approved scope, requirements, acceptance criteria |
| `product/app_flow.md` | Caller, agent, safety, and failure journeys |
| `product/ui_ux_brief.md` | Voice and console experience rules |
| `product/safety_policy.md` | Prohibited behavior, escalation precedence, response rules |
| `technical/technical_requirement_document.md` | Technical constraints and invariants |
| `technical/architecture.md` | Components, trust boundaries, runtime ownership |
| `technical/agora_integration.md` | Agora responsibilities and lifecycle |
| `technical/api_contract.md` | Planned internal HTTP/event contracts |
| `technical/backend_schema.md` | Planned persistent entities and constraints |
| `technical/operations.md` | Configuration, deployment, monitoring, incident behavior |
| `execution/features.md` | Actual feature implementation status |
| `execution/implementation_plan.md` | Ordered implementation work |
| `execution/test_plan.md` | Verification strategy and test scenarios |
| `execution/traceability.md` | Requirements-to-feature/test mapping |
| `execution/tech_debt.md` | Intentional implemented compromises |
| `decisions.md` | Accepted and proposed architectural decisions |

## Source-of-Truth Rules

Product intent comes from the PRD; technical constraints come from the TRD; architecture and schema describe approved planned design; `features.md` alone reports what currently exists. If code and documentation later disagree, record and resolve the discrepancy rather than silently changing one side.

## First Implementation Step

Run Phase 0/IP-001 and IP-004: validate the current Agora Python SDK/REST lifecycle, Hindi-English speech configuration, interruption behavior, transcript/event delivery, and browser-channel human handoff in an Agora sandbox.

## Safety

EchoSphere is not an emergency responder or professional adviser. It must not diagnose or provide authoritative medical, legal, financial, or emergency instructions. It discloses that it is AI, labels uncertainty, and escalates instead of guessing.
