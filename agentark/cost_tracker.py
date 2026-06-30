"""Cost Tracker — 多Agent/Cron成本追踪引擎

数据源:
  1. Hermes state.db sessions → 所有LLM调用的token/cost
  2. Hermes cron list → Cron job名称映射
  3. Apex economy.db → 项目预算管理

输出维度:
  - Per-cron-job: 每个定时任务的token/cost
  - Per-agent (Profile): 每个Agent Profile的消耗
  - Per-project: 按项目聚合 (羽球宝/Apex/FinOps/深圳地图)
  - Per-source: weixin/cli/cron/webui
  - Timeline: 小时/日/周/月趋势

Dashboard集成: /api/cost/* 端点
"""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field


HERMES_HOME = Path.home() / ".hermes"
STATE_DB = HERMES_HOME / "state.db"
CRON_CACHE_FILE = HERMES_HOME / "cost_tracker_cache.json"

# DeepSeek V4 Pro pricing (USD per 1M tokens)
PRICING = {
    "deepseek-v4-pro": {"input": 1.0, "output": 4.0},
    "deepseek-chat":   {"input": 0.14, "output": 0.28},
    "deepseek-r1":     {"input": 0.55, "output": 2.19},
    "claude-sonnet-4": {"input": 3.0, "output": 15.0},
    "gpt-4o":          {"input": 2.5, "output": 10.0},
}


@dataclass
class CronCost:
    """单个Cron任务成本"""
    job_id: str
    name: str
    schedule: str = ""
    sessions: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    avg_tokens_per_run: int = 0
    avg_cost_per_run: float = 0.0
    last_run: str = ""


@dataclass
class AgentCost:
    """单个Agent成本"""
    profile: str      # Hermes Profile名
    sessions: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    sources: dict = field(default_factory=dict)  # source → count


@dataclass
class ProjectCost:
    """项目成本聚合"""
    name: str
    emoji: str
    total_cost: float = 0.0
    cron_cost: float = 0.0
    interactive_cost: float = 0.0
    sessions: int = 0
    budget_limit: float = 5.0  # 月预算
    budget_used_pct: float = 0.0


@dataclass
class CostSnapshot:
    """成本快照"""
    timestamp: str
    total_cost_30d: float
    total_cost_today: float
    total_sessions_30d: int
    total_tokens_30d: int
    cron_jobs: list[CronCost]
    agents: list[AgentCost]
    projects: list[ProjectCost]
    hourly_trend: list[dict]  # [{hour, cost, tokens}]
    daily_trend: list[dict]   # [{date, cost, tokens}]
    source_breakdown: list[dict]  # [{source, cost, sessions}]


# ═══════════════════════════════════════════════
# Cron Name Cache
# ═══════════════════════════════════════════════

def _get_cron_names() -> dict[str, dict]:
    """获取所有cron job的名称和调度信息"""
    try:
        result = subprocess.run(
            ["hermes", "cron", "list"], capture_output=True, text=True, timeout=10
        )
        output = result.stdout
    except Exception:
        return {}

    cron_map = {}
    current_id = None
    current_info = {}

    for line in output.split("\n"):
        id_m = re.match(r'\s*([a-f0-9]+)\s+\[(\w+)\]', line)
        name_m = re.match(r'\s*Name:\s+(.+)', line)
        sched_m = re.match(r'\s*Schedule:\s+(.+)', line)

        if id_m:
            if current_id and current_info:
                cron_map[current_id] = current_info
            current_id = id_m.group(1)
            current_info = {"status": id_m.group(2)}
        elif name_m and current_id:
            current_info["name"] = name_m.group(1).strip()
        elif sched_m and current_id:
            current_info["schedule"] = sched_m.group(1).strip()

    if current_id and current_info:
        cron_map[current_id] = current_info

    return cron_map


# ═══════════════════════════════════════════════
# Cost Queries
# ═══════════════════════════════════════════════

def _parse_job_id_from_session(session_id: str) -> Optional[str]:
    """从session ID提取cron job ID"""
    m = re.match(r'cron_([a-f0-9]+)_', session_id)
    return m.group(1) if m else None


