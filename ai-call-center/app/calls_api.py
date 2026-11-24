from __future__ import annotations

import asyncio
import base64
import json
import time
from typing import Any

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from . import audio, db
from .config import settings
from .providers import stt, tts
from .telephony import CallRecord, call_manager

router = APIRouter()
COOKIE = "cc_session"


class CallRequest(BaseModel):
    phone: str = ""
    scenario: str = "sales"
    provider: str = "mock"


def _user(request: Request):
    return db.get_session_user(request.cookies.get(COOKIE))


def _unauthorized() -> JSONResponse:
    return JSONResponse({"detail": "Нужно войти в аккаунт"}, status_code=401)


# ── REST ────────────────────────────────────────────────────────────────────
@router.post("/api/calls")
async def start_call(request: Request, payload: CallRequest):
    user = _user(request)
    if not user:
        return _unauthorized()
    try:
        call = call_manager.create(user["id"], payload.phone, payload.scenario, payload.provider)
        info = await call_manager.start(call)
        return {"ok": True, **info}
    except Exception as exc:
        return JSONResponse({"ok": False, "detail": str(exc)}, status_code=400)


@router.get("/api/calls")
def list_calls(request: Request):
    user = _user(request)
    if not user:
        return _unauthorized()
    return [
        {
            "id": row["id"],
            "phone": row["phone"],
            "scenario": row["scenario"],
            "provider": row["provider"],
            "status": row["status"],
            "result": row["result"],
            "created_at": row["created_at"],
        }
        for row in db.list_calls(user["id"])
    ]


@router.get("/api/calls/{call_id}")
def get_call(request: Request, call_id: int):
    user = _user(request)
    if not user:
        return _unauthorized()
    row = db.get_call(call_id, user["id"])
    if not row:
        return JSONResponse({"detail": "Звонок не найден"}, status_code=404)
    return {
        "id": row["id"],
        "phone": row["phone"],
        "scenario": row["scenario"],
        "status": row["status"],
        "result": row["result"],
        "transcript": json.loads(row["transcript"] or "[]"),
    }


@router.post("/api/calls/{call_id}/hangup")
async def hangup(request: Request, call_id: int):
    user = _user(request)
    if not user:
        return _unauthorized()
    call = call_manager.get(call_id)
    if call and call.user_id == user["id"]:
        await call_manager.finish(call)
    else:
        db.finish_call(call_id, result="Прервано пользователем", status="completed")
    return {"ok": True}


# ── Webhooks телефонии ──────────────────────────────────────────────────────
@router.post("/twilio/voice", include_in_schema=False)
async def twilio_voice(request: Request):
    call_id = int(request.query_params.get("call_id", 0))
    scenario = request.query_params.get("scenario", "sales")
    base = settings.public_ws_url or str(request.base_url).replace("http", "ws", 1).rstrip("/") + "/ws/twilio"
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response><Connect>"
        f'<Stream url="{base}?call_id={call_id}&amp;scenario={scenario}"></Stream>'
        "</Connect></Response>"
    )
    return Response(xml, media_type="application/xml")


@router.post("/twilio/status", include_in_schema=False)
async def twilio_status(request: Request):
    form = await request.form()
    call_id = int(request.query_params.get("call_id", 0))
    status = str(form.get("CallStatus", ""))
    mapping = {
        "ringing": "ringing",
        "in-progress": "in_progress",
        "completed": "completed",
        "failed": "failed",
        "busy": "failed",
        "no-answer": "failed",
    }
    if call_id and status in mapping:
        db.set_call_status(call_id, mapping[status])
    return {"ok": True}


