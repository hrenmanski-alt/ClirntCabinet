"""Полная версия: один промпт → сайты, реклама, соцсети, звонки, цена."""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 4300, 2800
INK, MUTED, LINE, DASH = "#1f2937", "#5b6478", "#3f51b5", "#8a94ad"
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

f_title = ImageFont.truetype(FB, 56)
f_sub = ImageFont.truetype(F, 26)
f_band = ImageFont.truetype(FB, 30)
f_head = ImageFont.truetype(FB, 22)
f_body = ImageFont.truetype(F, 17)
f_label = ImageFont.truetype(F, 17)

img = Image.new("RGB", (W, H), "#f5f7fb")
draw = ImageDraw.Draw(img)
rnd = random.Random(7)
band_labels: list[tuple[int, str]] = []

BANDS = [
    (150, 380, "1 ПРОМПТ И ПЛАН"),
    (420, 650, "2 ИНСТРУМЕНТЫ GITHUB / HUGGING FACE"),
    (690, 920, "3 САЙТЫ И ПУБЛИКАЦИЯ"),
    (960, 1190, "4 МЕТРИКА И ЯНДЕКС ДИРЕКТ"),
    (1230, 1460, "5 СОЦСЕТИ И МЕССЕНДЖЕРЫ"),
    (1500, 1730, "6 ИИ-ВЕДУЩИЕ КАНАЛОВ"),
    (1770, 2000, "7 КОЛЛ-ЦЕНТР"),
    (2040, 2270, "8 ДАННЫЕ, ЦЕНА И ОКУПАЕМОСТЬ"),
    (2310, 2540, "9 РЕЗУЛЬТАТ КЛИЕНТУ"),
]

BOXES = [
    ("Промпт клиента", "одна фраза"), ("Ниша и город", "анализ запроса"),
    ("BusinessPlanner", "9 шагов"), ("План работ", "модули + смета"),
    ("Подтверждение", "человек решает"), ("PricingEngine", "цена и ROI"),
    ("GitHub registry", "поиск репозиториев"), ("HF registry", "модели и Spaces"),
    ("Allowlist", "только проверенное"), ("Метаданные", "без чужого кода"),
    ("config.py", "настройки"), ("HTTPS_PROXY", "иностранный сервер"),
    ("Шаблоны сайтов", "beauty / shop / service"), ("SiteBuilder", "сборка по анкете"),
    ("/sites/new", "2–3 вопроса"), ("Публикация", "поддомен"),
    ("Nginx + Docker", "раздача сайта"), ("Деплой", "хостинг по API"),
    ("Счётчик Метрики", "ID + токен"), ("Цели", "заявка, звонок, покупка"),
    ("Кампания Директа", "черновик"), ("Группы объявлений", "тексты и цены"),
    ("Лимит бюджета", "не тратить без подтверждения"), ("Статистика", "отчёт в кабинет"),
    ("Telegram", "канал и бот"), ("VK", "сообщество"),
    ("WhatsApp", "другие мессенджеры"), ("Metricool", "планировщик постов"),
    ("Контент-план", "темы и график"), ("Очередь модерации", "перед публикацией"),
    ("Контент-редактор", "посты и тексты"), ("Ответчик", "сообщения и комменты"),
    ("Аналитик охватов", "метрики каналов"), ("Планировщик", "время выхода"),
    ("Тон и стиль", "голос бренда"), ("Фильтр безопасности", "правила площадок"),
    ("CallManager", "реестр звонков"), ("DialogueEngine", "сценарии и LLM"),
    ("STT", "речь → текст"), ("TTS", "текст → речь"),
    ("Телефония", "Mock / Twilio / Novofon"), ("Журнал calls", "транскрипт и заявка"),
    ("users", "владельцы"), ("sites", "сайты клиента"),
    ("workflows", "автоматизации"), ("invoices", "счета"),
    ("calls", "звонки и лиды"), ("app.db", "SQLite, WAL"),
    ("Личный кабинет", "всё в одном окне"), ("Отчёт по бизнесу", "сайт + реклама + соцсети"),
    ("Кнопка «Стоп»", "остановить всё"), ("DEV_LOG", "журнал работ"),
    ("Ветви Git", "feature/*"), ("Итог", "готовый бизнес"),
]

XS = [120 + i * 700 for i in range(6)]
BW = 620


def center_text(lines, font, cx, top, fill=INK, step=23):
    for i, line in enumerate(lines):
        bb = draw.textbbox((0, 0), line, font=font)
        draw.text((cx - (bb[2] - bb[0]) / 2, top + i * step), line, font=font, fill=fill)


def band(y1, y2, label):
    draw.rounded_rectangle((60, y1, W - 60, y2), radius=22, fill="#ffffff",
                           outline="#d8deea", width=3)
    band_labels.append((y1, label))


