"""Small, bounded client for a local llama.cpp OpenAI-compatible server."""
from __future__ import annotations

import json
from urllib.request import Request, urlopen
import re


HANDOFF_LANGUAGE = re.compile(
    r'\b(human|person|representative|agent|more help|not helpful|didn.t help|did not help|not solved|still not|unsatisfied)\b',
    re.IGNORECASE,
)


def needs_interpretation(utterance: str, retrieved_answer: str) -> bool:
    """Avoid an expensive local generation for acknowledgements/confirmations."""
    return bool(retrieved_answer or HANDOFF_LANGUAGE.search(utterance) or '?' in utterance)


class LlamaCppClient:
    def __init__(self, base_url: str, model: str = 'qwen1.5-1.8b-chat', timeout_seconds: float = 8.0):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout_seconds = timeout_seconds

    def answer(self, language: str, utterance: str, retrieved_answer: str, history: list[dict] | None = None):
        prompt = {'language': language, 'customer_message': utterance,
                  'approved_answer': retrieved_answer or None, 'recent_context': (history or [])[-6:]}
        messages = [
            {'role': 'system', 'content': (
                'Return JSON only: customer_need, answer, satisfied, wants_human. Use only approved_answer. '
                'If it is missing, answer must be empty. Give short troubleshooting steps and never repeat '
                'the customer message. Never give professional advice or claim an action was completed. '
                'Set wants_human true only when the customer explicitly asks for a person or says the answer failed.')},
            {'role': 'user', 'content': json.dumps(prompt, ensure_ascii=False)},
        ]
        request = Request(self.base_url + '/v1/chat/completions',
                          data=json.dumps({'model': self.model, 'messages': messages, 'temperature': 0.1,
                                           'max_tokens': 128, 'response_format': {'type': 'json_object'},
                                           'chat_template_kwargs': {'enable_thinking': False}},
                                          ensure_ascii=False).encode(),
                          headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read())
            proposal = json.loads(payload['choices'][0]['message']['content'])
        except (OSError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
            return None
        if not isinstance(proposal, dict) or not isinstance(proposal.get('customer_need'), str) or not isinstance(proposal.get('answer'), str):
            return None
        if len(proposal['customer_need']) > 300 or len(proposal['answer']) > 1200:
            return None
        # A small model can over-predict escalation. Require an observable
        # customer phrase before accepting that proposal as a handoff trigger.
        wants_human = proposal.get('wants_human') is True and bool(HANDOFF_LANGUAGE.search(utterance))
        return {'customer_need': proposal['customer_need'].strip(), 'answer': proposal['answer'].strip(),
                'satisfied': proposal.get('satisfied') is True, 'wants_human': wants_human}
