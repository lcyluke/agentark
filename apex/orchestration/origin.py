"""
Origin Agent — 始祖Agent · 项目群总指挥官
═══════════════════════════════════════════════════
能力:
  1. 技能复制迁移 — 将自己的skills/expertise注入任何agent的profile
  2. 权限继承 — 被注入的agent获得origin授权的command权限
  3. 项目群管理 — 管理多个独立项目的PM agent + 资源平衡
  4. 战略目标下达 — 设定项目OKR + 预期效果 + 追踪进度
  5. 任意窗口切换 — 通过Hermes skill从任何chat切回origin模式

航海隐喻: 始祖Agent = 舰队总司令(Admiral)
         项目PM Agent = 各舰舰长(Captain)
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from apex.core.profile import ProfileManager, APEX_HOME, Profile, SoulConfig

ORIGIN_PROFILE_NAME = "origin"

# ── Origin Agent 专属技能集 ──────────────────────────────────

ORIGIN_SKILLS = [
    "origin-command",         # 始祖指令：切换/sync/replicate
    "profile-replication",    # 技能复制迁移引擎
    "portfolio-management",   # 项目群管理
    "resource-balancing",     # 资源平衡
    "pm-agent-deployment",    # PM agent部署
    "strategic-oversight",    # 战略监控
    "hermes-agent",           # Hermes集成
    "kanban-orchestrator",    # Kanban编排
    "multi-agent-system-design",
    "subagent-driven-development",
    "writing-plans",
    "prd-writing",
]

ORIGIN_EXPERTISE = [
    "多项目群管理 (Portfolio Management)",
    "Agent技能复制与迁移",
    "战略目标分解 (OKR → Epic → Task)",
    "跨项目资源平衡与调度",
    "PM Agent模板化部署",
    "Agent舰队健康监控",
    "自动化任务编排",
    "技术决策与架构评审",
]

ORIGIN_PERSONALITY = (
    "舰队总司令，冷静、果断、全局视野。"
    "用航海隐喻下达指令：目标=航向，资源=燃料，风险=暗礁。"
    "每条消息以「⚓」开头，锚定战略方向。"
)


# ════════════════════════════════════════════════════════════
# PM Agent 模板（部署到各项目）
# ════════════════════════════════════════════════════════════

PM_SKILLS = [
    "prd-writing",
    "writing-plans",
    "kanban-orchestrator",
    "subagent-driven-development",
    "kanban-worker",
    "hermes-agent",
    "multi-agent-system-design",
    "requesting-code-review",
    "test-driven-development",
    "github-pr-workflow",
    "github-issues",
]

PM_EXPERTISE = [
    "PRD & 需求文档撰写",
    "用户故事 & 用例分析",
    "用户分层 & RFM模型",
    "OKR / KPI 拆解",
    "Roadmap规划 & 优先级管理",
    "MVP定义 & 迭代策略",
    "Kanban任务编排",
    "多Agent协调与调度",
    "代码审查与质量门控",
    "GitHub PR/Issue管理",
]

PM_PERSONALITY = (
    "项目舰长，执行力强、结构化思维。"
    "一切以航海日志形式记录：Sprint=航段，Task=航行节点，Blocker=暗礁。"
    "输出格式：目标 → 拆解 → 分配 → 追踪 → 复盘"
)


# ════════════════════════════════════════════════════════════
# 项目群数据库
# ════════════════════════════════════════════════════════════

PORTFOLIO_DB = APEX_HOME / "portfolio.db"


def _portfolio_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(PORTFOLIO_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            strategic_goal TEXT DEFAULT '',
            expected_outcome TEXT DEFAULT '',
            pm_agent TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            priority INTEGER DEFAULT 2,
            total_tasks INTEGER DEFAULT 0,
            completed_tasks INTEGER DEFAULT 0,
            created_at TEXT DEFAULT '',
            updated_at TEXT DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id TEXT NOT NULL,
            resource_type TEXT DEFAULT 'agent',
            resource_name TEXT DEFAULT '',
            allocation_pct INTEGER DEFAULT 100,
            FOREIGN KEY(portfolio_id) REFERENCES portfolios(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id TEXT NOT NULL,
            title TEXT NOT NULL,
            target_date TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            notes TEXT DEFAULT '',
            FOREIGN KEY(portfolio_id) REFERENCES portfolios(id)
        )
    """)
    conn.commit()
    return conn


# ════════════════════════════════════════════════════════════
# OriginAgent 核心类
# ════════════════════════════════════════════════════════════

