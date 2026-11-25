"""Нарочно огромная и запутанная схема всей архитектуры ClirntCabinet.

13 слоёв, 100+ блоков, сотни связей, обратные петли и технический шум.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 6000, 4200
INK = "#1f2937"
MUTED = "#5b6478"
LINE = "#3f51b5"
DASH = "#8a94ad"

F_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
F_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

f_title = ImageFont.truetype(F_BOLD, 72)
f_sub = ImageFont.truetype(F_REG, 34)
f_band = ImageFont.truetype(F_BOLD, 34)
f_head = ImageFont.truetype(F_BOLD, 24)
f_body = ImageFont.truetype(F_REG, 18)
f_label = ImageFont.truetype(F_REG, 17)

img = Image.new("RGB", (W, H), "#f5f7fb")
draw = ImageDraw.Draw(img)
rnd = random.Random(42)
band_labels: list[tuple[int, str]] = []

BANDS = [
    (160, 420, "00 ВХОД / ВЫХОД"),
    (440, 700, "01 КЛИЕНТЫ И РОЛИ"),
    (720, 980, "02 ПРЕЗЕНТАЦИЯ / UI"),
    (1000, 1260, "03 HTTP / WS СЛОЙ"),
    (1280, 1540, "04 ПРИКЛАДНАЯ ЛОГИКА"),
    (1560, 1820, "05 ДОМЕН"),
    (1840, 2100, "06 РЕЧЬ И ЗВУК"),
    (2120, 2380, "07 ТЕЛЕФОНИЯ"),
    (2400, 2660, "08 ВНЕШНИЕ API"),
    (2680, 2940, "09 ДАННЫЕ И ХРАНИЛИЩА"),
    (2960, 3220, "10 ИНФРАСТРУКТУРА / ДЕПЛОЙ"),
    (3240, 3500, "11 ФОНОВЫЕ ПРОЦЕССЫ"),
    (3520, 3780, "12 НАБЛЮДЕНИЕ И БЕЗОПАСНОСТЬ"),
    (3800, 4060, "13 ПЛАНЫ / ГРИЗЛИ-БОКС"),
]

COLUMNS = [
    ("HTTP/1.1", "запросы, cookies"), ("WebSocket", "полнодуплекс"),
    ("TLS 1.3", "сертификат, ngrok"), ("REST JSON", "Content-Type"),
    ("TwiML XML", "webhook"), ("SIP over UDP", "5060, REGISTER"),
    ("RTP/RTCP", "200 мс, jitter"), ("multipart", "WAV, файлы"),
    ("Клиент ЛК", "не технарь"), ("Админ", "шаблоны, тарифы"),
    ("Абонент", "звонящий человек"), ("Менеджер", "заявки в работе"),
    ("Бот Telegram", "уведомления"), ("Оператор", "эскалация"),
    ("Аудитор", "логи, отчёты"), ("Супервизор", "квоты, лимиты"),
    ("/login", "email + пароль"), ("/register", "соль, PBKDF2"),
    ("/dashboard", "счётчики, действия"), ("/catalog", "рецепты, цены"),
    ("/calls", "журнал, виджет"), ("/billing", "счета, оплата"),
    ("/sites/new", "анкета шаблона"), ("/static/*", "CSS, JS, шрифты"),
    ("main.py", "FastAPI app"), ("portal.py", "HTML-роуты"),
    ("calls_api.py", "REST + WS"), ("SessionMiddleware", "cc_session"),
    ("StaticFiles", "mount /static"), ("Pydantic", "CallRequest"),
    ("CORS", "origin policy"), ("RateLimit", "заглушка"),
    ("AuthService", "verify_password"), ("UserRepo", "get_session_user"),
    ("SiteRepo", "CRUD sites"), ("InvoiceRepo", "CRUD invoices"),
    ("CallRepo", "CRUD calls"), ("WorkflowRepo", "CRUD workflows"),
    ("EventBus", "in-memory"), ("TaskQueue", "asyncio tasks"),
    ("DialogueEngine", "LLM / rules"), ("Session", "history, data"),
    ("CallManager", "CallRecord"), ("CallProvider", "ABC"),
    ("Billing", "тарифы, лимиты"), ("WorkflowEngine", "блоки, DAG"),
    ("SiteBuilder", "рендер шаблона"), ("ResultExtractor", "имя, телефон"),
    ("SpeechToText", "audio → text"), ("TextToSpeech", "text → audio"),
    ("audio.py", "mu-law ↔ PCM"), ("VAD", "RMS, порог 350"),
    ("SilenceTimer", "700 мс"), ("FrameSplitter", "160 байт / 20 мс"),
    ("WAVCodec", "24 → 8 кГц"), ("BargeIn", "event clear"),
    ("MockProvider", "демо"), ("TwilioProvider", "REST Calls.json"),
    ("NovofonProvider", "SIP заготовка"), ("Asterisk", "план: шлюз"),
    ("FreeSWITCH", "план: медиа"), ("StreamSid", "карта потоков"),
    ("StatusCallback", "webhook"), ("Hangup", "completed"),
    ("OpenAI /v1", "chat completions"), ("Whisper STT", "gpt-4o-mini-transcribe"),
    ("OpenAI TTS", "gpt-4o-mini-tts"), ("Twilio Cloud", "звонки, SID"),
    ("Novofon SIP", "DID, транк"), ("Telegram API", "sendMessage"),
    ("ЮKassa", "план: платежи"), ("SMS gateway", "план: код"),
    ("users", "email, соль, хэш"), ("sessions", "token, TTL"),
    ("sites", "template, JSON"), ("workflows", "recipe, JSON"),
    ("invoices", "amount, status"), ("calls", "transcript, result"),
    ("app.db", "SQLite, WAL"), ("exports/backups", "CSV, ZIP"),
    ("uvicorn", "ASGI сервер"), ("Nginx", "reverse proxy"),
    ("Docker", "контейнер"), ("config.py", "dotenv"),
    (".env", "секреты"), ("ngrok", "wss туннель"),
    ("Volume", "data/app.db"), ("cron", "бэкап по ночам"),
    ("process_speech", "async task"), ("greeting", "первая реплика"),
    ("respond", "диалог"), ("finish", "итог в базу"),
    ("retry", "429/5xx backoff"), ("fallback", "вежливый ответ"),
    ("cleanup", "cancelled tasks"), ("heartbeat", "ping/health"),
    ("DEV_LOG.md", "журнал коммитов"), ("print log", "stderr"),
    ("health", "/api/health"), ("metrics", "счётчики"),
    ("trace id", "сквозной ID"), ("Git branch", "feature/*"),
    ("Deploy key", "ed25519"), ("Secret scan", "gitignore"),
    ("PostgreSQL", "вместо SQLite"), ("Redis", "очередь, кэш"),
    ("Celery", "фоновые задачи"), ("WebRTC", "звонок в браузере"),
    ("AI-консьерж", "сбор требований"), ("Payments", "реальные деньги"),
    ("CRM", "интеграции"), ("ML-оценка", "качество диалога"),
]
assert len(COLUMNS) == len(BANDS) * 8

XS = [120 + i * 730 for i in range(8)]
BW = 650


def center_text(lines, font, cx, top, fill=INK, step=24):
    for i, line in enumerate(lines):
        bb = draw.textbbox((0, 0), line, font=font)
        draw.text((cx - (bb[2] - bb[0]) / 2, top + i * step), line, font=font, fill=fill)


def band_rect(y1, y2, label):
    draw.rounded_rectangle((60, y1, W - 60, y2), radius=24, fill="#ffffff",
                           outline="#d8deea", width=3)
    band_labels.append((y1, label))


def box(rect, head, body, fill, border):
    draw.rounded_rectangle(rect, radius=12, fill=fill, outline=border, width=3)
    x1, y1, _, _ = rect
    cx = (rect[0] + rect[2]) / 2
    center_text([head], f_head, cx, y1 + 12)
    center_text([body], f_body, cx, y1 + 44, fill=MUTED, step=22)


def dash_segment(p1, p2, color, width, dash=16, gap=12):
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if not length:
        return
    ux, uy = dx / length, dy / length
    pos = 0.0
    while pos < length:
        end = min(pos + dash, length)
        draw.line([(p1[0] + ux * pos, p1[1] + uy * pos),
                   (p1[0] + ux * end, p1[1] + uy * end)], fill=color, width=width)
        pos += dash + gap


def arrow(points, color=LINE, width=3, dashed=False, head=True):
    if dashed:
        for a, b in zip(points, points[1:]):
            dash_segment(a, b, color, width)
    else:
        draw.line(points, fill=color, width=width, joint="curve")
    if head:
        p1, p2 = points[-2], points[-1]
        ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        size = 16
        a = ang + math.pi - math.pi / 7
        b = ang + math.pi + math.pi / 7
        draw.polygon([p2,
                      (p2[0] + size * math.cos(a), p2[1] + size * math.sin(a)),
                      (p2[0] + size * math.cos(b), p2[1] + size * math.sin(b))], fill=color)


def tag(text, x, y):
    bb = draw.textbbox((0, 0), text, font=f_label)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    draw.rounded_rectangle((x - w / 2 - 8, y - h / 2 - 5, x + w / 2 + 8, y + h / 2 + 7),
                           radius=6, fill="#ffffff", outline="#d8deea")
    draw.text((x - w / 2, y - h / 2), text, font=f_label, fill=MUTED)


center_text(["ClirntCabinet — МЕГА-АРХИТЕКТУРА (намеренно перегруженная)"],
            f_title, W / 2, 30)
center_text(["14 слоёв • 112 модулей • сотни связей • обратные петли • technical noise"],
            f_sub, W / 2, 110, fill=MUTED)

# Полосы и блоки
centers: dict[int, tuple[int, int, int, int]] = {}
idx = 0
for bi, (y1, y2, label) in enumerate(BANDS):
    band_rect(y1, y2, label)
    palette = ["#eef2ff", "#f1f5f9", "#ede9fe", "#e0f2fe", "#fff5e6", "#fee2e2", "#e8f5ee"]
    border = ["#4059a8", "#64748b", "#5b4bdb", "#0369a1", "#b45309", "#b91c1c", "#2f855a"]
    for ci, x in enumerate(XS):
        head, body = COLUMNS[idx]
        rect = (x, y1 + 40, x + BW, y1 + 220)
        box(rect, head, body, palette[(bi + ci) % len(palette)], border[(bi + ci) % len(border)])
        centers[idx] = rect
        idx += 1

# Горизонтальные цепочки внутри полосы
for bi in range(len(BANDS)):
    base = bi * 8
    for ci in range(7):
        a, b = centers[base + ci], centers[base + ci + 1]
        arrow([(a[2], (a[1] + a[3]) / 2), (b[0], (b[1] + b[3]) / 2)],
              color=LINE, width=3)

# Вертикальные связи между полосами
for bi in range(len(BANDS) - 1):
    for ci in range(8):
        a, b = centers[bi * 8 + ci], centers[(bi + 1) * 8 + ci]
        arrow([((a[0] + a[2]) / 2, a[3]), ((b[0] + b[2]) / 2, b[1])],
              color="#4f6bb5", width=3)

# Диагональные перекрёстные связи (детерминированный «шум»)
tags_words = ["ACK", "retry↑", "event", "sync", "async", "cache", "TTL", "fallback",
              "callback", "stream", "WS", "HTTP", "SIP", "RTP", "queue", "push",
              "poll", "5xx", "gRPC", "ack", "trace", "heat", "lambda", "hook"]
for i in range(180):
    a_i = rnd.randrange(len(COLUMNS))
    b_i = rnd.randrange(len(COLUMNS))
    if a_i == b_i:
        continue
    a, b = centers[a_i], centers[b_i]
    p1 = (rnd.randint(a[0], a[2]), rnd.randint(a[1], a[3]))
    p2 = (rnd.randint(b[0], b[2]), rnd.randint(b[1], b[3]))
    mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
    dashed = rnd.random() < 0.35
    arrow([p1, mid, p2], color=DASH if dashed else LINE, width=2, dashed=dashed)
    if i % 4 == 0:
        tag(rnd.choice(tags_words), mid[0], mid[1])

# Обратные петли: последний слой → первый
for ci in (0, 3, 7):
    tail = centers[len(COLUMNS) - 8 + ci]
    head_b = centers[ci]
    arrow([(tail[0], (tail[1] + tail[3]) / 2),
           (30, (tail[1] + tail[3]) / 2),
           (30, (head_b[1] + head_b[3]) / 2),
           (head_b[0], (head_b[1] + head_b[3]) / 2)],
          color=DASH, dashed=True, width=4)

center_text(["НИЖНЯЯ ПЕТЛЯ: результат → база → кабинет → клиент → новый звонок → ..."],
            f_label, W / 2, 4110, fill=MUTED)

# Заголовки полос — поверх всех линий
for y1, text in band_labels:
    draw.rounded_rectangle((60, y1, 900, y1 + 52), radius=14, fill=LINE)
    draw.text((80, y1 + 8), text, font=f_band, fill="#ffffff")

out = Path(__file__).resolve().parent.parent / "docs" / "architecture_mega.png"
img.save(out)
print("saved", out, "size", W, "x", H)
