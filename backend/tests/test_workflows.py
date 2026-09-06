from conftest import FakeGateway
from echosphere import create_app


def start_voice(client, language='ta-IN'):
    response = client.post('/api/sessions', json={'requested_language': language})
    assert response.status_code == 201
    data = response.json
    return '/api/sessions/' + data['session_id'], {'Authorization': 'Bearer ' + data['caller_capability']}, data


def provider_turn(client, app, data, utterance, event_id='turn-1'):
    service = app.extensions['session_service']
    return client.post('/api/sessions/' + data['session_id'] + '/llm/chat/completions',
                       headers={'Authorization': 'Bearer ' + service.control_token(data['session_id'])},
                       json={'messages': [{'role': 'user', 'content': utterance}], 'event_id': event_id})


def test_voice_case_and_text_turn_route_is_not_public(settings):
    config = settings
    app = create_app(config, FakeGateway())
    app.config.update(TESTING=True)
    client = app.test_client()
    url, headers, data = start_voice(client)
    assert data['mode'] == 'voice'
    assert data['rtc']
    assert client.post(url + '/turns', json={'text': 'hello', 'event_id': 'x'}, headers=headers).status_code == 404
    assert provider_turn(client, app, data, 'இணைய இணைப்பு வேலை செய்யவில்லை').status_code == 200
    state = client.get(url, headers=headers).json
    assert state['mode'] == 'voice'
    assert any(turn['speaker'] == 'ai' and 'முப்பது' in turn['text'] for turn in state['transcript'])


def test_caller_cannot_read_queue(client):
    _, headers, _ = start_voice(client)
    assert client.get('/api/queue', headers=headers).status_code in {401, 403}


def test_customer_can_send_optional_text_message(client):
    url, headers, _ = start_voice(client)
    response = client.post(url + '/messages', json={'text': 'I need help with my internet'}, headers=headers)
    assert response.status_code == 200
    assert any(turn['speaker'] == 'caller' and turn['text'] == 'I need help with my internet' for turn in response.json['transcript'])


def test_handoff_claim_is_exclusive_and_ticket_is_independent(app, client):
    url, caller, data = start_voice(client)
    state = client.post(url + '/escalations', json={'trigger': 'human_request'}, headers=caller).json
    escalation = state['conversation']['escalation']
    queue = client.get('/api/queue').json['items']
    assert any(item['session_id'] == data['session_id'] and item['status'] == 'escalating' for item in queue)
    payload = {'escalation_id': escalation['id'], 'snapshot_version': escalation['version']}
    assert client.post(url + '/handoff/accept', json=payload).status_code == 200
    assert client.post(url + '/handoff/accept', json=payload).status_code == 200
    connected = client.post(url + '/handoff/connected', json={'media_ready': True})
    assert connected.status_code == 200
    assert connected.json['status'] == 'human_connected'
    assert connected.json['provider_status'] == 'stopped'
    message = client.post(url + '/messages', json={'text': 'I am here to help.'})
    assert message.status_code == 200
    assert message.json['transcript'][-1]['speaker'] == 'human'


def test_custom_llm_requires_separate_provider_auth(client):
    _, headers, data = start_voice(client)
    response = client.post('/api/sessions/' + data['session_id'] + '/llm/chat/completions', headers=headers, json={'messages': []})
    assert response.status_code in {401, 403}


def test_operator_can_clear_pending_handoff_queue(client):
    url, caller, data = start_voice(client)
    client.post(url + '/escalations', json={'trigger': 'human_request'}, headers=caller)
    response = client.post('/api/queue/clear')
    assert response.status_code == 200
    assert response.json['cleared'] == 1
    assert client.get('/api/queue').json['items'] == []
