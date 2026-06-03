"""Apex — Fleet Monitor CLI Commands.

Agent status dashboard with real-time state tracking, skill levels,
and interactive detail views.

Commands:
  apex fleet status        — Fleet overview dashboard (live-updating)
  apex fleet show <agent>  — Detailed agent view (role, skills, tasks, stats)
  apex fleet refresh       — Force refresh all agent states
  apex fleet history       — Show recent fleet snapshot history
"""

from __future__ import annotations

import os
import sys
import time
import json
import signal
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.columns import Columns
from rich import box
from rich.progress import Progress, BarColumn, TextColumn
from rich.align import Align

from apex.interface.agent_monitor import (
    get_monitor, FleetMonitor, FleetSnapshot,
    AgentState, AgentStatus, LEVELS, LEVEL_LABELS,
)

console = Console()


# ════════════════════════════════════════════════════════════════
# Dashboard Renderers
# ════════════════════════════════════════════════════════════════


def render_fleet_overview(snapshot: FleetSnapshot) -> None:
    """Render a full fleet overview dashboard."""
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    # ── Header ──
    header = Panel(
        f"[bold]🤖 APEX FLEET COMMAND CENTER[/]          "
        f"[dim]{now}[/]\n"
        f"{snapshot.summary()}",
        border_style="blue",
    )
    console.print(header)
    console.print()

    if not snapshot.agents:
        console.print("[yellow]No agents registered yet. Create profiles with: apex team template <name>[/]")
        return

    # ── State-breakdown cards ──
    by_state = {s: [] for s in AgentState}
    for agent in snapshot.agents.values():
        by_state[agent.state].append(agent)

    state_cards = []
    for state in AgentState:
        agents_in_state = by_state[state]
        if not agents_in_state:
            continue
        names = ", ".join(
            f"{a.emoji}[cyan]{a.name}[/]"
            for a in agents_in_state[:8]
        )
        if len(agents_in_state) > 8:
            names += f" [dim]+{len(agents_in_state)-8} more[/]"
        state_cards.append(Panel(
            f"[bold]{state.emoji} {state.label_cn}[/]  [dim]{len(agents_in_state)} agents[/]\n{names}",
            border_style="green" if state == AgentState.WORKING else (
                "white" if state == AgentState.IDLE else (
                    "yellow" if state == AgentState.WAITING else "red"
                )
            ),
            padding=(1, 2),
            width=40,
        ))

    if state_cards:
        cols = Columns(state_cards, equal=True, expand=True)
        console.print(cols)
        console.print()

    # ── Main Agent Table ──
    table = Table(
        title="👥 Agent Status",
        border_style="cyan", box=box.ROUNDED,
        header_style="bold cyan",
    )
    table.add_column("State", width=3)
    table.add_column("Agent", style="white", no_wrap=True)
    table.add_column("Role", style="dim")
    table.add_column("Active Tasks", justify="center")
    table.add_column("Skills", justify="center")
    table.add_column("Highest Skill", style="yellow")
    table.add_column("Completions", justify="right")
    table.add_column("Idle", justify="right")
    table.add_column("Connection", style="dim")

    for agent in snapshot.agents.values():
        state_icon = agent.state.emoji
        state_style = {
            "working": "green",
            "idle": "white",
            "waiting": "yellow",
            "stopped": "red",
        }.get(agent.state.value, "white")

        # Active tasks display
        if agent.active_tasks:
            task_str = "\n".join(
                f"[cyan]{t.title[:18]}[/] {'█' * int(t.progress_pct // 20)}"
                for t in agent.active_tasks[:2]
            )
            if len(agent.active_tasks) > 2:
                task_str += f"\n[dim]+{len(agent.active_tasks)-2} more[/]"
        else:
            task_str = "[dim]—[/]"

        # Idle time
        if agent.state == AgentState.STOPPED:
            idle_str = "[red]offline[/]"
        elif agent.idle_minutes < 60:
            idle_str = f"[green]{agent.idle_minutes:.0f}m[/]"
        elif agent.idle_minutes < 1440:
            idle_str = f"[yellow]{agent.idle_minutes/60:.1f}h[/]"
        else:
            idle_str = f"[red]{agent.idle_minutes/1440:.1f}d[/]"

        # Connection status
        if agent.wrapper_exists:
            conn_str = "🟢 CLI"
        elif agent.hermes_profile_exists:
            conn_str = "🟡 Profile"
        elif agent.profile_exists:
            conn_str = "🔵 Apex"
        else:
            conn_str = "🔴 None"

        skill_count = str(agent.skill_count) if agent.skill_count > 0 else "[dim]0[/]"

        table.add_row(
            f"[{state_style}]{state_icon}[/]",
            f"[{state_style}]{agent.name}[/]",
            agent.role[:22] if agent.role else "[dim]—[/]",
            task_str or "[dim]—[/]",
            skill_count,
            agent.highest_skill_level,
            str(agent.work_stats.total_completed) if agent.work_stats.total_completed else "[dim]0[/]",
            idle_str,
            conn_str,
        )

    console.print(table)
    console.print()

    # ── Skill summary footer ──
    if snapshot.total_skills > 0:
        console.print(f"[dim]📊 Fleet skill pool: {snapshot.total_skills} skills across {snapshot.total_agents} agents "
                      f"| Avg level: {sum(a.avg_skill_level for a in snapshot.agents.values() if a.avg_skill_level > 0) / max(len([a for a in snapshot.agents.values() if a.avg_skill_level > 0]), 1):.1f}[/]")
    console.print()