def get_cron_costs(days: int = 30) -> list[CronCost]:
    """获取所有Cron任务的成本明细"""
    if not STATE_DB.exists():
        return []

    cron_names = _get_cron_names()
    cutoff = (datetime.now() - timedelta(days=days)).timestamp()

    conn = sqlite3.connect(str(STATE_DB))
    try:
        rows = conn.execute("""
            SELECT id, input_tokens, output_tokens, estimated_cost_usd, started_at
            FROM sessions
            WHERE source = 'cron' AND started_at > ?
            ORDER BY started_at DESC
        """, (cutoff,)).fetchall()

        # 按job_id聚合
        job_stats: dict[str, dict] = {}
        for sid, inp, out, cost, ts in rows:
            job_id = _parse_job_id_from_session(sid)
            if not job_id:
                continue

            if job_id not in job_stats:
                job_stats[job_id] = {
                    "sessions": 0, "input": 0, "output": 0, "cost": 0.0, "last_ts": 0
                }
            s = job_stats[job_id]
            s["sessions"] += 1
            s["input"] += (inp or 0)
            s["output"] += (out or 0)
            s["cost"] += (cost or 0)
            s["last_ts"] = max(s["last_ts"], ts or 0)

        result = []
        for job_id, stats in job_stats.items():
            cinfo = cron_names.get(job_id, {})
            name = cinfo.get("name", f"unknown-{job_id[:8]}")
            total_tok = stats["input"] + stats["output"]
            result.append(CronCost(
                job_id=job_id[:12],
                name=name,
                schedule=cinfo.get("schedule", ""),
                sessions=stats["sessions"],
                input_tokens=stats["input"],
                output_tokens=stats["output"],
                estimated_cost=round(stats["cost"], 4),
                avg_tokens_per_run=total_tok // max(stats["sessions"], 1),
                avg_cost_per_run=round(stats["cost"] / max(stats["sessions"], 1), 6),
                last_run=datetime.fromtimestamp(stats["last_ts"]).strftime("%m-%d %H:%M")
                    if stats["last_ts"] else "never",
            ))

        result.sort(key=lambda x: x.estimated_cost, reverse=True)
        return result
    finally:
        conn.close()


def get_agent_costs(days: int = 30) -> list[AgentCost]:
    """获取各Agent Profile的成本明细"""
    if not STATE_DB.exists():
        return []

    cutoff = (datetime.now() - timedelta(days=days)).timestamp()

    conn = sqlite3.connect(str(STATE_DB))
    try:
        # 尝试从 handoff_state 或 source 推断 agent
        # 先按 source 聚合，然后用 handoff_platform 细分
        rows = conn.execute("""
            SELECT 
                COALESCE(handoff_platform, source) as agent,
                source,
                COUNT(*) as cnt,
                COALESCE(SUM(input_tokens), 0),
                COALESCE(SUM(output_tokens), 0),
                COALESCE(SUM(estimated_cost_usd), 0)
            FROM sessions
            WHERE started_at > ?
            GROUP BY agent, source
            ORDER BY SUM(estimated_cost_usd) DESC
        """, (cutoff,)).fetchall()

        # 聚合到agent
        agent_map: dict[str, AgentCost] = {}
        for agent, source, cnt, inp, out, cost in rows:
            agent_key = agent or source or "unknown"
            if agent_key not in agent_map:
                agent_map[agent_key] = AgentCost(profile=agent_key)
            ac = agent_map[agent_key]
            ac.sessions += cnt
            ac.input_tokens += (inp or 0)
            ac.output_tokens += (out or 0)
            ac.estimated_cost += (cost or 0)
            ac.sources[source or "unknown"] = ac.sources.get(source or "unknown", 0) + cnt

        result = list(agent_map.values())
        result.sort(key=lambda x: x.estimated_cost, reverse=True)
        return result
    finally:
        conn.close()


def get_source_breakdown(days: int = 30) -> list[dict]:
    """按来源渠道的成本分解"""
    if not STATE_DB.exists():
        return []

    cutoff = (datetime.now() - timedelta(days=days)).timestamp()
    conn = sqlite3.connect(str(STATE_DB))
    try:
        rows = conn.execute("""
            SELECT source, COUNT(*), 
                   COALESCE(SUM(input_tokens+output_tokens), 0),
                   COALESCE(SUM(estimated_cost_usd), 0)
            FROM sessions
            WHERE started_at > ?
            GROUP BY source
            ORDER BY SUM(estimated_cost_usd) DESC
        """, (cutoff,)).fetchall()

        return [
            {"source": r[0] or "unknown", "sessions": r[1],
             "tokens": r[2], "cost": round(r[3], 4)}
            for r in rows
        ]
    finally:
        conn.close()


