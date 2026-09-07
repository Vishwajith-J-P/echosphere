# EchoSphere

EchoSphere is a real-time Hindi-English-Tamil voice AI prototype for customer assistance, public information, and non-clinical support intake. It uses Agora Conversational AI in the live voice path, collects the minimum useful facts, confirms critical details, and transfers to a human whenever confidence or policy requires human judgement.

## Current Status

Phase 0 is in progress. A Flask API now provides durable local sessions, deterministic intake, protected operator handoff, and a controlled Agora Conversational AI gateway; a React caller page supports text fallback, Hindi/English/Tamil language selection, RTC microphone processing, transcript/fact views, and a console. Targeted backend tests, frontend tests, typecheck, build, and local Playwright workflows pass. Live sandbox speech, provider transcripts, code-switching, barge-in, and real Agora handoff are not yet verified.

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
| `docs/technical/development_setup.md` | Exact setup, environment variables, commands, and smoke checks |
| `docs/technical/api_contract.md` | Planned internal HTTP/event contracts |
| `docs/technical/backend_schema.md` | Persistent entities, migration 1, and constraints |
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

Use three PowerShell terminals. Copy `.env.example` to `.env` first and fill in the Agora credentials, `SECRET_KEY`, and HTTPS `PUBLIC_BASE_URL`. Never commit `.env`.

Terminal 1 — start Qwen through llama.cpp:

```powershell
& "D:\dev_env\llama-b9873-bin-win-vulkan-x64\llama-server.exe" `
  -m "D:\models\weights\qwen3-1.7b-q4_k_m.gguf" `
  --host 127.0.0.1 --port 8080 --ctx-size 4096
```

Terminal 2 — start the Flask backend:

```powershell
cd D:\projects\echosphere
conda activate echosphere
$env:LLAMA_CPP_URL = "http://127.0.0.1:8080"
$env:LLAMA_CPP_MODEL = "qwen3-1.7b-q4_k_m.gguf"
cd backend
python -m pip install -r requirements.txt
python run.py
```

Terminal 3 — start the React/Vite frontend:

```powershell
cd D:\projects\echosphere\frontend
npm ci
npm run dev
```

Open `http://localhost:3000`, permit microphone access, and choose **Start voice assistance**. Confirm the backend with `http://127.0.0.1:8000/health/ready` and llama.cpp with `http://127.0.0.1:8080/health`. Start only one Flask process on port `8000`; duplicate backend processes can produce inconsistent Agora startup results. Speech enters through the browser microphone and the Agora agent returns speech. The customer transcript appears in the conversation panel, and text fallback is available during an active session.

## Safety

EchoSphere is not an emergency responder or professional adviser. It must not diagnose or provide authoritative medical, legal, financial, or emergency instructions. It discloses that it is AI, labels uncertainty, and escalates instead of guessing.