def render_agent_detail(agent_name: str) -> None:
    """Render detailed view for a single agent."""
    monitor = get_monitor()
    agent = monitor.get_agent(agent_name, force_refresh=True)
    if not agent:
        console.print(f"[red]Agent '{agent_name}' not found.[/]")
        return

    now = time.strftime("%H:%M:%S")
    state_style = {
        "working": "green",
        "idle": "white",
        "waiting": "yellow",
        "stopped": "red",
    }.get(agent.state.value, "white")

    # ── Identity Panel ──
    lines = [
        f"[bold]{agent.emoji} {agent.role}[/]",
        f"State: [{state_style}]● {agent.state.emoji} {agent.state.label_cn}[/]",
        f"Agent ID: [cyan]{agent.name}[/]",
    ]
    if agent.tags:
        tags_str = " | ".join(agent.tags[:5])
        lines.append(f"Expertise: [dim]{tags_str}[/]")

    # Connection status
    conn_parts = []
    if agent.profile_exists:
        conn_parts.append("✅ Apex Profile")
    if agent.hermes_profile_exists:
        conn_parts.append("✅ Hermes Profile")
    if agent.wrapper_exists:
        conn_parts.append("✅ CLI Wrapper")
    if not conn_parts:
        conn_parts.append("❌ No Profile")
    lines.append(f"Connection: {' | '.join(conn_parts)}")

    if agent.heartbeat_status and agent.heartbeat_status != "unknown":
        hb_color = "green" if agent.heartbeat_status == "healthy" else "red"
        lines.append(f"Heartbeat: [{hb_color}]{agent.heartbeat_status}[/]")

    if agent.last_seen > 0:
        last_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(agent.last_seen))
        lines.append(f"Last active: [dim]{last_str}[/]")

    console.print(Panel(
        "\n".join(lines),
        title=f"🤖 Agent Profile — {agent.name}",
        border_style=state_style,
    ))
    console.print()

    # ── Skills Table ──
    if agent.skill_count > 0:
        try:
            from apex.interface.skill_registry import get_registry
            r = get_registry()
            skills = r.get_agent_skills(agent.name)
        except Exception:
            skills = []

        if skills:
            skill_table = Table(
                title=f"🎯 Skills — {agent.skill_count} total, avg level {agent.avg_skill_level:.1f}, highest {agent.highest_skill_level}",
                border_style="green", box=box.SIMPLE,
            )
            skill_table.add_column("Skill", style="cyan")
            skill_table.add_column("Level", style="yellow")
            skill_table.add_column("Confidence", style="white")
            skill_table.add_column("Evidence", justify="right")

            for s in skills[:10]:
                lvl = s.get("level", "L0")
                conf = s.get("confidence", 0)
                ev = s.get("evidence_count", 0)
                conf_bar = "█" * int(conf * 10) + "░" * (10 - int(conf * 10))
                lvl_label = LEVEL_LABELS.get(lvl, lvl)
                skill_table.add_row(
                    s["skill_name"],
                    f"{lvl} {lvl_label.split('(')[0].strip()}",
                    f"{conf_bar}",
                    f"{'🧾' * min(ev, 3)}{f' +{ev-3}' if ev > 3 else ''}" if ev else "[dim]0[/]",
                )
            console.print(skill_table)
            if len(skills) > 10:
                console.print(f"[dim]... and {len(skills)-10} more skills. Use 'apex skill show {agent.name}' for full list.[/]")
            console.print()

    # ── Active Tasks ──
    if agent.active_tasks:
        task_table = Table(
            title=f"📋 Active Tasks ({len(agent.active_tasks)})",
            border_style="blue", box=box.SIMPLE,
        )
        task_table.add_column("ID", style="dim", width=16)
        task_table.add_column("Title", style="white")
        task_table.add_column("Progress", style="green")
        task_table.add_column("Age", style="yellow")
        task_table.add_column("Priority", style="dim")

        for t in agent.active_tasks:
            bar = "█" * int(t.progress_pct // 10) + "░" * (10 - int(t.progress_pct // 10))
            age_h = t.age_hours
            age_str = f"{age_h:.1f}h" if age_h < 24 else f"{age_h/24:.1f}d"
            priority_str = "🔴" if t.priority == 0 else ("🟡" if t.priority == 1 else "⚪")
            task_table.add_row(
                t.id, t.title[:40],
                f"{bar} {t.progress_pct:.0f}%",
                age_str,
                priority_str,
            )
        console.print(task_table)
        console.print()

    # ── Work Stats ──
    ws = agent.work_stats
    if ws.total_completed > 0 or ws.total_failed > 0:
        total = ws.total_completed + ws.total_failed
        success_pct = ws.total_completed / total * 100 if total > 0 else 0
        success_bar = "🟢" * int(success_pct // 10) + "🔴" * (10 - int(success_pct // 10))

        console.print(Panel(
            f"[bold]📊 Work Statistics[/]\n"
            f"Completed: [green]{ws.total_completed}[/] | Failed: [red]{ws.total_failed}[/] | "
            f"Rate: [{'green' if success_pct > 80 else 'yellow' if success_pct > 50 else 'red'}]{success_pct:.0f}%[/]\n"
            f"{success_bar}\n"
            f"Current idle: {'[green]Active' if agent.idle_minutes < 5 else f'[yellow]{agent.idle_minutes:.0f}m' if agent.idle_minutes < 60 else f'[red]{agent.idle_minutes/60:.1f}h'}[/]\n"
            f"Session started: {time.strftime('%Y-%m-%d %H:%M', time.localtime(agent.current_session_start)) if agent.current_session_start else '[dim]N/A[/]'}",
            title="📈 Performance",
            border_style="cyan",
        ))

    # ── Navigation hint ──
    console.print(f"\n[dim]💡 Tip: Use 'apex fleet status' for overview | 'apex skill show {agent.name}' for full skills | 'apex task list --assignee {agent.name}' for all tasks[/]")


def render_fleet_history(limit: int = 10) -> None:
    """Show recent fleet snapshot history from saved reports."""
    reports_dir = Path.home() / ".apex" / "fleet-reports"
    if not reports_dir.exists():
        console.print("[yellow]No fleet history yet. Run 'apex fleet status' first.[/]")
        return

    reports = sorted(reports_dir.glob("*.json"), reverse=True)
    if not reports:
        console.print("[yellow]No fleet history found.[/]")
        return

    console.print(Panel(
        f"[bold]📜 Fleet History — Last {min(len(reports), limit)} snapshots[/]",
        border_style="blue",
    ))
    console.print()

    table = Table(border_style="cyan", box=box.SIMPLE)
    table.add_column("Time", style="dim")
    table.add_column("Total", justify="right")
    table.add_column("🟢 Working", style="green")
    table.add_column("⚪ Idle", style="white")
    table.add_column("🟡 Waiting", style="yellow")
    table.add_column("🔴 Stopped", style="red")
    table.add_column("Skills", justify="right", style="blue")

    for report_file in reports[:limit]:
        try:
            data = json.loads(report_file.read_text())
            ts = data.get("timestamp", 0)
            time_str = time.strftime("%m-%d %H:%M", time.localtime(ts))
            total = data.get("total_agents", 0)
            working = data.get("working_count", 0)
            idle = data.get("idle_count", 0)
            waiting = data.get("waiting_count", 0)
            stopped = data.get("stopped_count", 0)
            skills = data.get("total_skills", 0)
            table.add_row(time_str, str(total), str(working), str(idle), str(waiting), str(stopped), str(skills))
        except Exception:
            table.add_row(report_file.stem[-16:], "—", "—", "—", "—", "—", "—")

    console.print(table)
    console.print(f"\n[dim]Reports directory: {reports_dir}[/]")


def save_fleet_snapshot(snapshot: FleetSnapshot) -> Path:
    """Save a fleet snapshot as JSON for history."""
    reports_dir = Path.home() / ".apex" / "fleet-reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    report_file = reports_dir / f"fleet-{ts}.json"

    data = {
        "timestamp": snapshot.timestamp,
        "total_agents": snapshot.total_agents,
        "working_count": snapshot.working_count,
        "idle_count": snapshot.idle_count,
        "waiting_count": snapshot.waiting_count,
        "stopped_count": snapshot.stopped_count,
        "total_skills": snapshot.total_skills,
        "agents": {k: v.to_dict() for k, v in snapshot.agents.items()},
    }
    report_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return report_file


# ════════════════════════════════════════════════════════════════
# CLI Commands
# ════════════════════════════════════════════════════════════════


def status_cmd(live: bool = False):
    """Show fleet status dashboard.

    Args:
        live: If True, show a live-updating dashboard (Ctrl+C to exit).
    """
    monitor = get_monitor()

    if live:
        # Live-updating dashboard
        def _render_live():
            snapshot = monitor.snapshot(force_refresh=True)
            return _build_live_dashboard(snapshot)

        try:
            with Live(_render_live(), refresh_per_second=0.5, screen=True) as live_display:
                while True:
                    time.sleep(2)
                    live_display.update(_render_live())
        except KeyboardInterrupt:
            console.print("\n[dim]Live dashboard stopped.[/]")
    else:
        # Static snapshot
        snapshot = monitor.snapshot(force_refresh=True)
        render_fleet_overview(snapshot)

        # Save history
        saved = save_fleet_snapshot(snapshot)
        console.print(f"[dim]Snapshot saved: {saved}[/]")


def _build_live_dashboard(snapshot: FleetSnapshot) -> Table:
    """Build a Rich Table for live display."""
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    table = Table(
        title=f"🤖 APEX FLEET — {now}",
        border_style="cyan", box=box.ROUNDED,
        header_style="bold cyan",
        title_style="bold",
    )
    table.add_column("", width=2)
    table.add_column("Agent", style="white", no_wrap=True)
    table.add_column("Role", style="dim", width=20)
    table.add_column("State", width=10)
    table.add_column("Task", width=22)
    table.add_column("Skills", justify="center", width=6)
    table.add_column("Done", justify="right", width=4)
    table.add_column("Idle", justify="right", width=6)

    for agent in snapshot.agents.values():
        state_style = {
            "working": "green",
            "idle": "white",
            "waiting": "yellow",
            "stopped": "red",
        }.get(agent.state.value, "white")

        # Task progress mini bar
        if agent.active_tasks:
            task_text = agent.active_tasks[0].title[:20]
        else:
            task_text = "[dim]—[/]"

        # Idle time
        if agent.state == AgentState.STOPPED:
            idle_str = "[red]OFF[/]"
        elif agent.idle_minutes < 60:
            idle_str = f"[green]{agent.idle_minutes:.0f}m[/]"
        elif agent.idle_minutes < 1440:
            idle_str = f"[yellow]{agent.idle_minutes/60:.1f}h[/]"
        else:
            idle_str = f"[red]{agent.idle_minutes/1440:.1f}d[/]"

        table.add_row(
            f"[{state_style}]{agent.state.emoji}[/]",
            f"[{state_style}]{agent.name}[/]",
            agent.role[:20] if agent.role else "[dim]—[/]",
            f"[{state_style}]{agent.state.label_cn}[/]",
            task_text,
            str(agent.skill_count),
            str(agent.work_stats.total_completed) if agent.work_stats.total_completed else "0",
            idle_str,
        )

    # Summary footer
    table.caption = (
        f"Total: {snapshot.total_agents} agents | "
        f"🟢 {snapshot.working_count} | "
        f"⚪ {snapshot.idle_count} | "
        f"🟡 {snapshot.waiting_count} | "
        f"🔴 {snapshot.stopped_count} | "
        f"📊 {snapshot.total_skills} skills"
    )

    return table


def show_cmd(agent_name: str):
    """Show detailed view for a specific agent."""
    render_agent_detail(agent_name)


def refresh_cmd():
    """Force refresh all agent states."""
    monitor = get_monitor()
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Scanning fleet...", total=1)
        snapshot = monitor.snapshot(force_refresh=True)
        progress.update(task, completed=1)

    console.print(f"[green]✅ Fleet refreshed: {snapshot.total_agents} agents scanned[/]")
    console.print(snapshot.summary())

    # Save
    saved = save_fleet_snapshot(snapshot)
    console.print(f"[dim]Snapshot saved: {saved}[/]")


def history_cmd(limit: int = 10):
    """Show fleet snapshot history."""
    render_fleet_history(limit=limit)
