"""Сверх подробная схема всей архитектуры ClirntCabinet."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 3000, 2120
INK = "#1f2937"
MUTED = "#5b6478"
LINE = "#3f51b5"
DASH = "#8a94ad"

F_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
F_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

f_title = ImageFont.truetype(F_BOLD, 46)
f_sub = ImageFont.truetype(F_REG, 24)
f_band = ImageFont.truetype(F_BOLD, 26)
f_head = ImageFont.truetype(F_BOLD, 21)
f_body = ImageFont.truetype(F_REG, 16)
f_label = ImageFont.truetype(F_REG, 16)

img = Image.new("RGB", (W, H), "#f5f7fb")
draw = ImageDraw.Draw(img)
band_labels: list[tuple[int, str]] = []


def center_text(lines, font, cx, top, fill=INK, step=24):
    for i, line in enumerate(lines):
        bb = draw.textbbox((0, 0), line, font=font)
        draw.text((cx - (bb[2] - bb[0]) / 2, top + i * step), line, font=font, fill=fill)


def band(y1, y2, label):
    draw.rounded_rectangle((60, y1, W - 60, y2), radius=20, fill="#ffffff",
                           outline="#d8deea", width=2)
    band_labels.append((y1, label))


def box(rect, head, body=(), fill="#eef2ff", border=LINE):
    draw.rounded_rectangle(rect, radius=14, fill=fill, outline=border, width=3)
    x1, y1, x2, y2 = rect
    cx = (x1 + x2) / 2
    center_text([head], f_head, cx, y1 + 14)
    if body:
        center_text(list(body), f_body, cx, y1 + 46, fill=MUTED, step=22)


def arrow(points, color=LINE, width=3, dashed=False, head=True):
    if dashed:
        for a, b in zip(points, points[1:]):
            dash_segment(a, b, color, width)
    else:
        draw.line(points, fill=color, width=width, joint="curve")
    if head:
        p1, p2 = points[-2], points[-1]
        ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        size = 15
        a = ang + math.pi - math.pi / 7
        b = ang + math.pi + math.pi / 7
        pa = (p2[0] + size * math.cos(a), p2[1] + size * math.sin(a))
        pb = (p2[0] + size * math.cos(b), p2[1] + size * math.sin(b))
        draw.polygon([p2, pa, pb], fill=color)


def dash_segment(p1, p2, color, width, dash=14, gap=10):
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


def label(text, x, y):
    bb = draw.textbbox((0, 0), text, font=f_label)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    draw.rounded_rectangle((x - w / 2 - 8, y - h / 2 - 5, x + w / 2 + 8, y + h / 2 + 7),
                           radius=6, fill="#ffffff")
    draw.text((x - w / 2, y - h / 2), text, font=f_label, fill=MUTED)


center_text(["ClirntCabinet — ПОЛНАЯ АРХИТЕКТУРА"], f_title, W / 2, 30)
center_text(["Все слои, файлы, сервисы, база данных, внешние API и связи между ними"],
            f_sub, W / 2, 88, fill=MUTED)

# ── Полосы ──────────────────────────────────────────────────────────────────
band(140, 300, "1. ПОЛЬЗОВАТЕЛИ")
band(340, 580, "2. ИНТЕРФЕЙС (браузер)")
band(620, 800, "3. FASTAPI — приложение")
band(840, 1040, "4. ДОМЕН — бизнес-логика")
band(1080, 1340, "5. ИНФРАСТРУКТУРА")
band(1380, 1600, "6. ВНЕШНИЕ СЕРВИСЫ")
band(1640, 1960, "7. ДАННЫЕ")

# ── 1. Пользователи ─────────────────────────────────────────────────────────
box((120, 180, 780, 280), "КЛИЕНТ (малый бизнес)",
    ["не умеет пользоваться ИИ", "выбирает готовое решение"], "#eef2ff")
box((1120, 180, 1780, 280), "АДМИНИСТРАТОР",
    ["шаблоны, тарифы, логи", "добавляет рецепты"], "#f1f5f9")
box((2120, 180, 2880, 280), "АБОНЕНТ (конечный человек)",
    ["получает звонок или чат", "оставляет заявку"], "#e8f5ee", "#2f855a")

# ── 2. Интерфейс ────────────────────────────────────────────────────────────
pages = [
    (120, "/login /register", ["вход и регистрация"]),
    (600, "/dashboard", ["статистика, действия"]),
    (1080, "/catalog", ["5 готовых рецептов"]),
    (1560, "/calls", ["журнал, голосовой виджет"]),
    (2040, "/billing", ["счета, оплата"]),
    (2520, "/sites/new", ["анкета для сайта"]),
]
for x, head, body in pages:
    box((x, 375, x + 400, 485), head, body, "#eef2ff")

box((120, 505, 2880, 565), "ОБЩИЙ UI: Jinja2-шаблоны + portal.css + call_widget.js",
    [], "#f1f5f9", "#64748b")

# ── 3. FastAPI ──────────────────────────────────────────────────────────────
box((120, 650, 640, 780), "main.py", ["точка входа", "mount /static"], "#ede9fe", "#5b4bdb")
box((700, 650, 1320, 780), "portal.py", ["кабинет, каталог", "сайты, счета, /calls"], "#ede9fe", "#5b4bdb")
box((1380, 650, 2100, 780), "calls_api.py", ["REST /api/calls", "WS /ws/twilio, /ws/browser", "TwiML /twilio/*"], "#ede9fe", "#5b4bdb")
box((2160, 650, 2880, 780), "Auth / сессии", ["cookie cc_session", "PBKDF2, user_id"], "#fff5e6", "#b45309")

# ── 4. Домен ────────────────────────────────────────────────────────────────
domain = [
    (120, "DialogueEngine", ["LLM / сценарии", "история, имя, телефон"]),
    (700, "CallManager", ["жизненный цикл звонка", "реестр CallRecord"]),
    (1280, "Billing", ["счета, тарифы", "лимиты"]),
    (1860, "WorkflowEngine", ["план: готовые блоки", "без произвольного кода"]),
    (2440, "SiteBuilder", ["шаблоны сайтов", "публикация (план)"]),
]
for x, head, body in domain:
    box((x, 875, x + 440, 1010), head, body, "#ede9fe", "#5b4bdb")

# ── 5. Инфраструктура ───────────────────────────────────────────────────────
infra = [
    (120, "SpeechToText", ["речь → текст", "stt.transcribe()"]),
    (600, "TextToSpeech", ["текст → речь", "tts.synthesize()"]),
    (1080, "audio.py", ["mu-law ↔ PCM", "8 кГц, 20 мс, RMS/VAD"]),
    (1560, "MockProvider", ["демо-звонок", "без сети"]),
    (2040, "TwilioProvider", ["REST Calls.json", "звонок + WebSocket"]),
    (2520, "NovofonProvider", ["SIP + шлюз", "заготовка"]),
]
for x, head, body in infra:
    fill = "#fee2e2" if "Provider" in head else "#e0f2fe"
    border = "#b91c1c" if "Provider" in head else "#0369a1"
    box((x, 1120, x + 400, 1260), head, body, fill, border)

box((120, 1280, 2880, 1325), "telegram-уведомления • json/csv-экспорт • бэкап SQLite • DEV_LOG",
    [], "#f1f5f9", "#64748b")

# ── 6. Внешние сервисы ──────────────────────────────────────────────────────
external = [
    (120, "OpenAI-совместимый API", ["LLM, STT, TTS", "OPENAI_BASE_URL"]),
    (700, "Twilio Cloud", ["звонки, номера, WebSocket", "медиа из коробки"]),
    (1280, "Novofon SIP", ["российские номера", "+ Asterisk/FreeSWITCH"]),
    (1860, "Telegram API", ["уведомления", "заявки"]),
    (2440, "Платежи (план)", ["ЮKassa / СБП", "сейчас демо"]),
]
for x, head, body in external:
    box((x, 1420, x + 440, 1560), head, body, "#fff5e6", "#b45309")

# ── 7. Данные ───────────────────────────────────────────────────────────────
tables = [
    (120, "users", ["email, соль, хэш"]),
    (600, "sessions", ["token, user_id"]),
    (1080, "sites", ["template, data(JSON)"]),
    (1560, "workflows", ["recipe, config(JSON)"]),
    (2040, "invoices", ["amount, status"]),
    (2520, "calls", ["transcript, result"]),
]
for x, head, body in tables:
    box((x, 1680, x + 400, 1810), head, body, "#e8f5ee", "#2f855a")

box((120, 1840, 2880, 1910), "data/app.db (SQLite)  •  exports/*.csv  •  backups/*.db  •  .env (секреты, не в git)",
    [], "#f1f5f9", "#64748b")

# ── Связи: пользователи → интерфейс ────────────────────────────────────────
arrow([(450, 280), (320, 375)])
arrow([(650, 280), (800, 375)])
arrow([(1450, 280), (1300, 375)])
arrow([(2300, 280), (1760, 375)])

# ── Интерфейс → FastAPI ─────────────────────────────────────────────────────
arrow([(320, 485), (2480, 650)])
arrow([(800, 485), (1000, 650)])
arrow([(1280, 485), (1000, 650)])
arrow([(1760, 485), (1740, 650)])
arrow([(2240, 485), (1000, 650)])
arrow([(2720, 485), (1000, 650)])
arrow([(1500, 565), (380, 650)], color=DASH, dashed=True)

# ── FastAPI → домен ─────────────────────────────────────────────────────────
arrow([(380, 780), (340, 875)])
arrow([(1000, 780), (1500, 875)])
arrow([(1000, 780), (2660, 875)])
arrow([(1740, 780), (920, 875)])
arrow([(2520, 780), (2100, 875)])

# ── Домен → инфраструктура ──────────────────────────────────────────────────
arrow([(340, 1010), (320, 1120)])
arrow([(340, 1010), (800, 1120)])
arrow([(920, 1010), (1280, 1120)])
arrow([(920, 1010), (1760, 1120)])
arrow([(920, 1010), (2240, 1120)])
arrow([(920, 1010), (2720, 1120)])

# ── Инфраструктура → внешние сервисы ────────────────────────────────────────
arrow([(320, 1260), (340, 1420)])
arrow([(800, 1260), (340, 1420)])
arrow([(2240, 1260), (920, 1420)])
arrow([(2720, 1260), (1500, 1420)])
arrow([(1500, 1325), (2080, 1420)], color=DASH, dashed=True)

# ── Внешние → данные / абонент ──────────────────────────────────────────────
arrow([(920, 1560), (2720, 1810)], color=DASH, dashed=True)
label("результат звонка в базу", 1820, 1620)
arrow([(1620, 1420), (2500, 280)], color=DASH, dashed=True)
label("звонок абоненту", 2460, 980)

# ── Домен → таблицы ─────────────────────────────────────────────────────────
for x_start, x_end in [(250, 320), (830, 800), (1500, 1280), (2080, 1760), (2660, 2720)]:
    arrow([(x_start, 1010), (x_end, 1680)], color="#7c8aa5", width=2)
arrow([(2520, 780), (820, 1680)], color="#7c8aa5", width=2)

center_text(["Схема сгенерирована: tools/draw_architecture_full.py  •  GitHub: hrenmanski-alt/ClirntCabinet"],
            f_label, W / 2, 2020, fill=MUTED)

# Заголовки полос рисуем последними, чтобы они не перекрывались блоками
for y1, text in band_labels:
    draw.rounded_rectangle((60, y1, 460, y1 + 44), radius=12, fill=LINE)
    draw.text((78, y1 + 8), text, font=f_band, fill="#ffffff")

out = Path(__file__).resolve().parent.parent / "docs" / "architecture_full.png"
img.save(out)
print("saved", out)
