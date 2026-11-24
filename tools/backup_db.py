"""Бэкап SQLite-базы с именем по дате и времени.

Запуск: python3 tools/backup_db.py
Результат: backups/app_YYYYMMDD_HHMMSS.db
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "ai-call-center" / "data" / "app.db"
BACKUPS = ROOT / "backups"

if not DB.exists():
    raise SystemExit(f"База не найдена: {DB}")

BACKUPS.mkdir(exist_ok=True)
name = "app_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".db"
target = BACKUPS / name
shutil.copy2(DB, target)
print(f"Бэкап готов: {target} ({target.stat().st_size} байт)")
