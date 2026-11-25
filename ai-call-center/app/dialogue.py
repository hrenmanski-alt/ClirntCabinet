from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx

from .config import settings

SCENARIOS = ("sales", "support", "reminder", "generic")

_END_MARKER = "[END]"

_RULES: dict[str, list[str]] = {
    "sales": [
        "Здравствуйте! Меня зовут Алиса, я представитель компании «Новые решения». Удобно сейчас поговорить?",
        "Отлично. Подскажите, что вас интересует: автоматизация звонков, поддержка клиентов или что-то другое?",
        "Приятно познакомиться, {name}! Расскажите кратко, какую задачу вы хотите решить — и я подберу подходящий вариант.",
        "Спасибо, понял. Оставьте, пожалуйста, номер телефона, чтобы менеджер мог связаться с вами и прислать детали.",
        "Принял: {name}, телефон {phone}. Менеджер свяжется с вами в ближайшее время. Спасибо за разговор, до свидания!",
    ],
    "support": [
        "Здравствуйте! Это поддержка. Чем могу помочь?",
        "Понял. Опишите, пожалуйста, проблему подробнее — что именно произошло?",
        "Спасибо, {name}. Если можно, уточните номер заказа или дату обращения.",
        "Принял информацию: {issue}. Мы создали обращение и вернёмся с ответом в течение рабочего дня.",
        "Обращение зарегистрировано. Если появятся вопросы — напишите нам в чат. Хорошего дня!",
    ],
    "reminder": [
        "Здравствуйте! Это напоминание о вашей записи. Удобно сейчас подтвердить визит?",
        "Запись подтверждена. Если планы изменились, могу перенести встречу на удобное для вас время.",
        "Хорошо, зафиксировал: {answer}. Изменения внесены в систему.",
        "Спасибо! Напоминание закрыто. До свидания.",
    ],
    "generic": [
        "Здравствуйте! Я AI-ассистент. Чем могу быть полезен?",
        "Понял вас. Расскажите немного подробнее, пожалуйста.",
        "Спасибо за информацию. Я передал ваш запрос специалисту.",
        "Если у вас есть ещё вопросы — задавайте, я на связи.",
        "Спасибо за разговор! До свидания.",
    ],
}

_LLM_SYSTEM = """Ты — русскоязычный AI-ассистент call-центра. Правила:
- Отвечай коротко, живой разговорной речью, 1–2 предложения.
- Не используй списки, markdown и эмодзи — текст будет озвучен голосом.
- Задавай по одному вопросу за раз.
- Сценарий: {scenario}.
- Если диалог логически завершён (клиент согласился, попрощался, данные собраны),
  добавь в конец последнего ответа ровно токен [END].
- Никогда не выдумывай данные клиента: если чего-то не хватает — вежливо спроси."""


@dataclass
class Session:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    scenario: str = "sales"
    step: int = 0
    history: list[dict[str, str]] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    finished: bool = False

    def add(self, role: str, text: str) -> None:
        self.history.append({"role": role, "content": text})


@dataclass
class Reply:
    text: str
    end_call: bool = False


