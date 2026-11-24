from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    mode: str = os.getenv("AI_CALL_MODE", "demo").lower()
    scenario: str = os.getenv("AI_CALL_SCENARIO", "sales").lower()
    language: str = os.getenv("AI_CALL_LANGUAGE", "ru").lower()

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    stt_model: str = os.getenv("STT_MODEL", "gpt-4o-mini-transcribe")
    tts_model: str = os.getenv("TTS_MODEL", "gpt-4o-mini-tts")
    tts_voice: str = os.getenv("TTS_VOICE", "nova")

    call_provider: str = os.getenv("CALL_PROVIDER", "mock").lower()
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_from_number: str = os.getenv("TWILIO_FROM_NUMBER", "")
    public_ws_url: str = os.getenv("PUBLIC_WS_URL", "").strip()
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "").strip()

    novofon_sip_host: str = os.getenv("NOVOFON_SIP_HOST", "").strip()
    novofon_sip_user: str = os.getenv("NOVOFON_SIP_USER", "").strip()
    novofon_sip_password: str = os.getenv("NOVOFON_SIP_PASSWORD", "").strip()
    novofon_from_number: str = os.getenv("NOVOFON_FROM_NUMBER", "").strip()
    novofon_gateway_ws_url: str = os.getenv("NOVOFON_GATEWAY_WS_URL", "").strip()

    vad_threshold: int = _int("VAD_THRESHOLD", 350)
    silence_ms: int = _int("SILENCE_MS", 700)
    max_utterance_ms: int = _int("MAX_UTTERANCE_MS", 15000)

    @property
    def brain_is_llm(self) -> bool:
        return self.mode == "openai" and bool(self.openai_api_key)

    @property
    def server_audio(self) -> bool:
        """Нужна ли серверная обработка аудио (для телефонного потока)."""
        return self.mode == "openai" and bool(self.openai_api_key)


settings = Settings()
