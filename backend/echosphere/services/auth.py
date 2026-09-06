import hashlib
import secrets
import time

from werkzeug.security import check_password_hash, generate_password_hash

from ..errors import ApiError


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class AuthService:
    def __init__(self, database):
        self.database = database

    def create_user(self, username, password, role):
        if role not in {'agent', 'supervisor'} or len(password) < 12 or not 1 <= len(username) <= 80:
            raise ValueError('Use an agent/supervisor role and a password with at least 12 characters')
        with self.database.transaction() as connection:
            connection.execute('INSERT INTO users VALUES(?,?,?)', (username, generate_password_hash(password), role))

    def login(self, username, password):
        with self.database.transaction() as connection:
            row = connection.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
        if not row or not check_password_hash(row['password_hash'], password):
            raise ApiError('UNAUTHORIZED', 'The username or password is incorrect.', 401)
        token = secrets.token_urlsafe(32)
        with self.database.transaction() as connection:
            connection.execute('DELETE FROM operator_sessions WHERE expires_at<?', (time.time(),))
            connection.execute('INSERT INTO operator_sessions VALUES(?,?,?)', (digest(token), username, time.time() + 28800))
        return {'token': token, 'username': username, 'role': row['role']}

    def identify(self, token):
        with self.database.transaction() as connection:
            row = connection.execute('SELECT username,role FROM operator_sessions JOIN users USING(username) WHERE token_hash=? AND expires_at>?', (digest(token), time.time())).fetchone()
        return dict(row) if row else None

    def logout(self, token):
        with self.database.transaction() as connection:
            connection.execute('DELETE FROM operator_sessions WHERE token_hash=?', (digest(token),))
