"""Apex — Hybrid Memory System
Short-term (SQLite) + Long-term (Vector) + Shared (Knowledge Graph)
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


class Memory:
    """Agent memory system"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._init_db()

    def _init_db(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                source TEXT DEFAULT '',
                confidence REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key)
        """)
        self._conn.commit()

    def remember(self, key: str, value: str, source: str = "", confidence: float = 1.0):
        """Store a memory"""
        self._conn.execute(
            "INSERT INTO memories (key, value, source, confidence) VALUES (?, ?, ?, ?)",
            (key, value, source, confidence),
        )
        self._conn.commit()

    def recall(self, key: str) -> Optional[str]:
        """Recall a memory"""
        cursor = self._conn.execute(
            "SELECT value FROM memories WHERE key = ? ORDER BY confidence DESC LIMIT 1",
            (key,),
        )
        row = cursor.fetchone()
        if row:
            self._conn.execute(
                "UPDATE memories SET accessed_at = CURRENT_TIMESTAMP WHERE key = ?",
                (key,),
            )
            self._conn.commit()
            return row[0]
        return None

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Search memories (FTS5 simple search)"""
        cursor = self._conn.execute(
            """SELECT key, value, source, confidence FROM memories
               WHERE key LIKE ? OR value LIKE ?
               ORDER BY confidence DESC LIMIT ?""",
            (f"%{query}%", f"%{query}%", limit),
        )
        return [
            {"key": row[0], "value": row[1], "source": row[2], "confidence": row[3]}
            for row in cursor.fetchall()
        ]

    def forget(self, key: str):
        """Delete a memory"""
        self._conn.execute("DELETE FROM memories WHERE key = ?", (key,))
        self._conn.commit()

    def clear(self):
        """Clear all memories"""
        self._conn.execute("DELETE FROM memories")
        self._conn.commit()
