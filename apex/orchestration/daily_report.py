"""
三项目日报聚合引擎 — Project Daily Report Engine
═══════════════════════════════════════════════════════

从多数据源聚合三个项目(羽球宝AI / Apex / 深圳羽球地图)的日报数据:
  - Hermes sessions → token消耗 + 费用
  - Task Manager → 任务进度
  - Ops Manager → bugs/releases
  - Fleet → profile健康状态
  - Auth Engine → 授权统计
  - 服务健康检查

输出: 结构化日报 JSON，供 Dashboard 面板消费
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

HERMES_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))
APEX_HOME = Path(os.environ.get("APEX_HOME", os.path.expanduser("~/.apex")))
TZ = timezone(timedelta(hours=8))

# ════════════════════════════════════════════════════════════
# 三项目定义 (同步自 message_router.py)
# ════════════════════════════════════════════════════════════

PROJECTS = {
    "badminton-coach-ai": {
        "key": "badminton-coach-ai",
        "name": "羽球宝AI搭子",
        "emoji": "🏸",
        "path": os.path.expanduser("~/Desktop/2026AIAPP/workspace/badminton-coach-ai"),
        "color": "#f97316",
        "profiles": ["badminton-pm", "architect", "ai-algorithm", "ai-vision", "frontend-dev", "content-marketing"],
        "services": ["http://127.0.0.1:8000/docs"],
        "order": 1,
    },
    "apex": {
        "key": "apex",
        "name": "Apex Dashboard",
        "emoji": "🦅",
        "path": os.path.expanduser("~/Desktop/2026AIAPP/Apex"),
        "color": "#3b82f6",
        "profiles": ["default", "ops-engineer", "security-compliance", "apex-pm"],
        "services": ["http://127.0.0.1:8080"],
        "order": 2,
    },
    "shenzhen-badminton": {
        "key": "shenzhen-badminton",
        "name": "深圳羽球地图",
        "emoji": "🗺️",
        "path": os.path.expanduser("~/Desktop/2026AIAPP/shenzhen-badminton"),
        "color": "#22c55e",
        "profiles": ["content-marketing", "fundraising-pitch"],
        "services": [],
        "order": 3,
    },
}


@dataclass
class ProjectDailyReport:
    """单个项目的日报"""
    key: str
    name: str
    emoji: str
    color: str
    # Token / 成本
    today_tokens: int = 0
    today_cost: float = 0.0
    total_tokens: int = 0
    total_cost: float = 0.0
    sessions_today: int = 0
    # 任务
    tasks_total: int = 0
    tasks_done: int = 0
    tasks_in_progress: int = 0
    tasks_blocked: int = 0
    tasks_todo: int = 0
    # Bug
    bugs_open: int = 0
    bugs_critical: int = 0
    # 服务健康
    services_healthy: int = 0
    services_total: int = 0
    # Git 活动
    git_commits_today: int = 0
    git_branch: str = ""
    # 授权
    auth_pending: int = 0
    auth_active: int = 0
    # 数据时间戳
    updated_at: str = ""


@dataclass
class DailyReport:
    """日报总览"""
    date: str = ""
    timestamp: int = 0
    projects: list[ProjectDailyReport] = field(default_factory=list)
    # 总计
    total_tokens_today: int = 0
    total_cost_today: float = 0.0
    total_tasks_done: int = 0
    total_bugs_open: int = 0
    all_services_healthy: bool = True
    # 系统
    uptime_seconds: int = 0
    cron_active: int = 0
    gpu_online: int = 0
    gpu_total: int = 0


# ════════════════════════════════════════════════════════════
# 数据采集
# ════════════════════════════════════════════════════════════

def _get_today_start() -> float:
    """今日 00:00 时间戳"""
    now = datetime.now(TZ)
    return now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()


def _collect_token_stats(project_key: str) -> dict:
    """从 Hermes sessions 按 project 标签聚合 token/cost"""
    state_db = HERMES_HOME / "state.db"
    if not state_db.exists():
        return {"today_tokens": 0, "today_cost": 0, "total_tokens": 0, "total_cost": 0, "sessions_today": 0}

    # Map project key → likely source patterns
    source_map = {
        "badminton-coach-ai": ["badminton", "羽球宝", "badminton-coach", "yuji"],
        "apex": ["apex", "kanban", "fleet", "dashboard", "origin", "pm-report"],
        "shenzhen-badminton": ["shenzhen", "深圳", "ball-map"],
    }

    patterns = source_map.get(project_key, [project_key])

    conn = sqlite3.connect(str(state_db))
    try:
        today_start = _get_today_start()

        # Build LIKE clauses
        like_clauses = " OR ".join(["source LIKE ?" for _ in patterns])
        like_params = [f"%{p}%" for p in patterns]

        # Today
        today_row = conn.execute(
            f"""SELECT
                COALESCE(SUM(input_tokens + output_tokens), 0) as tokens,
                COALESCE(SUM(estimated_cost_usd), 0) as cost,
                COUNT(*) as sessions
            FROM sessions
            WHERE started_at > ? AND ({like_clauses})""",
            [today_start] + like_params,
        ).fetchone()

        # All time
        all_row = conn.execute(
            f"""SELECT
                COALESCE(SUM(input_tokens + output_tokens), 0) as tokens,
                COALESCE(SUM(estimated_cost_usd), 0) as cost
            FROM sessions
            WHERE ({like_clauses})""",
            like_params,
        ).fetchone()

        return {
            "today_tokens": int(today_row[0]) if today_row else 0,
            "today_cost": round(today_row[1], 4) if today_row and today_row[1] else 0,
            "total_tokens": int(all_row[0]) if all_row else 0,
            "total_cost": round(all_row[1], 4) if all_row and all_row[1] else 0,
            "sessions_today": int(today_row[2]) if today_row else 0,
        }
    finally:
        conn.close()


def _collect_task_stats(project_key: str) -> dict:
    """从 Apex task manager 按 project 聚合任务统计"""
    ops_db = APEX_HOME / "ops.db"
    if not ops_db.exists():
        return {"total": 0, "done": 0, "in_progress": 0, "blocked": 0, "todo": 0}

    # Try task_manager first (has project field)
    tm_db = APEX_HOME / "task_manager.db"
    if tm_db.exists():
        conn = sqlite3.connect(str(tm_db))
        try:
            today_start = _get_today_start()
            stats = {}
            for status in ["done", "in_progress", "blocked"]:
                cnt = conn.execute(
                    "SELECT COUNT(*) FROM tasks WHERE project = ? AND workflow_status = ?",
                    (project_key, status),
                ).fetchone()[0]
                stats[status] = cnt

            # Todo: draft, requested, approved, pm_review, assigned
            todo_cnt = conn.execute(
                """SELECT COUNT(*) FROM tasks WHERE project = ?
                   AND workflow_status IN ('draft','requested','pm_review','approved','assigned')""",
                (project_key,),
            ).fetchone()[0]

            total = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE project = ?",
                (project_key,),
            ).fetchone()[0]

            return {
                "total": total,
                "done": stats.get("done", 0),
                "in_progress": stats.get("in_progress", 0),
                "blocked": stats.get("blocked", 0),
                "todo": todo_cnt,
            }
        finally:
            conn.close()

    # Fallback to ops.db
    conn = sqlite3.connect(str(ops_db))
    try:
        # ops.db tasks don't have project field — use tags
        total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        done = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='done'").fetchone()[0]
        in_prog = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='in_progress'").fetchone()[0]
        blocked = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='blocked'").fetchone()[0]
        return {
            "total": total,
            "done": done,
            "in_progress": in_prog,
            "blocked": blocked,
            "todo": total - done - in_prog - blocked,
        }
    finally:
        conn.close()


def _collect_bug_stats(project_key: str) -> dict:
    """Bug 统计"""
    ops_db = APEX_HOME / "ops.db"
    if not ops_db.exists():
        return {"open": 0, "critical": 0}

    conn = sqlite3.connect(str(ops_db))
    try:
        open_bugs = conn.execute(
            "SELECT COUNT(*) FROM bugs WHERE status NOT IN ('verified','closed')"
        ).fetchone()[0]
        critical = conn.execute(
            "SELECT COUNT(*) FROM bugs WHERE severity='critical' AND status NOT IN ('verified','closed')"
        ).fetchone()[0]
        return {"open": open_bugs, "critical": critical}
    finally:
        conn.close()


def _check_services(project_key: str) -> dict:
    """检查项目服务健康"""
    proj = PROJECTS.get(project_key, {})
    urls = proj.get("services", [])
    healthy = 0
    details = []

    for url in urls:
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Apex-DailyReport/1.0")
            with urllib.request.urlopen(req, timeout=4) as resp:
                details.append({"url": url, "healthy": True, "code": resp.status})
                healthy += 1
        except Exception as e:
            details.append({"url": url, "healthy": False, "error": str(e)[:60]})

    return {"healthy": healthy, "total": len(urls), "details": details}


def _collect_git_stats(project_key: str) -> dict:
    """Git 活动统计"""
    proj = PROJECTS.get(project_key, {})
    path = proj.get("path", "")
    if not path or not os.path.isdir(path):
        return {"commits_today": 0, "branch": ""}

    import subprocess
    today = datetime.now(TZ).strftime("%Y-%m-%d")

    try:
        # Commits today
        r = subprocess.run(
            ["git", "-C", path, "log", "--oneline", f"--since={today}T00:00:00+08:00",
             "--until={today}T23:59:59+08:00"],
            capture_output=True, text=True, timeout=5,
        )
        commits = len([l for l in r.stdout.strip().split("\n") if l]) if r.returncode == 0 else 0

        # Branch
        r2 = subprocess.run(
            ["git", "-C", path, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=3,
        )
        branch = r2.stdout.strip() if r2.returncode == 0 else ""

        return {"commits_today": commits, "branch": branch}
    except Exception:
        return {"commits_today": 0, "branch": ""}


def _collect_auth_stats(project_key: str) -> dict:
    """授权统计"""
    auth_db = HERMES_HOME / "auth" / "grants.db"
    if not auth_db.exists():
        return {"pending": 0, "active": 0}

    # Map project to likely agents
    agent_map = {
        "badminton-coach-ai": ["badminton-pm", "architect", "ai-algorithm", "ai-vision", "frontend-dev"],
        "apex": ["default", "ops-engineer", "security-compliance", "apex-pm"],
        "shenzhen-badminton": ["content-marketing", "fundraising-pitch"],
    }
    agents = agent_map.get(project_key, [])

    conn = sqlite3.connect(str(auth_db))
    try:
        now = int(time.time())
        if agents:
            placeholders = ",".join(["?" for _ in agents])
            pending = conn.execute(
                f"SELECT COUNT(*) FROM grants WHERE status='pending' AND agent IN ({placeholders})",
                agents,
            ).fetchone()[0]
            active = conn.execute(
                f"SELECT COUNT(*) FROM grants WHERE status='approved' AND expires_at > ? AND agent IN ({placeholders})",
                [now] + agents,
            ).fetchone()[0]
        else:
            pending = 0
            active = 0
        return {"pending": pending, "active": active}
    finally:
        conn.close()


def _collect_gpu_status() -> dict:
    """GPU 状态 (通过 Apex API)"""
    try:
        req = urllib.request.Request("http://127.0.0.1:8080/api/gpu/status")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return {
                "online": data.get("instances_online", 0),
                "total": data.get("total", 0),
            }
    except Exception:
        return {"online": 0, "total": 0}


def _collect_cron_status() -> int:
    """Cron 活跃数"""
    try:
        import subprocess
        r = subprocess.run(
            ["hermes", "cron", "list"], capture_output=True, text=True, timeout=5
        )
        return sum(1 for line in r.stdout.split("\n") if "[active]" in line)
    except Exception:
        return 0


# ════════════════════════════════════════════════════════════
# 日报生成
# ════════════════════════════════════════════════════════════

def generate_report() -> DailyReport:
    """生成三项目日报"""

    now = datetime.now(TZ)
    report = DailyReport(
        date=now.strftime("%Y-%m-%d"),
        timestamp=int(now.timestamp()),
    )

    for key, proj in sorted(PROJECTS.items(), key=lambda x: x[1]["order"]):
        token = _collect_token_stats(key)
        tasks = _collect_task_stats(key)
        bugs = _collect_bug_stats(key)
        svc = _check_services(key)
        git = _collect_git_stats(key)
        auth = _collect_auth_stats(key)

        pr = ProjectDailyReport(
            key=key,
            name=proj["name"],
            emoji=proj["emoji"],
            color=proj["color"],
            today_tokens=token["today_tokens"],
            today_cost=token["today_cost"],
            total_tokens=token["total_tokens"],
            total_cost=token["total_cost"],
            sessions_today=token["sessions_today"],
            tasks_total=tasks["total"],
            tasks_done=tasks["done"],
            tasks_in_progress=tasks["in_progress"],
            tasks_blocked=tasks["blocked"],
            tasks_todo=tasks["todo"],
            bugs_open=bugs["open"],
            bugs_critical=bugs["critical"],
            services_healthy=svc["healthy"],
            services_total=svc["total"],
            git_commits_today=git["commits_today"],
            git_branch=git["branch"],
            auth_pending=auth["pending"],
            auth_active=auth["active"],
            updated_at=now.strftime("%H:%M:%S"),
        )
        report.projects.append(pr)

        # 聚合
        report.total_tokens_today += token["today_tokens"]
        report.total_cost_today += token["today_cost"]
        report.total_tasks_done += tasks["done"]
        report.total_bugs_open += bugs["open"]
        if svc["total"] > 0 and svc["healthy"] < svc["total"]:
            report.all_services_healthy = False

    # 系统级
    gpu = _collect_gpu_status()
    report.gpu_online = gpu["online"]
    report.gpu_total = gpu["total"]
    report.cron_active = _collect_cron_status()

    return report


def generate_json_report() -> dict:
    """生成 JSON 格式日报 (供 API 返回)"""
    report = generate_report()

    projects_json = []
    for pr in report.projects:
        # Build a health bar: tasks
        task_ratio = (pr.tasks_done / max(pr.tasks_total, 1)) * 100
        health_status = "🟢"
        if task_ratio < 30:
            health_status = "🔴"
        elif task_ratio < 60:
            health_status = "🟡"

        # Service status
        svc_status = "🟢"
        if pr.services_total > 0 and pr.services_healthy < pr.services_total:
            svc_status = "🔴"
        elif pr.services_total == 0:
            svc_status = "⚪"

        projects_json.append({
            "key": pr.key,
            "name": pr.name,
            "emoji": pr.emoji,
            "color": pr.color,
            "health": {
                "status": health_status,
                "task_pct": round(task_ratio, 1),
                "service_status": svc_status,
            },
            "tokens": {
                "today": pr.today_tokens,
                "today_fmt": _fmt_tokens(pr.today_tokens),
                "today_cost": round(pr.today_cost, 4),
                "total": pr.total_tokens,
                "total_fmt": _fmt_tokens(pr.total_tokens),
                "total_cost": round(pr.total_cost, 4),
                "sessions_today": pr.sessions_today,
            },
            "tasks": {
                "total": pr.tasks_total,
                "done": pr.tasks_done,
                "in_progress": pr.tasks_in_progress,
                "blocked": pr.tasks_blocked,
                "todo": pr.tasks_todo,
                "progress_bar": _progress_bar(pr.tasks_done, pr.tasks_total),
            },
            "bugs": {
                "open": pr.bugs_open,
                "critical": pr.bugs_critical,
            },
            "services": {
                "healthy": pr.services_healthy,
                "total": pr.services_total,
            },
            "git": {
                "commits_today": pr.git_commits_today,
                "branch": pr.git_branch,
            },
            "auth": {
                "pending": pr.auth_pending,
                "active": pr.auth_active,
            },
            "updated_at": pr.updated_at,
        })

    # 总体摘要
    all_ok = report.all_services_healthy and report.total_bugs_open == 0

    return {
        "date": report.date,
        "timestamp": report.timestamp,
        "summary": {
            "status": "🟢 全绿" if all_ok else ("🟡 注意" if report.all_services_healthy else "🔴 异常"),
            "all_ok": all_ok,
            "total_tokens_today": report.total_tokens_today,
            "total_tokens_fmt": _fmt_tokens(report.total_tokens_today),
            "total_cost_today": round(report.total_cost_today, 4),
            "total_tasks_done": report.total_tasks_done,
            "total_bugs_open": report.total_bugs_open,
            "projects_count": len(report.projects),
        },
        "system": {
            "uptime_seconds": report.uptime_seconds,
            "cron_active": report.cron_active,
            "gpu_online": report.gpu_online,
            "gpu_total": report.gpu_total,
        },
        "projects": projects_json,
    }


def _fmt_tokens(n: int) -> str:
    """格式化 token 数"""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def _progress_bar(done: int, total: int) -> str:
    """ASCII 进度条"""
    if total == 0:
        return "░░░░░░░░░░"
    blocks = int(done / max(total, 1) * 10)
    return "█" * blocks + "░" * (10 - blocks)


# ════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════

def main():
    import sys
    report = generate_json_report()
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"   Apex 三项目日报 — {report['date']}")
        print(f"{'='*60}")
        print(f"   总体: {report['summary']['status']} | "
              f"Token {report['summary']['total_tokens_fmt']} | "
              f"费用 ${report['summary']['total_cost_today']:.4f}")
        print(f"{'='*60}")
        for p in report["projects"]:
            print(f"\n  {p['emoji']} {p['name']} [{p['health']['status']}]")
            print(f"     Tokens: {p['tokens']['today_fmt']} today | ${p['tokens']['today_cost']:.4f}")
            print(f"     Tasks:  {p['tasks']['progress_bar']} {p['tasks']['done']}/{p['tasks']['total']} "
                  f"(🚧{p['tasks']['in_progress']} ⛔{p['tasks']['blocked']})")
            if p["bugs"]["open"]:
                print(f"     Bugs:   🔴 {p['bugs']['open']} open ({p['bugs']['critical']} critical)")
            if p["services"]["total"] > 0:
                svc_icon = "🟢" if p["services"]["healthy"] == p["services"]["total"] else "🔴"
                print(f"     SVCS:   {svc_icon} {p['services']['healthy']}/{p['services']['total']}")
            if p["git"]["commits_today"]:
                print(f"     Git:    {p['git']['commits_today']} commits ({p['git']['branch']})")
            if p["auth"]["pending"]:
                print(f"     Auth:   ⏳ {p['auth']['pending']} pending")
        print(f"\n{'='*60}")
        print(f"   🖥️  GPU: {report['system']['gpu_online']}/{report['system']['gpu_total']} | "
              f"⏱️ Cron: {report['system']['cron_active']} active")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
