# UI/UX Brief

## Experience Direction

EchoSphere should feel calm, credible, and operational—not playful or anthropomorphic. The voice experience is primary; the screen supports comprehension and human operations. Never use a human avatar or wording that obscures that the assistant is AI.

## Voice Interaction Principles

- Disclose AI status at the start and keep a human option available.
- Use short sentences, one question at a time, plain Hindi/English, and the caller's current language.
- Permit natural code-switching; never force a restart or scold language changes.
- Yield immediately on barge-in and do not finish an obsolete response.
- Acknowledge emotion without diagnosing it: “I’m sorry this is difficult” is acceptable; clinical conclusions are not.
- For unclear input, name the uncertain fragment and ask a narrow question.
- Read phone numbers digit-by-digit and confirm all critical details explicitly.
- Say “I understood…” or “You said…” for caller statements; never present inference as fact.
- Once escalation begins, stop the questionnaire and explain the transfer briefly.

## Caller Simulator

The demo page contains:

1. clear “Start voice assistance” control and microphone disclosure;
2. AI identity, privacy/recording status, supported languages, and “Talk to a person” action;
3. connection and turn indicator: Connecting, Listening, AI speaking, Reconnecting, Transferring, Human connected;
4. live captions with speaker labels and language tags;
5. critical-detail confirmation cards with Confirm/Correct controls as an accessible fallback to speech;
6. end-call control and actionable error/retry state.

Do not show raw confidence decimals to callers. Use helpful language such as “I didn’t catch the location clearly.”

## Agent/Supervisor Console

```text
+----------------+---------------------------+----------------------+
| Escalation     | Live transcript           | Case context         |
| queue          | speaker + language         | reason + summary     |
| priority/state | confidence flags inline   | confirmed/tentative  |
| wait time      |                           | open questions       |
|                |                           | ticket + Accept      |
+----------------+---------------------------+----------------------+
```

On small screens, use queue -> session -> context drill-down instead of three squeezed columns.

### Information Hierarchy

1. Safety/escalation reason and transfer status.
2. Accept/continue-call action.
3. Confirmed facts.
4. Unresolved/tentative details and next question.
5. Summary and transcript.
6. Integration/audit diagnostics.

Confirmed and tentative values must differ by icon, label, and text—not color alone. Safety flags are observations/categories, not diagnoses. Confidence details expose reason codes and bands; raw scores may appear only in a diagnostic disclosure.

## Visual System

- Neutral dark navy/charcoal for structure, off-white surfaces, calm blue for active states.
- Amber means attention/uncertainty; red is reserved for failed/safety-critical states; green means completed/connected, never merely “high confidence.”
- Use a legible system sans-serif. Minimum 16 px body/caption transcript text and comfortable line height.
- Use an 8 px spacing base and restrained motion.
- Respect `prefers-reduced-motion`; never use flashing urgency indicators.

## Accessibility

- Meet WCAG 2.2 AA for the implemented prototype where applicable.
- All controls work by keyboard with visible focus and logical order.
- Live transcript uses an appropriate live-region strategy that does not repeatedly interrupt screen readers; finalized turns are navigable.
- Provide text equivalents for audio state and do not rely on waveform animation.
- Buttons use action labels (“Accept transfer”), not ambiguous icons alone.
- Dialog focus is trapped/restored correctly; errors are associated with controls.
- Hindi text uses a font stack with clear Devanagari support and correct language attributes.

## Reusable Patterns

### UI-001 — Turn Status

Persistent compact status for connection/listening/speaking/transfer. It uses text plus icon; animated only when useful.

### UI-002 — Fact Confidence Card

Displays label, current value, source, state (`tentative`, `confirmed`, `corrected`, `unresolved`), and confirmation time. Caller view offers Confirm/Correct; console view is read-only except authorized human annotation.

### UI-003 — Escalation Banner

Shows reason category, current transfer state, queue/wait status if known, and primary action. It never reveals model chain-of-thought or alarming speculation.

### UI-004 — Integration Status

Shows Pending, Synced, Retry scheduled, or Failed with a supervisor retry action. Transfer state is displayed independently.

## Content Examples

- Disclosure: “I’m an AI assistant. I can help collect the basic details, and you can ask for a person at any time.”
- Uncertainty: “I heard the issue, but I’m not sure I caught the location. Could you say just the area name again?”
- Confirmation: “To confirm, your callback number is … Is that correct?”
- Boundary: “I can’t provide authoritative guidance about that. I’ll connect you with a trained person and share what you’ve told me.”
- Transfer: “I’m transferring you now. I’ll pass along the confirmed details so you don’t have to start over.”

## Prohibited UX

- Hidden recording, consent, or retention behavior.
- Countdown pressure, manipulative retention, or discouraging a human request.
- “Solved” or success states for unconfirmed/inferred information.
- Medical/legal/financial/emergency recommendation cards.
- Exposing internal prompts, secrets, raw exceptions, or chain-of-thought.

## Planned Page States

All pages define loading, empty, permission-denied, recoverable error, terminal error, and reconnect behavior as applicable. No UI is implemented yet; patterns become established only after implementation and verification.
