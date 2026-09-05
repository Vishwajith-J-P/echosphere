# EchoSphere

EchoSphere is a real-time Hindi-English voice AI prototype for customer assistance, public information, and non-clinical support intake. It uses Agora Conversational AI in the live voice path, collects the minimum useful facts, confirms critical details, and transfers to a human whenever confidence or policy requires human judgement.

## Current Status

Phase 0 is in progress. A Flask API now issues scoped Agora session credentials and controls a Conversational AI agent through a provider gateway; a React caller page joins Agora RTC, publishes noise-processed microphone audio, plays the remote agent, and ends the session. Automated API tests and the production web build pass. Live sandbox speech, transcripts, code-switching, barge-in, and handoff are not yet verified.

## Documentation Map

| Document | Authority |
|---|---|
| `docs/README.md` | Documentation index, ownership, and reading paths |
| `docs/project_blueprint.md` | Consolidated project, stack, modules, and delivery summary |
| `docs/product/project_requirement_document.md` | Approved scope, requirements, acceptance criteria |
| `docs/product/app_flow.md` | Caller, agent, safety, and failure journeys |
| `docs/product/ui_ux_brief.md` | Voice and console experience rules |
| `docs/product/safety_policy.md` | Prohibited behavior, escalation precedence, response rules |
| `docs/technical/technical_requirement_document.md` | Technical constraints and invariants |
| `docs/technical/architecture.md` | Components, trust boundaries, runtime ownership |
| `docs/technical/agora_integration.md` | Agora responsibilities and lifecycle |
| `docs/technical/api_contract.md` | Planned internal HTTP/event contracts |
| `docs/technical/backend_schema.md` | Planned persistent entities and constraints |
| `docs/technical/operations.md` | Configuration, deployment, monitoring, incident behavior |
| `docs/execution/features.md` | Actual feature implementation status |
| `docs/execution/ai_harness_contract.md` | Mandatory implementation-agent rules and completion gates |
| `docs/execution/implementation_plan.md` | Ordered implementation work |
| `docs/execution/test_plan.md` | Verification strategy and test scenarios |
| `docs/execution/traceability.md` | Requirements-to-feature/test mapping |
| `docs/execution/tech_debt.md` | Intentional implemented compromises |
| `docs/decisions.md` | Accepted and proposed architectural decisions |

## Source-of-Truth Rules

Product intent comes from the PRD; technical constraints come from the TRD; architecture and schema describe approved planned design; `features.md` alone reports what currently exists. If code and documentation later disagree, record and resolve the discrepancy rather than silently changing one side.

## Run the Current Slice

```powershell
conda activate echosphere
cd backend
python run.py
```

In a second terminal:

```powershell
conda activate echosphere
cd frontend
npm run dev
```

Open the Vite URL, permit microphone access, and start a session. Copy `.env.example` to `.env` and provide server-side Agora credentials first. Never commit `.env`. Remaining Phase 0 work is live sandbox validation of speech configuration, transcripts/events, interruption, and browser-channel human handoff.

## Safety

EchoSphere is not an emergency responder or professional adviser. It must not diagnose or provide authoritative medical, legal, financial, or emergency instructions. It discloses that it is AI, labels uncertainty, and escalates instead of guessing.