# ── WebSocket: разговор в браузере ──────────────────────────────────────────
@router.websocket("/ws/browser")
async def browser_ws(websocket: WebSocket):
    await websocket.accept()
    user = db.get_session_user(websocket.cookies.get(COOKIE))
    if not user:
        await websocket.close(code=4401)
        return

    call_id = int(websocket.query_params.get("call_id", 0))
    scenario = websocket.query_params.get("scenario", settings.scenario)
    call = call_manager.get(call_id) if call_id else None
    if not call:
        call = call_manager.create(user["id"], "браузер", scenario, "mock")
        await call_manager.start(call)

    try:
        await websocket.send_json({"type": "ready", "call_id": call.id})
        greeting = await call_manager.greeting(call)
        await websocket.send_json(
            {"type": "reply", "text": greeting.text, "end": greeting.end_call}
        )
        if greeting.end_call:
            return

        while True:
            message = await websocket.receive_json()
            kind = message.get("type")
            if kind == "stop":
                break
            if kind != "text":
                continue
            text = str(message.get("text", "")).strip()
            if not text:
                continue
            reply = await call_manager.respond(call, text)
            await websocket.send_json(
                {"type": "reply", "text": reply.text, "end": reply.end_call}
            )
            if reply.end_call:
                break
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        print(f"[ws/browser] error: {exc}")
    finally:
        if call_manager.get(call.id):
            await call_manager.finish(call)


# ── WebSocket: телефонный аудиопоток ────────────────────────────────────────
@router.websocket("/ws/twilio")
async def twilio_ws(websocket: WebSocket):
    await websocket.accept()
    call_id = int(websocket.query_params.get("call_id", 0))
    call = call_manager.get(call_id)
    if not call:
        row = db.get_call(call_id)
        if row:
            scenario = websocket.query_params.get("scenario", row["scenario"])
            call = CallRecord(
                id=call_id,
                user_id=row["user_id"],
                provider=row["provider"],
                phone=row["phone"],
                scenario=scenario,
                session=call_manager.engine.new_session(scenario),
            )
            call_manager.calls[call_id] = call
    if not call:
        await websocket.close(code=4404)
        return

    tasks: set[asyncio.Task] = set()

    async def send_media(payload: bytes) -> None:
        if not call.stream_sid:
            return
        for frame in audio.split_frames(payload):
            await websocket.send_json(
                {
                    "event": "media",
                    "streamSid": call.stream_sid,
                    "media": {"payload": base64.b64encode(frame).decode()},
                }
            )

    async def process_speech() -> None:
        if call.processing:
            return
        async with call.lock:
            if call.processing:
                return
            call.processing = True
            try:
                pcm = bytes(call.audio_buffer)
                call.audio_buffer.clear()
                text = await stt.transcribe(pcm)
                if not text:
                    return
                reply = await call_manager.respond(call, text)
                if settings.server_audio:
                    voice = await tts.synthesize(reply.text)
                    if voice:
                        await send_media(voice)
                if reply.end_call and call.stream_sid:
                    await websocket.send_json(
                        {"event": "clear", "streamSid": call.stream_sid}
                    )
            except Exception as exc:
                print(f"[ws/twilio] processing error: {exc}")
            finally:
                call.processing = False
                call.last_voice = time.monotonic()
                call.started_speaking = False

    try:
        while True:
            message = await websocket.receive_json()
            event = message.get("event")

            if event == "start":
                start = message.get("start", {})
                call.stream_sid = start.get("streamSid")
                call_manager.attach_stream(call, call.stream_sid or "")
                greeting = await call_manager.greeting(call)
                if settings.server_audio:
                    voice = await tts.synthesize(greeting.text)
                    if voice:
                        await send_media(voice)

            elif event == "media":
                payload = base64.b64decode(message["media"]["payload"])
                pcm = audio.mulaw_to_pcm(payload)
                call.audio_buffer.extend(pcm)
                level = audio.rms(pcm)
                now = time.monotonic()

                if level > settings.vad_threshold:
                    if not call.started_speaking and call.stream_sid:
                        # Абонент перебил ИИ — прекращаем воспроизведение
                        await websocket.send_json(
                            {"event": "clear", "streamSid": call.stream_sid}
                        )
                        call.started_speaking = True
                    call.last_voice = now

                silence_ms = (now - call.last_voice) * 1000
                long_enough = len(call.audio_buffer) >= settings.vad_threshold * 4
                if (
                    silence_ms >= settings.silence_ms
                    and long_enough
                    and not call.processing
                ):
                    task = asyncio.create_task(process_speech())
                    tasks.add(task)
                    task.add_done_callback(tasks.discard)

            elif event == "stop":
                break

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        print(f"[ws/twilio] error: {exc}")
    finally:
        for task in tasks:
            task.cancel()
        if call_manager.get(call.id):
            await call_manager.finish(call)
