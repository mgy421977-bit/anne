"""Local SQLite-backed interaction memory for offline ANNE operation."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path


class LocalMemory:
    """Minimal durable memory backend with no network dependency."""

    def __init__(self, db_path: str | Path = "anne_offline.db") -> None:
        self.conn = sqlite3.connect(str(db_path))
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS interactions ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, "
            "user_input TEXT, response TEXT, learning TEXT, confidence REAL)"
        )
        self.conn.commit()

    def context(self, limit: int = 8) -> str:
        rows = self.conn.execute(
            "SELECT timestamp, user_input, learning, response FROM interactions "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        if not rows:
            return "No local memories have been recorded yet."
        return "\n\n---\n\n".join(
            f"[{row[0]}] USER: {row[1]}\nLEARNING: {row[2]}\nRESPONSE: {row[3]}"
            for row in rows
        )

    def save(
        self,
        user_input: str,
        response: str,
        learning: str,
        confidence: float = 0.5,
    ) -> str:
        timestamp = datetime.now(UTC).isoformat()
        self.conn.execute(
            "INSERT INTO interactions(timestamp, user_input, response, learning, confidence) "
            "VALUES (?, ?, ?, ?, ?)",
            (timestamp, user_input, response, learning, max(0.0, min(1.0, confidence))),
        )
        self.conn.commit()
        row_id = self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return f"local:interactions/{row_id}"


__all__ = ["LocalMemory"]
