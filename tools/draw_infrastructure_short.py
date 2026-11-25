"""Короткая схема инфраструктуры: 18 блоков, читается с телефона."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 2600, 1600
INK, MUTED, LINE = "#1f2937", "#5b6478", "#3f51b5"
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

f_title = ImageFont.truetype(FB, 46)
f_sub = ImageFont.truetype(F, 22)
f_head = ImageFont.truetype(FB, 22)
f_body = ImageFont.truetype(F, 17)
f_label = ImageFont.truetype(F, 18)

img = Image.new("RGB", (W, H), "#f5f7fb")
draw = ImageDraw.Draw(img)


def text(lines, font, cx, top, fill=INK, step=24):
    for i, line in enumerate(lines):
        bb = draw.textbbox((0, 0), line, font=font)
        draw.text((cx - (bb[2] - bb[0]) / 2, top + i * step), line, font=font, fill=fill)


def box(rect, head, body, fill="#eef2ff", border=LINE):
    draw.rounded_rectangle(rect, radius=16, fill=fill, outline=border, width=3)
    cx = (rect[0] + rect[2]) / 2
    text([head], f_head, cx, rect[1] + 16)
    if body:
        text(body, f_body, cx, rect[1] + 48, fill=MUTED, step=23)


def arrow(points, color=LINE, width=3, dashed=False):
    if dashed:
        for a, b in zip(points, points[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy)
            if not length:
                continue
            ux, uy = dx / length, dy / length
            pos = 0.0
            while pos < length:
                end = min(pos + 15, length)
                draw.line([(a[0] + ux * pos, a[1] + uy * pos),
                           (a[0] + ux * end, a[1] + uy * end)], fill=color, width=width)
                pos += 25
    else:
        draw.line(points, fill=color, width=width, joint="curve")
    p1, p2 = points[-2], points[-1]
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    size = 15
    draw.polygon([p2,
                  (p2[0] + size * math.cos(ang + math.pi - 0.45), p2[1] + size * math.sin(ang + math.pi - 0.45)),
                  (p2[0] + size * math.cos(ang + math.pi + 0.45), p2[1] + size * math.sin(ang + math.pi + 0.45))], fill=color)


text(["ClirntCabinet — инфраструктура коротко"], f_title, W / 2, 28)
text(["18 блоков вместо 112 • всё главное на одной картинке"], f_sub, W / 2, 88, fill=MUTED)

# Ряд 1
box((180, 150, 700, 250), "КЛИЕНТ", ["браузер / телефон"], "#eef2ff")
box((1000, 150, 1600, 250), "UI", ["Jinja2 + CSS + call_widget.js"], "#eef2ff")
box((1900, 150, 2420, 250), "FastAPI main.py", ["HTTP + WebSocket"], "#ede9fe", "#5b4bdb")

# Ряд 2
box((120, 330, 720, 450), "portal.py", ["кабинет, каталог, счета"], "#ede9fe", "#5b4bdb")
box((900, 330, 1600, 450), "calls_api.py", ["звонки, WS, TwiML"], "#ede9fe", "#5b4bdb")
box((1780, 330, 2480, 450), "business_api.py", ["план, инструменты, цена"], "#ede9fe", "#5b4bdb")

# Ряд 3
box((120, 520, 820, 650), "SQLite app.db", ["users, sessions, sites,", "workflows, invoices, calls"], "#e8f5ee", "#2f855a")
box((960, 520, 1640, 650), "CallManager + DialogueEngine", ["жизненный цикл звонка", "сценарии ИИ"], "#ede9fe", "#5b4bdb")
box((1780, 520, 2480, 650), "BusinessPlanner + PricingEngine", ["план из 9 шагов", "цена и окупаемость"], "#ede9fe", "#5b4bdb")

# Ряд 4
box((120, 720, 600, 830), "audio.py", ["mu-law ↔ PCM, VAD"], "#e0f2fe", "#0369a1")
box((680, 720, 1160, 830), "providers.py", ["STT + TTS"], "#e0f2fe", "#0369a1")
box((1240, 720, 1720, 830), "telephony.py", ["Mock / Twilio / Novofon"], "#fee2e2", "#b91c1c")
box((1800, 720, 2480, 830), "tool_registry", ["GitHub + Hugging Face"], "#fff5e6", "#b45309")

# Ряд 5
box((120, 910, 760, 1030), "OpenAI-совместимый API", ["LLM, STT, TTS", "через HTTPS_PROXY"], "#fff5e6", "#b45309")
box((900, 910, 1560, 1030), "Twilio / Novofon SIP", ["звонки + Asterisk"], "#fee2e2", "#b91c1c")
box((1700, 910, 2480, 1030), "GitHub API + HF API", ["поиск инструментов"], "#fff5e6", "#b45309")

# Ряд 6
box((120, 1110, 820, 1230), "Яндекс Директ + Метрика", ["реклама и статистика (план)"], "#e8f5ee", "#2f855a")
box((960, 1110, 1560, 1230), "Соцсети и ИИ-ведущие", ["Metricool / Telegram / VK"], "#e8f5ee", "#2f855a")
box((1700, 1110, 2480, 1230), "Деплой: uvicorn, Nginx, Docker", [" ngrok → публичный URL"], "#f1f5f9", "#64748b")

# Ряд 7
box((120, 1310, 1180, 1420), "Данные: exports/*.csv • backups/*.db • .env", [], "#f1f5f9", "#64748b")
box((1300, 1310, 2480, 1420), "Безопасность: PBKDF2 • HttpOnly • без чужого кода • подтверждение денег", [], "#f1f5f9", "#64748b")

# Связи
arrow([(700, 200), (1000, 200)])
arrow([(1600, 200), (1900, 200)])
arrow([(2160, 250), (430, 330)])
arrow([(2160, 250), (1250, 330)])
arrow([(2160, 250), (2130, 330)])
arrow([(420, 450), (470, 520)])
arrow([(1250, 450), (1300, 520)])
arrow([(2130, 450), (2130, 520)])
arrow([(1300, 650), (920, 720)])
arrow([(1300, 650), (1500, 720)])
arrow([(2130, 650), (2140, 720)])
arrow([(360, 830), (440, 910)])
arrow([(920, 830), (1250, 910)])
arrow([(2140, 830), (2090, 910)])
arrow([(440, 1030), (470, 1110)])
arrow([(1250, 1030), (1260, 1110)])
arrow([(2090, 1030), (2090, 1110)])
arrow([(470, 1230), (650, 1310)])
arrow([(1260, 1230), (1500, 1310)])
arrow([(2090, 1230), (2100, 1310)], color="#8a94ad", dashed=True)

text(["Файл: INFRASTRUCTURE.md • репозиторий: hrenmanski-alt/ClirntCabinet"], f_label, W / 2, 1500, fill=MUTED)

out = Path(__file__).resolve().parent.parent / "docs" / "infrastructure_short.png"
img.save(out)
print("saved", out)
