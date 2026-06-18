"""Apex Monitor — Agent status panel with Rich terminal UI.

Pulls data from:
  - ~/finopsai/data/agent_monitor.json    — agent heartbeats
  - ~/finopsai/data/badminton_tasks.json  — badminton pipeline
  - ~/Desktop/2026workspace/LLM-Training/data/badminton/metadata/
    smart_clip_report.json                — clip statistics

Usage:
  apex monitor status          # Rich terminal panel
  apex monitor status --json   # JSON output (for dashboard)
  apex monitor status --watch 60  # auto-refresh every 60s
  apex monitor skills          # agent skill summary
  apex monitor tasks           # task board
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.progress import BarColumn, Progress, TextColumn
from rich.text import Text
from rich.columns import Columns
from rich import box

console = Console()

# ─── Data paths ──────────────────────────────────────────────────
TZ = timezone(timedelta(hours=8))
FINOPs = Path.home() / "finopsai" / "data"
BADMINTON = Path.home() / "Desktop/2026workspace/LLM-Training/data/badminton"

HERMES_SKILLS = Path.home() / ".hermes" / "skills"
APEX_SKILLS = Path.home() / ".apex" / "skill-registry.yaml"


# ─── Data loading ────────────────────────────────────────────────

def _load_json(path: Path) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def _time_ago(timestamp_str: str | None) -> str:
    if not timestamp_str:
        return "从未"
    try:
        ts = timestamp_str
        if ts.endswith("Z"):
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        elif "+" in ts[-6:]:
            dt = datetime.fromisoformat(ts)
        else:
            dt = datetime.fromisoformat(ts)

        now = datetime.now(TZ)
        diff = now - dt.astimezone(TZ)
        if diff.total_seconds() < 0:
            return "刚刚"
        mins = int(diff.total_seconds() / 60)
        if mins < 1:
            return f"{int(diff.total_seconds())}秒前"
        if mins < 60:
            return f"{mins}分钟前"
        hours = mins // 60
        if hours < 24:
            return f"{hours}小时{mins%60}分钟前"
        return f"{hours//24}天前"
    except Exception:
        return str(timestamp_str)[:16] if timestamp_str else "?"


# ─── Core data models ────────────────────────────────────────────

class MonitorData:
    """All data loaded for the monitor panel."""

    def __init__(self):
        self.agents: list[dict] = []
        self.tasks: list[dict] = []
        self.milestones: list[dict] = []
        self.collection_progress: dict = {}
        self.clips_total: int = 0
        self.now = datetime.now(TZ)

    @classmethod
    def load(cls) -> "MonitorData":
        data = cls()
        agents_data = _load_json(FINOPs / "agent_monitor.json")
        tasks_data = _load_json(FINOPs / "badminton_tasks.json")
        report = _load_json(BADMINTON / "metadata" / "smart_clip_report.json")

        data.agents = agents_data.get("agents", [])
        data.tasks = tasks_data.get("tasks", [])
        data.milestones = tasks_data.get("milestones", [])
        data.collection_progress = tasks_data.get("project_status", {}).get(
            "collection_progress", {}
        )

        if report:
            data.clips_total = report.get("summary", {}).get("clips_generated", 0)

        return data

    @property
    def active(self) -> list[dict]:
        return [a for a in self.agents if a.get("status") == "active"]

    @property
    def warning(self) -> list[dict]:
        return [a for a in self.agents if a.get("status") == "warning"]

    @property
    def offline(self) -> list[dict]:
        return [a for a in self.agents if a.get("status") == "offline"]

    def tasks_by_owner(self, owner: str) -> list[dict]:
        return [t for t in self.tasks if t.get("owner") == owner]

    def tasks_by_status(self, status: str) -> list[dict]:
        return [t for t in self.tasks if t.get("status") == status]


# ─── Rich Renderers ──────────────────────────────────────────────

def render_status_panel(data: MonitorData) -> None:
    """Render the full agent status panel with Rich."""

    # ── Header ──
    header = Panel(
        f"[bold]🤖 Agent 任务执行状态面板[/]\n"
        f"[dim]刷新时间: {data.now.strftime('%Y-%m-%d %H:%M:%S')}[/]",
        border_style="cyan",
    )
    console.print(header)

    # ── Summary bar ──
    summary_colors = {
        "active": "green",
        "warning": "yellow",
        "offline": "red",
    }
    parts = [f"Agent 总数: [bold]{len(data.agents)}[/]"]
    for status, label in [("active", "活跃"), ("warning", "警告"), ("offline", "离线")]:
        count = len([a for a in data.agents if a.get("status") == status])
        color = summary_colors[status]
        parts.append(f"[{color}]● {label}: {count}[/]")

    console.print(Panel("  │  ".join(parts), border_style="blue"))
    console.print()

    # ── Agent table ──
    table = Table(
        box=box.ROUNDED,
        border_style="blue",
        header_style="bold cyan",
        show_header=True,
    )
    table.add_column("", width=2)
    table.add_column("Agent", style="bold white", min_width=22)
    table.add_column("状态", justify="center", width=8)
    table.add_column("最后心跳", justify="center", width=16)
    table.add_column("任务", justify="center", width=10)
    table.add_column("当前任务", style="dim", max_width=36)

    for a in data.agents:
        name = a.get("name", "?")
        if name == "BadmintonCoach_LuB":
            continue

        status = a.get("status", "offline")
        hb = a.get("last_heartbeat")
        hb_str = _time_ago(hb)

        owner_tasks = data.tasks_by_owner(name)
        n_tasks = len(owner_tasks)
        n_done = sum(1 for t in owner_tasks if t.get("status") == "completed")

        icon = {"active": "✅", "warning": "⚠️", "offline": "❌"}.get(status, "❓")
        status_color = {"active": "green", "warning": "yellow", "offline": "red"}.get(
            status, "white"
        )

        if n_tasks > 0:
            progress = f"{n_done}/{n_tasks}"
        elif status == "active":
            progress = "运行中"
        else:
            progress = "—"

        # Show in-progress task refs
        active_tasks = [
            t for t in owner_tasks if t.get("status") == "in_progress"
        ]
        task_refs = " ← ".join(t.get("id", "?") for t in active_tasks[:3])
        if len(active_tasks) > 3:
            task_refs += f" +{len(active_tasks)-3}"

        table.add_row(
            icon,
            name[:24],
            f"[{status_color}]{status}[/]",
            hb_str,
            progress,
            task_refs,
        )

    # Badminton coach (special row)
    coach = [a for a in data.agents if a.get("name") == "BadmintonCoach_LuB"]
    if coach:
        c = coach[0]
        table.add_row(
            "🏸",
            "BadmintonCoach_LuB",
            f"[green]{c.get('status', 'active')}[/]",
            _time_ago(c.get("last_heartbeat")),
            "羽球宝统筹",
            "",
        )

    console.print(table)
    console.print()

    # ── Badminton pipeline ──
    render_badminton_pipeline(data)

    # ── Footer ──
    console.print()
    console.print(
        f"[dim]命令: apex monitor status           "
        f"实时: apex monitor status --watch 60           "
        f"JSON: apex monitor status --json[/]"
    )


def render_badminton_pipeline(data: MonitorData):
    """Render the badminton pipeline progress section."""
    cp = data.collection_progress
    if not cp and not data.milestones:
        return

    pct = cp.get("P0_downloaded", 0) / max(1, cp.get("P0_target", 810)) * 100

    # Collection progress bar
    bar_len = 20
    filled = int(bar_len * min(100, pct) / 100)
    bar = "█" * filled + "░" * (bar_len - filled)

    # Clips progress
    clip_max = max(1, cp.get("P0_downloaded", 1))
    clip_pct = min(100, data.clips_total / clip_max * 3)
    c_filled = int(bar_len * min(1, data.clips_total / max(1, 100)))
    c_bar = "█" * c_filled + "░" * (bar_len - c_filled)

    lines = [
        f"采集: [{bar}] {cp.get('P0_downloaded', 0)}/{cp.get('P0_target', '?')} ({pct:.0f}%)",
        f"剪辑: [{c_bar}] {data.clips_total} smart_clips",
        f"任务: {len(data.tasks)}个",
    ]

    # Active tasks
    for s in ["in_progress", "pending"]:
        for t in data.tasks_by_status(s)[:4]:
            tid = t.get("id", "?")
            name = t.get("name", t.get("title", "?"))[:35]
            owner = t.get("owner", "?")[:15]
            lines.append(f"[{s:12s}] {tid:10s} {name:35s} → {owner}")

    # Milestones
    for m in data.milestones[-4:]:
        ms = m.get("status", "?")
        icon = {"completed": "✅", "in_progress": "🔄", "pending": "⏳"}.get(ms, "❓")
        mid = m.get("id", "?")
        name = m.get("name", "?")[:28]
        prog = m.get("progress", "?")
        target = m.get("target", "?")
        lines.append(f"{icon} {mid}: {name:28s} {str(prog):>5s}  Target: {target}")

    console.print(
        Panel("\n".join(lines), title="🏸 羽球宝流水线进度", border_style="green")
    )


def render_json(data: MonitorData) -> None:
    """Output JSON format for dashboard consumption."""
    # Per-agent detail
    agent_detail = []
    for a in data.agents[:15]:
        owner_tasks = data.tasks_by_owner(a.get("name", ""))
        agent_detail.append(
            {
                "name": a.get("name"),
                "status": a.get("status"),
                "hb_age": _time_ago(a.get("last_heartbeat")),
                "tasks_total": len(owner_tasks),
                "tasks_done": sum(
                    1 for t in owner_tasks if t.get("status") == "completed"
                ),
            }
        )

    # Tasks by status
    task_counts = {}
    for t in data.tasks:
        s = t.get("status", "?")
        task_counts[s] = task_counts.get(s, 0) + 1

    output = {
        "timestamp": data.now.isoformat(),
        "agents": {
            "total": len(data.agents),
            "active": len(data.active),
            "warning": len(data.warning),
            "offline": len(data.offline),
            "detail": agent_detail,
        },
        "badminton": {
            "collection": f"{data.collection_progress.get('P0_downloaded', 0)}/{data.collection_progress.get('P0_target', '?')}",
            "clipped": data.collection_progress.get("P0_clipped", 0),
            "smart_clips": data.clips_total,
            "tasks": task_counts,
            "tasks_detail": [
                {
                    "id": t.get("id"),
                    "name": t.get("name", t.get("title")),
                    "status": t.get("status"),
                    "owner": t.get("owner"),
                }
                for t in data.tasks[:20]
            ],
        },
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


# ─── Skills Monitor ──────────────────────────────────────────────

def render_skills_panel() -> None:
    """Render agent skill summary from Hermes profiles and Apex skill registry."""

    console.print()
    console.print(Panel("[bold]🧠 Agent Skills 总览[/]", border_style="cyan"))

    # Scan Hermes profiles for skill count
    profiles_dir = Path.home() / ".hermes" / "profiles"
    agent_skills: dict[str, dict] = {}

    if profiles_dir.exists():
        for pdir in sorted(profiles_dir.iterdir()):
            if not pdir.is_dir():
                continue
            name = pdir.name

            # Count skills
            skills_dir = pdir / "skills"
            skill_count = 0
            if skills_dir.exists():
                skill_count = len(
                    [f for f in skills_dir.rglob("SKILL.md") if f.is_file()]
                )

            # Check SOUL
            soul_file = pdir / "SOUL.md"
            has_soul = soul_file.exists()

            # Check config for model
            model = "?"
            config_file = pdir / "config.yaml"
            if config_file.exists():
                try:
                    import yaml
                    with open(config_file) as f:
                        cfg = yaml.safe_load(f) or {}
                    model = cfg.get("model", {}).get("default", "?")
                except Exception:
                    pass

            agent_skills[name] = {
                "skill_count": skill_count,
                "has_soul": has_soul,
                "model": model,
            }

    if not agent_skills:
        console.print("[dim]No agent profiles found. Run 'apex fleet init' first.[/]")
        return

    table = Table(box=box.ROUNDED, border_style="blue", header_style="bold cyan")
    table.add_column("Agent", style="bold white")
    table.add_column("Skills", justify="center")
    table.add_column("SOUL", justify="center")
    table.add_column("Model", style="dim")
    table.add_column("Wrapper", style="dim")

    for name, info in sorted(agent_skills.items()):
        skill_str = str(info["skill_count"])
        soul_icon = "✅" if info["has_soul"] else "❌"
        wrapper_path = Path.home() / ".local" / "bin" / name
        has_wrapper = "✅" if wrapper_path.exists() else "❌"

        table.add_row(
            name,
            skill_str,
            soul_icon,
            info["model"],
            has_wrapper,
        )

    console.print(table)
    console.print()

    # Global skills count
    global_skills = 0
    if HERMES_SKILLS.exists():
        global_skills = len(
            [f for f in HERMES_SKILLS.rglob("SKILL.md") if f.is_file()]
        )

    console.print(
        f"[dim]Agent profiles: {len(agent_skills)}  │  "
        f"Global skills: {global_skills}  │  "
        f"Skills dir: ~/.hermes/skills/[/]"
    )
    console.print()


# ─── Watch mode ──────────────────────────────────────────────────

def watch_loop(json_output: bool = False, interval: int = 60):
    """Live-refreshing monitor loop."""
    try:
        while True:
            console.clear()
            data = MonitorData.load()
            if json_output:
                render_json(data)
            else:
                render_status_panel(data)
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[dim]👋 退出监控[/]")


# ─── Main entry ─────────────────────────────────────────────────

def cmd_status(json_output: bool = False, watch: int = 0):
    """Entry point for 'apex monitor status'."""
    if watch > 0:
        watch_loop(json_output=json_output, interval=watch)
    else:
        data = MonitorData.load()
        if json_output:
            render_json(data)
        else:
            render_status_panel(data)


def cmd_skills():
    """Entry point for 'apex monitor skills'."""
    render_skills_panel()
