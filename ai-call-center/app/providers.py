from __future__ import annotations

import httpx

from .audio import to_wav, wav_to_mulaw
from .config import settings


class SpeechToText:
    """Whisper-совместимый STT. В demo-режиме распознавание делает браузер."""

    async def transcribe(self, pcm_8k: bytes) -> str:
        if not settings.server_audio:
            return ""
        if len(pcm_8k) < 1600:
            return ""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.openai_base_url}/audio/transcriptions",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    files={"file": ("speech.wav", to_wav(pcm_8k), "audio/wav")},
                    data={"model": settings.stt_model, "language": settings.language},
                )
                response.raise_for_status()
                return response.json().get("text", "").strip()
        except Exception as exc:
            print(f"[stt] error: {exc}")
            return ""


class TextToSpeech:
    """TTS → mu-law 8 кГц для телефонного потока. В демо говорит браузер."""

    async def synthesize(self, text: str) -> bytes:
        if not settings.server_audio or not text.strip():
            return b""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.openai_base_url}/audio/speech",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    json={
                        "model": settings.tts_model,
                        "voice": settings.tts_voice,
                        "input": text[:1000],
                        "response_format": "wav",
                    },
                )
                response.raise_for_status()
                return wav_to_mulaw(response.content)
        except Exception as exc:
            print(f"[tts] error: {exc}")
            return b""


stt = SpeechToText()
tts = TextToSpeech()
