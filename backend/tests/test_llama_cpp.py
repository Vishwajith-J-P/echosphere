from __future__ import annotations

import json

from echosphere.services.llama_cpp import LlamaCppClient, needs_interpretation


def test_interpretation_skips_simple_acknowledgements():
    assert needs_interpretation('yes', '') is False
    assert needs_interpretation('My internet is not working', 'Restart the router.') is True
    assert needs_interpretation('That did not help me', '') is True


def test_llama_cpp_client_parses_structured_answer(monkeypatch):
    seen = {}

    class Response:
        def read(self):
            return json.dumps({
                'choices': [{'message': {'content': json.dumps({
                    'customer_need': 'internet outage',
                    'answer': 'Restart the router once and wait thirty seconds.',
                    'satisfied': True,
                    'wants_human': False,
                })}}]
            }).encode()

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def fake_urlopen(request, timeout):
        seen['url'] = request.full_url
        seen['timeout'] = timeout
        seen['body'] = json.loads(request.data)
        return Response()

    monkeypatch.setattr('echosphere.services.llama_cpp.urlopen', fake_urlopen)
    result = LlamaCppClient('http://127.0.0.1:8080').answer(
        language='en-IN',
        utterance='My internet is not working',
        retrieved_answer='Restart the router once and wait thirty seconds.',
    )

    assert result['customer_need'] == 'internet outage'
    assert result['satisfied'] is True
    assert seen['url'] == 'http://127.0.0.1:8080/v1/chat/completions'
    assert seen['body']['response_format']['type'] == 'json_object'


def test_llama_cpp_client_rejects_untrusted_or_malformed_output(monkeypatch):
    class Response:
        def read(self):
            return b'{"choices":[{"message":{"content":"not json"}}]}'

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr('echosphere.services.llama_cpp.urlopen', lambda *_args, **_kwargs: Response())
    assert LlamaCppClient('http://127.0.0.1:8080').answer('en-IN', 'hello', '') is None


def test_llama_cpp_does_not_accept_false_positive_handoff(monkeypatch):
    class Response:
        def read(self):
            return json.dumps({'choices': [{'message': {'content': json.dumps({
                'customer_need': 'internet outage', 'answer': 'Restart the router.',
                'satisfied': True, 'wants_human': True,
            })}}]}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr('echosphere.services.llama_cpp.urlopen', lambda *_args, **_kwargs: Response())
    result = LlamaCppClient('http://127.0.0.1:8080').answer('en-IN', 'My internet is not working', 'Restart the router.')
    assert result['wants_human'] is False
