# Колл-центр: как работает подробно

## 1. Общая схема

```text
Клиент (кабинет)
      │  POST /api/calls
      ▼
CallManager ──► CallProvider (Twilio или Mock)
      │              │
      │              ├─ реальный звонок на телефон
      │              └─ WebSocket с аудио
      ▼
AudioPipeline: mu-law → PCM → буфер → VAD → STT
      │
      ▼
DialogueEngine (LLM или локальный сценарий)
      │
      ▼
TextToSpeech → WAV → 8 кГц mu-law → WebSocket → в трубку
      │
      ▼
db.calls: транскрипт, результат, статус → журнал в кабинете
```

## 2. Компоненты

| Компонент | Файл | Назначение |
|-----------|------|------------|
| `CallManager` | `app/telephony.py` | Реестр активных звонков, создание/завершение, связь с БД |
| `CallProvider` | `app/telephony.py` | Абстракция: `MockProvider` и `TwilioProvider` |
| `AudioPipeline` | `app/audio.py` | Перекодирование звука, буферизация, определить паузу (VAD) |
| `SpeechToText` | `app/providers.py` | Голос → текст (Whisper-совместимый API) |
| `DialogueEngine` | `app/dialogue.py` | Текст → ответ ИИ, состояние разговора |
| `TextToSpeech` | `app/providers.py` | Ответ → голос (WAV → mu-law) |
| `calls_api` | `app/calls_api.py` | REST и WebSocket endpoints |

## 3. Жизненный цикл звонка

```text
created → dialing → ringing → in_progress → processing answer → in_progress
                                                   │
                                                   ▼
                                            completed / failed
```

- `created` — запись создана в базе.
- `dialing` — запрос на исходящий звонок отправлен провайдеру.
- `ringing` — абоненту звонят.
- `in_progress` — абонент ответил, идёт разговор.
- `completed` — сценарий завершён, результат сохранён.
- `failed` — ошибка провайдера/сети/API.

## 4. Реальный звонок через телефонного провайдера

### 4.1 Исходящий звонок
Сервер делает:

```http
POST https://api.twilio.com/2010-04-01/Accounts/{SID}/Calls.json
Authorization: Basic <SID:TOKEN>
Content-Type: application/x-www-form-urlencoded

To=+79991234567
From=+1234567890
Url=https://ВАШ_ДОМЕН/twilio/voice?call_id=42&scenario=sales
StatusCallback=https://ВАШ_ДОМЕН/twilio/status
```

### 4.2 Вебхук возвращает TwiML

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="wss://ВАШ_ДОМЕН/ws/twilio?call_id=42"></Stream>
  </Connect>
