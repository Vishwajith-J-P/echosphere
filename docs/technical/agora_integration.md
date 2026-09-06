# Agora Integration Specification

## Status

Partially implemented and vendor-validated as of 2026-09-06. Voice is the primary caller path: the browser publishes microphone audio, Agora Conversational AI performs speech recognition/response synthesis, and the browser subscribes to the agent audio. The server uses `agora-agents` 2.7.2 and the browser uses `agora-rtc-sdk-ng` 4.24.3. Secure token creation, durable local lifecycle tests, and a controlled CustomLLM endpoint pass locally; live Hindi-English-Tamil model/voice behavior remains unverified.

## Role in EchoSphere

Agora supplies the realtime channel, caller/agent media transport, Conversational AI agent lifecycle, and configured ASR → LLM → TTS voice pipeline. EchoSphere supplies case state, deterministic orchestration, safety/confidence policy, human queueing, persistence, and ticketing.

Official Agora documentation states that the caller and agent join the same RTC channel; the business server starts/stops the agent, and configured models perform ASR, LLM, and TTS processing:

- https://docs.agora.io/en/ai/get-started/quickstart
- https://docs.agora.io/en/ai/build/start-stop-agent

The setup workflow was cross-checked against the official [Agora Skills](https://docs.agora.io/en/introduction/agora-skills) guidance, the [Agora Conversational AI quickstart](https://docs.agora.io/en/ai/get-started/quickstart), the [Agora Next.js agent quickstart](https://github.com/AgoraIO-Conversational-AI/agent-quickstart-nextjs), and the supplemental [Agora CLI walkthrough](https://www.youtube.com/watch?v=YGhnI5f3bp8). The written documentation and observed CLI output are the verification authority; the video is orientation only.

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

The researched implementation path, repository candidates, model-identifier compatibility warning, and live gates are in [Voice gap resolution](gap_resolution.md). This is the required companion for IP-003/IP-004 and IP-023/IP-024. Candidate source code is not evidence of working product behavior.

The initial gateway configures managed Deepgram STT (`nova-3`, multilingual), OpenAI (`gpt-4o-mini`), and MiniMax TTS (`speech-2.6-turbo`) identifiers to reduce credential variables. These exact identifiers and the selected voice are implementation hypotheses until a live agent starts successfully.

The tested combination of `agora-rtm` 2.2.3 and `agora-agent-client-toolkit` 1.2.0 has incompatible RTC peer constraints, so neither is installed in the Phase 0 browser baseline. IP-004 must select a compatible, officially supported version matrix before transcript/event code is added.

Use Agora Console/CLI to select a project with RTC and Conversational AI enabled and run `agora project doctor --feature convoai`. The official Python agent SDK is currently installed as `agora-agents`; pin the verified version in project dependencies rather than relying on an unbounded latest release.

Start Phase 0 with Agora-managed model credentials to reduce variables. For the Indian-language path, `SPEECH_PROVIDER=sarvam` selects Sarvam STT (`saaras:v3`) and Sarvam TTS (`priya`) through the Agora agent; the default Deepgram/MiniMax path remains available. Select the production-like ASR/TTS only after testing Hindi, English, Tamil, mixed utterances, digits/names, noise, and latency. “Multilingual” provider marketing is not acceptance evidence.

## Session Lifecycle

1. Backend allocates collision-resistant channel name and distinct numeric or string UIDs for the voice channel.
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
2. Authorized human reviews the snapshot and atomically accepts its version.
3. Backend issues agent join data; human joins the existing RTC channel and media readiness is verified.
4. EchoSphere stops/reconciles the AI agent; ordinary AI collection remains suppressed throughout escalation.
5. Mark human connected after media readiness and AI shutdown/suppression are observed. Caller and human remain in the RTC channel. Acceptance alone is not proof of connection.

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
