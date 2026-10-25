"""SQLite map of learner → Backboard thread, plus failed-check counts for the ladder."""

from __future__ import annotations

import os
import sqlite3
import threading
from pathlib import Path


def data_dir() -> Path:
    return Path(os.environ.get("ACADEMY_DATA_DIR", "/tmp/academy"))


class AcademyStore:
    def __init__(self, path: Path | None = None):
        self.path = path or (data_dir() / "memory.sqlite")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS threads (
                    learner_id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS failed_checks (
                    learner_id TEXT NOT NULL,
                    level_id TEXT NOT NULL,
                    n INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (learner_id, level_id)
                );
                CREATE TABLE IF NOT EXISTS demo_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    memory TEXT NOT NULL
                );
                """
            )

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_thread(self, learner_id: str) -> str | None:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT thread_id FROM threads WHERE learner_id = ?", (learner_id,)).fetchone()
        return None if row is None else row["thread_id"]

    def set_thread(self, learner_id: str, thread_id: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO threads (learner_id, thread_id) VALUES (?, ?) "
                "ON CONFLICT(learner_id) DO UPDATE SET thread_id = excluded.thread_id",
                (learner_id, thread_id),
            )

    def get_meta(self, key: str) -> str | None:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return None if row is None else row["value"]

    def set_meta(self, key: str, value: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    def increment_failed(self, learner_id: str, level_id: str) -> int:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO failed_checks (learner_id, level_id, n) VALUES (?, ?, 1)
                ON CONFLICT(learner_id, level_id) DO UPDATE SET n = n + 1
                """,
                (learner_id, level_id),
            )
            row = conn.execute(
                "SELECT n FROM failed_checks WHERE learner_id = ? AND level_id = ?",
                (learner_id, level_id),
            ).fetchone()
        return int(row["n"])

    def failed_count(self, learner_id: str, level_id: str) -> int:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT n FROM failed_checks WHERE learner_id = ? AND level_id = ?",
                (learner_id, level_id),
            ).fetchone()
        return 0 if row is None else int(row["n"])

    def add_demo_message(self, thread_id: str, content: str, memory: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO demo_messages (thread_id, content, memory) VALUES (?, ?, ?)",
                (thread_id, content, memory),
            )

    def demo_messages(self, thread_id: str) -> list[str]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT content FROM demo_messages WHERE thread_id = ? ORDER BY id",
                (thread_id,),
            ).fetchall()
        return [row["content"] for row in rows]
