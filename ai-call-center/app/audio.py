from __future__ import annotations

import audioop
import io
import wave

TWILIO_RATE = 8000  # Гц, 8-bit mu-law, моно
FRAME_MS = 20
FRAME_BYTES = TWILIO_RATE * FRAME_MS // 1000 * 2  # 320 байт 16-бит PCM = 160 байт mu-law


def mulaw_to_pcm(payload: bytes) -> bytes:
    """8 кГц mu-law (Twilio) → 16-бит linear PCM."""
    return audioop.ulaw2lin(payload, 2)


def pcm_to_mulaw(pcm: bytes) -> bytes:
    return audioop.lin2ulaw(pcm, 2)


def to_wav(pcm: bytes, rate: int = TWILIO_RATE) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm)
    return buf.getvalue()


def wav_to_mulaw(data: bytes) -> bytes:
    """WAV от TTS → 8 кГц mu-law, готовый к отправке в Twilio."""
    with wave.open(io.BytesIO(data), "rb") as wav:
        rate = wav.getframerate()
        channels = wav.getnchannels()
        width = wav.getsampwidth()
        pcm = wav.readframes(wav.getnframes())
    if channels > 1:
        pcm = audioop.tomono(pcm, width, 0.5, 0.5)
        channels = 1
    if width != 2:
        pcm = audioop.lin2lin(pcm, width, 2)
        width = 2
    if rate != TWILIO_RATE:
        pcm, _ = audioop.ratecv(pcm, width, channels, rate, TWILIO_RATE, None)
    return pcm_to_mulaw(pcm)


def split_frames(payload: bytes, frame_size: int = 160) -> list[bytes]:
    """Режем mu-law на 20-мс кадры для Twilio <Stream>."""
    return [payload[i : i + frame_size] for i in range(0, len(payload), frame_size)]


def rms(pcm: bytes) -> int:
    return audioop.rms(pcm, 2) if len(pcm) >= 2 else 0
