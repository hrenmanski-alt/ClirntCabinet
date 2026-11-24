from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx

from . import db
from .config import settings
from .dialogue import DialogueEngine, Reply, Session


@dataclass
class CallRecord:
    id: int
    user_id: int
    provider: str
    phone: str
    scenario: str
    session: Session
    status: str = "created"
    provider_sid: str | None = None
    stream_sid: str | None = None
    audio_buffer: bytearray = field(default_factory=bytearray)
    last_voice: float = field(default_factory=time.monotonic)
    started_speaking: bool = False
    processing: bool = False
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    transcript: list[dict[str, str]] = field(default_factory=list)
    created_at: float = field(default_factory=time.monotonic)


class CallProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def start_call(self, call: CallRecord) -> dict[str, Any]:
        """Инициирует исходящий звонок."""

    @abstractmethod
    async def hangup(self, call: CallRecord) -> None:
        """Завершает звонок."""


class MockProvider(CallProvider):
    """Демо-провайдер: звонок имитируется, всё остальное работает по-настоящему."""

    name = "mock"

    async def start_call(self, call: CallRecord) -> dict[str, Any]:
        call.status = "in_progress"
        db.set_call_status(call.id, "in_progress")
        return {"call_id": call.id, "mode": "demo", "status": "in_progress"}

    async def hangup(self, call: CallRecord) -> None:
        call.status = "completed"
        db.set_call_status(call.id, "completed")


class TwilioProvider(CallProvider):
    """Реальные исходящие звонки через Twilio REST API."""

    name = "twilio"

    async def start_call(self, call: CallRecord) -> dict[str, Any]:
        missing = [
            name
            for name, value in (
                ("TWILIO_ACCOUNT_SID", settings.twilio_account_sid),
                ("TWILIO_AUTH_TOKEN", settings.twilio_auth_token),
                ("TWILIO_FROM_NUMBER", settings.twilio_from_number),
                ("PUBLIC_BASE_URL", settings.public_base_url),
            )
            if not value
        ]
        if missing:
            raise RuntimeError("Не настроены: " + ", ".join(missing))

        voice_url = (
            f"{settings.public_base_url}/twilio/voice"
            f"?call_id={call.id}&scenario={call.scenario}"
        )
        status_url = f"{settings.public_base_url}/twilio/status?call_id={call.id}"

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "https://api.twilio.com/2010-04-01/Accounts/"
                f"{settings.twilio_account_sid}/Calls.json",
                auth=httpx.BasicAuth(settings.twilio_account_sid, settings.twilio_auth_token),
                data={
                    "To": call.phone,
                    "From": settings.twilio_from_number,
                    "Url": voice_url,
                    "StatusCallback": status_url,
                },
            )
            response.raise_for_status()
            sid = response.json().get("sid", "")

        call.provider_sid = sid
        call.status = "dialing"
        db.set_call_status(call.id, "dialing")
        return {"call_id": call.id, "mode": "real", "provider_sid": sid, "status": "dialing"}

    async def hangup(self, call: CallRecord) -> None:
        if not call.provider_sid:
            return
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                "https://api.twilio.com/2010-04-01/Accounts/"
                f"{settings.twilio_account_sid}/Calls/{call.provider_sid}.json",
                auth=httpx.BasicAuth(settings.twilio_account_sid, settings.twilio_auth_token),
                data={"Status": "completed"},
            )


class NovofonProvider(CallProvider):
    """Заготовка под российского SIP-провайдера Novofon.

    В отличие от Twilio, у Novofon нет готового WebSocket-медиа в таком же виде:
    нужен SIP-шлюз (Asterisk / FreeSWITCH), который принимает звонок и отдаёт
    аудио на наш сервер. Код шлюза появится после получения SIP-доступа.
    """

    name = "novofon"

    async def start_call(self, call: CallRecord) -> dict[str, Any]:
        raise RuntimeError(
            "Novofon требует SIP-шлюз (Asterisk/FreeSWITCH) и данные доступа. "
            "Смотрите NOVOFON.md."
        )

    async def hangup(self, call: CallRecord) -> None:
        return None


class CallManager:
    """Управляет жизненным циклом звонков и связывает их с ИИ-ядром."""

    def __init__(self) -> None:
        self.engine = DialogueEngine()
        self.calls: dict[int, CallRecord] = {}
        self.providers: dict[str, CallProvider] = {
            "mock": MockProvider(),
            "twilio": TwilioProvider(),
            "novofon": NovofonProvider(),
        }

    def create(self, user_id: int, phone: str, scenario: str, provider: str) -> CallRecord:
        provider = provider if provider in self.providers else "mock"
        session = self.engine.new_session(scenario)
        call_id = db.create_call(user_id, phone, scenario, provider)
        call = CallRecord(
            id=call_id,
            user_id=user_id,
            provider=provider,
            phone=phone,
            scenario=scenario,
            session=session,
        )
        self.calls[call_id] = call
        return call

    def get(self, call_id: int) -> CallRecord | None:
        return self.calls.get(call_id)

    def attach_stream(self, call: CallRecord, stream_sid: str) -> None:
        call.stream_sid = stream_sid
        call.status = "in_progress"
        db.set_call_status(call.id, "in_progress")

    async def start(self, call: CallRecord) -> dict[str, Any]:
        return await self.providers[call.provider].start_call(call)

    async def greeting(self, call: CallRecord) -> Reply:
        reply = await self.engine.greeting(call.session)
        await self._record(call, "assistant", reply.text)
        if reply.end_call:
            await self.finish(call)
        return reply

    async def respond(self, call: CallRecord, text: str) -> Reply:
        reply = await self.engine.reply(call.session, text)
        await self._record(call, "user", text)
        await self._record(call, "assistant", reply.text)
        if reply.end_call:
            await self.finish(call, result=self._result(call))
        return reply

    async def finish(self, call: CallRecord, result: str | None = None) -> None:
        call.status = "completed"
        db.finish_call(call.id, result=result or self._result(call), status="completed")
        try:
            await self.providers[call.provider].hangup(call)
        except Exception as exc:
            print(f"[call] hangup error: {exc}")
        self.calls.pop(call.id, None)

    async def fail(self, call: CallRecord, reason: str = "") -> None:
        call.status = "failed"
        db.finish_call(call.id, result=reason, status="failed")
        self.calls.pop(call.id, None)

    async def _record(self, call: CallRecord, role: str, text: str) -> None:
        call.transcript.append({"role": role, "text": text})
        db.append_transcript(call.id, role, text)

    @staticmethod
    def _result(call: CallRecord) -> str:
        data = call.session.data
        parts = []
        if data.get("name"):
            parts.append(f"Клиент: {data['name']}")
        if data.get("phone"):
            parts.append(f"Телефон: {data['phone']}")
        if data.get("interest"):
            parts.append(f"Интерес: {data['interest']}")
        if data.get("issue"):
            parts.append(f"Вопрос: {data['issue']}")
        return "; ".join(parts) or "Диалог завершён"


call_manager = CallManager()
