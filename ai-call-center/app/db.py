from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Any

_DB_PATH = Path(
    os.getenv("DB_PATH", str(Path(__file__).resolve().parent.parent / "data" / "app.db"))
)
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                template TEXT NOT NULL,
                title TEXT NOT NULL,
                data TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'draft',
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                recipe TEXT NOT NULL,
                title TEXT NOT NULL,
                config TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'created',
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                amount INTEGER NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                provider TEXT NOT NULL DEFAULT 'mock',
                phone TEXT NOT NULL DEFAULT '',
                scenario TEXT NOT NULL DEFAULT 'sales',
                status TEXT NOT NULL DEFAULT 'created',
                transcript TEXT NOT NULL DEFAULT '[]',
                result TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL,
                finished_at REAL
            );
            """
        )


# ── Пароли ──────────────────────────────────────────────────────────────────
def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 120_000).hex()
    return salt, digest


def verify_password(password: str, salt: str, digest: str) -> bool:
    return secrets.compare_digest(hash_password(password, salt)[1], digest)


# ── Пользователи и сессии ───────────────────────────────────────────────────
def create_user(email: str, password: str) -> int | None:
    email = email.strip().lower()
    salt, digest = hash_password(password)
    try:
        with connect() as conn:
            cur = conn.execute(
                "INSERT INTO users (email, salt, password_hash, created_at) VALUES (?,?,?,?)",
                (email, salt, digest, time.time()),
            )
            return int(cur.lastrowid)
    except sqlite3.IntegrityError:
        return None


def get_user_by_email(email: str) -> sqlite3.Row | None:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
        ).fetchone()


def get_user_by_id(user_id: int) -> sqlite3.Row | None:
    with connect() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    with connect() as conn:
        conn.execute(
            "INSERT INTO sessions (token, user_id, created_at) VALUES (?,?,?)",
            (token, user_id, time.time()),
        )
    return token


def get_session_user(token: str | None) -> sqlite3.Row | None:
    if not token:
        return None
    with connect() as conn:
        return conn.execute(
            """SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id
               WHERE s.token = ?""",
            (token,),
        ).fetchone()


def delete_session(token: str | None) -> None:
    if not token:
        return
    with connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


# ── Проекты пользователя ────────────────────────────────────────────────────
def create_site(user_id: int, template: str, title: str, data: dict[str, Any]) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO sites (user_id, template, title, data, created_at) VALUES (?,?,?,?,?)",
            (user_id, template, title, json.dumps(data, ensure_ascii=False), time.time()),
        )
        return int(cur.lastrowid)


def list_sites(user_id: int) -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM sites WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()


def create_workflow(user_id: int, recipe: str, title: str, config: dict[str, Any]) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO workflows (user_id, recipe, title, config, created_at) VALUES (?,?,?,?,?)",
            (user_id, recipe, title, json.dumps(config, ensure_ascii=False), time.time()),
        )
        return int(cur.lastrowid)


def list_workflows(user_id: int) -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM workflows WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()


def create_invoice(user_id: int, amount: int, description: str) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO invoices (user_id, amount, description, created_at) VALUES (?,?,?,?)",
            (user_id, amount, description, time.time()),
        )
        return int(cur.lastrowid)


def list_invoices(user_id: int) -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM invoices WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()


def pay_invoice(invoice_id: int, user_id: int) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE invoices SET status = 'paid' WHERE id = ? AND user_id = ?",
            (invoice_id, user_id),
        )


# ── Звонки ──────────────────────────────────────────────────────────────────
def create_call(user_id: int, phone: str, scenario: str, provider: str) -> int:
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO calls (user_id, provider, phone, scenario, status, created_at)
               VALUES (?,?,?,?,?,?)""",
            (user_id, provider, phone, scenario, "created", time.time()),
        )
        return int(cur.lastrowid)


def list_calls(user_id: int) -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM calls WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()


def get_call(call_id: int, user_id: int | None = None) -> sqlite3.Row | None:
    with connect() as conn:
        if user_id is None:
            return conn.execute("SELECT * FROM calls WHERE id = ?", (call_id,)).fetchone()
        return conn.execute(
            "SELECT * FROM calls WHERE id = ? AND user_id = ?", (call_id, user_id)
        ).fetchone()


def set_call_status(call_id: int, status: str) -> None:
    with connect() as conn:
        conn.execute("UPDATE calls SET status = ? WHERE id = ?", (status, call_id))


def append_transcript(call_id: int, role: str, text: str) -> None:
    with connect() as conn:
        row = conn.execute("SELECT transcript FROM calls WHERE id = ?", (call_id,)).fetchone()
        if not row:
            return
        transcript = json.loads(row["transcript"] or "[]")
        transcript.append({"role": role, "text": text})
        conn.execute(
            "UPDATE calls SET transcript = ? WHERE id = ?",
            (json.dumps(transcript, ensure_ascii=False), call_id),
        )


def finish_call(call_id: int, result: str = "", status: str = "completed") -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE calls SET status = ?, result = ?, finished_at = ? WHERE id = ?",
            (status, result, time.time(), call_id),
        )


def stats(user_id: int) -> dict[str, int]:
    with connect() as conn:
        def count(table: str) -> int:
            return conn.execute(
                f"SELECT COUNT(*) AS n FROM {table} WHERE user_id = ?", (user_id,)
            ).fetchone()["n"]

        return {
            "sites": count("sites"),
            "workflows": count("workflows"),
            "invoices": count("invoices"),
            "calls": count("calls"),
        }
