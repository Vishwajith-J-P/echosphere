from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from uuid import uuid4

from ..domain.conversation import Conversation, TERMINAL
from ..domain.faq import is_question, limitation, lookup as lookup_faq
from ..errors import ApiError
from ..storage import Database
from .auth import AuthService, digest


class SessionService:
    def __init__(self, gateway, settings, database=None):
        self._gateway, self._settings = gateway, settings
        self.database = database or Database(settings.database_path)
        self.auth = AuthService(self.database)

    def control_token(self, session_id):
        return hmac.new(self._settings.secret_key.encode(), ('provider:' + session_id).encode(), hashlib.sha256).hexdigest()

    def _authorized(self, connection, session_id, capability, operator=None):
        row, state = Database.load(connection, session_id)
        if row is None:
            raise ApiError('NOT_FOUND', 'The requested session was not found.', 404)
        if operator is None and (not secrets.compare_digest(row['capability_hash'], digest(capability)) or row['expires_at'] < time.time()):
            raise ApiError('NOT_FOUND', 'The requested session was not found.', 404)
        if operator and operator.get('username') not in {'provider', 'system'}:
            escalation = state['conversation'].get('escalation')
            role = operator.get('role')
            allowed = role == 'supervisor' or (escalation and (escalation.get('assigned_to') == operator['username'] or escalation.get('status') in {'requested', 'offered'}))
            if not allowed:
                raise ApiError('FORBIDDEN', 'This session is not available to this operator.', 403)
        return state

    def create(self, requested_language):
        session_id, capability = str(uuid4()), secrets.token_urlsafe(32)
        state = {'session_id': session_id, 'channel': 'echosphere-' + uuid4().hex,
                 'caller_uid': secrets.randbelow(900000000) + 100000000,
                 'agent_uid': secrets.randbelow(900000000) + 1000000000,
                 'human_uid': secrets.randbelow(900000000) + 2000000000,
                 'requested_language': requested_language, 'mode': 'voice', 'status': 'created',
                 'desired': 'active', 'agent_id': None, 'provider_status': 'idle', 'created_at': time.time(),
                 'conversation': Conversation.new(requested_language), 'transcript': [], 'snapshot': None,
                 'ticket_status': 'not_requested', 'last_activity_at': time.time(), 'generation': 0}
        rtc = self._join_material(state, state['caller_uid'])
        with self.database.transaction() as connection:
            active = connection.execute("SELECT count(*) FROM sessions WHERE json_extract(data,'$.desired')='active' AND expires_at>?", (time.time(),)).fetchone()[0]
            if active >= self._settings.max_sessions:
                raise ApiError('RATE_LIMITED', 'The demo is at capacity. Please try again shortly.', 429)
            connection.execute('INSERT INTO sessions VALUES(?,?,?,?,?)', (session_id, digest(capability), time.time() + self._settings.max_call_seconds + 300, json.dumps(state, ensure_ascii=False), time.time()))
            Database.event(connection, session_id, 'session.created', {'mode': 'voice', 'language': requested_language})
        return {**self._public(state), 'caller_capability': capability, 'rtc': rtc}

    def _join_material(self, state, uid):
        return {'app_id': self._settings.agora_app_id, 'channel': state['channel'], 'uid': uid,
                'token': self._gateway.issue_token(state['channel'], uid),
                'expires_at': int(time.time()) + self._settings.agora_token_ttl_seconds}

    def get(self, session_id, capability='', operator=None):
        with self.database.transaction() as connection:
            return self._public(self._authorized(connection, session_id, capability, operator))

    @staticmethod
    def _public(state):
        return {key: state[key] for key in ('session_id', 'status', 'requested_language', 'mode', 'provider_status',
                'conversation', 'transcript', 'snapshot', 'ticket_status', 'created_at', 'generation')} | {
                    'agent_connected': False, 'agent_uid': state['agent_uid'], 'human_uid': state['human_uid']}

    def start(self, session_id, capability):
        with self.database.transaction() as connection:
            state = self._authorized(connection, session_id, capability)
            if state['status'] != 'created':
                if state['desired'] == 'active':
                    return self._public(state)
                raise ApiError('STATE_CONFLICT', 'This session cannot be restarted.', 409)
            state.update(status='connecting', provider_status='starting')
            Database.save(connection, state)
        try:
            started = self._gateway.start(session_id=session_id, channel=state['channel'], caller_uid=state['caller_uid'],
                agent_uid=state['agent_uid'], requested_language=state['requested_language'], control_token=self.control_token(session_id))
        except Exception as exc:
            with self.database.transaction() as connection:
                _, state = Database.load(connection, session_id)
                state['provider_status'] = 'unknown'
                if state['desired'] == 'active':
                    state.update(status='failed', desired='ended')
                Database.event(connection, session_id, 'provider.start.failed')
                Database.save(connection, state)
            raise ApiError('AGORA_UNAVAILABLE', 'Voice could not start. Check Agora and speech provider setup.', 503) from exc
        with self.database.transaction() as connection:
            _, state = Database.load(connection, session_id)
            state.update(agent_id=started.agent_id, provider_status='running')
            end_won = state['desired'] == 'ended'
            if not end_won and state['status'] == 'connecting':
                state['status'] = 'disclosure'
            Database.event(connection, session_id, 'provider.started')
            Database.save(connection, state)
        if end_won:
            return self.end(session_id, capability)
        return self.get(session_id, capability)

    def _stop(self, state):
        if hasattr(self._gateway, 'stop_agent'):
            self._gateway.stop_agent(state['session_id'], state['agent_id'])
        else:
            self._gateway.stop(state['session_id'])

    def end(self, session_id, capability='', operator=None):
        with self.database.transaction() as connection:
            state = self._authorized(connection, session_id, capability, operator)
            if state['status'] == 'ended' and state['provider_status'] == 'stopped':
                return self._public(state)
            state.update(desired='ended', status='ending', generation=state['generation'] + 1)
            state['conversation']['status'] = 'ended'
            Database.save(connection, state)
        success = True
        try:
            if state['mode'] == 'voice':
                self._stop(state)
        except Exception:
            success = False
        with self.database.transaction() as connection:
            _, state = Database.load(connection, session_id)
            state.update(status='ended' if success else 'ending', provider_status='stopped' if success else 'cleanup_pending')
            Database.event(connection, session_id, 'session.ended' if success else 'provider.cleanup.pending')
            Database.save(connection, state)
        return self._public(state)

    @staticmethod
    def _append(state, speaker, text, delivery='text'):
        state['transcript'].append({'sequence': len(state['transcript']) + 1, 'speaker': speaker, 'text': text,
            'language': state['conversation']['language'], 'created_at': time.time(), 'delivery': delivery})

    def _checkpoint(self, connection, state):
        call = state['conversation']
        state['status'] = call['status']
        if call['escalation'] or call['status'] == 'completing':
            if call['escalation'] and call['escalation']['status'] in {'requested', 'offered'}:
                version = connection.execute('SELECT coalesce(max(version),0)+1 FROM handoff_snapshots WHERE session_id=?', (state['session_id'],)).fetchone()[0]
                snapshot = Conversation.snapshot(call)
                snapshot.update(version=version, transcript_through_sequence=len(state['transcript']))
                connection.execute('INSERT INTO handoff_snapshots VALUES(?,?,?)', (state['session_id'], version, json.dumps(snapshot, ensure_ascii=False)))
                call['escalation']['version'] = version
                state['snapshot'] = snapshot
            job_id = f"{state['session_id']}:{call['revision']}"
            connection.execute('INSERT OR IGNORE INTO integration_jobs(id,session_id,version,payload) VALUES(?,?,?,?)',
                (job_id, state['session_id'], call['revision'], json.dumps(Conversation.snapshot(call), ensure_ascii=False)))
            state['ticket_status'] = 'pending'
        Database.save(connection, state)

    def command(self, session_id, capability, action, payload, operator=None, provider=False):
        fingerprint = digest(json.dumps({'action': action, 'payload': payload}, sort_keys=True, ensure_ascii=False))
        event_id = payload.get('event_id')
        with self.database.transaction() as connection:
            state = self._authorized(connection, session_id, capability, operator)
            if state['desired'] != 'active' or state['status'] in TERMINAL:
                raise ApiError('STATE_CONFLICT', 'This session has ended.', 409)
            if event_id:
                previous = connection.execute('SELECT * FROM processed_events WHERE session_id=? AND event_id=?', (session_id, event_id)).fetchone()
                if previous:
                    if previous['body_hash'] != fingerprint:
                        raise ApiError('STATE_CONFLICT', 'Event ID was reused with different content.', 409)
                    return json.loads(previous['response'])
            call = state['conversation']
            state['generation'] += 1
            state['last_activity_at'] = time.time()
            try:
                if action == 'turn':
                    if len(state['transcript']) >= 300:
                        raise ApiError('RATE_LIMITED', 'The turn limit was reached. Request a person or end the call.', 429)
                    self._append(state, 'human' if operator and call['status'] == 'human_connected' else 'caller', payload['text'])
                    before = json.loads(json.dumps(call))
                    reply = '' if call['status'] == 'human_connected' else Conversation.turn(call, payload['text'], speech_confirmation=provider and payload.get('confirmation_context', False))
                    faq = lookup_faq(payload['text'], call['language']) if provider else None
                    if provider and not before['fields'] and not before['challenge'] and call['escalation'] is None and (faq or is_question(payload['text'])):
                        call = before
                        state['conversation'] = call
                        reply = (faq or limitation(call['language'])) + ' ' + Conversation.prompt(call)
                elif action == 'confirm':
                    reply = Conversation.confirm(call, payload['challenge_id'])
                elif action == 'correct':
                    reply = Conversation.correct(call, payload['field'], payload['value'])
                elif action == 'escalate':
                    reply = Conversation.escalate(call, 'human_request')
                elif action == 'language':
                    call['language'] = payload['language']
                    call['language_history'].append(payload['language'])
                    reply = Conversation.prompt(call)
                elif action == 'interrupt':
                    for turn in reversed(state['transcript']):
                        if turn['speaker'] == 'ai':
                            turn['delivery'] = 'interrupted_or_unknown'
                            break
                    reply = ''
                else:
                    raise ApiError('VALIDATION_ERROR', 'Unknown command.', 400)
            except ValueError as exc:
                raise ApiError('STATE_CONFLICT', str(exc), 409) from exc
            if reply:
                self._append(state, 'ai', reply, 'unknown' if state['mode'] == 'voice' else 'text')
            Database.event(connection, session_id, 'conversation.' + action, {'revision': call['revision'], 'status': call['status'], 'actor': 'provider' if provider else 'operator' if operator else 'caller'})
            self._checkpoint(connection, state)
            result = {**self._public(state), 'reply': reply}
            if event_id:
                connection.execute('INSERT INTO processed_events VALUES(?,?,?,?)', (session_id, event_id, fingerprint, json.dumps(result, ensure_ascii=False)))
            return result

    def queue(self, limit=50, offset=0):
        with self.database.transaction() as connection:
            rows = connection.execute("SELECT data FROM sessions WHERE json_extract(data,'$.conversation.escalation') IS NOT NULL ORDER BY updated_at DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        result = []
        for row in rows:
            state = json.loads(row['data'])
            result.append({'session_id': state['session_id'], 'status': state['status'], 'language': state['conversation']['language'],
                'escalation': state['conversation']['escalation'], 'ticket_status': state['ticket_status'], 'mode': state['mode']})
        return {'items': result, 'limit': limit, 'offset': offset}

    def accept(self, session_id, operator, payload):
        with self.database.transaction() as connection:
            state = self._authorized(connection, session_id, '', operator)
            escalation = state['conversation']['escalation']
            if not escalation or state['desired'] != 'active':
                raise ApiError('STATE_CONFLICT', 'No active transfer is available.', 409)
            if escalation['assigned_to'] and escalation['assigned_to'] != operator['username']:
                raise ApiError('STATE_CONFLICT', 'Another operator has accepted this call.', 409)
            if escalation['id'] != payload['escalation_id'] or escalation['version'] != payload['snapshot_version']:
                raise ApiError('STALE_HANDOFF_SNAPSHOT', 'The handoff context changed. Review it again.', 409)
            if escalation['status'] not in {'requested', 'offered', 'accepted'}:
                raise ApiError('STATE_CONFLICT', 'This transfer is no longer available.', 409)
            escalation.update(assigned_to=operator['username'], status='accepted', accepted_at=time.time())
            state['status'] = state['conversation']['status'] = 'transferring'
            state['generation'] += 1
            Database.event(connection, session_id, 'handoff.accepted', {'operator': operator['username'], 'snapshot_version': escalation['version']})
            Database.save(connection, state)
        return {**self._public(state), 'rtc': self._join_material(state, state['human_uid']) if state['mode'] == 'voice' else None}

    def connected(self, session_id, operator, media_ready=False):
        with self.database.transaction() as connection:
            state = self._authorized(connection, session_id, '', operator)
            escalation = state['conversation']['escalation']
            if not escalation or escalation['assigned_to'] != operator['username']:
                raise ApiError('FORBIDDEN', 'This call is not assigned to you.', 403)
            if state['desired'] != 'active' or escalation['status'] not in {'accepted', 'connected'}:
                raise ApiError('STATE_CONFLICT', 'The transfer is no longer active.', 409)
            if not media_ready:
                raise ApiError('TRANSFER_UNAVAILABLE', 'Media readiness has not been observed.', 409)
            if state['mode'] == 'voice':
                verifier = getattr(self._gateway, 'verify_participants', None)
                if verifier is None or not verifier(state['channel'], state['caller_uid'], state['human_uid']):
                    raise ApiError('TRANSFER_UNAVAILABLE', 'The caller and human audio participants are not both ready.', 503)
        try:
            if state['mode'] == 'voice':
                self._stop(state)
        except Exception as exc:
            raise ApiError('TRANSFER_UNAVAILABLE', 'AI shutdown is pending. Do not announce connected yet.', 503) from exc
        with self.database.transaction() as connection:
            _, state = Database.load(connection, session_id)
            if state['desired'] != 'active':
                raise ApiError('STATE_CONFLICT', 'The caller ended the session.', 409)
            state['conversation']['escalation'].update(status='connected', connected_at=time.time())
            state['conversation'].update(status='human_connected', case_status='human_active')
            state.update(status='human_connected', provider_status='stopped')
            state['generation'] += 1
            Database.event(connection, session_id, 'handoff.connected', {'operator': operator['username']})
            Database.save(connection, state)
        return self._public(state)

    def renew(self, session_id, capability, operator=None):
        with self.database.transaction() as connection:
            state = self._authorized(connection, session_id, capability, operator)
            if state['desired'] != 'active':
                raise ApiError('STATE_CONFLICT', 'The session ended.', 409)
            if operator and (not state['conversation']['escalation'] or state['conversation']['escalation']['assigned_to'] != operator['username']):
                raise ApiError('FORBIDDEN', 'This channel is not assigned to you.', 403)
        return {'rtc': self._join_material(state, state['human_uid'] if operator else state['caller_uid'])}

    def run_jobs(self):
        # The local ticket adapter atomically deduplicates and records success.
        with self.database.transaction() as connection:
            jobs = connection.execute("SELECT * FROM integration_jobs WHERE status IN ('pending','retry_scheduled') AND next_attempt_at<=? ORDER BY version LIMIT 20", (time.time(),)).fetchall()
            for job in jobs:
                connection.execute('INSERT INTO tickets VALUES(?,?,?,?) ON CONFLICT(session_id) DO UPDATE SET version=excluded.version,payload=excluded.payload WHERE tickets.version<excluded.version',
                                   ('CASE-' + job['session_id'][:8], job['session_id'], job['version'], job['payload']))
                connection.execute("UPDATE integration_jobs SET status='succeeded',attempts=attempts+1 WHERE id=?", (job['id'],))
                _, state = Database.load(connection, job['session_id'])
                current = connection.execute("SELECT count(*) FROM integration_jobs WHERE session_id=? AND status!='succeeded'", (job['session_id'],)).fetchone()[0]
                state['ticket_status'] = 'synced' if current == 0 else 'pending'
                Database.event(connection, job['session_id'], 'ticket.sync.succeeded')
                Database.save(connection, state)

    def retry_job(self, job_id):
        with self.database.transaction() as connection:
            row = connection.execute('SELECT status FROM integration_jobs WHERE id=?', (job_id,)).fetchone()
            if not row:
                raise ApiError('NOT_FOUND', 'Job not found.', 404)
            if row['status'] == 'succeeded':
                return {'status': 'succeeded'}
            connection.execute("UPDATE integration_jobs SET status='pending',next_attempt_at=0 WHERE id=?", (job_id,))
        return {'status': 'pending'}

    def maintain(self):
        now = time.time()
        with self.database.transaction() as connection:
            states = [json.loads(row[0]) for row in connection.execute('SELECT data FROM sessions')]
        for state in states:
            escalation = state['conversation']['escalation']
            expired_queue = state['desired'] == 'active' and escalation and escalation['status'] in {'requested', 'offered', 'accepted'} and now - escalation.get('accepted_at', escalation['requested_at']) > self._settings.queue_wait_seconds
            if expired_queue:
                with self.database.transaction() as connection:
                    _, current = Database.load(connection, state['session_id'])
                    current['conversation']['escalation']['status'] = 'failed'
                    Database.event(connection, state['session_id'], 'handoff.failed', {'reason': 'QUEUE_TIMEOUT'})
                    Database.save(connection, current)
            if expired_queue or (state['desired'] == 'active' and now - state['created_at'] > self._settings.max_call_seconds) or state['status'] == 'ending':
                self.end(state['session_id'], operator={'username': 'system'})
        self.run_jobs()

    def purge(self):
        with self.database.transaction() as connection:
            cursor = connection.execute("DELETE FROM sessions WHERE updated_at<? AND json_extract(data,'$.status')='ended' AND json_extract(data,'$.provider_status')='stopped' AND NOT EXISTS(SELECT 1 FROM integration_jobs WHERE session_id=sessions.id AND status!='succeeded')", (time.time() - self._settings.retention_hours * 3600,))
        return cursor.rowcount
