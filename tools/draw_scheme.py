"""Рисует простую схему ClirntCabinet со всеми связями линиями."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1600, 1120
INK = "#20263a"
MUTED = "#5b6478"
LINE = "#4059a8"
DASH = "#8a94ad"

FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

f_title = ImageFont.truetype(FONT_BOLD, 42)
f_sub = ImageFont.truetype(FONT_REG, 22)
f_head = ImageFont.truetype(FONT_BOLD, 24)
f_body = ImageFont.truetype(FONT_REG, 17)
f_label = ImageFont.truetype(FONT_REG, 17)

img = Image.new("RGB", (W, H), "#f7f8fc")
draw = ImageDraw.Draw(img)


def text_center(lines: list[str], font: ImageFont.FreeTypeFont, cx: float, top: float,
                fill: str = INK, step: int = 28) -> None:
    for i, line in enumerate(lines):
        bb = draw.textbbox((0, 0), line, font=font)
        draw.text((cx - (bb[2] - bb[0]) / 2, top + i * step), line, font=font, fill=fill)


def box(key: str, rect: tuple[int, int, int, int], head: str, body: list[str],
        fill: str, border: str) -> None:
    draw.rounded_rectangle(rect, radius=16, fill=fill, outline=border, width=3)
    x1, y1, x2, y2 = rect
    cx = (x1 + x2) / 2
    text_center([head], f_head, cx, y1 + 16)
    if body:
        text_center(body, f_body, cx, y1 + 48, fill=MUTED, step=22)
    boxes[key] = rect


def dashed_segment(p1, p2, color=DASH, width=3, dash=13, gap=9) -> None:
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if not length:
        return
    ux, uy = dx / length, dy / length
    pos = 0.0
    while pos < length:
        end = min(pos + dash, length)
        draw.line(
            [(p1[0] + ux * pos, p1[1] + uy * pos), (p1[0] + ux * end, p1[1] + uy * end)],
            fill=color, width=width,
        )
        pos += dash + gap


def arrow(points, color=LINE, width=3, dashed: bool = False, head: bool = True) -> None:
    if dashed:
        for a, b in zip(points, points[1:]):
            dashed_segment(a, b, color, width)
    else:
        draw.line(points, fill=color, width=width, joint="curve")
    if head:
        p1, p2 = points[-2], points[-1]
        angle = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        size = 15
        a = angle + math.pi - math.pi / 7
        b = angle + math.pi + math.pi / 7
        pa = (p2[0] + size * math.cos(a), p2[1] + size * math.sin(a))
        pb = (p2[0] + size * math.cos(b), p2[1] + size * math.sin(b))
        draw.polygon([p2, pa, pb], fill=color)


def label(text: str, x: int, y: int) -> None:
    bb = draw.textbbox((0, 0), text, font=f_label)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    draw.rounded_rectangle((x - w / 2 - 7, y - h / 2 - 4, x + w / 2 + 7, y + h / 2 + 6),
                           radius=6, fill="#f7f8fc")
    draw.text((x - w / 2, y - h / 2), text, font=f_label, fill=MUTED)


boxes: dict[str, tuple[int, int, int, int]] = {}

text_center(["ClirntCabinet — как всё работает"], f_title, W / 2, 32)
text_center(["Клиент выбирает готовое решение — сервер делает остальное. Все связи показаны линиями."],
            f_sub, W / 2, 92, fill=MUTED)

# ── Блоки ───────────────────────────────────────────────────────────────────
box("client", (70, 150, 350, 240), "КЛИЕНТ",
    ["браузер / телефон"], "#eef2ff", "#4059a8")
box("cabinet", (600, 150, 1000, 240), "ЛИЧНЫЙ КАБИНЕТ",
    ["FastAPI: вход, каталог, счета"], "#eef2ff", "#4059a8")
box("db", (1230, 150, 1560, 240), "БАЗА ДАННЫХ",
    ["пользователи, сайты,", "звонки, счета"], "#f1f5f9", "#64748b")

box("catalog", (70, 340, 500, 440), "КАТАЛОГ РЕШЕНИЙ",
    ["сайт, заявки, напоминания,", "автоответ, AI-звонки"], "#e8f5ee", "#2f855a")
box("billing", (580, 340, 900, 440), "СЧЕТА И ОПЛАТА",
    ["демо-режим / ЮKassa"], "#fff5e6", "#b45309")
box("core", (980, 340, 1560, 440), "ЯДРО АВТОМАТИЗАЦИЙ",
    ["готовые сценарии без программистов"], "#ede9fe", "#5b4bdb")

box("telegram", (650, 540, 920, 640), "TELEGRAM",
    ["уведомления и заявки"], "#e0f2fe", "#0369a1")
box("ai", (980, 540, 1250, 640), "ИИ-ДИАЛОГ",
    ["готовые сценарии:", "продажи, поддержка"], "#ede9fe", "#5b4bdb")
box("telephony", (1280, 540, 1560, 640), "ТЕЛЕФОНИЯ",
    ["Twilio / демо"], "#fee2e2", "#b91c1c")

box("result", (650, 740, 920, 840), "РЕЗУЛЬТАТ",
    ["заявка и статус"], "#e8f5ee", "#2f855a")
box("speech", (980, 740, 1250, 840), "STT → ИИ → TTS",
    ["речь в текст и обратно"], "#ede9fe", "#5b4bdb")
box("call", (1280, 740, 1560, 840), "ЗВОНОК ЧЕЛОВЕКУ",
    ["телефон / браузер"], "#fee2e2", "#b91c1c")

# ── Линии ───────────────────────────────────────────────────────────────────
arrow([(350, 195), (600, 195)])
label("выбор решения", 475, 178)

arrow([(1000, 195), (1230, 195)])
label("сохранить", 1115, 178)

arrow([(700, 240), (285, 340)])
arrow([(500, 390), (580, 390)])
arrow([(900, 390), (980, 390)])
label("оплата запускает", 940, 372)

arrow([(1100, 440), (785, 540)])
arrow([(1240, 440), (1115, 540)])
arrow([(1390, 440), (1405, 540)])

arrow([(785, 640), (785, 740)])
arrow([(1115, 640), (1115, 740)])
label("речь → текст → речь", 1115, 690)
arrow([(1405, 640), (1405, 740)])

arrow([(980, 790), (920, 790)])
arrow([(1405, 840), (1405, 885), (785, 885), (785, 840)])
arrow([(650, 790), (40, 790), (40, 195), (70, 195)], color=DASH, dashed=True, head=True)
label("результат виден клиенту", 250, 770)

img.save(Path(__file__).resolve().parent.parent / "docs" / "scheme.png")
print("saved docs/scheme.png")
