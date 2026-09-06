from __future__ import annotations

import hashlib
import json
import secrets
import time

from flask import Blueprint, Response, current_app, jsonify, request, stream_with_context
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from typing import Literal

from ..errors import ApiError
from ..services.sessions import SessionService

api = Blueprint("api", __name__)


def service() -> SessionService:
    return current_app.extensions["session_service"]


def bearer_token() -> str:
    value = request.headers.get("Authorization", "")
    if not value.startswith("Bearer "):
        raise ApiError("UNAUTHORIZED", "A session capability is required.", 401)
    return value.removeprefix("Bearer ").strip()


@api.get("/health/live")
def health_live():
    return jsonify(status="ok")


@api.get("/health/ready")
def health_ready():
    current_app.extensions['database'].connection.execute('SELECT 1')
    return jsonify(status='ready', agora='configured' if voice_ready() else 'setup_required')


def voice_ready():
    settings = current_app.config['SETTINGS']
    return bool(settings.agora_app_id and settings.agora_app_certificate and settings.agora_customer_id
                and settings.agora_customer_secret and settings.public_base_url
                and (settings.speech_provider != 'sarvam' or settings.sarvam_api_key))


def voice_requirements():
    settings = current_app.config['SETTINGS']
    checks = {
        'agora_app_id': bool(settings.agora_app_id),
        'agora_app_certificate': bool(settings.agora_app_certificate),
        'agora_customer_credentials': bool(settings.agora_customer_id and settings.agora_customer_secret),
        'public_https_url': bool(settings.public_base_url),
        'sarvam_api_key': settings.speech_provider != 'sarvam' or bool(settings.sarvam_api_key),
    }
    return {'ready': all(checks.values()), 'checks': checks}


@api.get('/capabilities')
def capabilities():
    return jsonify(voice_ready=voice_ready(), voice_requirements=voice_requirements(), languages=['hi-IN', 'en-IN', 'ta-IN'], recording=False,
                   speech_provider=current_app.config['SETTINGS'].speech_provider,
                   audio_input=True, audio_output=True, synthetic_only=False)


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class MediaReadyInput(Input):
    media_ready: bool = False


class SessionInput(Input):
    requested_language: Literal['hi-IN', 'en-IN', 'ta-IN'] = 'en-IN'
    client: dict | None = None


class EscalationInput(Input):
    trigger: Literal['human_request'] = 'human_request'


class AcceptInput(Input):
    escalation_id: str = Field(min_length=1, max_length=80)
    snapshot_version: int = Field(ge=1, strict=True)


class LoginInput(Input):
    access_token: str = Field(min_length=1, max_length=256)


def payload(model):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError('VALIDATION_ERROR', 'A JSON object is required.', 400)
    try:
        return model.model_validate(data).model_dump()
    except ValidationError:
        raise ApiError('VALIDATION_ERROR', 'The request contains invalid or unsupported fields.', 400)


def operator(required=False, supervisor=False):
    identity = current_app.extensions['auth_service'].identify(bearer_token())
    if required and not identity:
        raise ApiError('FORBIDDEN', 'Operator access is required.', 403)
    if supervisor and (not identity or identity['role'] != 'supervisor'):
        raise ApiError('FORBIDDEN', 'Supervisor access is required.', 403)
    return identity


@api.post("/sessions")
def create_session():
    data = payload(SessionInput)
    current_app.extensions['database'].limit('create:' + (request.remote_addr or 'local'), 10)
    if not current_app.testing and not voice_ready():
        raise ApiError('VOICE_SETUP_REQUIRED', 'Voice needs Agora credentials, speech provider setup, and a public HTTPS backend URL.', 503)
    result = service().create(requested_language=data['requested_language'])
    return jsonify(result), 201


@api.get("/sessions/<session_id>")
def get_session(session_id: str):
    return jsonify(service().get(session_id, bearer_token(), operator()))


@api.post("/sessions/<session_id>/start")
def start_session(session_id: str):
    return jsonify(service().start(session_id, bearer_token())), 202


@api.post("/sessions/<session_id>/end")
def end_session(session_id: str):
    return jsonify(service().end(session_id, bearer_token(), operator())), 202


@api.post('/auth/login')
def login():
    data = payload(LoginInput)
    current_app.extensions['database'].limit('login:' + (request.remote_addr or 'local'), 8)
    return jsonify(current_app.extensions['auth_service'].login(data['access_token']))


@api.post('/auth/logout')
def logout():
    current_app.extensions['auth_service'].logout(bearer_token())
    return jsonify(status='signed_out')


@api.get('/queue')
def queue():
    operator(required=True)
    try:
        limit, offset = int(request.args.get('limit', 50)), int(request.args.get('offset', 0))
        if not 1 <= limit <= 100 or offset < 0:
            raise ValueError()
    except ValueError:
        raise ApiError('VALIDATION_ERROR', 'Invalid pagination.', 400)
    return jsonify(service().queue(limit, offset))


def command(session_id, action, data):
    identity = operator()
    if identity and action in {'confirm', 'correct'}:
        raise ApiError('FORBIDDEN', 'Only the caller can confirm or correct their facts.', 403)
    if identity and action == 'turn':
        state = service().get(session_id, operator=identity)
        escalation = state['conversation']['escalation']
        if not escalation or escalation['assigned_to'] != identity['username'] or state['status'] != 'human_connected':
            raise ApiError('FORBIDDEN', 'Join your assigned call before sending a message.', 403)
    current_app.extensions['database'].limit('command:' + session_id, 90)
    return jsonify(service().command(session_id, bearer_token(), action, data, identity))


