"""Apex Project Operations Center — PM协作引擎

Handles:
  1. Agent workload tracking (饱和度/空闲度)
  2. Auto task assignment (技能匹配 + 负载均衡)
  3. PM polling reports (项目状态 + 瓶颈识别)
  4. Knowledge sharing (跨Agent学习 + 重复问题检测)

Design: PM schedules a "standup meeting" → system checks all agents →
        report what's done, what's blocked, who's free → auto-assign new tasks
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict

from apex.core.profile import APEX_HOME


# ══════════════════════════════════════════
# Agent Workload Tracking
# ══════════════════════════════════════════

def get_agent_workloads() -> dict:
    """Get workload stats for all agents across all projects"""
    kanban_db = APEX_HOME / "kanban.db"
    if not kanban_db.exists():
        return {"error": "kanban.db not found", "agents": []}

    conn = sqlite3.connect(str(kanban_db))
    conn.row_factory = sqlite3.Row
    try:
        # Get all non-done tasks grouped by assignee
        rows = conn.execute("""
            SELECT assignee, status, COUNT(*) as count, priority
            FROM tasks
            WHERE status IN ('ready', 'in_progress', 'todo', 'blocked')
            GROUP BY assignee, status
        """).fetchall()

        # Build per-agent stats
        agent_stats = defaultdict(lambda: {
            "total_active": 0, "in_progress": 0, "ready": 0, "blocked": 0, "todo": 0,
            "priority_sum": 0, "capacity": 5,  # default capacity
        })

        for row in rows:
            a = row["assignee"] or "unassigned"
            s = row["status"]
            c = row["count"]
            agent_stats[a]["total_active"] += c
            agent_stats[a][s] = c
            if row["priority"]:
                agent_stats[a]["priority_sum"] += c * int(row["priority"])

        # Calculate workload %
        agents = []
        for name, stats in agent_stats.items():
            cap = stats["capacity"]
            load_pct = min(100, round(stats["total_active"] / cap * 100))
            saturation = "idle" if load_pct < 30 else "busy" if load_pct < 70 else "overloaded"
            agents.append({
                "agent_id": name,
                "active_tasks": stats["total_active"],
                "in_progress": stats["in_progress"],
                "ready": stats["ready"],
                "blocked": stats["blocked"],
                "todo": stats["todo"],
                "load_pct": load_pct,
                "saturation": saturation,
                "capacity": cap,
                "free_slots": max(0, cap - stats["total_active"]),
            })

        # Also get completed recently (last 7 days)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        done_rows = conn.execute("""
            SELECT assignee, COUNT(*) as done_count
            FROM tasks
            WHERE status = 'done' AND completed_at > ?
            GROUP BY assignee
        """, (week_ago,)).fetchall()

        done_map = {r["assignee"]: r["done_count"] for r in done_rows}

        for a in agents:
            a["completed_7d"] = done_map.get(a["agent_id"], 0)
            a["velocity"] = round(a["completed_7d"] / 7, 1)  # tasks/day

        agents.sort(key=lambda a: a["load_pct"], reverse=True)

        return {
            "total_agents": len(agents),
            "total_active_tasks": sum(a["active_tasks"] for a in agents),
            "agents": agents,
            "summary": {
                "idle": sum(1 for a in agents if a["saturation"] == "idle"),
                "busy": sum(1 for a in agents if a["saturation"] == "busy"),
                "overloaded": sum(1 for a in agents if a["saturation"] == "overloaded"),
            },
        }
    finally:
        conn.close()


# ══════════════════════════════════════════
# Auto Task Assignment Engine
# ══════════════════════════════════════════

# Agent skill profiles for matching
AGENT_SKILLS = {
    # ── 开发线 ──
    "default": ["general", "coordination", "documentation", "orchestration"],
    "frontend-dev": ["react", "vue", "wechat-miniprogram", "html", "css", "javascript", "ui-ux"],
    "backend-dev": ["fastapi", "python", "database", "api", "microservices"],
    "fullstack-dev": ["react", "fastapi", "python", "fullstack", "deployment"],
    "architect": ["system-design", "api-design", "database-schema", "architecture", "scalability"],
    "devops": ["ci-cd", "docker", "kubernetes", "monitoring", "deployment", "infrastructure"],
    "ops-engineer": ["linux", "nginx", "ssl", "backup", "ssh", "auto-shutdown"],
    # ── AI线 ──
    "ai-algorithm": ["machine-learning", "deep-learning", "data-analysis", "python", "recommendation"],
    "ai-vision": ["computer-vision", "image-processing", "mediapipe", "opencv", "pose-estimation"],
    # ── PM线 ──
    "apex-pm": ["apex", "orchestration", "authorization", "dashboard", "kanban"],
    "badminton-pm": ["project-management", "prd", "sprint-planning", "stakeholder", "badminton"],
    "product-manager": ["product-strategy", "user-research", "roadmap", "mvp"],
    "project-manager": ["project-management", "kanban", "sprint", "coordination"],
    "requirements-analyst": ["requirements", "user-stories", "specification", "analysis"],
    # ── 安全线 ──
    "security-compliance": ["security-audit", "compliance", "gdpr", "privacy", "policy"],
    "security-by-design": ["threat-modeling", "secure-design", "architecture-review"],
    "vulnerability-scanner": ["vulnerability", "scanning", "cve", "dependency-check"],
    "penetration-tester": ["penetration-testing", "exploit", "red-team", "owasp"],
    "audit-guardian": ["audit", "hash-chain", "immutable-log", "verification"],
    # ── 内容/商业线 ──
    "content-marketing": ["copywriting", "seo", "social-media", "blogging", "branding"],
    "editor": ["editing", "quality-assurance", "proofreading", "style-guide"],
    "writer": ["writing", "content-creation", "storytelling", "blogging"],
    "publisher": ["publishing", "formatting", "distribution", "cms"],
    "fundraising-pitch": ["pitch-deck", "financial-model", "investor-relations", "valuation"],
    # ── 质量线 ──
    "qa-engineer": ["testing", "quality-assurance", "test-automation", "bug-tracking"],
    "skill-evaluator": ["evaluation", "benchmark", "skill-assessment", "metrics"],
    "test-agent": ["testing", "sandbox", "experiment", "validation"],
    # ── 舰队管理线（监控Agent） ──
    "fleet-commander": ["fleet", "monitoring", "dashboard", "coordination", "status"],
    "gpu-sentinel": ["gpu", "nvidia-smi", "cost-tracking", "auto-shutdown", "ssh"],
    "token-guardian": ["token", "cost", "budget", "usage-tracking", "optimization"],
    "session-scout": ["session", "classification", "summarization", "discovery"],
    "cron-medic": ["cron", "health-check", "scheduler", "failure-detection"],
    "profile-syncer": ["profile", "sync", "gateway", "state", "mapping"],
    # ── 项目模板 Agent ──
    "羽球宝AI_backend": ["fastapi", "python", "database", "api"],
    "羽球宝AI_frontend": ["wechat-miniprogram", "react", "ui-ux", "responsive"],
    "羽球宝AI_devops": ["ci-cd", "monitoring", "deployment", "auto-shutdown"],
    "羽球宝AI_content": ["copywriting", "video-editing", "social-media"],
    "羽球宝AI_pm": ["project-management", "product-strategy", "user-research"],
}


def match_task_to_agent(task_title: str, task_description: str = "") -> dict:
    """Auto-match a task to the best agent based on skills and workload"""
    # Extract keywords from task
    text = (task_title + " " + task_description).lower()
    
    # Score each agent
    scores = []
    for agent_id, skills in AGENT_SKILLS.items():
        score = 0
        matched = []
        for skill in skills:
            if skill in text or skill.replace("-", " ") in text:
                score += 10
                matched.append(skill)
        # Also check partial matches
        for skill in skills:
            for word in text.split():
                if len(word) > 3 and word in skill:
                    score += 2
        if score > 0:
            scores.append({"agent_id": agent_id, "score": score, "matched_skills": matched})
    
    scores.sort(key=lambda s: s["score"], reverse=True)
    
    # Get workloads
    workloads = get_agent_workloads()
    agent_loads = {a["agent_id"]: a for a in workloads.get("agents", [])}
    
    # Adjust scores by workload
    for s in scores:
        load = agent_loads.get(s["agent_id"], {})
        load_pct = load.get("load_pct", 0)
        # Penalty for overloaded, bonus for idle
        if load_pct > 80:
            s["score"] -= 20
        elif load_pct < 30:
            s["score"] += 10
        s["current_load"] = load_pct
        s["free_slots"] = load.get("free_slots", 0)
    
    scores.sort(key=lambda s: s["score"], reverse=True)
    
    return {
        "task": task_title,
        "candidates": scores[:5],
        "recommended": scores[0] if scores else None,
        "total_candidates": len(scores),
    }


def auto_assign_task(title: str, description: str = "", priority: int = 2) -> dict:
    """Auto-assign a task to the best available agent"""
    match = match_task_to_agent(title, description)
    rec = match.get("recommended")
    
    if not rec:
        return {"error": "No suitable agent found", "match": match}
    
    # Create the task
    try:
        from apex.orchestration.kanban import Kanban
        kb = Kanban(APEX_HOME / "kanban.db")
        task = kb.create_task(
            title=title,
            assignee=rec["agent_id"],
            description=description,
            priority=priority,
        )
        return {
            "ok": True,
            "assigned_to": rec["agent_id"],
            "match_score": rec["score"],
            "matched_skills": rec["matched_skills"],
            "task_id": task.id,
            "candidates": match["candidates"][:3],
        }
    except Exception as e:
        return {"error": str(e), "match": match}


# ══════════════════════════════════════════
# PM Standup / Polling Report
# ══════════════════════════════════════════

def generate_standup_report(project: str = None) -> dict:
    """Generate a PM standup report — like a daily scrum meeting"""
    workloads = get_agent_workloads()
    
    # Get project tasks
    kanban_db = APEX_HOME / "kanban.db"
    conn = sqlite3.connect(str(kanban_db))
    conn.row_factory = sqlite3.Row
    
    # Filter by project if specified
    project_filter = f"%{project}%" if project else "%"
    
    # Recently completed (24h)
    day_ago = (datetime.now() - timedelta(hours=24)).isoformat()
    just_done = conn.execute("""
        SELECT assignee, COUNT(*) as count, GROUP_CONCAT(title, '||') as titles
        FROM tasks
        WHERE status = 'done' AND completed_at > ?
        GROUP BY assignee
    """, (day_ago,)).fetchall()
    
    # Currently blocked
    blocked = conn.execute("""
        SELECT assignee, title, priority
        FROM tasks WHERE status = 'blocked'
        ORDER BY priority ASC
    """).fetchall()
    
    # In progress
    in_progress = conn.execute("""
        SELECT assignee, title, priority
        FROM tasks WHERE status = 'in_progress'
    """).fetchall()
    
    # Ready to be picked up
    ready_tasks = conn.execute("""
        SELECT id, title, priority, assignee
        FROM tasks WHERE status = 'ready'
        ORDER BY priority ASC
        LIMIT 10
    """).fetchall()
    
    conn.close()
    
    # Agent-wise summary
    agent_updates = []
    for a in workloads.get("agents", []):
        agent_updates.append({
            "agent": a["agent_id"],
            "load": f"{a['load_pct']}% ({a['saturation']})",
            "active": a["active_tasks"],
            "done_today": next((d["count"] for d in just_done if d["assignee"] == a["agent_id"]), 0),
            "velocity": a["velocity"],
            "free_slots": a["free_slots"],
        })
    
    # Auto-suggest task assignments for ready tasks
    suggestions = []
    for rt in ready_tasks[:5]:
        match = match_task_to_agent(rt["title"], "")
        if match.get("recommended"):
            suggestions.append({
                "task_id": rt["id"],
                "task": rt["title"][:60],
                "priority": rt["priority"],
                "suggested_agent": match["recommended"]["agent_id"],
                "score": match["recommended"]["score"],
                "current_assignee": rt["assignee"],
            })
    
    return {
        "timestamp": datetime.now().isoformat(),
        "project": project or "all",
        "summary": {
            "total_agents": workloads["total_agents"],
            "active_tasks": workloads["total_active_tasks"],
            "completed_24h": sum(d["count"] for d in just_done),
            "blocked_count": len(blocked),
            "ready_to_assign": len(ready_tasks),
            "idle_agents": workloads["summary"]["idle"],
            "overloaded_agents": workloads["summary"]["overloaded"],
        },
        "blockers": [
            {"agent": b["assignee"], "task": b["title"][:80], "priority": b["priority"]}
            for b in blocked
        ],
        "in_progress": [
            {"agent": ip["assignee"], "task": ip["title"][:80], "priority": ip["priority"]}
            for ip in in_progress
        ],
        "agent_standings": agent_updates,
        "auto_suggestions": suggestions,
        "workload_distribution": workloads["summary"],
    }


# ══════════════════════════════════════════
# Knowledge Sharing / Cross-Agent Learning
# ══════════════════════════════════════════

# Known solutions database (problem → solution → who solved it)
KNOWN_SOLUTIONS = {
    "wechat mini program payment integration": {
        "solution": "Use wx.requestPayment with prepay_id from backend /api/user/pay",
        "solved_by": "羽球宝AI_backend",
        "tags": ["wechat", "payment", "miniprogram"],
    },
    "mediapipe pose landmarker import error": {
        "solution": "from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmarker, _RunningMode as RM",
        "solved_by": "ai-vision",
        "tags": ["mediapipe", "python", "pose"],
    },
    "flask cors error": {
        "solution": "Use flask-cors: from flask_cors import CORS; CORS(app)",
        "solved_by": "architect",
        "tags": ["flask", "cors", "web"],
    },
    "autodl ssh connection refused": {
        "solution": "Instance may be stopped. Check AutoDL console. Use SSH key, not password.",
        "solved_by": "ops-engineer",
        "tags": ["autodl", "ssh", "gpu"],
    },
}


def search_solutions(problem: str) -> dict:
    """Search for known solutions to a problem"""
    text = problem.lower()
    matches = []
    for p, s in KNOWN_SOLUTIONS.items():
        score = 0
        for tag in s["tags"]:
            if tag in text:
                score += 3
        for word in text.split():
            if len(word) > 3 and word in p:
                score += 2
        if score > 0:
            matches.append({"problem": p, "score": score, **s})
    
    matches.sort(key=lambda m: m["score"], reverse=True)
    
    return {
        "query": problem,
        "matches": matches[:5],
        "found": len(matches) > 0,
        "tip": "No matching solution found. Consider documenting this problem for future agents." if not matches else None,
    }


def record_solution(problem: str, solution: str, solved_by: str, tags: list = None) -> dict:
    """Record a new solution for cross-agent learning"""
    KNOWN_SOLUTIONS[problem.lower()] = {
        "solution": solution,
        "solved_by": solved_by,
        "tags": tags or [],
    }
    return {"ok": True, "recorded": problem[:80], "total_solutions": len(KNOWN_SOLUTIONS)}


def get_knowledge_base_stats() -> dict:
    """Get knowledge sharing statistics"""
    by_agent = defaultdict(int)
    all_tags = defaultdict(int)
    for p, s in KNOWN_SOLUTIONS.items():
        by_agent[s["solved_by"]] += 1
        for tag in s["tags"]:
            all_tags[tag] += 1
    
    return {
        "total_solutions": len(KNOWN_SOLUTIONS),
        "top_contributors": dict(sorted(by_agent.items(), key=lambda x: x[1], reverse=True)[:5]),
        "top_tags": dict(sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:10]),
    }