class DialogueEngine:
    """Гибрид: LLM при наличии ключа, иначе детерминированные сценарии."""

    def __init__(self, use_llm: bool | None = None) -> None:
        self.use_llm = settings.brain_is_llm if use_llm is None else use_llm

    def new_session(self, scenario: str | None = None, session_id: str | None = None) -> Session:
        scenario = (scenario or settings.scenario).lower()
        if scenario not in SCENARIOS:
            scenario = "generic"
        return Session(id=session_id or str(uuid.uuid4()), scenario=scenario)

    async def reply(self, session: Session, user_text: str) -> Reply:
        user_text = (user_text or "").strip()
        if not user_text:
            return Reply("Извините, я не расслышал. Повторите, пожалуйста.")
        if session.finished:
            return Reply("Разговор уже завершён. До свидания!", end_call=True)

        if self.use_llm:
            result = await self._llm_reply(session, user_text)
        else:
            result = self._rule_reply(session, user_text)

        session.add("user", user_text)
        session.add("assistant", result.text)
        if result.end_call:
            session.finished = True
        return result

    async def greeting(self, session: Session) -> Reply:
        """Первая реплика — ассистент говорит первым."""
        if self.use_llm and not session.history:
            result = await self._llm_reply(session, "Поздоровайся и представься.")
        else:
            result = Reply(_RULES[session.scenario][0])
            session.step = 1
        session.add("assistant", result.text)
        if result.end_call:
            session.finished = True
        return result

    # ── LLM ──────────────────────────────────────────────────────────────────
    async def _llm_reply(self, session: Session, user_text: str) -> Reply:
        messages = [
            {"role": "system", "content": _LLM_SYSTEM.format(scenario=session.scenario)}
        ]
        if session.data:
            messages.append(
                {"role": "system", "content": "Уже известные данные: " + str(session.data)}
            )
        messages.extend(session.history[-12:])
        messages.append({"role": "user", "content": user_text})

        try:
            async with httpx.AsyncClient(timeout=20.0, proxy=settings.https_proxy or None) as client:
                response = await client.post(
                    f"{settings.openai_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    json={
                        "model": settings.llm_model,
                        "messages": messages,
                        "temperature": 0.4,
                        "max_tokens": 180,
                    },
                )
                response.raise_for_status()
                text = response.json()["choices"][0]["message"]["content"].strip()
        except Exception as exc:  # сеть/лимиты — не роняем звонок
            text = "Извините, небольшая задержка. Повторите, пожалуйста, ваш вопрос."
            print(f"[dialogue] LLM error: {exc}")

        end_call = _END_MARKER in text
        return Reply(text.replace(_END_MARKER, "").strip(), end_call)

    # ── Локальные сценарии ───────────────────────────────────────────────────
    def _rule_reply(self, session: Session, user_text: str) -> Reply:
        text = user_text.lower().strip()
        script = _RULES[session.scenario]
        step = session.step

        if any(word in text for word in ("до свидан", "пока", "не интересно", "отбой", "хватит")):
            session.step = len(script)
            return Reply("Понял вас. Спасибо за разговор, до свидания!", end_call=True)

        # Извлекаем данные из любой реплики
        if "name" not in session.data:
            found = _extract_name(user_text)
            if found:
                session.data["name"] = found
        if "phone" not in session.data:
            found = _extract_phone(user_text)
            if found:
                session.data["phone"] = found

        if session.scenario == "sales":
            return self._sales(session, text, script, step)
        if session.scenario == "support":
            return self._support(session, text, script, step)
        if session.scenario == "reminder":
            return self._reminder(session, text, script, step)
        return self._generic(session, script, step)

    @staticmethod
    def _sales(session: Session, text: str, script: list[str], step: int) -> Reply:
        if step == 0:
            session.step = 1
            return Reply(script[0])
        if step == 1:
            session.step = 2
            return Reply(script[1])
        if step == 2:
            if "name" not in session.data:
                return Reply("Как к вам обращаться?")
            session.step = 3
            session.data["interest"] = user_snippet(text)
            return Reply(script[2].format(name=session.data["name"]))
        if step == 3:
            if "phone" not in session.data:
                return Reply("Подскажите номер телефона — он понадобится менеджеру.")
            session.step = 4
            return Reply(script[3])
        session.step = 5
        return Reply(
            script[4].format(name=session.data.get("name", "коллега"), phone=session.data["phone"]),
            end_call=True,
        )

    @staticmethod
    def _support(session: Session, text: str, script: list[str], step: int) -> Reply:
        if step == 0:
            session.step = 1
            return Reply(script[0])
        if step == 1:
            session.step = 2
            session.data["issue"] = user_snippet(text)
            return Reply(script[1])
        if step == 2:
            if "name" not in session.data:
                return Reply("Представьтесь, пожалуйста, как к вам обращаться?")
            session.step = 3
            return Reply(script[2].format(name=session.data["name"]))
        if step == 3:
            session.step = 4
            return Reply(script[3].format(issue=session.data.get("issue", "ваш вопрос")))
        session.step = 5
        return Reply(script[4], end_call=True)

    @staticmethod
    def _reminder(session: Session, text: str, script: list[str], step: int) -> Reply:
        if step == 0:
            session.step = 1
            return Reply(script[0])
        if step == 1:
            session.step = 2
            answer = "подтверждено" if any(w in text for w in ("да", "конечно", "подтвержда")) else "изменено"
            session.data["answer"] = answer
            return Reply(script[1])
        if step == 2:
            if any(w in text for w in ("перенес", "друг", "завтра", "послезавтра")):
                session.data["answer"] = "перенос на другое время"
            session.step = 3
            return Reply(script[2].format(answer=session.data["answer"]))
        session.step = 4
        return Reply(script[3], end_call=True)

    @staticmethod
    def _generic(session: Session, script: list[str], step: int) -> Reply:
        if step < len(script) - 1:
            session.step += 1
            return Reply(script[step])
        session.step += 1
        return Reply(script[-1], end_call=True)


def user_snippet(text: str, limit: int = 120) -> str:
    return text[:limit].strip()


def _extract_name(text: str) -> str | None:
    m = re.search(r"(?:меня зовут|это|я)\s+([А-ЯЁA-Z][а-яёa-z]{1,19})", text, re.IGNORECASE)
    if m:
        return m.group(1).capitalize()
    # «Анна», «Иван Петров» как отдельные слова в начале фразы
    m = re.match(r"^\s*([А-ЯЁ][а-яё]+)", text)
    if m and m.group(1).lower() not in ("да", "нет", "здравствуйте", "алло", "привет"):
        return m.group(1)
    return None


def _extract_phone(text: str) -> str | None:
    digits = re.sub(r"\D", "", text)
    if len(digits) >= 10:
        return "+" + digits[-11:] if len(digits) >= 11 else digits
    return None
