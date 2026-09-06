from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class Settings:
    agora_app_id: str
    agora_app_certificate: str
    agora_customer_id: str
    agora_customer_secret: str
    agora_region: str = "global"
    agora_agent_area: str = "ap"
    agora_token_ttl_seconds: int = 3600
    app_env: str = "development"
    secret_key: str = ""
    operator_access_token: str = ''
    operator_username: str = 'supervisor'
    database_path: str = ':memory:'
    public_base_url: str = ''
    speech_provider: str = 'deepgram'
    sarvam_api_key: str = ''
    sarvam_stt_model: str = 'saaras:v3'
    sarvam_tts_speaker: str = 'priya'
    tts_model: str = 'speech-2.6-turbo'
    tts_voice: str = 'English_CalmWoman'
    max_sessions: int = 10
    max_call_seconds: int = 1800
    queue_wait_seconds: int = 120
    retention_hours: int = 24

    @classmethod
    def from_environment(cls) -> "Settings":
        load_dotenv(PROJECT_ROOT / ".env", override=False)
        required = ("SECRET_KEY",)
        missing = [name for name in required if not os.getenv(name, "").strip()]
        if missing:
            raise ConfigurationError(
                "Missing required environment variables: " + ", ".join(missing)
            )

        try:
            token_ttl = int(os.getenv("AGORA_TOKEN_TTL_SECONDS", "3600"))
        except ValueError as exc:
            raise ConfigurationError(
                "AGORA_TOKEN_TTL_SECONDS must be an integer"
            ) from exc
        if not 300 <= token_ttl <= 86400:
            raise ConfigurationError(
                "AGORA_TOKEN_TTL_SECONDS must be between 300 and 86400"
            )

        return cls(
            agora_app_id=os.getenv("AGORA_APP_ID", '').strip(),
            agora_app_certificate=os.getenv("AGORA_APP_CERTIFICATE", '').strip(),
            agora_customer_id=os.getenv("AGORA_CUSTOMER_ID", '').strip(),
            agora_customer_secret=os.getenv("AGORA_CUSTOMER_SECRET", '').strip(),
            agora_region=os.getenv("AGORA_REGION", "global").strip().lower(),
            agora_agent_area=os.getenv("AGORA_AGENT_AREA", "ap").strip().lower(),
            agora_token_ttl_seconds=token_ttl,
            app_env=os.getenv("APP_ENV", "development").strip().lower(),
            secret_key=os.getenv("SECRET_KEY", ""),
            operator_access_token=os.getenv('OPERATOR_ACCESS_TOKEN', '').strip(),
            operator_username=os.getenv('OPERATOR_USERNAME', 'supervisor').strip() or 'supervisor',
            database_path=os.getenv('DATABASE_PATH', str(PROJECT_ROOT / 'instance' / 'echosphere.sqlite3')),
            public_base_url=os.getenv('PUBLIC_BASE_URL', '').rstrip('/'),
            speech_provider=os.getenv('SPEECH_PROVIDER', 'deepgram'),
            sarvam_api_key=os.getenv('SARVAM_API_KEY', ''),
            sarvam_stt_model=os.getenv('SARVAM_STT_MODEL', 'saaras:v3'),
            sarvam_tts_speaker=os.getenv('SARVAM_TTS_SPEAKER', 'priya'),
            tts_model=os.getenv('AGORA_TTS_MODEL', 'speech-2.6-turbo'),
            tts_voice=os.getenv('AGORA_TTS_VOICE', 'English_CalmWoman'),
            max_sessions=int(os.getenv('MAX_ACTIVE_SESSIONS', '10')),
            max_call_seconds=int(os.getenv('MAX_CALL_SECONDS', '1800')),
            queue_wait_seconds=int(os.getenv('QUEUE_WAIT_SECONDS', '120')),
            retention_hours=int(os.getenv('RETENTION_HOURS', '24')),
        )

    def __post_init__(self):
        if self.agora_agent_area not in {'us', 'eu', 'ap', 'cn'}:
            raise ConfigurationError('AGORA_AGENT_AREA must be us, eu, ap, or cn')
        if self.speech_provider not in {'deepgram', 'sarvam'}:
            raise ConfigurationError('SPEECH_PROVIDER must be deepgram or sarvam')
        if self.public_base_url:
            from urllib.parse import urlsplit
            parsed = urlsplit(self.public_base_url)
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ConfigurationError('PUBLIC_BASE_URL must be a public HTTPS base URL')
        if not 1 <= self.max_sessions <= 100 or not 60 <= self.max_call_seconds <= 7200:
            raise ConfigurationError('Session limits are outside the supported prototype range')
        if not 10 <= self.queue_wait_seconds <= 600 or not 1 <= self.retention_hours <= 168:
            raise ConfigurationError('Queue or retention limit is outside the supported range')
