# Agora Integration Specification

## Status

Planned and partially vendor-validated from official documentation current on 2026-09-03. Exact SDK versions and Hindi-English provider choices remain Phase 0 deliverables.

## Role in EchoSphere

Agora supplies the realtime channel, caller/agent media transport, Conversational AI agent lifecycle, and configured ASR → LLM → TTS voice pipeline. EchoSphere supplies case state, deterministic orchestration, safety/confidence policy, human queueing, persistence, and ticketing.

Official Agora documentation states that the caller and agent join the same RTC channel; the business server starts/stops the agent, and configured models perform ASR, LLM, and TTS processing:

- https://docs.agora.io/en/ai/get-started/quickstart
- https://docs.agora.io/en/ai/build/start-stop-agent

## Credentials and Boundaries

| Credential/data | Location |
|---|---|
| Agora App ID | Server configuration; may be sent to the RTC client as required |
| App Certificate | Server secret only |
| Agora REST Customer ID/Secret | Server secret only |
| Caller RTC token | Short-lived browser capability, bound to channel/UID/role |
| Agent RTC token | Server-to-Agora configuration only |
| `agent_id` | Persisted operational reference |

Never log secrets or full tokens. Token TTL must cover expected call duration plus a small reconnect margin, with renewal implemented before expiry for longer calls.

## Provisioning and Baseline

Use Agora Console/CLI to select a project with RTC and Conversational AI enabled and run `agora project doctor --feature convoai`. The official Python agent SDK is currently installed as `agora-agents`; pin the verified version in project dependencies rather than relying on an unbounded latest release.

Start Phase 0 with Agora-managed model credentials to reduce variables. Select the production-like ASR/TTS only after testing Hindi, English, mixed utterances, digits/names, noise, and latency. “Multilingual” provider marketing is not acceptance evidence.

## Session Lifecycle

1. Backend allocates collision-resistant channel name and distinct numeric or string UIDs compatible with the selected mode.
2. Backend creates the local session/case transactionally.
3. Backend returns caller App ID/channel/UID/token plus an EchoSphere caller capability; it never returns REST credentials or App Certificate.
4. Browser joins RTC and publishes microphone audio.
5. Backend starts the Conversational AI agent with the same channel and caller UID list using the Agora Agents SDK or the v2 `join` REST endpoint.
6. Persist returned `agent_id` and reconcile local status with vendor events/status queries.
7. At completion/handoff acceptance, backend calls the SDK stop operation or v2 `leave` endpoint exactly once logically; retries are idempotent locally.
8. Browser leaves after human continuation or session end.

Official REST endpoints documented by Agora are:

```text
POST /api/conversational-ai-agent/v2/projects/{appid}/join
POST /api/conversational-ai-agent/v2/projects/{appid}/agents/{agentId}/leave
```

Do not call these directly from the browser.

## Conversation Configuration

The agent receives:

- concise AI disclosure and supported-domain instructions;
- the non-negotiable safety boundary;
- current conversation state and only the next permitted action;
- bounded history plus confirmed/tentative context;
- controlled tools or a custom orchestration endpoint;
- greeting, failure message, idle timeout, and selected ASR/TTS/LLM configuration.

Prompting is defense in depth. The backend validates all proposed field changes and tool calls. The model cannot confirm fields, raise privileges, write arbitrary tickets, or cancel escalation.

## Event Normalization

The exact Agora transcript/runtime mechanism is selected in IP-004. Whatever supported mechanism is chosen must normalize into:

| EchoSphere event | Required data |
|---|---|
| `participant.joined/left` | channel, UID, role, provider timestamp |
| `caller.turn.partial` | ephemeral text, language if available, sequence |
| `caller.turn.final` | final text, timing, confidence/audio metadata if available |
| `agent.turn.started/final/interrupted` | turn ID, spoken/final text, timing |
| `agent.status.changed` | agent ID, state, safe failure code |
| `media.quality.changed` | available quality indicators |

Vendor event names must be mapped in the adapter and must not leak into domain logic. Persist finalized turns; partials remain ephemeral by default. Store provider event IDs for deduplication and handle out-of-order delivery.

Do not claim webhook signatures, delivery order, confidence scores, or audio-quality fields until IP-004 confirms the selected interface provides them.

## Barge-In and Noise

- Configure Agora-supported interruption/turn-detection features.
- When caller speech begins during AI output, suppress/cancel obsolete output where supported.
- An interrupted AI turn records only what was observably played/finalized; unsent generated text is not presented as spoken.
- Primary-speaker/background-noise options may assist, but EchoSphere still treats ambiguous speech as low/unknown confidence and asks a focused repair.
- Measure barge-in suppression from caller speech detection to agent-audio stop.

## Human Handoff

Prototype handoff:

1. EchoSphere commits the context snapshot.
2. Authorized human joins the existing RTC channel using a server-issued agent token.
3. Console confirms context delivery and the human accepts.
4. EchoSphere stops the AI agent.
5. Caller and human remain in the RTC channel.

This is an EchoSphere composition of Agora RTC participation and agent lifecycle, not a claim of native PSTN/contact-center transfer. External telephony requires a dedicated, separately validated adapter.

## Failure and Reconciliation

- Join timeout: query status when supported before retrying to avoid duplicate agents.
- Agent starts but local response is lost: reconcile by unique session name/agent listing or documented status API.
- Event gap/out-of-order delivery: refresh authoritative session state and mark transcript gaps.
- Token nearing expiry: renew through authenticated server flow.
- Agora unavailable: bounded retry, then safe human/manual fallback; never loop indefinitely.

## Phase 0 Evidence Required

- Pinned SDK/API versions and payload fixtures.
- Working browser + Python/Flask start/stop proof.
- Hindi, English, code-switch, numeric details, noisy audio, and barge-in results.
- Verified event source, authentication, ordering, redelivery, and limits.
- Human join/AI stop transition proof.
- Recorded observed latency and failure behavior.