def box(rect, head, body, fill, border):
    draw.rounded_rectangle(rect, radius=14, fill=fill, outline=border, width=3)
    cx = (rect[0] + rect[2]) / 2
    center_text([head], f_head, cx, rect[1] + 14)
    center_text([body], f_body, cx, rect[1] + 46, fill=MUTED)


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
                end = min(pos + 16, length)
                draw.line([(a[0] + ux * pos, a[1] + uy * pos),
                           (a[0] + ux * end, a[1] + uy * end)], fill=color, width=width)
                pos += 26
    else:
        draw.line(points, fill=color, width=width, joint="curve")
    p1, p2 = points[-2], points[-1]
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    size = 15
    draw.polygon([p2,
                  (p2[0] + size * math.cos(ang + math.pi - 0.45), p2[1] + size * math.sin(ang + math.pi - 0.45)),
                  (p2[0] + size * math.cos(ang + math.pi + 0.45), p2[1] + size * math.sin(ang + math.pi + 0.45))], fill=color)


def tag(text, x, y):
    bb = draw.textbbox((0, 0), text, font=f_label)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    draw.rounded_rectangle((x - w / 2 - 8, y - h / 2 - 5, x + w / 2 + 8, y + h / 2 + 7),
                           radius=6, fill="#ffffff", outline="#d8deea")
    draw.text((x - w / 2, y - h / 2), text, font=f_label, fill=MUTED)


center_text(["ClirntCabinet — ПОЛНАЯ ВЕРСИЯ: один промпт → готовый бизнес"],
            f_title, W / 2, 30)
center_text(["сайты, реклама, соцсети, мессенджеры, ИИ-ведущие, звонки, цена и окупаемость"],
            f_sub, W / 2, 96, fill=MUTED)

palette = ["#eef2ff", "#ede9fe", "#e0f2fe", "#e8f5ee", "#fff5e6", "#fee2e2"]
borders = ["#4059a8", "#5b4bdb", "#0369a1", "#2f855a", "#b45309", "#b91c1c"]

centers: dict[int, tuple[int, int, int, int]] = {}
idx = 0
for bi, (y1, y2, label) in enumerate(BANDS):
    band(y1, y2, label)
    for ci, x in enumerate(XS):
        head, body = BOXES[idx]
        rect = (x, y1 + 42, x + BW, y1 + 212)
        box(rect, head, body, palette[(bi + ci) % 6], borders[(bi + ci) % 6])
        centers[idx] = rect
        idx += 1

assert idx == len(BOXES)

for bi in range(len(BANDS)):
    for ci in range(5):
        a, b = centers[bi * 6 + ci], centers[bi * 6 + ci + 1]
        arrow([(a[2], (a[1] + a[3]) / 2), (b[0], (b[1] + b[3]) / 2)])

for bi in range(len(BANDS) - 1):
    for ci in range(6):
        a, b = centers[bi * 6 + ci], centers[(bi + 1) * 6 + ci]
        arrow([((a[0] + a[2]) / 2, a[3]), ((b[0] + b[2]) / 2, b[1])], color="#4f6bb5")

words = ["event", "HTTP", "WS", "ack", "retry", "cache", "TTL", "stream", "push", "sync", "queue"]
for i in range(80):
    a_i, b_i = rnd.randrange(len(BOXES)), rnd.randrange(len(BOXES))
    if a_i == b_i:
        continue
    a, b = centers[a_i], centers[b_i]
    p1 = (rnd.randint(a[0], a[2]), rnd.randint(a[1], a[3]))
    p2 = (rnd.randint(b[0], b[2]), rnd.randint(b[1], b[3]))
    mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
    dashed = rnd.random() < 0.3
    arrow([p1, mid, p2], color=DASH if dashed else LINE, width=2, dashed=dashed)
    if i % 6 == 0:
        tag(rnd.choice(words), mid[0], mid[1])

tail = centers[len(BOXES) - 1]
head_b = centers[0]
arrow([(tail[0], (tail[1] + tail[3]) / 2), (30, (tail[1] + tail[3]) / 2),
       (30, (head_b[1] + head_b[3]) / 2), (head_b[0], (head_b[1] + head_b[3]) / 2)],
      color=DASH, dashed=True, width=4)

for y1, text in band_labels:
    draw.rounded_rectangle((60, y1, 1000, y1 + 52), radius=14, fill=LINE)
    draw.text((80, y1 + 8), text, font=f_band, fill="#ffffff")

center_text(["Петля: готовый бизнес → отчёт → новый промпт → улучшение"],
            f_label, W / 2, 2670, fill=MUTED)

out = Path(__file__).resolve().parent.parent / "docs" / "business_full.png"
img.save(out)
print("saved", out, W, "x", H)
