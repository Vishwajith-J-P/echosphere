# Development Setup and Implementation Handoff

## Purpose and Status

This is the concrete setup reference for building and running the EchoSphere prototype. It supplements the product, architecture, API, schema, and execution documents; it does not expand product scope. The repository currently contains a partial Phase 0 implementation. Use `docs/execution/features.md` to determine what is implemented.

## Repository Layout

```text
backend/
  run.py                         Flask development entry point
  requirements.txt               runtime Python dependencies
  requirements-dev.txt           test/development dependencies
  echosphere/config.py           environment configuration
  echosphere/api/routes.py       HTTP routes
  echosphere/services/           session and Agora gateway services
  tests/                         backend tests
frontend/
  package.json                   scripts and pinned JavaScript dependencies
  src/App.tsx                    caller page composition
  src/useVoiceSession.ts         browser Agora RTC lifecycle
  src/api.ts                     backend API client
  src/styles.css                 caller styling
docs/                            canonical requirements and build contract
```

Do not treat generated directories (`frontend/node_modules`, `frontend/dist`, Python caches, or pytest cache directories) as source. Do not edit generated artifacts by hand.

## Pinned Phase 0 Dependencies

The current manifests are the source of truth for installed versions:

| Area | Version |
|---|---|
| Python | 3.13 in the `echosphere` Conda environment |
| Flask | 3.1.3 |
| Agora Python agents | 2.7.2 |
| Pydantic | 2.13.5 |
| python-dotenv | 1.2.3 |
| requests | 2.34.2 |
| React / React DOM | 19.2.4 |
| TypeScript | 5.9.3 |
| Vite | 7.3.6 |
| Agora Web RTC SDK | 4.24.3 |
| Vitest | 3.2.7 |

Do not upgrade or add a provider SDK to resolve a feature gap without recording the compatibility decision in `docs/decisions.md` and the technical-debt register.

## Environment Variables

Copy `.env.example` to the location loaded by the Flask process. Values below are names and purposes only; never commit real values.

| Variable | Required for local Agora run | Meaning / safe default |
|---|---:|---|
| `AGORA_APP_ID` | Yes | Agora project App ID; may be sent to the browser as join configuration |
| `AGORA_APP_CERTIFICATE` | Yes | Server-only token signing secret; never return or log |
| `AGORA_CUSTOMER_ID` | Yes for agent control | Server-only Agora REST customer ID |
| `AGORA_CUSTOMER_SECRET` | Yes for agent control | Server-only Agora REST customer secret |
| `AGORA_REGION` | No | `global` unless the bound project requires another region |
| `AGORA_AGENT_AREA` | No | `ap` unless the project is provisioned elsewhere |
| `AGORA_TOKEN_TTL_SECONDS` | No | `3600`; use a short-lived value suitable for the demo |
| `APP_ENV` | No | `development` locally |
| `SECRET_KEY` | Yes outside tests | Random server-side signing key; never use a published example value |
| `DATABASE_PATH` | No | `instance/echosphere.sqlite3`; durable local SQLite store |
| `PUBLIC_BASE_URL` | Voice only | Public HTTPS URL used by Agora CustomLLM to call the controlled API |
| `SPEECH_PROVIDER` | No | `deepgram` fallback or `sarvam` for Sarvam STT/TTS |
| `SARVAM_API_KEY` | Sarvam only | Server-side provider credential; never expose it to the browser |

The browser may receive only the App ID, channel, UID, short-lived RTC token, expiry, and opaque caller capability. It must never receive the App Certificate, customer credentials, ticket credentials, or server signing key.

## Obtaining Credentials

