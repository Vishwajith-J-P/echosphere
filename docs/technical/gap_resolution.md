# Voice implementation gap resolution

## Scope and evidence

Research baseline: 2026-09-05. These are implementation directions and candidate references, not completed capabilities. Follow the existing Flask/React architecture and feature registry. Agora Conversational AI remains mandatory. The workshop suggestion to add payments or bookings does not expand EchoSphere's approved scope: its agent actions are case updates, ticket synchronization, and contextual human escalation.

The workshop reports 300 free Conversational AI minutes. Verify the account's current allowance, expiry, model charges, and region before a live run; this is not a guaranteed budget or permission for unbounded tests. The supplied X post could not be retrieved. The Discord invitation and video are community context, not verified API contracts.

## Sources and reuse choices

| Gap | Source | Intended reuse and limit |
|---|---|---|
| Working voice baseline | [Official Python starter](https://github.com/AgoraIO-Conversational-AI/agent-quickstart-python) | Compare server lifecycle and client event integration; adapt through the existing gateway, do not replace Flask wholesale |
| Browser lifecycle/events | [Official Next.js starter](https://github.com/AgoraIO-Conversational-AI/agent-quickstart-nextjs) | Reference RTC join, cleanup, token and transcript patterns; Next.js is not a required migration |
| Python model configuration | [Agora Python SDK quick start](https://github.com/AgoraIO/agora-agents-python/blob/main/docs/getting-started/quick-start.md) | Current builder/auth examples; latest examples are not assumed compatible with installed 2.7.2 |
| Optional noise suppression | [Xiph RNNoise](https://github.com/xiph/rnnoise) | Candidate DSP denoiser; native code requires a reviewed browser/WASM bridge or a separately designed media adapter |
| Optional speech detection | [Silero VAD](https://github.com/snakers4/silero-vad) | Candidate for offline fixture segmentation or a measured VAD experiment; neither denoiser nor primary-speaker identifier |
| Workflow setup | [Start with AI](https://docs.agora.io/en/introduction/start-with-ai) and [Agora Skills](https://docs.agora.io/en/introduction/agora-skills) | Inspect official setup workflows; do not scaffold over this repository or overwrite local credentials |
| Example discovery | [Agora Recipes](https://recipes.agora.io/) | Find demonstrations; verify each underlying repository before reuse |

Before importing code, record its exact commit/tag, license and required notices, model-weight license if relevant, dependency compatibility, platform requirements, and test evidence. Public source availability alone is not reuse permission. None of these candidates is installed by this documentation change. Keep downloaded examples isolated from source and credentials; review scripts before running them.

## Managed voice baseline

Start with Agora-managed Deepgram STT, OpenAI LLM, and MiniMax TTS. The [official Python quick start](https://github.com/AgoraIO/agora-agents-python/blob/main/docs/getting-started/quick-start.md) documents supported managed global models without separate vendor keys. Managed access still needs valid Agora authentication and account availability. Preserve the currently configured REST credentials until the chosen SDK authentication mode is verified.

Pin the complete model/voice/region/SDK tuple from an actual successful sandbox run. Do not normalize model identifiers by intuition: the current upstream MiniMax example uses `speech_2_6_turbo`, while the existing integration notes contain `speech-2.6-turbo`. Inspect the installed SDK's accepted schema and capture the outgoing payload before selecting the correct identifier. Record version drift in IP-003. Alternative Gemini, Claude, Sarvam, or ElevenLabs integrations require a separately checked Agora adapter, language support, credentials, and cost; provider names alone do not prove compatibility.

## Audio cleaning and interruption

The target path is microphone -> client echo/noise processing -> Agora RTC -> managed STT -> controlled response -> TTS -> Agora RTC playback. Do not route raw audio through Flask merely to add a filter.

1. Establish the current RTC microphone track baseline with supported echo cancellation, noise suppression, and gain control. Record actual options and device behavior; requested processing does not prove effective processing.
2. Test quiet audio, fan/traffic noise, speakerphone echo, and background people separately. Denoising is not diarization and does not establish which speaker is the caller.
3. Use supported Agora turn/interruption controls. Keep one authority for turn completion; adding a second VAD must not discard quiet speech or prematurely close Hindi pauses.
4. Measure caller speech onset to playback suppression, preserve the interrupting utterance, invalidate obsolete response directives, and retain confirmed fields. Never claim generated text was played when playback evidence is unavailable; label that delivery unknown.
5. Consider RNNoise only after baseline failures are measured. Document sample format/resampling, frame buffering, browser worker/worklet placement, latency, CPU, bypass behavior, and cleanup. Compare identical fixtures with and without the filter. Reject processing that clips words or worsens critical-field capture.
6. Unknown speaker attribution or overlapping speech leaves extracted details tentative. Ask a focused repair; escalate after two unsuccessful repairs for the same critical need.

## Hindi-English handling

[Deepgram documents Nova-3 multilingual code-switching](https://developers.deepgram.com/changelog/2025/3/31), including Hindi and English, with `model=nova-3` and `language=multi`. Those are provider configuration values; verify that the selected Agora adapter exposes/maps them. A UI language preference must not lock recognition into English-only mode.

Preserve original Unicode transcript and per-turn language metadata when available; missing metadata remains unknown. Maintain detected current language separately from caller-confirmed handoff preference. Test Hindi script, English, and switches within one sentence. A model's language support does not prove the selected TTS voice pronounces Hindi, names, and numbers correctly.

[Deepgram's numeral documentation](https://developers.deepgram.com/docs/numerals) excludes Hindi numeral formatting in Nova-3 multilingual mode. Preserve number text, normalize only unambiguous digit sequences with provenance, and read back every callback digit. Do not infer a country code, omitted digit, or phone number from ambiguous Hindi quantities. Corrections produce a new tentative version; background speech cannot confirm it.

## Response control and confidence

Transcript display alone does not enforce policy. Before F-006 completion, prove that the selected Agora integration passes proposed responses through EchoSphere control before they reach TTS. Validate a documented tool/custom-LLM control interface with the pinned SDK. Define authentication, request schema, timeout, cancellation, response generation ID, and replay behavior in the adapter contract.

The orchestrator chooses permitted actions: disclose, ask one priority question, read back a current field, clarify one uncertainty, explain transfer, or end. The model may propose extraction and phrasing; it cannot confirm a field or start arbitrary external actions. Reject stale generation IDs after interruption/escalation. On policy/control failure, suppress unsafe automation and invoke the configured handoff path. A managed prompt-only spike is acceptable for synthetic connectivity testing but does not satisfy deterministic safety requirements. If managed LLM control cannot meet this boundary, record the verified limitation and evaluate a supported custom endpoint before proceeding.

Missing provider confidence is `unknown`, not a fabricated probability. Hard policy/human requests override scores. Track failed repairs per critical need; language switching and a clear correction are not failures. A clarification timeout is distinct from a misunderstood answer. Maintain reason codes and current field versions in durable session state.

## Human escalation contract

Human transfer is application work built from RTC participation and agent lifecycle, not a guaranteed feature of an example repository:

1. Set escalating and stop ordinary questions. Commit an immutable snapshot containing confirmed/tentative facts, language, open questions, reason, transcript boundary, and neutral summary.
2. Offer to an authorized human queue. Review context before acceptance. Acceptance atomically claims the escalation and its snapshot version; competing agents receive conflict.
3. After acceptance, issue that agent's scoped RTC join data. Observe human join/audio readiness before announcing connected. Acceptance alone is not connection evidence.
4. Stop/reconcile the AI agent; do not stop the entire caller RTC channel. Prevent unguarded AI output during the wait, especially on safety escalation.
5. Mark human connected only after verified media readiness and AI shutdown/suppression. If join or stop fails, preserve context and show a failure/wait state; use only the configured fallback.

Ticket synchronization is independent: persist a job alongside the case/handoff transaction, then perform network IO after commit. The local adapter must durably deduplicate create requests and support versioned updates. For an external provider timeout after possible success, reconcile with its idempotency/reference mechanism before retrying create. A retry button reuses the job identity. No repository can provide organization-specific queue staffing or fallback contacts; the browser demo uses a real second participant and a clearly labeled unavailable state when absent.

## Delivery gates

| Work | Existing task/features | Required evidence |
|---|---|---|
| Managed call and version matrix | IP-001, IP-003; F-001 | Successful start/audio/stop, redacted payload, versions, region, bounded test duration |
| Trusted transcript/control interface | IP-004, IP-021; F-001, F-006 | Actual event fixtures, authentication, duplicate/reorder tests, policy-before-speech proof |
| Multilingual/noise/interruption | IP-023, IP-024; F-002, F-003 | TS-001/002 with quiet and noisy controls, critical digits, measured suppression |
| Fields and deterministic policy | IP-012/013/014; F-004/005/006 | Confirmation version checks, repair exhaustion, safety and human-request precedence |
| Transfer and ticketing | IP-030 through IP-034; F-007/008/009 | Two-browser human call, acceptance race, failed join, lost ticket response, durable retry |

Remaining live gates are not closed by research. Test entitlement, managed model/voice availability, event trust, pre-speech policy control, and peer-version compatibility in the account. These need technical evidence, not additional generic product context.
