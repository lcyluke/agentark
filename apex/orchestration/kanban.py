"""Apex — 智能Kanban
任务队列 + 状态管理 + AI建议。
"""
from __future__ import annotations

import json
import uuid
import sqlite3
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


TASK_STATUS_TODO = "todo"
TASK_STATUS_READY = "ready"
TASK_STATUS_IN_PROGRESS = "in_progress"
TASK_STATUS_BLOCKED = "blocked"
TASK_STATUS_DONE = "done"
TASK_STATUS_FAILED = "failed"


@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    assignee: str = ""
    status: str = TASK_STATUS_TODO
    priority: int = 2
    parent_id: Optional[str] = None
    depends_on: list[str] = field(default_factory=list)
    output: str = ""
    cost: float = 0.0
    created_at: str = ""
    completed_at: Optional[str] = None


class Kanban:
    """智能看板 — 管理Agent任务队列"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._init_db()

    def _init_db(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                assignee TEXT DEFAULT '',
                status TEXT DEFAULT 'todo',
                priority INTEGER DEFAULT 2,
                parent_id TEXT,
                depends_on TEXT DEFAULT '[]',
                output TEXT DEFAULT '',
                cost REAL DEFAULT 0.0,
                created_at TEXT DEFAULT '',
                completed_at TEXT
            )
        """)
        self._conn.commit()

    def create_task(self, title: str, **kwargs) -> Task:
        """创建任务"""
        task_id = kwargs.get("id", f"t_{uuid.uuid4().hex[:8]}")
        task = Task(
            id=task_id,
            title=title,
            description=kwargs.get("description", ""),
            assignee=kwargs.get("assignee", ""),
            status=kwargs.get("status", TASK_STATUS_TODO),
            priority=kwargs.get("priority", 2),
            parent_id=kwargs.get("parent_id"),
            depends_on=kwargs.get("depends_on", []),
            created_at=datetime.now().isoformat(),
        )
        self._conn.execute(
            """INSERT INTO tasks
               (id, title, description, assignee, status, priority, parent_id, depends_on, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task.id, task.title, task.description, task.assignee,
                task.status, task.priority, task.parent_id,
                json.dumps(task.depends_on), task.created_at,
            ),
        )
        self._conn.commit()
        return task

    def update_task(self, task_id: str, **updates):
        """更新任务"""
        allowed = {"status", "assignee", "output", "cost", "title", "description", "priority"}
        sets = []
        values = []
        for k, v in updates.items():
            if k in allowed:
                sets.append(f"{k} = ?")
                if k == "depends_on":
                    values.append(json.dumps(v))
                else:
                    values.append(v)
        if not sets:
            return
        if "status" in updates and updates["status"] in (TASK_STATUS_DONE, TASK_STATUS_FAILED):
            sets.append("completed_at = ?")
            values.append(datetime.now().isoformat())
        values.append(task_id)
        self._conn.execute(f"UPDATE tasks SET {', '.join(sets)} WHERE id = ?", values)
        self._conn.commit()

    def get_task(self, task_id: str) -> Optional[Task]:
        cursor = self._conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return Task(
            id=row[0], title=row[1], description=row[2], assignee=row[3],
            status=row[4], priority=row[5], parent_id=row[6],
            depends_on=json.loads(row[7]), output=row[8], cost=row[9],
            created_at=row[10], completed_at=row[11],
        )

    def list_tasks(self, status: str = None, assignee: str = None) -> list[Task]:
        """列出任务"""
        query = "SELECT * FROM tasks"
        params = []
        conditions = []
        if status:
            conditions.append("status = ?")
            params.append(status)
        if assignee:
            conditions.append("assignee = ?")
            params.append(assignee)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY priority, created_at ASC"

        cursor = self._conn.execute(query, params)
        tasks = []
        for row in cursor.fetchall():
            tasks.append(Task(
                id=row[0], title=row[1], description=row[2], assignee=row[3],
                status=row[4], priority=row[5], parent_id=row[6],
                depends_on=json.loads(row[7]), output=row[8], cost=row[9],
                created_at=row[10], completed_at=row[11],
            ))
        return tasks

    def get_ready_tasks(self) -> list[Task]:
        """获取所有可就绪的任务（依赖已满足的）"""
        tasks = self.list_tasks(status=TASK_STATUS_TODO)
        ready = []
        for task in tasks:
            if not task.depends_on:
                task.status = TASK_STATUS_READY
                self.update_task(task.id, status=TASK_STATUS_READY)
                ready.append(task)
            else:
                deps_met = all(
                    self.get_task(dep_id) and self.get_task(dep_id).status == TASK_STATUS_DONE
                    for dep_id in task.depends_on
                )
                if deps_met:
                    task.status = TASK_STATUS_READY
                    self.update_task(task.id, status=TASK_STATUS_READY)
                    ready.append(task)
        return ready

    def ai_suggestions(self) -> list[str]:
        """简单的AI建议（Phase 2: 真正的AI驱动）"""
        suggestions = []
        tasks = self.list_tasks()
        in_progress = [t for t in tasks if t.status == TASK_STATUS_IN_PROGRESS]
        todo = [t for t in tasks if t.status == TASK_STATUS_TODO]
        if len(in_progress) >= 3:
            suggestions.append(f"当前有{len(in_progress)}个任务在进行中，建议集中处理避免并行过多")
        if todo:
            suggestions.append(f"还有{len(todo)}个待办任务等待分配")
        return suggestions