</Response>
```

Это говорит провайдеру: «после ответа передай звук этого звонка на наш WebSocket».

### 4.3 Поток аудио

Провайдер шлёт JSON-события по WebSocket:

```json
{"event": "connected", "protocol": "Call"}
{"event": "start", "start": {"streamSid": "MZ...", "callSid": "CA...", "customParameters": {}}}
{"event": "media", "streamSid": "MZ...", "media": {"payload": "base64 mu-law", "timestamp": "123"}}
{"event": "stop", "streamSid": "MZ..."}
```

Наш сервер:

1. Декодирует `payload` из base64.
2. `audioop.ulaw2lin(payload, 2)` — mu-law 8 бит → 16-бит PCM, 8 кГц.
3. Добавляет PCM в буфер звонка.
4. Считает `audioop.rms()` — громкость. Если громкость выше порога `VAD_THRESHOLD`, обновляет время последней речи.
5. Когда наступает тишина дольше `SILENCE_MS` (по умолчанию 700 мс) и в буфере достаточно звука — запускается обработка.
6. Пока ИИ думает, новые реплики абонента продолжают копиться в буфер (не теряются).

### 4.4 Ответ обратно в трубку

1. STT получает WAV из буфера и возвращает текст.
2. DialogueEngine добавляет реплику в историю и возвращает ответ.
3. TTS генерирует WAV (обычно 24 кГц).
4. `wav_to_mulaw()`: моно, 16 бит, ресемплинг в 8 кГц, `audioop.lin2ulaw()`.
5. Разрезаем на кадры по 160 байт (20 мс) и шлём:

```json
{"event": "media", "streamSid": "MZ...", "media": {"payload": "base64 mu-law"}}
```

6. Если абонент начал говорить во время воспроизведения — шлём `{"event": "clear", "streamSid": "..."}` и прекращаем отдавать кадры.

## 5. Демо-режим (без телефонии)

- `MockProvider` не делает сетевых вызовов: создаёт запись `calls` и сразу переводит её в `in_progress`.
- Разговор идёт через WebSocket `/ws/browser`:
  - браузер шлёт `{"type": "text", "text": "..."}` (или распознанную речь);
  - сервер отвечает `{"type": "reply", "text": "..."}`;
  - браузер озвучивает ответ через `speechSynthesis`.
- Для микрофона используется Web Speech API: `webkitSpeechRecognition` с `lang = "ru-RU"`.
- Результат сохраняется в базу так же, как при реальном звонке.

## 6. Протокол WebSocket `/ws/browser`

| Направление | Сообщение | Описание |
|-------------|-----------|----------|
| клиент → сервер | `{"type":"start","scenario":"sales"}` | Начать разговор |
| сервер → клиент | `{"type":"ready"}` | Готов к приёму речи |
| клиент → сервер | `{"type":"text","text":"Здравствуйте"}` | Реплика абонента |
| сервер → клиент | `{"type":"reply","text":"...","end":false}` | Ответ ИИ |
| сервер → клиент | `{"type":"reply","text":"...","end":true}` | Конец сценария |
| клиент → сервер | `{"type":"stop"}` | Завершить |

## 7. Таблица `calls`

| Поле | Тип | Что хранит |
|------|-----|------------|
| `id` | INTEGER | Первичный ключ |
| `user_id` | INTEGER | Владелец звонка |
| `provider` | TEXT | `mock` или `twilio` |
| `phone` | TEXT | Номер абонента |
| `scenario` | TEXT | `sales`, `support`, `reminder`, `generic` |
| `status` | TEXT | См. жизненный цикл |
| `transcript` | JSON | Массив реплик `{role, text}` |
| `result` | TEXT | Краткий итог (например, «заинтересован») |
| `created_at` | REAL | Время создания |
| `finished_at` | REAL | Время завершения |

## 8. REST API

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/calls` | Создать и запустить звонок `{phone, scenario, provider}` |
| GET | `/api/calls` | Список звонков пользователя |
| GET | `/api/calls/{id}` | Детали звонка с транскриптом |
| POST | `/api/calls/{id}/hangup` | Прервать звонок |
| POST | `/twilio/voice` | TwiML-вебхук провайдера |
| POST | `/twilio/status` | Webhook о статусе звонка |
| WS | `/ws/twilio` | Аудиопоток телефонного звонка |
| WS | `/ws/browser` | Голосовой разговор в браузере |

## 9. Настройки окружения

| Переменная | По умолчанию | Назначение |
|------------|--------------|------------|
| `AI_CALL_MODE` | `demo` | `demo` — локальные сценарии, `openai` — LLM+STT+TTS |
| `CALL_PROVIDER` | `mock` | `mock` или `twilio` |
| `OPENAI_API_KEY` | — | Ключ для LLM/STT/TTS |
| `TWILIO_ACCOUNT_SID` | — | SID аккаунта |
| `TWILIO_AUTH_TOKEN` | — | Токен аккаунта |
| `TWILIO_FROM_NUMBER` | — | Наш номер для исходящих |
| `PUBLIC_WS_URL` | — | Публичный `wss://.../ws/twilio` |
| `PUBLIC_BASE_URL` | — | Публичный `https://...` для вебхуков |
| `VAD_THRESHOLD` | `350` | Порог громкости (RMS) для начала речи |
| `SILENCE_MS` | `700` | Пауза перед обработкой реплики |
| `MAX_UTTERANCE_MS` | `15000` | Максимальная длина одной реплики |

## 10. Отказоустойчивость

- Ошибка LLM → вежливая фраза «повторите, пожалуйста» и продолжение звонка.
- Пустой результат STT → повторный запрос, звонок не падает.
- Ошибка TTS → реплика пропускается, в лог пишется причина.
- Потеря WebSocket → звонок переводится в `failed`, транскрипт сохраняется.
- `MAX_UTTERANCE_MS` защищает от бесконечной речи: буфер принудительно обрабатывается.

## 11. Что доделываем сегодня (24 ноября)

- `app/telephony.py`: `CallRecord`, `MockProvider`, `TwilioProvider`.
- `app/calls_api.py`: REST + WebSocket endpoints.
- Таблица `calls` и методы в `db.py`.
- Страница `/calls` в кабинете и голосовой JS-виджет.
- Тесты: `MockProvider`, протокол `/ws/browser`, трансформация аудио.
