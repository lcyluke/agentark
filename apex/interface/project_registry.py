"""Apex Project Registry — 项目立项 + 模块架构 + Agent能力档案

Manages:
  1. Project proposals (立项 → 始祖Agent审批)
  2. Module architecture (目标 → 模块 → 子功能 → Agent分配)
  3. Agent capability profiles (技能积累 + 项目经历 + Model对比)
"""
from __future__ import annotations

import json
import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from collections import defaultdict


APEX_HOME = Path(os.path.expanduser("~/.apex"))
PROJECTS_FILE = APEX_HOME / "projects_registry.json"
KANBAN_DB = APEX_HOME / "kanban.db"

# Model comparison data for Agent capability profiles
MODEL_COMPARISON = {
    "deepseek-chat": {
        "cost_1m_input": 0.14, "cost_1m_output": 0.28,
        "coding": 8, "reasoning": 7, "speed": 9, "cost_efficiency": 10,
        "best_for": ["日常编码", "简单问答", "批量任务"],
    },
    "deepseek-v4-pro": {
        "cost_1m_input": 1.0, "cost_1m_output": 4.0,
        "coding": 9, "reasoning": 9, "speed": 8, "cost_efficiency": 7,
        "best_for": ["架构设计", "复杂推理", "代码审查"],
    },
    "claude-sonnet-4": {
        "cost_1m_input": 3.0, "cost_1m_output": 15.0,
        "coding": 10, "reasoning": 10, "speed": 7, "cost_efficiency": 3,
        "best_for": ["系统设计", "安全审计", "关键决策"],
    },
    "gpt-4o": {
        "cost_1m_input": 2.5, "cost_1m_output": 10.0,
        "coding": 9, "reasoning": 9, "speed": 6, "cost_efficiency": 4,
        "best_for": ["多模态分析", "创意内容", "复杂调试"],
    },
}

# Default skill categories for tracking
SKILL_CATEGORIES = [
    "frontend", "backend", "devops", "ai-ml", "security",
    "project-management", "content", "data-analysis", "testing",
]


def _load_registry() -> dict:
    """Load or initialize project registry"""
    if PROJECTS_FILE.exists():
        with open(PROJECTS_FILE) as f:
            return json.load(f)
    return {
        "projects": {},
        "agent_profiles": {},
        "meta": {"version": 1, "created_at": datetime.now().isoformat()},
    }


def _save_registry(data: dict):
    """Save project registry"""
    data["meta"]["updated_at"] = datetime.now().isoformat()
    with open(PROJECTS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


# ══════════════════════════════════════════
# Project CRUD + 审批
# ══════════════════════════════════════════

def propose_project(name: str, goal: str, modules: list = None) -> dict:
    """Propose a new project (requires 始祖Agent approval)"""
    data = _load_registry()
    if name in data["projects"]:
        return {"error": f"Project '{name}' already exists"}

    data["projects"][name] = {
        "name": name,
        "goal": goal,
        "status": "proposed",  # proposed → approved → active → completed
        "approved_by": None,
        "approved_at": None,
        "proposed_at": datetime.now().isoformat(),
        "modules": modules or [],
        "created_at": datetime.now().isoformat(),
    }
    _save_registry(data)
    return {"ok": True, "project": name, "status": "proposed"}


def approve_project(name: str, approver: str = "始祖Agent·小卢") -> dict:
    """Approve a project (始祖Agent action)"""
    data = _load_registry()
    if name not in data["projects"]:
        return {"error": f"Project '{name}' not found"}

    proj = data["projects"][name]
    if proj["status"] == "approved":
        return {"ok": True, "project": name, "status": "already_approved"}

    proj["status"] = "approved"
    proj["approved_by"] = approver
    proj["approved_at"] = datetime.now().isoformat()
    _save_registry(data)
    return {"ok": True, "project": name, "status": "approved", "by": approver}


def list_approved_projects() -> list[dict]:
    """List only approved/active projects"""
    data = _load_registry()
    projects = []
    for name, proj in data["projects"].items():
        if proj.get("status") in ("approved", "active", "completed"):
            # Count tasks from kanban
            task_count = _count_project_tasks(name)
            module_count = len(proj.get("modules", []))
            sub_func_count = sum(len(m.get("sub_functions", [])) for m in proj.get("modules", []))
            projects.append({
                "name": name,
                "goal": proj.get("goal", "")[:100],
                "status": proj.get("status", "approved"),
                "task_count": task_count,
                "module_count": module_count,
                "sub_function_count": sub_func_count,
                "approved_by": proj.get("approved_by"),
            })
    return sorted(projects, key=lambda p: p["task_count"], reverse=True)


def _count_project_tasks(project_name: str) -> int:
    """Count tasks for a project from Kanban"""
    if not KANBAN_DB.exists():
        return 0
    try:
        conn = sqlite3.connect(str(KANBAN_DB))
        count = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE title LIKE ?",
            (f"%[{project_name}]%",)
        ).fetchone()[0]
        conn.close()
        return count
    except:
        return 0


