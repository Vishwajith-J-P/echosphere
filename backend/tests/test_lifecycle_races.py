from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from echosphere.services.agora_gateway import AgentStart, AgoraGateway
from echosphere.services.sessions import SessionService


class ControlledGateway:
    """Model a remote provider whose start can complete after local hangup."""

    def __init__(self, *, block_start: bool = False, fail_stop_once: bool = False):
        self.start_entered = Event()
        self.release_start = Event()
        if not block_start:
            self.release_start.set()
        self.active_sessions: set[str] = set()
        self.fail_stop_once = fail_stop_once

    def issue_token(self, channel: str, uid: int) -> str:
        return "synthetic-token"

    def start(self, *, session_id: str, **_kwargs) -> AgentStart:
        self.start_entered.set()
        assert self.release_start.wait(timeout=5), "Test did not release provider start"
        self.active_sessions.add(session_id)
        return AgentStart(agent_id="synthetic-agent")

    def stop(self, session_id: str) -> None:
        if session_id in self.active_sessions and self.fail_stop_once:
            self.fail_stop_once = False
            raise RuntimeError("Synthetic provider stop failure")
        self.active_sessions.discard(session_id)


def test_late_start_cannot_resurrect_ended_session_or_leave_provider_active(settings):
    gateway = ControlledGateway(block_start=True)
    service = SessionService(gateway, settings)
    created = service.create("hi-IN")
    session_id, capability = created["session_id"], created["caller_capability"]

    with ThreadPoolExecutor(max_workers=1) as executor:
        start = executor.submit(service.start, session_id, capability)
        try:
            assert gateway.start_entered.wait(timeout=5), "Provider start was not entered"
            service.end(session_id, capability)
        finally:
            gateway.release_start.set()
        start.result(timeout=5)

    final = service.get(session_id, capability)
    assert final["status"] == "ended"
    assert final["agent_connected"] is False
    assert session_id not in gateway.active_sessions


def test_failed_stop_remains_pending_and_second_end_retries_cleanup(settings):
    gateway = ControlledGateway(fail_stop_once=True)
    service = SessionService(gateway, settings)
    created = service.create("ta-IN")
    session_id, capability = created["session_id"], created["caller_capability"]
    service.start(session_id, capability)

    # Transport failure may be returned as pending state or raised to the caller;
    # either way, state must preserve the outstanding cleanup obligation.
    try:
        service.end(session_id, capability)
    except RuntimeError:
        pass

    pending = service.get(session_id, capability)
    assert pending["status"] != "ended", "Failed stop must not claim completed cleanup"
    assert session_id in gateway.active_sessions

    ended = service.end(session_id, capability)
    assert ended["status"] == "ended"
    assert ended["agent_connected"] is False
    assert session_id not in gateway.active_sessions


def test_agora_gateway_keeps_failed_stop_provider_available_for_retry():
    class ProviderSession:
        active = True
        fail_stop_once = True

        def stop(self):
            if self.fail_stop_once:
                self.fail_stop_once = False
                raise RuntimeError("Synthetic provider stop failure")
            self.active = False

    # Inject the remote boundary without initializing the SDK or credentials.
    gateway = AgoraGateway.__new__(AgoraGateway)
    provider = ProviderSession()
    gateway._sessions = {"synthetic-session": provider}

    with pytest.raises(RuntimeError, match="Synthetic provider stop failure"):
        gateway.stop("synthetic-session")

    gateway.stop("synthetic-session")
    assert provider.active is False, "Retry must retain and stop the original provider"
