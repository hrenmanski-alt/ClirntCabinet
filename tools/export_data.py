"""Экспорт таблиц SQLite в CSV.

Запуск: python3 tools/export_data.py [имя_таблицы ...]
По умолчанию экспортируются users, calls, invoices.
"""

from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "ai-call-center" / "data" / "app.db"
OUT = ROOT / "exports"

TABLES = ("users", "calls", "invoices", "sites", "workflows")


def export(table: str) -> Path:
    if not DB.exists():
        raise SystemExit(f"База не найдена: {DB}")
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    if not rows:
        print(f"[skip] {table}: пусто")
        return OUT / f"{table}.csv"

    OUT.mkdir(exist_ok=True)
    path = OUT / f"{table}.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(dict(row) for row in rows)
    print(f"[ok] {table}: {len(rows)} строк → {path}")
    return path


if __name__ == "__main__":
    names = sys.argv[1:] or list(TABLES)
    for name in names:
        if name not in TABLES:
            print(f"[skip] неизвестная таблица: {name}")
            continue
        export(name)
