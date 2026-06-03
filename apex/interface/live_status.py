"""Apex Live Status — Real-time Hermes/Agent state tracking

Bridges Hermes runtime state into Apex Dashboard.
Tracks: running sessions, active processes, per-project task aggregation.
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import time
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


HERMES_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))
STATE_DB = HERMES_HOME / "state.db"
APEX_HOME = Path(os.path.expanduser("~/.apex"))


# ══════════════════════════════════════════
# Hermes Runtime Status
# ══════════════════════════════════════════

def get_hermes_runtime() -> dict:
    """Get real-time Hermes runtime status — running sessions, active agents"""
    if not STATE_DB.exists():
        return {"error": "state.db not found", "running_sessions": 0}

    conn = sqlite3.connect(str(STATE_DB))
    conn.row_factory = sqlite3.Row
    try:
        # Active sessions (not ended)
        active_sessions = conn.execute("""
            SELECT id, source, model, message_count, started_at,
                   input_tokens, output_tokens, estimated_cost_usd
            FROM sessions
            WHERE ended_at IS NULL
            ORDER BY started_at DESC
        """).fetchall()

        # Recently active (last 24h)
        cutoff = (datetime.now() - timedelta(hours=24)).timestamp()
        recent_count = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE started_at > ?", (cutoff,)
        ).fetchone()[0]

        # Session by source (last 24h)
        by_source = conn.execute("""
            SELECT source, COUNT(*) as cnt
            FROM sessions WHERE started_at > ?
            GROUP BY source ORDER BY cnt DESC
        """, (cutoff,)).fetchall()

        # Get running hermes CLI processes
        try:
            ps_result = subprocess.run(
                ["ps", "aux"], capture_output=True, text=True, timeout=5
            )
            running_cli = []
            for line in ps_result.stdout.split("\n"):
                if "hermes" in line and "gateway" not in line and "lsp" not in line and "webui" not in line:
                    if "/venv/bin/hermes" in line or "hermes chat" in line or "hermes -" in line:
                        parts = line.split()
                        if len(parts) >= 11:
                            running_cli.append({
                                "pid": parts[1],
                                "cpu": parts[2],
                                "mem": parts[3],
                                "command": " ".join(parts[10:]),
                                "started": " ".join(parts[8:10]) if len(parts) >= 10 else "?",
                            })
        except:
            running_cli = []

        return {
            "active_sessions": len(active_sessions),
            "recent_24h_sessions": recent_count,
            "running_processes": len(running_cli),
            "processes": running_cli,
            "sessions": [
                {
                    "id": s["id"][:20],
                    "source": s["source"],
                    "model": s["model"],
                    "messages": s["message_count"],
                    "tokens": (s["input_tokens"] or 0) + (s["output_tokens"] or 0),
                    "cost": round(s["estimated_cost_usd"] or 0, 4),
                    "started": datetime.fromtimestamp(s["started_at"]).strftime("%H:%M"),
                    "runtime_min": round((time.time() - s["started_at"]) / 60, 1),
                }
                for s in active_sessions[:10]
            ],
            "by_source": [
                {"source": r["source"], "count": r["cnt"]}
                for r in by_source
            ],
        }
    finally:
        conn.close()


# ══════════════════════════════════════════
# Per-Project Task Aggregation
# ══════════════════════════════════════════

def get_project_dashboard(project: str) -> dict:
    """Get comprehensive project view: tasks, agents, workload, standup"""
    kanban_db = APEX_HOME / "kanban.db"
    if not kanban_db.exists():
        return {"error": "kanban.db not found"}

    conn = sqlite3.connect(str(kanban_db))
    conn.row_factory = sqlite3.Row
    try:
        # Filter tasks by project name (fuzzy match in title)
        project_filter = f"%{project}%"

        # Task status breakdown
        status_counts = conn.execute("""
            SELECT status, COUNT(*) as count
            FROM tasks WHERE title LIKE ?
            GROUP BY status
        """, (project_filter,)).fetchall()

        # Agent workload for this project
        agent_tasks = conn.execute("""
            SELECT assignee, status, COUNT(*) as count
            FROM tasks WHERE title LIKE ?
            GROUP BY assignee, status
        """, (project_filter,)).fetchall()

        # Build per-agent stats
        agent_stats = defaultdict(lambda: {
            "total": 0, "done": 0, "in_progress": 0, "ready": 0, "blocked": 0, "todo": 0
        })
        for row in agent_tasks:
            a = row["assignee"] or "unassigned"
            s = row["status"]
            agent_stats[a]["total"] += row["count"]
            agent_stats[a][s] = row["count"]

        agents = []
        for name, stats in agent_stats.items():
            load = min(100, round(stats["total"] / 5 * 100))
            agents.append({
                "agent_id": name,
                "total_tasks": stats["total"],
                "done": stats["done"],
                "in_progress": stats["in_progress"],
                "ready": stats["ready"],
                "blocked": stats["blocked"],
                "todo": stats["todo"],
                "load_pct": load,
                "saturation": "idle" if load < 30 else "busy" if load < 70 else "overloaded",
            })
        agents.sort(key=lambda a: a["load_pct"], reverse=True)

        # Recent completions (24h) for standup
        day_ago = (datetime.now() - timedelta(hours=24)).isoformat()
        recent_done = conn.execute("""
            SELECT assignee, title, completed_at
            FROM tasks
            WHERE title LIKE ? AND status = 'done' AND completed_at > ?
            ORDER BY completed_at DESC LIMIT 20
        """, (project_filter, day_ago)).fetchall()

        # Blockers
        blockers = conn.execute("""
            SELECT assignee, title, priority
            FROM tasks WHERE title LIKE ? AND status = 'blocked'
            ORDER BY priority ASC
        """, (project_filter,)).fetchall()

        # Ready to assign
        ready = conn.execute("""
            SELECT id, title, priority, assignee
            FROM tasks WHERE title LIKE ? AND status = 'ready'
            ORDER BY priority ASC LIMIT 10
        """, (project_filter,)).fetchall()

        # Project health score
        total = sum(r["count"] for r in status_counts)
        done = sum(r["count"] for r in status_counts if r["status"] == "done")
        blocked_count = sum(r["count"] for r in status_counts if r["status"] == "blocked")
        health = 100 if total == 0 else round(done / total * 100)

        return {
            "project": project,
            "total_tasks": total,
            "status": {r["status"]: r["count"] for r in status_counts},
            "health_pct": health,
            "health_status": "healthy" if health > 70 else "warning" if health > 40 else "critical",
            "agents": agents,
            "agent_count": len(agents),
            "blockers": [
                {"agent": b["assignee"], "task": b["title"][:80], "priority": b["priority"]}
                for b in blockers
            ],
            "ready_to_assign": len(ready),
            "ready_tasks": [
                {"id": r["id"][:12], "title": r["title"][:60], "priority": r["priority"], "assignee": r["assignee"]}
                for r in ready[:5]
            ],
            "standup": {
                "completed_24h": len(recent_done),
                "completions": [
                    {"agent": d["assignee"], "task": d["title"][:80]}
                    for d in recent_done[:10]
                ],
            },
            "timestamp": datetime.now().isoformat(),
        }
    finally:
        conn.close()


# ══════════════════════════════════════════
# Auto Standup Report (triggered on task completion)
# ══════════════════════════════════════════

def generate_task_completion_standup(task_id: str) -> dict:
    """Generate a standup report when a task is completed"""
    kanban_db = APEX_HOME / "kanban.db"
    if not kanban_db.exists():
        return {"error": "kanban.db not found"}

    conn = sqlite3.connect(str(kanban_db))
    conn.row_factory = sqlite3.Row
    try:
        # Get the completed task
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            return {"error": f"Task {task_id} not found"}

        project = task["title"].split("]")[0].replace("[", "") if "]" in (task["title"] or "") else "unknown"
        assignee = task["assignee"] or "unassigned"

        # What else is this agent working on?
        agent_tasks = conn.execute("""
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN status='in_progress' THEN 1 ELSE 0 END) as in_progress,
                   SUM(CASE WHEN status='ready' THEN 1 ELSE 0 END) as ready
            FROM tasks WHERE assignee = ? AND status != 'done'
        """, (assignee,)).fetchone()

        # Project remaining tasks
        project_remaining = conn.execute("""
            SELECT COUNT(*) FROM tasks 
            WHERE title LIKE ? AND status NOT IN ('done', 'failed')
        """, (f"%{project}%",)).fetchone()[0]

        # Who is free to take new tasks?
        all_agents = conn.execute("""
            SELECT assignee, COUNT(*) as load
            FROM tasks WHERE status IN ('ready', 'in_progress', 'todo')
            GROUP BY assignee ORDER BY load ASC LIMIT 3
        """).fetchall()

        return {
            "task_id": task_id,
            "task_title": task["title"][:80],
            "completed_by": assignee,
            "project": project,
            "agent_status": {
                "remaining_tasks": agent_tasks["total"] if agent_tasks else 0,
                "in_progress": agent_tasks["in_progress"] if agent_tasks else 0,
                "ready": agent_tasks["ready"] if agent_tasks else 0,
            },
            "project_remaining": project_remaining,
            "suggestion": f"🎉 {assignee} 刚完成了「{task['title'][:40]}」。项目 {project} 还剩 {project_remaining} 个任务。",
            "next_available": [
                {"agent": a["assignee"], "load": a["load"]}
                for a in all_agents if a["assignee"]
            ],
            "timestamp": datetime.now().isoformat(),
        }
    finally:
        conn.close()


def list_projects() -> list[dict]:
    """Auto-discover projects from task titles"""
    kanban_db = APEX_HOME / "kanban.db"
    if not kanban_db.exists():
        return []

    conn = sqlite3.connect(str(kanban_db))
    conn.row_factory = sqlite3.Row
    try:
        # Extract project names from task titles like [ProjectName] ...
        rows = conn.execute("SELECT DISTINCT title FROM tasks WHERE title LIKE '[%]%'").fetchall()

        projects = {}
        for r in rows:
            title = r["title"] or ""
            if title.startswith("["):
                end = title.find("]")
                if end > 0:
                    pname = title[1:end]
                    if pname not in projects:
                        # Count tasks for this project
                        count = conn.execute(
                            "SELECT COUNT(*) FROM tasks WHERE title LIKE ?",
                            (f"%[{pname}]%",)
                        ).fetchone()[0]
                        projects[pname] = count

        # Also add teams from fleet
        teams_file = HERMES_HOME / "fleet_teams.json"
        if teams_file.exists():
            import json
            with open(teams_file) as f:
                teams_data = json.load(f)
            for name, team in teams_data.get("teams", {}).items():
                if name not in projects:
                    projects[name] = len(team.get("members", []))

        return [
            {"name": name, "task_count": count, "has_team": name in (teams_data.get("teams", {}) if teams_file.exists() else {})}
            for name, count in sorted(projects.items(), key=lambda x: x[1], reverse=True)
        ]
    finally:
        conn.close()
