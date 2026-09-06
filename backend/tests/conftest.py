from __future__ import annotations

import pytest

from echosphere import create_app
from echosphere.config import Settings


class FakeGateway:
    def issue_token(self, channel: str, uid: int) -> str:
        return f"token-{channel}-{uid}"

    def start(self, **_kwargs):
        return type("Started", (), {"agent_id": "agent-test"})()

    def stop(self, _session_id: str) -> None:
        return None

    def verify_participants(self, _channel: str, _caller_uid: int, _human_uid: int) -> bool:
        return True


@pytest.fixture
def settings() -> Settings:
    return Settings(
        agora_app_id="test-app-id",
        agora_app_certificate="test-certificate",
        agora_customer_id="test-customer",
        agora_customer_secret="test-secret",
        app_env="test",
        secret_key="test-only",
    )


@pytest.fixture
def app(settings):
    application = create_app(settings, gateway=FakeGateway())
    application.config.update(TESTING=True)
    return application


@pytest.fixture
def client(app):
    return app.test_client()
