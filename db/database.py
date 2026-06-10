"""
CP Manager — Database Layer
Uses Python standard library sqlite3.
"""

import os
import sqlite3
from pathlib import Path

# ── Database path ──────────────────────────────────────────────────────────────
DB_DIR = Path.home() / ".cp-manager"
DB_PATH = DB_DIR / "cp-manager.db"
SCHEMA_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = SCHEMA_DIR / "schema.sql"


def get_connection() -> sqlite3.Connection:
    """Return a sqlite3.Connection with row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create the database directory, connect, and run schema.sql."""
    DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = get_connection()
    try:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


def read_setting(key: str) -> str | None:
    """Read a setting value by key. Returns None if not found."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None
    finally:
        conn.close()


def save_setting(key: str, value: str) -> None:
    """Upsert a setting key/value pair."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO settings (key, value) VALUES (?, ?)
               ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
            (key, value),
        )
        conn.commit()
    finally:
        conn.close()