# ══════════════════════════════════════════
# Project Module Architecture
# ══════════════════════════════════════════

def get_project_detail(name: str) -> dict:
    """Get full project detail: goal + modules + sub-functions + agent assignments"""
    data = _load_registry()
    if name not in data["projects"]:
        return {"error": f"Project '{name}' not found"}

    proj = data["projects"][name]
    modules = proj.get("modules", [])

    # Enrich modules with agent task counts
    for mod in modules:
        for sf in mod.get("sub_functions", []):
            agent = sf.get("assigned_agent", "")
            if agent:
                sf["agent_tasks_done"] = _count_agent_project_tasks(agent, name, "done")
                sf["agent_tasks_total"] = _count_agent_project_tasks(agent, name)
            else:
                sf["agent_tasks_done"] = 0
                sf["agent_tasks_total"] = 0

    # Agent assignments for this project
    agent_assignments = _get_project_agent_assignments(name)

    return {
        "name": name,
        "goal": proj.get("goal", ""),
        "status": proj.get("status", "proposed"),
        "approved_by": proj.get("approved_by"),
        "module_count": len(modules),
        "sub_function_count": sum(len(m.get("sub_functions", [])) for m in modules),
        "modules": modules,
        "agents": agent_assignments,
        "created_at": proj.get("created_at"),
    }


def add_project_module(project: str, module_name: str, description: str = "") -> dict:
    """Add a module to a project"""
    data = _load_registry()
    if project not in data["projects"]:
        return {"error": f"Project '{project}' not found"}

    proj = data["projects"][project]
    proj.setdefault("modules", [])
    proj["modules"].append({
        "name": module_name,
        "description": description,
        "sub_functions": [],
    })
    _save_registry(data)
    return {"ok": True, "module": module_name}


def add_sub_function(project: str, module_name: str, func_name: str,
                     description: str = "", assigned_agent: str = "") -> dict:
    """Add a sub-function to a module"""
    data = _load_registry()
    if project not in data["projects"]:
        return {"error": f"Project '{project}' not found"}

    mod = next((m for m in data["projects"][project].get("modules", [])
                if m["name"] == module_name), None)
    if not mod:
        return {"error": f"Module '{module_name}' not found"}

    mod.setdefault("sub_functions", [])
    mod["sub_functions"].append({
        "name": func_name,
        "description": description,
        "assigned_agent": assigned_agent,
    })
    _save_registry(data)
    return {"ok": True, "sub_function": func_name}


def _get_project_agent_assignments(project: str) -> list[dict]:
    """Get agents assigned to a project with their task stats"""
    if not KANBAN_DB.exists():
        return []

    conn = sqlite3.connect(str(KANBAN_DB))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("""
            SELECT assignee, 
                   COUNT(*) as total,
                   SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) as done,
                   SUM(CASE WHEN status='in_progress' THEN 1 ELSE 0 END) as in_progress,
                   SUM(CASE WHEN status='ready' THEN 1 ELSE 0 END) as ready,
                   SUM(CASE WHEN status='blocked' THEN 1 ELSE 0 END) as blocked
            FROM tasks 
            WHERE title LIKE ? AND assignee IS NOT NULL AND assignee != ''
            GROUP BY assignee
        """, (f"%[{project}]%",)).fetchall()

        return [
            {
                "agent_id": r["assignee"],
                "total": r["total"],
                "done": r["done"],
                "in_progress": r["in_progress"],
                "ready": r["ready"],
                "blocked": r["blocked"],
                "load_pct": min(100, round(r["total"] / 5 * 100)),
            }
            for r in rows
        ]
    finally:
        conn.close()


def _count_agent_project_tasks(agent: str, project: str, status: str = None) -> int:
    """Count tasks for a specific agent in a project"""
    if not KANBAN_DB.exists():
        return 0
    try:
        conn = sqlite3.connect(str(KANBAN_DB))
        if status:
            count = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE title LIKE ? AND assignee = ? AND status = ?",
                (f"%[{project}]%", agent, status)
            ).fetchone()[0]
        else:
            count = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE title LIKE ? AND assignee = ?",
                (f"%[{project}]%", agent)
            ).fetchone()[0]
        conn.close()
        return count
    except:
        return 0


# ══════════════════════════════════════════
# Agent Capability Profiles
# ══════════════════════════════════════════

