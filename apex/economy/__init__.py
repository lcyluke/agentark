"""Apex — Token Economy (Token Economics)
Intelligent budget allocation + Task-value-based model routing + Cost dashboard.
Core goal: Save 95% of costs while maintaining 95%+ capability.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta

from apex.core.profile import Profile, APEX_HOME


@dataclass
class ModelRoute:
    """Model routing rule"""
    task_type: str
    model: str
    provider: str
    cost_per_1k_input: float  # USD
    cost_per_1k_output: float
    quality_score: int  # 1-10

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens * self.cost_per_1k_input / 1000 +
                output_tokens * self.cost_per_1k_output / 1000)


# ─── Default model routing table ───
MODEL_ROUTES = [
    # 🟢 Low-cost tasks -> Local free
    ModelRoute("simple-reply", "llama3-8b", "ollama", 0, 0, 3),
    ModelRoute("simple-edit", "llama3-8b", "ollama", 0, 0, 4),
    # 🟡 Medium tasks -> DeepSeek (high cost-effectiveness)
    ModelRoute("code-review", "deepseek-v4-pro", "deepseek", 0.001, 0.004, 9),
    ModelRoute("bug-fix", "deepseek-v4-pro", "deepseek", 0.001, 0.004, 9),
    ModelRoute("api-design", "deepseek-v4-pro", "deepseek", 0.001, 0.004, 9),
    ModelRoute("writing", "deepseek-v4-pro", "deepseek", 0.001, 0.004, 9),
    ModelRoute("data-analysis", "deepseek-v4-pro", "deepseek", 0.001, 0.004, 9),
    # 🔴 High-complexity tasks -> Claude
    ModelRoute("architecture", "claude-sonnet", "anthropic", 0.003, 0.015, 10),
    ModelRoute("system-design", "claude-sonnet", "anthropic", 0.003, 0.015, 10),
    # 🟣 Vision tasks -> Claude Vision
    ModelRoute("vision", "claude-sonnet", "anthropic", 0.003, 0.015, 9),
    # ⚪ Default
    ModelRoute("default", "deepseek-v4-pro", "deepseek", 0.001, 0.004, 8),
]

TASK_TYPE_KEYWORDS = {
    "architecture": ["architecture", "design pattern", "system design", "architecture", "scalability"],
    "system-design": ["system architecture", "technology selection", "distributed", "database design", "schema"],
    "code-review": ["review", "review", "code review", "code review"],
    "bug-fix": ["bug", "fix", "fix", "error", "debug", "debug"],
    "api-design": ["api", "rest", "graphql", "endpoint", "api design"],
    "writing": ["copy", "documentation", "blog", "article", "content", "copywriting"],
    "data-analysis": ["data analysis", "statistics", "data", "analyze", "analysis"],
    "simple-reply": ["hello", "hi", "simple", "reply", "format"],
    "simple-edit": ["rename", "format", "rename", "format", "minor edit"],
    "vision": ["image", "image", "image", "vision", "screenshot", "screenshot"],
}


def classify_task(task: str) -> str:
    """Intelligently classify task type"""
    task_lower = task.lower()
    for task_type, keywords in TASK_TYPE_KEYWORDS.items():
        if any(kw in task_lower for kw in keywords):
            return task_type
    return "default"


def select_model(task: str, budget_remaining: float = 1.0) -> ModelRoute:
    """Select the best cost-effective model based on task and budget"""
    task_type = classify_task(task)

    # Find matching route
    for route in MODEL_ROUTES:
        if route.task_type == task_type:
            # Budget check
            if route.cost_per_1k_input > 0 and budget_remaining < 0.01 and route.cost_per_1k_input > 0.001:
                # Downgrade when budget is low
                for fallback in MODEL_ROUTES:
                    if fallback.task_type == "default":
                        return fallback
            return route

    return MODEL_ROUTES[-1]  # default


# ─── Budget Management ───
@dataclass
class BudgetAccount:
    """Budget account"""
    project: str
    monthly_limit: float  # USD
    used: float = 0.0
    warning_threshold: float = 0.8  # 80% triggers warning


class BudgetManager:
    """Budget manager — similar to a banking system"""

    def __init__(self, db_path: Path = APEX_HOME / "economy.db"):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                project TEXT PRIMARY KEY,
                monthly_limit REAL DEFAULT 5.0,
                used REAL DEFAULT 0.0,
                warning_threshold REAL DEFAULT 0.8
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project TEXT NOT NULL,
                amount REAL NOT NULL,
                task_type TEXT DEFAULT '',
                model TEXT DEFAULT '',
                task_preview TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._conn.commit()

    def get_or_create_account(self, project: str, monthly_limit: float = 5.0) -> BudgetAccount:
        cursor = self._conn.execute("SELECT * FROM accounts WHERE project = ?", (project,))
        row = cursor.fetchone()
        if row:
            return BudgetAccount(project=row[0], monthly_limit=row[1], used=row[2], warning_threshold=row[3])
        self._conn.execute(
            "INSERT INTO accounts (project, monthly_limit) VALUES (?, ?)",
            (project, monthly_limit),
        )
        self._conn.commit()
        return BudgetAccount(project=project, monthly_limit=monthly_limit)

    def record_usage(self, project: str, amount: float, task_type: str = "", model: str = "", task: str = ""):
        """Record a token consumption"""
        self._conn.execute(
            "UPDATE accounts SET used = used + ? WHERE project = ?",
            (amount, project),
        )
        self._conn.execute(
            """INSERT INTO transactions (project, amount, task_type, model, task_preview)
               VALUES (?, ?, ?, ?, ?)""",
            (project, amount, task_type, model, task[:100]),
        )
        self._conn.commit()

    def get_balance(self, project: str) -> tuple[float, float, float]:
        """Get balance info (used, limit, remaining)"""
        account = self.get_or_create_account(project)
        remaining = account.monthly_limit - account.used
        return account.used, account.monthly_limit, max(0, remaining)

    def check_warning(self, project: str) -> Optional[str]:
        """Check if a warning is needed"""
        account = self.get_or_create_account(project)
        if account.monthly_limit == 0:
            return None
        ratio = account.used / account.monthly_limit
        if ratio >= 1.0:
            return f"🔴 {project}: Monthly budget exhausted (${account.used:.2f}/${account.monthly_limit:.2f})"
        elif ratio >= account.warning_threshold:
            return f"🟡 {project}: Budget usage at {ratio:.0%} (${account.used:.2f}/${account.monthly_limit:.2f})"
        return None

    def get_daily_report(self) -> str:
        """Generate today's cost report"""
        today = datetime.now().strftime("%Y-%m-%d")
        # Get today's transactions
        cursor = self._conn.execute(
            """SELECT project, SUM(amount), COUNT(*) FROM transactions
               WHERE date(created_at) = date('now')
               GROUP BY project""",
        )
        rows = cursor.fetchall()
        if not rows:
            return "📊 No token consumption today"

        report = "📊 **Today's Cost Report**\n"
        total = 0.0
        for project, amount, count in rows:
            total += amount
            report += f"  • {project}: ${amount:.4f} ({count} calls)\n"
        report += f"  ─────────────\n  **Daily Total: ${total:.4f}**"
        return report

    def transfer_budget(self, from_project: str, to_project: str, amount: float) -> bool:
        """Transfer budget across projects"""
        from_acc = self.get_or_create_account(from_project)
        to_acc = self.get_or_create_account(to_project)
        available = from_acc.monthly_limit - from_acc.used
        if amount > available:
            return False
        self._conn.execute("UPDATE accounts SET used = used - ? WHERE project = ?", (amount, from_project))
        self._conn.execute("UPDATE accounts SET used = used - ? WHERE project = ?", (-amount, to_project))
        self._conn.commit()
        return True


class TokenRouter:
    """Intelligent router — automatically select the best model based on task type"""

    def __init__(self, budget_mgr: BudgetManager = None):
        self.budget_mgr = budget_mgr or BudgetManager()

    def route(self, task: str, profile: Profile = None, project: str = "default") -> dict:
        """Select the optimal route for a task"""
        task_type = classify_task(task)
        _, _, remaining = self.budget_mgr.get_balance(project) if self.budget_mgr else (0, 5, 5)

        route = select_model(task, budget_remaining=remaining)

        return {
            "task_type": task_type,
            "model": route.model,
            "provider": route.provider,
            "estimated_cost_per_1k": route.cost_per_1k_input,
            "quality_score": route.quality_score,
            "budget_remaining": remaining,
        }
