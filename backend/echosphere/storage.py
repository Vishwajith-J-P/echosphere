"""SQLite repositories for one-process prototype operation.

Transactions serialize aggregate changes and their audit/outbox writes. No provider
network call runs inside a transaction. See docs/technical/backend_schema.md.
"""
import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path

MIGRATION_1 = '''
CREATE TABLE IF NOT EXISTS sessions (
 id TEXT PRIMARY KEY, capability_hash TEXT NOT NULL, expires_at REAL NOT NULL,
 data TEXT NOT NULL, updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_events (
 sequence INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
 event_type TEXT NOT NULL, payload TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS processed_events (
 session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
 event_id TEXT NOT NULL, body_hash TEXT NOT NULL, response TEXT NOT NULL,
 PRIMARY KEY(session_id, event_id)
);
CREATE TABLE IF NOT EXISTS handoff_snapshots (
 session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
 version INTEGER NOT NULL, data TEXT NOT NULL, PRIMARY KEY(session_id, version)
);
CREATE TABLE IF NOT EXISTS integration_jobs (
 id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
 version INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0,
 next_attempt_at REAL NOT NULL DEFAULT 0, last_error TEXT, payload TEXT NOT NULL,
 UNIQUE(session_id, version)
);
CREATE TABLE IF NOT EXISTS tickets (
 id TEXT PRIMARY KEY, session_id TEXT NOT NULL UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
 version INTEGER NOT NULL, payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS admission (bucket TEXT NOT NULL, window INTEGER NOT NULL, count INTEGER NOT NULL, PRIMARY KEY(bucket, window));
PRAGMA user_version=1;
'''

MIGRATION_2 = '''
DROP TABLE IF EXISTS operator_sessions;
DROP TABLE IF EXISTS users;
PRAGMA user_version=2;
'''


class Database:
    def __init__(self, path: str):
        if path != ':memory:':
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, check_same_thread=False, isolation_level=None, timeout=10)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.execute('PRAGMA journal_mode=WAL')
        self.lock = threading.RLock()
        version = self.connection.execute('PRAGMA user_version').fetchone()[0]
        if version > 2:
            raise RuntimeError('Database is newer than this application')
        if version == 0:
            self.connection.executescript('BEGIN IMMEDIATE;\n' + MIGRATION_1 + '\nCOMMIT;')
            version = 1
        if version == 1:
            self.connection.executescript('BEGIN IMMEDIATE;\n' + MIGRATION_2 + '\nCOMMIT;')

    @contextmanager
    def transaction(self):
        with self.lock:
            self.connection.execute('BEGIN IMMEDIATE')
            try:
                yield self.connection
                self.connection.execute('COMMIT')
            except BaseException:
                self.connection.execute('ROLLBACK')
                raise

    @staticmethod
    def load(connection, session_id):
        row = connection.execute('SELECT * FROM sessions WHERE id=?', (session_id,)).fetchone()
        return (row, json.loads(row['data'])) if row else (None, None)

    @staticmethod
    def save(connection, state):
        connection.execute('UPDATE sessions SET data=?,updated_at=? WHERE id=?',
                           (json.dumps(state, ensure_ascii=False), time.time(), state['session_id']))

    @staticmethod
    def event(connection, session_id, event_type, payload=None):
        connection.execute('INSERT INTO audit_events(session_id,event_type,payload,created_at) VALUES(?,?,?,?)',
                           (session_id, event_type, json.dumps(payload or {}), time.time()))

    def limit(self, bucket: str, maximum: int, seconds=60):
        from .errors import ApiError
        window = int(time.time()) // seconds
        with self.transaction() as connection:
            connection.execute('DELETE FROM admission WHERE window<?', (window - 2,))
            connection.execute('INSERT INTO admission VALUES(?,?,1) ON CONFLICT(bucket,window) DO UPDATE SET count=count+1', (bucket, window))
            count = connection.execute('SELECT count FROM admission WHERE bucket=? AND window=?', (bucket, window)).fetchone()[0]
        if count > maximum:
            raise ApiError('RATE_LIMITED', 'Too many requests. Please wait and try again.', 429)
