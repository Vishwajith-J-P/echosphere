"""Isolated browser fixture for the voice-only surface. Never imports local .env."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from echosphere import create_app
from echosphere.config import Settings
from echosphere.cli import start_maintenance


class NoVoiceGateway:
    def issue_token(self, *_):
        raise RuntimeError('Live voice is disabled in browser fixtures')


app = create_app(Settings('', '', '', '', secret_key='synthetic-browser-only-key', app_env='test'), NoVoiceGateway())
app.extensions['auth_service'].create_user('demo-agent', 'synthetic-browser-password', 'supervisor')
start_maintenance(app)
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8100, threaded=True, use_reloader=False)