class OriginAgent:
    """始祖Agent — 项目群总指挥官"""

    def __init__(self):
        self.pm = ProfileManager()
        self._ensure_origin_profile()

    def _ensure_origin_profile(self):
        """确保origin profile存在且拥有完整能力"""
        try:
            existing = self.pm.load(ORIGIN_PROFILE_NAME)
            # 升级：确保skills总是最新的
            if set(existing.skills) != set(ORIGIN_SKILLS) or \
               set(existing.soul.expertise) != set(ORIGIN_EXPERTISE):
                existing.skills = ORIGIN_SKILLS
                existing.soul.expertise = ORIGIN_EXPERTISE
                existing.soul.personality = ORIGIN_PERSONALITY
                existing.auto_improve = True
                self.pm.save(existing)
                return {"status": "upgraded", "name": ORIGIN_PROFILE_NAME}
        except FileNotFoundError:
            pass

        origin = Profile(
            name=ORIGIN_PROFILE_NAME,
            display="⚓ 始祖 · 舰队总司令",
            soul=SoulConfig(
                role="Origin Agent — 项目群总指挥官",
                expertise=ORIGIN_EXPERTISE,
                personality=ORIGIN_PERSONALITY,
                communication="航海隐喻，⚓锚定航向，每条消息以「⚓」开头。战略优先，数据驱动。",
            ),
            skills=ORIGIN_SKILLS,
            auto_improve=True,
            token_budget=500_000,
        )
        self.pm.save(origin)
        return {"status": "created", "name": ORIGIN_PROFILE_NAME}

    # ── 核心能力1: 技能复制迁移 ─────────────────────────────

    def replicate_to(self, target_profile_name: str, strategy: str = "merge") -> dict:
        """将自己的skills/expertise复制到目标agent。

        strategy:
          - "merge": 合并（保留目标原有技能 + 新增）
          - "replace": 完全替换为origin的技能集
          - "pm": 注入PM agent标准技能集
        """
        try:
            target = self.pm.load(target_profile_name)
        except FileNotFoundError:
            return {"error": f"Profile '{target_profile_name}' 不存在，请先创建"}

        if strategy == "replace":
            target.skills = ORIGIN_SKILLS.copy()
            target.soul.expertise = ORIGIN_EXPERTISE.copy()
            target.soul.personality = ORIGIN_PERSONALITY
            target.auto_improve = True
            target.token_budget = 200_000
            action = "replace"
        elif strategy == "pm":
            target.skills = list(set(target.skills + PM_SKILLS))
            target.soul.expertise = list(set(target.soul.expertise + PM_EXPERTISE))
            target.soul.personality = PM_PERSONALITY
            target.auto_improve = True
            target.token_budget = 150_000
            action = "pm_template"
        else:  # merge
            target.skills = list(set(target.skills + ORIGIN_SKILLS))
            target.soul.expertise = list(set(target.soul.expertise + ORIGIN_EXPERTISE))
            target.auto_improve = True
            action = "merge"

        self.pm.save(target)

        return {
            "ok": True,
            "target": target_profile_name,
            "action": action,
            "skills_count": len(target.skills),
            "expertise_count": len(target.soul.expertise),
            "message": f"⚓ 技能已通过{action}方式注入 {target_profile_name}",
        }

    def replicate_to_all(self) -> dict:
        """将PM能力注入所有现有项目agent。"""
        results = {}
        for name in self.pm.list():
            if name in (ORIGIN_PROFILE_NAME, "default"):
                continue
            # Only replicate to project-specific agents
            if any(prefix in name for prefix in ["backend", "frontend", "pm", "devops", "content"]):
                r = self.replicate_to(name, strategy="pm")
                results[name] = r
        return {
            "ok": True,
            "replicated": len(results),
            "targets": list(results.keys()),
            "message": f"⚓ 已向{len(results)}个agent注入PM能力",
        }

    # ── 核心能力2: 项目群管理 ──────────────────────────────

    def list_portfolios(self) -> list[dict]:
        conn = _portfolio_conn()
        rows = conn.execute(
            "SELECT * FROM portfolios ORDER BY priority, created_at"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def create_portfolio(self, name: str, description: str = "",
                         strategic_goal: str = "",
                         expected_outcome: str = "",
                         pm_agent: str = "") -> dict:
        pid = f"pf_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        conn = _portfolio_conn()
        conn.execute("""
            INSERT INTO portfolios(id, name, description, strategic_goal,
                                   expected_outcome, pm_agent, created_at, updated_at)
            VALUES(?,?,?,?,?,?,?,?)
        """, (pid, name, description, strategic_goal, expected_outcome, pm_agent, now, now))
        conn.commit()

        # Auto-create PM agent if name provided
        if pm_agent:
            self._deploy_pm_agent(pm_agent, name)

        row = conn.execute("SELECT * FROM portfolios WHERE id=?", (pid,)).fetchone()
        conn.close()

        return {
            "ok": True,
            "portfolio": dict(row) if row else {},
            "pm_agent_deployed": bool(pm_agent),
            "message": f"⚓ 新建项目群: {name}" + (f"，PM agent: {pm_agent}" if pm_agent else ""),
        }

    def _deploy_pm_agent(self, agent_name: str, portfolio_name: str):
        """部署独立PM agent到项目。"""
        try:
            self.pm.load(agent_name)
            # 已存在，注入PM能力
            self.replicate_to(agent_name, strategy="pm")
        except FileNotFoundError:
            pm_profile = Profile(
                name=agent_name,
                display=f"🚢 {portfolio_name} · 项目舰长",
                soul=SoulConfig(
                    role=f"Project Manager — {portfolio_name}",
                    expertise=PM_EXPERTISE,
                    personality=PM_PERSONALITY,
                    communication="结构化输出：目标→拆解→分配→追踪→复盘。航海日志格式。",
                ),
                skills=PM_SKILLS,
                auto_improve=True,
                token_budget=150_000,
            )
            self.pm.save(pm_profile)

    def update_portfolio(self, portfolio_id: str, **updates) -> dict:
        allowed = {"name", "description", "strategic_goal", "expected_outcome",
                    "status", "priority", "pm_agent"}
        sets = []
        values = []
        for k, v in updates.items():
            if k in allowed:
                sets.append(f"{k}=?")
                values.append(v)
        if not sets:
            return {"error": "无可更新字段"}

        sets.append("updated_at=?")
        values.append(datetime.now().isoformat())
        values.append(portfolio_id)

        conn = _portfolio_conn()
        conn.execute(f"UPDATE portfolios SET {', '.join(sets)} WHERE id=?", values)
        conn.commit()
        row = conn.execute("SELECT * FROM portfolios WHERE id=?", (portfolio_id,)).fetchone()
        conn.close()

        return {"ok": True, "portfolio": dict(row) if row else {}}

    def get_portfolio_status(self, portfolio_id: str) -> dict:
        conn = _portfolio_conn()
        pf = conn.execute("SELECT * FROM portfolios WHERE id=?", (portfolio_id,)).fetchone()
        if not pf:
            conn.close()
            return {"error": "项目不存在"}

        milestones = conn.execute(
            "SELECT * FROM portfolio_milestones WHERE portfolio_id=? ORDER BY target_date",
            (portfolio_id,)
        ).fetchall()
        resources = conn.execute(
            "SELECT * FROM portfolio_resources WHERE portfolio_id=?",
            (portfolio_id,)
        ).fetchall()
        conn.close()

        pf_dict = dict(pf)
        pf_dict["milestones"] = [dict(m) for m in milestones]
        pf_dict["resources"] = [dict(r) for r in resources]

        # Fetch Kanban tasks for this project
        from apex.orchestration.kanban import Kanban
        kdb = APEX_HOME / "kanban.db"
        if kdb.exists():
            k = Kanban(kdb)
            pm = pf_dict.get("pm_agent", "")
            tasks = k.list_tasks(assignee=pm) if pm else []
            pf_dict["tasks"] = [
                {"id": t.id, "title": t.title, "status": t.status}
                for t in tasks[:20]
            ]
            pf_dict["task_summary"] = {
                "total": len(tasks),
                "done": sum(1 for t in tasks if t.status == "done"),
                "in_progress": sum(1 for t in tasks if t.status == "in_progress"),
            }

        return pf_dict

    def add_milestone(self, portfolio_id: str, title: str,
                       target_date: str = "") -> dict:
        conn = _portfolio_conn()
        conn.execute("""
            INSERT INTO portfolio_milestones(portfolio_id, title, target_date)
            VALUES(?,?,?)
        """, (portfolio_id, title, target_date))
        conn.commit()
        conn.close()
        return {"ok": True, "message": f"⚓ 新里程碑: {title}"}

    # ── 核心能力3: 项目群总览 ──────────────────────────────

    def portfolio_overview(self) -> dict:
        """舰队总览 — 所有项目的状态汇总。"""
        portfolios = self.list_portfolios()
        total = len(portfolios)
        active = sum(1 for p in portfolios if p["status"] == "active")
        completed = sum(1 for p in portfolios if p["status"] == "completed")

        total_tasks = sum(p.get("total_tasks", 0) for p in portfolios)
        completed_tasks = sum(p.get("completed_tasks", 0) for p in portfolios)

        return {
            "timestamp": datetime.now().isoformat(),
            "fleets": total,
            "active": active,
            "completed": completed,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0,
            "portfolios": [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "status": p["status"],
                    "pm_agent": p.get("pm_agent", ""),
                    "strategic_goal": (p.get("strategic_goal") or "")[:80],
                }
                for p in portfolios
            ],
        }