AGENT_SKILLS_DB = {
    "default": {"role": "通用助手", "skills": ["general", "coordination"], "level": 3},
    "frontend-dev": {"role": "前端开发", "skills": ["react", "vue", "wechat-miniprogram", "html", "css", "javascript"], "level": 4},
    "architect": {"role": "系统架构师", "skills": ["system-design", "api-design", "database-schema"], "level": 5},
    "devops": {"role": "DevOps工程师", "skills": ["ci-cd", "docker", "kubernetes", "monitoring"], "level": 4},
    "ai-algorithm": {"role": "AI算法工程师", "skills": ["machine-learning", "deep-learning", "python"], "level": 5},
    "ai-vision": {"role": "视觉AI工程师", "skills": ["computer-vision", "mediapipe", "opencv"], "level": 4},
    "ops-engineer": {"role": "运维工程师", "skills": ["linux", "nginx", "ssl", "backup", "security"], "level": 4},
    "content-marketing": {"role": "内容运营", "skills": ["copywriting", "seo", "social-media"], "level": 3},
    "security-compliance": {"role": "安全合规", "skills": ["security-audit", "compliance", "gdpr"], "level": 4},
    "fundraising-pitch": {"role": "融资顾问", "skills": ["pitch-deck", "financial-model"], "level": 3},
    "yuji-pm": {"role": "项目经理", "skills": ["project-management", "prd", "sprint-planning"], "level": 4},
    "羽球宝AI_frontend": {"role": "前端开发工程师", "skills": ["wechat-miniprogram", "react", "ui-ux", "responsive"], "level": 5},
    "羽球宝AI_backend": {"role": "后端架构师", "skills": ["fastapi", "python", "database", "api"], "level": 5},
    "羽球宝AI_devops": {"role": "DevOps运维", "skills": ["ci-cd", "monitoring", "deployment", "auto-shutdown"], "level": 4},
    "羽球宝AI_content": {"role": "内容运营专家", "skills": ["copywriting", "video-editing", "social-media"], "level": 3},
    "羽球宝AI_pm": {"role": "产品经理", "skills": ["project-management", "product-strategy", "user-research"], "level": 4},
}


def get_agent_profile(agent_id: str) -> dict:
    """Get comprehensive agent capability profile"""
    skills_info = AGENT_SKILLS_DB.get(agent_id, {"role": "Agent", "skills": [], "level": 1})

    # Get task history from Kanban
    completed_projects = set()
    active_projects = set()
    if KANBAN_DB.exists():
        conn = sqlite3.connect(str(KANBAN_DB))
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT title, status FROM tasks WHERE assignee = ?",
                (agent_id,)
            ).fetchall()
            for r in rows:
                title = r["title"] or ""
                if title.startswith("["):
                    end = title.find("]")
                    if end > 0:
                        proj = title[1:end]
                        if r["status"] == "done":
                            completed_projects.add(proj)
                        else:
                            active_projects.add(proj)
        finally:
            conn.close()

    # Get current task queue
    task_queue = []
    if KANBAN_DB.exists():
        conn = sqlite3.connect(str(KANBAN_DB))
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT title, status, priority FROM tasks "
                "WHERE assignee = ? AND status IN ('ready', 'in_progress', 'todo', 'blocked') "
                "ORDER BY priority ASC, status DESC LIMIT 10",
                (agent_id,)
            ).fetchall()
            task_queue = [
                {"title": r["title"][:80], "status": r["status"], "priority": r["priority"]}
                for r in rows
            ]
        finally:
            conn.close()

    # Get model usage history
    model_usage = _get_agent_model_usage(agent_id)

    return {
        "agent_id": agent_id,
        "role": skills_info["role"],
        "level": skills_info["level"],
        "skills": skills_info["skills"],
        "completed_projects": list(completed_projects),
        "active_projects": list(active_projects),
        "task_queue": task_queue,
        "task_queue_count": len(task_queue),
        "model_usage": model_usage,
        "model_comparison": MODEL_COMPARISON,
    }


def _get_agent_model_usage(agent_id: str) -> dict:
    """Get model usage stats for an agent"""
    # Default: all models available with base scores
    usage = {}
    for model, info in MODEL_COMPARISON.items():
        usage[model] = {
            "available": True,
            "cost_1m_input": info["cost_1m_input"],
            "cost_1m_output": info["cost_1m_output"],
            "scores": {
                "coding": info["coding"],
                "reasoning": info["reasoning"],
                "speed": info["speed"],
                "cost_efficiency": info["cost_efficiency"],
            },
            "best_for": info["best_for"],
        }
    return usage


def get_all_agent_summaries() -> list[dict]:
    """Get lightweight summaries for all agents"""
    summaries = []
    for aid, info in AGENT_SKILLS_DB.items():
        task_count = 0
        if KANBAN_DB.exists():
            conn = sqlite3.connect(str(KANBAN_DB))
            try:
                task_count = conn.execute(
                    "SELECT COUNT(*) FROM tasks WHERE assignee = ? AND status != 'done'",
                    (aid,)
                ).fetchone()[0]
            finally:
                conn.close()

        summaries.append({
            "agent_id": aid,
            "role": info["role"],
            "skills": info["skills"],
            "skill_count": len(info["skills"]),
            "level": info["level"],
            "active_tasks": task_count,
        })
    return summaries