@api.post('/sessions/<session_id>/escalations')
def escalate(session_id):
    return command(session_id, 'escalate', payload(EscalationInput))


@api.post('/sessions/<session_id>/handoff/accept')
def accept(session_id):
    return jsonify(service().accept(session_id, operator(required=True), payload(AcceptInput)))


@api.post('/sessions/<session_id>/handoff/connected')
def connected(session_id):
    identity = operator(required=True)
    data = payload(MediaReadyInput)
    if data.get('media_ready') is not True:
        # Run assignment authorization before exposing readiness state.
        return jsonify(service().connected(session_id, identity, media_ready=False))
    return jsonify(service().connected(session_id, identity, media_ready=True))


@api.post('/sessions/<session_id>/token')
def renew(session_id):
    return jsonify(service().renew(session_id, bearer_token(), operator()))


@api.get('/sessions/<session_id>/events')
def events(session_id):
    identity, token, sessions = operator(), bearer_token(), service()
    sessions.get(session_id, token, identity)

    @stream_with_context
    def stream():
        previous = ''
        # Bounded streams permit credential revalidation and prevent permanent workers.
        for _ in range(25):
            if identity and not sessions.auth.identify(token):
                break
            try:
                state = sessions.get(session_id, token, identity)
            except ApiError:
                break
            encoded = json.dumps(state, ensure_ascii=False)
            if encoded != previous:
                yield f'event: snapshot\nid: {state["generation"]}\ndata: {encoded}\n\n'
                previous = encoded
            else:
                yield ': heartbeat\n\n'
            time.sleep(1)
    return Response(stream(), mimetype='text/event-stream', headers={'X-Accel-Buffering': 'no'})


@api.post('/sessions/<session_id>/llm/chat/completions')
def controlled_llm(session_id):
    sessions = service()
    if not secrets.compare_digest(bearer_token(), sessions.control_token(session_id)):
        raise ApiError('UNAUTHORIZED', 'Provider authentication required.', 401)
    state = sessions.get(session_id, operator={'username': 'provider'})
    if state['mode'] != 'voice' or state['status'] in {'ended', 'ending', 'failed', 'human_connected'}:
        raise ApiError('STATE_CONFLICT', 'Automation is inactive.', 409)
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get('messages'), list) or not 1 <= len(body['messages']) <= 100:
        raise ApiError('VALIDATION_ERROR', 'A bounded messages array is required.', 400)
    messages = body['messages']
    if any(not isinstance(item, dict) or not isinstance(item.get('content'), str) for item in messages):
        raise ApiError('VALIDATION_ERROR', 'Text messages are required.', 400)
    callers = [item for item in messages if item.get('role') == 'user']
    if not callers or not 1 <= len(callers[-1]['content']) <= 600:
        raise ApiError('VALIDATION_ERROR', 'A caller utterance is required.', 400)
    from ..domain.conversation import Conversation
    assistants = [item['content'] for item in messages if item.get('role') == 'assistant']
    expected = Conversation.prompt(json.loads(json.dumps(state['conversation'])))
    event_id = 'provider:' + hashlib.sha256(json.dumps(messages, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    result = sessions.command(session_id, '', 'turn', {'text': callers[-1]['content'], 'event_id': event_id,
        'confirmation_context': bool(assistants and assistants[-1] == expected)}, operator={'username': 'provider'}, provider=True)
    response_id = 'chatcmpl-' + event_id[-24:]
    # The whole bounded response is authorized before yielding any text to TTS.
    def output():
        latest = sessions.get(session_id, operator={'username': 'provider'})
        text = result['reply'] if latest['generation'] == result['generation'] else ''
        chunk = {'id': response_id, 'object': 'chat.completion.chunk', 'created': int(time.time()),
                 'model': 'echosphere-intake-v1', 'choices': [{'index': 0, 'delta': {'role': 'assistant', 'content': text}, 'finish_reason': None}]}
        yield 'data: ' + json.dumps(chunk, ensure_ascii=False) + '\n\n'
        chunk['choices'] = [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]
        yield 'data: ' + json.dumps(chunk) + '\n\ndata: [DONE]\n\n'
    return Response(output(), mimetype='text/event-stream')


@api.get('/integration-jobs')
def jobs():
    operator(required=True)
    with current_app.extensions['database'].transaction() as connection:
        rows = connection.execute('SELECT id,session_id,version,status,attempts,last_error FROM integration_jobs ORDER BY rowid DESC LIMIT 100').fetchall()
    return jsonify(items=[dict(row) for row in rows])


@api.post('/integration-jobs/<job_id>/retry')
def retry(job_id):
    operator(required=True, supervisor=True)
    return jsonify(service().retry_job(job_id))


@api.get('/diagnostics')
def diagnostics():
    operator(required=True, supervisor=True)
    with current_app.extensions['database'].transaction() as connection:
        rows = connection.execute('SELECT event_type,count(*) AS count FROM audit_events GROUP BY event_type').fetchall()
    return jsonify(events=[dict(row) for row in rows], voice_ready=voice_ready())