def get_timeline(days: int = 7, granularity: str = "daily") -> list[dict]:
    """获取时间线成本趋势"""
    if not STATE_DB.exists():
        return []

    conn = sqlite3.connect(str(STATE_DB))
    try:
        if granularity == "hourly":
            # 最近24小时按小时
            cutoff = (datetime.now() - timedelta(hours=24)).timestamp()
            rows = conn.execute("""
                SELECT 
                    CAST(strftime('%H', datetime(started_at, 'unixepoch', 'localtime')) AS INTEGER) as hour,
                    COUNT(*),
                    COALESCE(SUM(input_tokens+output_tokens), 0),
                    COALESCE(SUM(estimated_cost_usd), 0)
                FROM sessions
                WHERE started_at > ?
                GROUP BY hour
                ORDER BY hour
            """, (cutoff,)).fetchall()
            return [
                {"label": f"{r[0]:02d}:00", "sessions": r[1],
                 "tokens": r[2], "cost": round(r[3], 4)}
                for r in rows
            ]
        else:
            cutoff = (datetime.now() - timedelta(days=days)).timestamp()
            rows = conn.execute("""
                SELECT 
                    date(datetime(started_at, 'unixepoch', 'localtime')) as day,
                    COUNT(*),
                    COALESCE(SUM(input_tokens+output_tokens), 0),
                    COALESCE(SUM(estimated_cost_usd), 0)
                FROM sessions
                WHERE started_at > ?
                GROUP BY day
                ORDER BY day
            """, (cutoff,)).fetchall()
            return [
                {"label": r[0], "sessions": r[1],
                 "tokens": r[2], "cost": round(r[3], 4)}
                for r in rows
            ]
    finally:
        conn.close()


def get_summary() -> dict:
    """获取成本总览"""
    if not STATE_DB.exists():
        return {"error": "state.db not found"}

    conn = sqlite3.connect(str(STATE_DB))
    try:
        # 全部累计
        total = conn.execute("""
            SELECT COUNT(*), 
                   COALESCE(SUM(input_tokens+output_tokens), 0),
                   COALESCE(SUM(estimated_cost_usd), 0)
            FROM sessions
        """).fetchone()

        # 今日
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        today = conn.execute("""
            SELECT COUNT(*),
                   COALESCE(SUM(input_tokens+output_tokens), 0),
                   COALESCE(SUM(estimated_cost_usd), 0)
            FROM sessions WHERE started_at > ?
        """, (today_start,)).fetchone()

        # 本周
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0).timestamp()
        week = conn.execute("""
            SELECT COUNT(*),
                   COALESCE(SUM(input_tokens+output_tokens), 0),
                   COALESCE(SUM(estimated_cost_usd), 0)
            FROM sessions WHERE started_at > ?
        """, (week_start,)).fetchone()

        # 本月
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0).timestamp()
        month = conn.execute("""
            SELECT COUNT(*),
                   COALESCE(SUM(input_tokens+output_tokens), 0),
                   COALESCE(SUM(estimated_cost_usd), 0)
            FROM sessions WHERE started_at > ?
        """, (month_start,)).fetchone()

        # 30天
        d30_start = (datetime.now() - timedelta(days=30)).timestamp()
        d30 = conn.execute("""
            SELECT COUNT(*),
                   COALESCE(SUM(input_tokens+output_tokens), 0),
                   COALESCE(SUM(estimated_cost_usd), 0)
            FROM sessions WHERE started_at > ?
        """, (d30_start,)).fetchone()

        return {
            "total_sessions": total[0],
            "total_tokens": total[1],
            "total_cost": round(total[2], 4),
            "today_sessions": today[0],
            "today_tokens": today[1],
            "today_cost": round(today[2], 4),
            "week_sessions": week[0],
            "week_tokens": week[1],
            "week_cost": round(week[2], 4),
            "month_sessions": month[0],
            "month_tokens": month[1],
            "month_cost": round(month[2], 4),
            "d30_sessions": d30[0],
            "d30_tokens": d30[1],
            "d30_cost": round(d30[2], 4),
            "daily_avg_30d": round(d30[2] / 30, 4) if d30[2] else 0,
            "monthly_estimate": round(d30[2], 4),  # 30天≈1月
        }
    finally:
        conn.close()


