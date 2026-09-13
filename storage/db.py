"""SQLite storage for sync state and user feedback -- deliberately simple,
no ORM, since this is a single-user portfolio-scale tool."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path("data/kba.db")


@contextmanager
def _connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_state (
                connector_name TEXT PRIMARY KEY,
                last_sync_time TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                answer TEXT,
                rating INTEGER,          -- 1 = thumbs up, -1 = thumbs down
                created_at TEXT
            )
            """
        )


def get_last_sync_time(connector_name: str) -> Optional[datetime]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT last_sync_time FROM sync_state WHERE connector_name = ?",
            (connector_name,),
        ).fetchone()
    return datetime.fromisoformat(row[0]) if row else None


def set_last_sync_time(connector_name: str, timestamp: datetime):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO sync_state (connector_name, last_sync_time) VALUES (?, ?) "
            "ON CONFLICT(connector_name) DO UPDATE SET last_sync_time = excluded.last_sync_time",
            (connector_name, timestamp.isoformat()),
        )


def log_feedback(question: str, answer: str, rating: int):
    with _connect() as conn:
        conn.execute(
            "INSERT INTO feedback (question, answer, rating, created_at) VALUES (?, ?, ?, ?)",
            (question, answer, rating, datetime.now().isoformat()),
        )


def get_feedback_summary() -> dict:
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        positive = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating = 1").fetchone()[0]
    return {"total": total, "positive": positive, "negative": total - positive}
