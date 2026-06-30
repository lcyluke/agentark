#!/usr/bin/env python3
"""
Apex-Hermes Bridge Sync Engine
═══════════════════════════════════════════════════
作为 Hermes cron job 每 5 分钟运行一次，
读取 Hermes state.db / config / monitor.db 数据，
更新 Apex Dashboard Kanban 任务状态。

6 个监控 Agent 对应的任务是预创建的 Kanban 任务，
本脚本负责更新它们的 output / status 字段。
"""

import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

HERMES_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))
AGENTARK_HOME = Path(os.environ.get("AGENTARK_HOME", os.path.expanduser("~/.apex")))
STATE_DB = HERMES_HOME / "state.db"
KANBAN_DB = AGENTARK_HOME / "kanban.db"
MONITOR_DB = Path(os.path.expanduser("~/Desktop/2026AIAPP/monitor/logs/monitor.db"))

# ── Helper ──────────────────────────────────────────────────

def get_kanban() -> sqlite3.Connection:
    conn = sqlite3.connect(str(KANBAN_DB))
    conn.row_factory = sqlite3.Row
    # Ensure table exists (idempotent)
    conn.execute("""
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
    conn.commit()
    return conn

def upsert_task(conn, task_id: str, title: str, assignee: str, status: str = "in_progress",
                output: str = "", priority: int = 1, parent_id: str = "") -> str:
    """Insert or update a task. Returns task_id."""
    existing = conn.execute("SELECT id FROM tasks WHERE id=?", (task_id,)).fetchone()
    now = datetime.now().isoformat()
    if existing:
        if status in ("done", "failed"):
            conn.execute("""
                UPDATE tasks SET output=?, status=?, completed_at=?
                WHERE id=?
            """, (output[:5000], status, now, task_id))
        else:
            conn.execute("""
                UPDATE tasks SET output=?, status=?
                WHERE id=?
            """, (output[:5000], status, task_id))
    else:
        conn.execute("""
            INSERT INTO tasks(id, title, description, assignee, status, priority, parent_id, output, created_at)
            VALUES(?,?,?,?,?,?,?,?,?)
        """, (task_id, title, "", assignee, status, priority, parent_id, output[:5000], now))
    conn.commit()
    return task_id

# ── 1. Session Scout ────────────────────────────────────────

def sync_sessions(conn):
    """扫描 Hermes state.db 新会话，更新 Kanban。"""
    if not STATE_DB.exists():
        upsert_task(conn, "watch-sessions", "🔍 会话侦测", "session-scout",
                     status="blocked", output="state.db 不存在")
        return

    db = sqlite3.connect(str(STATE_DB))
    db.row_factory = sqlite3.Row

    # 最近 24h 会话
    cutoff = (datetime.now() - timedelta(days=1)).timestamp()
    recent = db.execute(
        "SELECT id, title, message_count, input_tokens, output_tokens, source, started_at, model "
        "FROM sessions WHERE started_at > ? ORDER BY started_at DESC", (cutoff,)
    ).fetchall()

    total = db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    today = db.execute(
        "SELECT COUNT(*) FROM sessions WHERE started_at > ?",
        (datetime.now().replace(hour=0, minute=0, second=0).timestamp(),)
    ).fetchone()[0]

    # Token totals
    tokens = db.execute(
        "SELECT COALESCE(SUM(input_tokens),0), COALESCE(SUM(output_tokens),0) FROM sessions WHERE started_at > ?",
        (cutoff,)
    ).fetchone()

    db.close()

    lines = [f"📊 总会话: {total} | 今日: {today} | 24h: {len(recent)}"]
    lines.append(f"💰 24h Token: {tokens[0]:,}入 + {tokens[1]:,}出 = {tokens[0]+tokens[1]:,}")
    lines.append("")
    for s in recent[:8]:
        title = (s["title"] or "untitled")[:40]
        src = s["source"] or "?"
        lines.append(f"  {src:8s} | {title}")

    output = "\n".join(lines)
    upsert_task(conn, "watch-sessions", "🔍 会话侦测 | {today}今日/{total}总计",
                 "session-scout", status="done", output=output)


# ── 2. Token Guardian ───────────────────────────────────────

def sync_tokens(conn):
    if not STATE_DB.exists():
        upsert_task(conn, "watch-tokens", "💰 Token预算", "token-guardian",
                     status="blocked", output="state.db 不存在")
        return

    db = sqlite3.connect(str(STATE_DB))
    db.row_factory = sqlite3.Row

    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0).timestamp()
    week_start = (now - timedelta(days=7)).timestamp()

    today = db.execute(
        "SELECT COALESCE(SUM(input_tokens),0), COALESCE(SUM(output_tokens),0), COALESCE(SUM(estimated_cost_usd),0) "
        "FROM sessions WHERE started_at > ?", (today_start,)
    ).fetchone()

    week = db.execute(
        "SELECT COALESCE(SUM(input_tokens),0), COALESCE(SUM(output_tokens),0), COALESCE(SUM(estimated_cost_usd),0) "
        "FROM sessions WHERE started_at > ?", (week_start,)
    ).fetchone()

    # Per-model
    models = db.execute(
        "SELECT model, COUNT(*), COALESCE(SUM(input_tokens+output_tokens),0), COALESCE(SUM(estimated_cost_usd),0) "
        "FROM sessions WHERE started_at > ? AND model IS NOT NULL GROUP BY model ORDER BY 3 DESC",
        (week_start,)
    ).fetchall()

    db.close()

    # Budget thresholds (configurable)
    daily_budget = 5.0   # $5/day
    weekly_budget = 25.0  # $25/week

    today_cost = round(today[2], 4)
    week_cost = round(week[2], 4)
    today_pct = round(today_cost / daily_budget * 100, 1)
    week_pct = round(week_cost / weekly_budget * 100, 1)

    alarm = ""
    if today_pct > 80:
        alarm = f"🚨 今日已用 {today_pct}% 预算！"

    lines = [
        f"📅 今日: {today[0]+today[1]:,} tokens | ${today_cost} ({today_pct}% 日预算)",
        f"📆 本周: {week[0]+week[1]:,} tokens | ${week_cost} ({week_pct}% 周预算)",
        alarm,
        "",
        "🤖 按模型分布 (本周):",
    ]
    for m in models[:6]:
        lines.append(f"  {m[0]:20s} | {m[2]:>10,}t | ${round(m[3],2):.2f}")

    output = "\n".join(lines)
    status = "in_progress" if today_pct > 80 else "done"
    upsert_task(conn, "watch-tokens", f"💰 Token预算 | 今日${today_cost}/{daily_budget}",
                 "token-guardian", status=status, output=output)


# ── 3. GPU Sentinel ─────────────────────────────────────────

def sync_gpu(conn):
    if not MONITOR_DB.exists():
        upsert_task(conn, "watch-gpu", "⚡ GPU监控", "gpu-sentinel",
                     status="blocked", output="monitor.db 不存在")
        return

    db = sqlite3.connect(str(MONITOR_DB))
    db.row_factory = sqlite3.Row

    latest = db.execute(
        "SELECT timestamp, gpu_name, utilization_gpu, utilization_memory, "
        "memory_used_mb, memory_total_mb, temperature_gpu, power_draw "
        "FROM gpu_metrics ORDER BY id DESC LIMIT 1"
    ).fetchone()

    cost = db.execute(
        "SELECT runtime_minutes, cost_yuan FROM cost_log ORDER BY id DESC LIMIT 1"
    ).fetchone()

    # 24h avg
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
    stats = db.execute(
        "SELECT COUNT(*), ROUND(AVG(utilization_gpu),1), ROUND(MAX(utilization_gpu),1) "
        "FROM gpu_metrics WHERE timestamp > ?", (cutoff,)
    ).fetchone()

    db.close()

    if not latest:
        upsert_task(conn, "watch-gpu", "⚡ GPU监控 | 离线", "gpu-sentinel",
                     status="blocked", output="无GPU数据")
        return

    util = latest["utilization_gpu"]
    temp = latest["temperature_gpu"]
    mem_pct = round(latest["memory_used_mb"] / latest["memory_total_mb"] * 100, 1) if latest["memory_total_mb"] else 0

    alarm = ""
    status = "done"
    if util < 5 and stats and stats[0] > 10:
        alarm = "🚨 GPU持续空闲！建议关机省成本"
        status = "in_progress"

    lines = [
        f"🖥️ {latest['gpu_name']}",
        f"📊 利用率: {util:.1f}% GPU | {mem_pct:.1f}% 显存 | {temp:.0f}°C",
        f"📈 24h平均: {stats[1]}% | 峰值: {stats[2]}%",
        f"💰 累计费用: ¥{cost[1]:.2f}" if cost and cost[1] else "💰 费用: 无数据",
        alarm,
    ]

    output = "\n".join(lines)
    upsert_task(conn, "watch-gpu", f"⚡ GPU | {util:.1f}% {latest['gpu_name']}",
                 "gpu-sentinel", status=status, output=output)


# ── 4. Profile Syncer ───────────────────────────────────────

def sync_profiles(conn):
    import subprocess
    try:
        result = subprocess.run(
            ["hermes", "profile", "list"], capture_output=True, text=True, timeout=10
        )
        output = result.stdout
    except Exception as e:
        upsert_task(conn, "watch-profiles", "📡 Profile状态", "profile-syncer",
                     status="blocked", output=f"hermes CLI不可用: {e}")
        return

    profiles = []
    for line in output.split("\n"):
        line = line.strip()
        if not line or line.startswith("──") or line.startswith("Profile"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            name = parts[0].replace("◆", "").replace("●", "")
            is_default = "◆" in line
            running = "running" in line.lower()
            profiles.append(f"  {'⭐' if is_default else '  '} {name:20s} {'🟢' if running else '🔴'}")

    status = "done"
    if not profiles:
        status = "blocked"

    upsert_task(conn, "watch-profiles", f"📡 Profile | {len(profiles)}个",
                 "profile-syncer", status=status, output="\n".join(profiles[:20]))


# ── 5. Cron Medic ────────────────────────────────────────────

def sync_cron(conn):
    import subprocess
    try:
        result = subprocess.run(
            ["hermes", "cron", "list"], capture_output=True, text=True, timeout=10
        )
        output = result.stdout
    except Exception as e:
        upsert_task(conn, "watch-cron", "🛡️ Cron巡检", "cron-medic",
                     status="blocked", output=f"hermes CLI不可用: {e}")
        return

    active = output.count("[active]")
    paused = output.count("[paused]")
    errors = output.count("[error]") + output.count("[failed]")

    status = "done"
    alarm = ""
    if errors > 0:
        status = "in_progress"
        alarm = f"🚨 {errors} 个cron异常！"

    lines = [
        f"⏰ 定时任务: {active}活跃 | {paused}暂停 | {errors}异常",
        alarm,
        output[:2000] if output else "(无输出)",
    ]

    upsert_task(conn, "watch-cron", f"🛡️ Cron | {active}活跃/{paused}暂停/{errors}异常",
                 "cron-medic", status=status, output="\n".join(lines))


# ── 6. Fleet Commander ──────────────────────────────────────

def sync_commander(conn):
    """汇总所有Agent状态，给出舰队总览。"""
    rows = conn.execute(
        "SELECT assignee, status, output FROM tasks WHERE id IN ('watch-sessions','watch-tokens','watch-gpu','watch-profiles','watch-cron')"
    ).fetchall()

    statuses = {r["assignee"]: r["status"] for r in rows}
    all_ok = all(s == "done" for s in statuses.values())
    blocked = [a for a, s in statuses.items() if s == "blocked"]
    active = [a for a, s in statuses.items() if s == "in_progress"]

    lines = [
        "⚓ 舰队状态报告",
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]
    if all_ok:
        lines.append("✅ 全部系统正常")
    else:
        if blocked:
            lines.append(f"🔴 离线: {', '.join(blocked)}")
        if active:
            lines.append(f"🟡 注意: {', '.join(active)}")

    output = "\n".join(lines)
    upsert_task(conn, "fleet-status", f"⚓ 舰队总览 | {datetime.now().strftime('%H:%M')}",
                 "fleet-commander", status="done", output=output)


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    conn = get_kanban()

    # 确保父任务存在
    for tid, title in [
        ("fleet-status", "⚓ 舰队总览"),
    ]:
        upsert_task(conn, tid, title, "fleet-commander", status="in_progress")

    # 按优先级执行（轻量级先跑，避免超时）
    sync_profiles(conn)    # 📡 最快: subprocess hermes profile list
    sync_cron(conn)        # 🛡️ 快: subprocess hermes cron list
    sync_sessions(conn)    # 🔍 中: 读取 state.db
    sync_tokens(conn)      # 💰 中: 读取 state.db
    sync_gpu(conn)         # ⚡ 慢: 读取 monitor.db
    sync_commander(conn)   # 🧭 汇总: 本地读取 kanban.db

    conn.close()
    print("✅ Apex-Hermes Bridge Sync: done")

if __name__ == "__main__":
    main()
