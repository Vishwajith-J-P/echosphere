from __future__ import annotations

from dataclasses import dataclass

from agora_agent import (
    Agent,
    Agora,
    Area,
    DeepgramSTT,
    MiniMaxTTS,
    CustomLLM,
    SarvamSTT,
    generate_convo_ai_token,
)

from ..config import Settings
from ..domain.conversation import COPY


SYSTEM_MESSAGE = """You are EchoSphere, an AI intake assistant.
Clearly identify yourself as AI. Speak briefly and calmly.
 Support Hindi, English, and Tamil, including natural code-switching.
When the caller states an issue, acknowledge it once and take the next permitted action: ask the next focused intake question, confirm or correct the current fact, queue a follow-up case after required facts are confirmed, or request a human. Never repeat an issue without asking a question or taking one of those actions.
Never provide medical diagnosis or authoritative legal, financial, or emergency advice.
If such judgement is requested, or the caller requests a human, say you will transfer them.
Use the caller's latest utterance and the conversation context to choose one useful next action. You can answer the approved local FAQ catalogue, collect and confirm issue details, explain the next step, or escalate. For basic support tasks, give short step-by-step instructions and then ask whether the task worked. If a task needs an external account, payment, reset, dispatch, or a policy decision, do not claim it was completed: record the request and offer a human. Never present uncertain information as confirmed fact."""


@dataclass(frozen=True, slots=True)
class AgentStart:
    agent_id: str


class AgoraGateway:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = Agora(
            area=self._area(settings.agora_agent_area),
            app_id=settings.agora_app_id,
            app_certificate=settings.agora_app_certificate,
        )
        self._sessions: dict[str, object] = {}

    @staticmethod
    def _area(region: str) -> Area:
        return {
            "us": Area.US,
            "eu": Area.EU,
            "ap": Area.AP,
            "cn": Area.CN,
        }[region]

    def issue_token(self, channel: str, uid: int) -> str:
        return generate_convo_ai_token(
            self._settings.agora_app_id,
            self._settings.agora_app_certificate,
            channel,
            uid,
            token_expire=self._settings.agora_token_ttl_seconds,
        )

    def start(
        self,
        *,
        session_id: str,
        channel: str,
        caller_uid: int,
        agent_uid: int,
        requested_language: str = 'en-IN',
        control_token: str = '',
    ) -> AgentStart:
        if not self._settings.public_base_url:
            raise ValueError('PUBLIC_BASE_URL is required for controlled voice')
        stt = (SarvamSTT(api_key=self._settings.sarvam_api_key, language='unknown',
                         model=self._settings.sarvam_stt_model, additional_params={'mode': 'transcribe'})
               if self._settings.speech_provider == 'sarvam' else
               DeepgramSTT(model='nova-3', language='ta' if requested_language == 'ta-IN' else 'multi'))
        agent = (
            Agent(self._client)
            .with_stt(stt)
            .with_llm(
                CustomLLM(
                    model='echosphere-intake-v1', api_key=control_token,
                    base_url=f'{self._settings.public_base_url}/api/sessions/{session_id}/llm/chat/completions',
                    system_messages=[{'role': 'system', 'content': SYSTEM_MESSAGE + '\nUse Hindi, English, or Tamil only. Follow the controlled response exactly; do not invent a resolution.'}],
                    greeting_message=COPY[requested_language]['greeting'],
                    failure_message=COPY[requested_language]['waiting'],
                    max_history=20,
                )
            )
            .with_tts(
                (SarvamTTS(
                    key=self._settings.sarvam_api_key,
                    speaker=self._settings.sarvam_tts_speaker,
                    target_language_code=requested_language,
                ) if self._settings.speech_provider == 'sarvam' else MiniMaxTTS(
                    model=self._settings.tts_model,
                    voice_id=self._settings.tts_voice,
                    language_boost="auto",
                ))
            )
        )
        provider_session = agent.create_session(
            channel=channel,
            agent_uid=str(agent_uid),
            remote_uids=[str(caller_uid)],
            name=session_id,
            idle_timeout=120,
        )
        agent_id = provider_session.start()
        self._sessions[session_id] = provider_session
        return AgentStart(agent_id=agent_id)

    def stop(self, session_id: str) -> None:
        provider_session = self._sessions.get(session_id)
        if provider_session is not None:
            provider_session.stop()
            self._sessions.pop(session_id, None)

    def stop_agent(self, session_id: str, agent_id: str | None):
        if session_id in self._sessions:
            return self.stop(session_id)
        if not agent_id:
            return
        # Server REST fallback restores cleanup after process restart.
        import requests
        response = requests.post(
            f'https://api.agora.io/api/conversational-ai-agent/v2/projects/{self._settings.agora_app_id}/agents/{agent_id}/leave',
            auth=(self._settings.agora_customer_id, self._settings.agora_customer_secret), timeout=(5, 10))
        if response.status_code not in {200, 204, 404}:
            raise RuntimeError('Agora cleanup is pending')

    def verify_participants(self, channel: str, caller_uid: int, human_uid: int) -> bool:
        """Check channel membership server-side before declaring a warm handoff connected.

        Agora's channel-user status endpoint is queried only by the server; browser
        presence is treated as a readiness hint, never as authoritative evidence.
        """
        import requests
        base = 'https://api.agora.io/dev/v1/channel/user/property'
        for uid in (caller_uid, human_uid):
            response = requests.get(f'{base}/{self._settings.agora_app_id}/{uid}/{channel}',
                                    auth=(self._settings.agora_customer_id, self._settings.agora_customer_secret),
                                    timeout=(5, 10))
            if response.status_code != 200 or not response.json().get('data', {}).get('in_channel', False):
                return False
        return True
