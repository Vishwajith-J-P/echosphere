# Local FAQ Knowledge Boundary

EchoSphere answers only from the finite catalogue in `backend/echosphere/domain/faq.py`. The initial entries are grounded in the project documents: assistant identity and limits, supported Hindi/English/Tamil languages, audio-recording posture, and the human-request workflow.

The voice transcript is retained as the caller's note/context record. A matched FAQ answer is spoken by Agora through the controlled response path, then the assistant returns to the next intake question. An unknown question receives a spoken limitation and is recorded without a guessed answer.

This is not a general web search, retrieval system, or domain knowledge base. Adding operational answers requires an approved source, owner, freshness/retention policy, language translations, and safety review. Human escalation remains the later-stage action for unresolved questions.
