"""Apex — Token Economy（Token经济系统）
智能预算分配 + 按任务价值路由模型 + 成本看板。
核心目标：省95%费用的同时保持95%+的能力。
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
    """模型路由规则"""
    task_type: str
    model: str
    provider: str
    cost_per_1k_input: float  # 美元
    cost_per_1k_output: float
    quality_score: int  # 1-10

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens * self.cost_per_1k_input / 1000 +
                output_tokens * self.cost_per_1k_output / 1000)


# ─── 预设模型路由表 ───
MODEL_ROUTES = [
    # 🟢 低成本任务 → 本地免费
    ModelRoute("simple-reply", "llama3-8b", "ollama", 0, 0, 3),
    ModelRoute("simple-edit", "llama3-8b", "ollama", 0, 0, 4),
    # 🟡 中等任务 → DeepSeek（高性价比）
    ModelRoute("code-review", "deepseek-chat", "deepseek", 0.0005, 0.002, 8),
    ModelRoute("bug-fix", "deepseek-chat", "deepseek", 0.0005, 0.002, 8),
    ModelRoute("api-design", "deepseek-chat", "deepseek", 0.0005, 0.002, 8),
    ModelRoute("writing", "deepseek-chat", "deepseek", 0.0005, 0.002, 8),
    ModelRoute("data-analysis", "deepseek-chat", "deepseek", 0.0005, 0.002, 8),
    # 🔴 高复杂度任务 → Claude
    ModelRoute("architecture", "claude-sonnet", "anthropic", 0.003, 0.015, 10),
    ModelRoute("system-design", "claude-sonnet", "anthropic", 0.003, 0.015, 10),
    # 🟣 视觉任务 → Claude Vision
    ModelRoute("vision", "claude-sonnet", "anthropic", 0.003, 0.015, 9),
    # ⚪ 默认
    ModelRoute("default", "deepseek-chat", "deepseek", 0.0005, 0.002, 7),
]

TASK_TYPE_KEYWORDS = {
    "architecture": ["架构", "设计模式", "系统设计", "architecture", "scalability"],
    "system-design": ["系统架构", "技术选型", "分布式", "database design", "schema"],
    "code-review": ["审查", "review", "code review", "代码审查"],
    "bug-fix": ["bug", "修复", "fix", "错误", "调试", "debug"],
    "api-design": ["api", "rest", "graphql", "endpoint", "接口设计"],
    "writing": ["文案", "文档", "博客", "文章", "content", "copywriting"],
    "data-analysis": ["数据分析", "统计", "data", "analyze", "分析"],
    "simple-reply": ["hello", "hi", "简单", "回复", "格式"],
    "simple-edit": ["重命名", "格式化", "rename", "format", "小修改"],
    "vision": ["图片", "图像", "image", "vision", "截图", "screenshot"],
}


def classify_task(task: str) -> str:
    """智能分类任务类型"""
    task_lower = task.lower()
    for task_type, keywords in TASK_TYPE_KEYWORDS.items():
        if any(kw in task_lower for kw in keywords):
            return task_type
    return "default"


def select_model(task: str, budget_remaining: float = 1.0) -> ModelRoute:
    """根据任务和预算选择最优性价比模型"""
    task_type = classify_task(task)

    # 找到匹配的路由
    for route in MODEL_ROUTES:
        if route.task_type == task_type:
            # 预算检查
            if route.cost_per_1k_input > 0 and budget_remaining < 0.01 and route.cost_per_1k_input > 0.001:
                # 预算不足时降级
                for fallback in MODEL_ROUTES:
                    if fallback.task_type == "default":
                        return fallback
            return route

    return MODEL_ROUTES[-1]  # default


# ─── 预算管理 ───
@dataclass
class BudgetAccount:
    """预算账户"""
    project: str
    monthly_limit: float  # 美元
    used: float = 0.0
    warning_threshold: float = 0.8  # 80%触发预警


class BudgetManager:
    """预算管理器 — 类似银行系统"""

    def __init__(self, db_path: Path = APEX_HOME / "economy.db"):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
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
        """记录一次Token消耗"""
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
        """获取余额信息 (used, limit, remaining)"""
        account = self.get_or_create_account(project)
        remaining = account.monthly_limit - account.used
        return account.used, account.monthly_limit, max(0, remaining)

    def check_warning(self, project: str) -> Optional[str]:
        """检查是否需要预警"""
        account = self.get_or_create_account(project)
        if account.monthly_limit == 0:
            return None
        ratio = account.used / account.monthly_limit
        if ratio >= 1.0:
            return f"🔴 {project}: 月度预算已用完 (${account.used:.2f}/${account.monthly_limit:.2f})"
        elif ratio >= account.warning_threshold:
            return f"🟡 {project}: 预算使用已达{ratio:.0%} (${account.used:.2f}/${account.monthly_limit:.2f})"
        return None

    def get_daily_report(self) -> str:
        """生成今日成本报告"""
        today = datetime.now().strftime("%Y-%m-%d")
        # 获取今日交易
        cursor = self._conn.execute(
            """SELECT project, SUM(amount), COUNT(*) FROM transactions
               WHERE date(created_at) = date('now')
               GROUP BY project""",
        )
        rows = cursor.fetchall()
        if not rows:
            return "📊 今日无Token消耗"

        report = "📊 **今日成本报告**\n"
        total = 0.0
        for project, amount, count in rows:
            total += amount
            report += f"  • {project}: ${amount:.4f} ({count}次调用)\n"
        report += f"  ─────────────\n  **今日总计: ${total:.4f}**"
        return report

    def transfer_budget(self, from_project: str, to_project: str, amount: float) -> bool:
        """跨项目调拨预算"""
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
    """智能路由 — 按任务类型自动选择最优模型"""

    def __init__(self, budget_mgr: BudgetManager = None):
        self.budget_mgr = budget_mgr or BudgetManager()

    def route(self, task: str, profile: Profile = None, project: str = "default") -> dict:
        """为任务选择最优路由"""
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
