"""Apex — Skill System
Evolvable skill packages that auto-optimize from execution feedback.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Skill:
    name: str
    description: str = ""
    prompt_template: str = ""
    examples: list[dict] = field(default_factory=list)
    pitfalls: list[str] = field(default_factory=list)
    confidence: float = 1.0
    use_count: int = 0
    success_count: int = 0

    def success_rate(self) -> float:
        if self.use_count == 0:
            return 1.0
        return self.success_count / self.use_count


class SkillManager:
    """Manage all skill packages"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                name TEXT PRIMARY KEY,
                description TEXT DEFAULT '',
                prompt_template TEXT DEFAULT '',
                examples TEXT DEFAULT '[]',
                pitfalls TEXT DEFAULT '[]',
                confidence REAL DEFAULT 1.0,
                use_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0
            )
        """)
        self._conn.commit()

    def register(self, skill: Skill):
        """Register a skill"""
        self._conn.execute(
            """INSERT OR REPLACE INTO skills
               (name, description, prompt_template, examples, pitfalls, confidence, use_count, success_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                skill.name,
                skill.description,
                skill.prompt_template,
                json.dumps(skill.examples),
                json.dumps(skill.pitfalls),
                skill.confidence,
                skill.use_count,
                skill.success_count,
            ),
        )
        self._conn.commit()

    def get(self, name: str) -> Optional[Skill]:
        cursor = self._conn.execute("SELECT * FROM skills WHERE name = ?", (name,))
        row = cursor.fetchone()
        if not row:
            return None
        return Skill(
            name=row[0],
            description=row[1],
            prompt_template=row[2],
            examples=json.loads(row[3]),
            pitfalls=json.loads(row[4]),
            confidence=row[5],
            use_count=row[6],
            success_count=row[7],
        )

    def list(self) -> list[Skill]:
        cursor = self._conn.execute("SELECT * FROM skills ORDER BY use_count DESC")
        skills = []
        for row in cursor.fetchall():
            skills.append(Skill(
                name=row[0],
                description=row[1],
                prompt_template=row[2],
                examples=json.loads(row[3]),
                pitfalls=json.loads(row[4]),
                confidence=row[5],
                use_count=row[6],
                success_count=row[7],
            ))
        return skills

    def record_use(self, name: str, success: bool):
        """Record a usage"""
        skill = self.get(name)
        if not skill:
            return
        skill.use_count += 1
        if success:
            skill.success_count += 1
        skill.confidence = skill.success_rate()
        self.register(skill)