1. Sign in to the [Agora Console](https://console.agora.io/) and open the EchoSphere project.
2. Copy the project **App ID** into `AGORA_APP_ID`.
3. In the project security/settings area, enable the primary **App Certificate** if it is disabled, then copy it into `AGORA_APP_CERTIFICATE`. This is the signing secret used by the backend to mint RTC tokens.
4. Open the account-level **Developer Toolkit → RESTful API** page, choose **Add a secret**, and create/download the REST credentials. Put the Customer ID in `AGORA_CUSTOMER_ID` and the Customer Secret in `AGORA_CUSTOMER_SECRET`. Agora documents that the Customer Secret may only be downloadable once, so store it securely immediately.
5. `SECRET_KEY` is not an Agora credential. Generate a long random value locally for Flask session/signing protection with a cryptographically secure generator, and place it only in the root `.env` file.

The Customer ID/Secret authenticate Agora REST API calls; they are separate from the project App ID/App Certificate. Never paste any of these values into chat, source control, browser code, screenshots, or issue comments. See the [Agora Console REST API reference](https://github.com/AgoraIO/docs-portal/blob/main/content/docs/en/api-reference/api-ref/console/solutions-agora-console-rest-api.md) for the authentication distinction.

## Local Commands

From the repository root, use two terminals.

Backend:

```powershell
conda activate echosphere
cd backend
python -m pip install -r requirements.txt
python run.py
```

Frontend:

```powershell
cd frontend
npm ci
npm run dev
```

The caller is voice-only. It requires the Agora values, `PUBLIC_BASE_URL`, and the selected provider credentials; there is no local text-only mode.

The browser caller is served by Vite. The backend URL and allowed origin must match the local configuration used by the current frontend. Never expose the Flask development server or an Agora secret endpoint publicly.

## Required Verification Commands

Run these before claiming a change is complete:

```powershell
cd backend
python -m pytest -p no:cacheprovider
cd ..\frontend
npm run typecheck
npm run build
npm test
npm run test:e2e
```

Provider-dependent behavior additionally requires the Agora sandbox evidence listed in `docs/execution/test_plan.md`; mocked gateway tests do not prove live speech or multilingual behavior.

## Phase 0 Smoke Checks

With valid server credentials and both processes running:

1. `GET /health/live` returns a process-health response without contacting Agora.
2. `GET /health/ready` reports local readiness and a safe provider degradation state if Agora is unavailable.
3. `POST /api/sessions` returns `201`, a session ID, short-lived RTC join data, and an opaque caller capability; no server secret appears.
4. `POST /api/sessions/{id}/start` returns an idempotent start response.
5. The browser joins the channel, publishes microphone audio, and can end the session.
6. Repeating start/end does not create a second logical operation.

Live transcript, code-switching, barge-in, noise repair, human join, ticket retry, and console behavior remain later-phase checks.

## Prototype Defaults for Unresolved Choices

Use these defaults unless a documented decision replaces them:

- ticket system: local/mock adapter;
- human transfer: authorized human joins the existing Agora RTC channel;
- console events: SSE after the event contract is validated;
- persistence: SQLite behind repository interfaces;
- recording: disabled;
- transcript retention: finalized turns only, synthetic data;
- supported languages: Hindi (`hi-IN`), English (`en-IN`), and Tamil (`ta-IN`);
- caller authentication: one short-lived capability bound to one session;
- operator authentication: none for the local console.

These defaults are for a demonstrable prototype. They do not authorize production deployment or domain-specific advice.

## Implementation Guardrails

- Keep Agora SDK objects inside the Agora gateway and browser media hook; domain policy must run without Agora.
- Treat all model/provider output as untrusted proposals.
- Never confirm a critical field without an explicit caller confirmation event for its current version.
- Stop ordinary questioning once escalation begins.
- Commit the handoff snapshot before attempting transfer; ticket failure cannot block transfer.
- Add or update tests and evidence before changing a feature from `PLANNED`/`IN_PROGRESS` to `COMPLETE`.
- Update the relevant docs after every contract, schema, architecture, or intentional-debt change.

## Missing Context That Does Not Block the Prototype

Production ticket vendor, telephony/PSTN provider, identity provider, database/job runner, retention period, consent wording, data residency, and final confidence thresholds are intentionally unresolved. The prototype must use the defaults above and keep these decisions isolated behind adapters/configuration. Ask the project owner only when selecting one of these for production would materially change the approved architecture or safety behavior.
