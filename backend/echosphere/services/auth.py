import hashlib
import hmac

from ..errors import ApiError


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class AuthService:
    """Passwordless operator authentication using one configured bearer secret."""

    def __init__(self, database, access_token='', username='supervisor'):
        self.database = database
        self.access_token = access_token
        self.username = username

    def login(self, access_token):
        if not self.access_token or not hmac.compare_digest(access_token, self.access_token):
            raise ApiError('UNAUTHORIZED', 'The operator access token is incorrect.', 401)
        return {'token': self.access_token, 'username': self.username, 'role': 'supervisor'}

    def identify(self, token):
        if self.access_token and token and hmac.compare_digest(token, self.access_token):
            return {'username': self.username, 'role': 'supervisor'}
        return None

    def logout(self, _token):
        return None