def get_full_snapshot() -> dict:
    """获取完整成本快照 — Dashboard数据源"""
    summary = get_summary()

    return {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "cron_jobs": [c.__dict__ for c in get_cron_costs(30)],
        "agents": [a.__dict__ for a in get_agent_costs(30)],
        "source_breakdown": get_source_breakdown(30),
        "daily_trend": get_timeline(7, "daily"),
        "hourly_trend": get_timeline(1, "hourly"),
        "pricing": PRICING,
    }


# ═══════════════════════════════════════════════
# 项目成本估算 (启发式)
# ═══════════════════════════════════════════════

PROJECT_KEYWORDS = {
    "badminton-coach-ai": {
        "name": "羽球宝AI搭子",
        "emoji": "🏸",
        "keywords": ["badminton", "羽球", "羽毛球", "动作", "训练"],
        "budget": 5.0,
    },
    "apex": {
        "name": "Apex Dashboard",
        "emoji": "🦅",
        "keywords": ["apex", "dashboard", "fleet", "bridge"],
        "budget": 10.0,
    },
    "finopsai": {
        "name": "FinOps AI",
        "emoji": "💰",
        "keywords": ["finops", "云成本", "SaaS", "billing"],
        "budget": 5.0,
    },
    "shenzhen-badminton": {
        "name": "深圳羽球地图",
        "emoji": "🗺️",
        "keywords": ["深圳", "地图", "场馆", "venue"],
        "budget": 3.0,
    },
}


def estimate_project_costs() -> list[ProjectCost]:
    """基于session title/keywords 估算各项目成本"""
    if not STATE_DB.exists():
        return []

    conn = sqlite3.connect(str(STATE_DB))
    try:
        # 获取最近30天所有session
        cutoff = (datetime.now() - timedelta(days=30)).timestamp()
        rows = conn.execute("""
            SELECT id, title, system_prompt, source,
                   COALESCE(input_tokens+output_tokens, 0) as tokens,
                   COALESCE(estimated_cost_usd, 0) as cost
            FROM sessions
            WHERE started_at > ?
        """, (cutoff,)).fetchall()

        # 按项目聚合
        project_stats = {
            key: {"cost": 0.0, "sessions": 0, "tokens": 0, "cron_cost": 0.0, "interactive_cost": 0.0}
            for key in PROJECT_KEYWORDS
        }
        project_stats["other"] = {"cost": 0.0, "sessions": 0, "tokens": 0, "cron_cost": 0.0, "interactive_cost": 0.0}

        for sid, title, sp, source, tokens, cost in rows:
            matched = False
            text = f"{title or ''} {sp or ''} {sid}".lower()

            for key, info in PROJECT_KEYWORDS.items():
                if any(kw.lower() in text for kw in info["keywords"]):
                    ps = project_stats[key]
                    ps["cost"] += (cost or 0)
                    ps["sessions"] += 1
                    ps["tokens"] += (tokens or 0)
                    if source == "cron":
                        ps["cron_cost"] += (cost or 0)
                    else:
                        ps["interactive_cost"] += (cost or 0)
                    matched = True
                    break

            if not matched:
                ps = project_stats["other"]
                ps["cost"] += (cost or 0)
                ps["sessions"] += 1
                ps["tokens"] += (tokens or 0)

        result = []
        for key, info in PROJECT_KEYWORDS.items():
            ps = project_stats[key]
            budget = info["budget"]
            result.append(ProjectCost(
                name=info["name"],
                emoji=info["emoji"],
                total_cost=round(ps["cost"], 4),
                cron_cost=round(ps["cron_cost"], 4),
                interactive_cost=round(ps["interactive_cost"], 4),
                sessions=ps["sessions"],
                budget_limit=budget,
                budget_used_pct=round(ps["cost"] / budget * 100, 1) if budget > 0 else 0,
            ))

        result.sort(key=lambda x: x.total_cost, reverse=True)
        return result
    finally:
        conn.close()
