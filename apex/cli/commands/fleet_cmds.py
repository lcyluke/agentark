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


def inspect_cmd(project: str = "", pm: str = ""):
    """全舰队巡检 — 项目进度 + Agent任务状态。

    每个项目的PM自动作为巡检Agent:
      🏸 羽球宝AI → badminton-pm
      🦅 Apex      → apex-pm
      💰 FinOps AI → finops-pm
    
    用法:
      apex fleet inspect              # 全项目巡检
      apex fleet inspect -p finopsai  # 单项目巡检
      apex fleet inspect -p badminton-coach-ai -pm badminton-pm  # 指定PM巡检
    """
    import subprocess
    
    cmd = ["python3", os.path.expanduser("~/.hermes/scripts/fleet_inspector.py")]
    if project:
        cmd.extend(["--project", project])
    if pm:
        cmd.extend(["--pm", pm])
    
    console.print(f"\n[bold cyan]⚓ 舰队巡检中...[/]")
    if project:
        from apex.orchestration.pipeline import PROJECT_AGENT_MAP
        proj_name = {"badminton-coach-ai": "🏸 羽球宝AI", "apex": "🦅 Apex", 
                     "finopsai": "💰 FinOps AI", "shenzhen-badminton": "🗺️ 深圳地图"}.get(project, project)
        pm_default = {"badminton-coach-ai": "badminton-pm", "apex": "apex-pm",
                      "finopsai": "finops-pm"}.get(project, "default")
        console.print(f"[dim]项目: {proj_name} | 巡检官: {pm or pm_default}[/]\n")
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.stdout.strip():
        console.print(result.stdout)
    else:
        console.print("[dim]所有项目无活动，舰队平稳 ⚓[/]")


# ════════════════════════════════════════════════════════════════
# 一体化舰队命令 — apex fleet deploy
# ════════════════════════════════════════════════════════════════


def deploy_cmd(
    requirement: str,
    project: str = "default",
    template: str = "webapp",
    auto_mode: bool = True,
    mode: str = "pipeline",
):
    """一键部署开发舰队：建队 → 拆解需求 → 分派任务 → 显示状态。

    Flow:
      1. 从模板创建团队（如尚不存在）
      2. AI 拆解需求
      3. 创建 Task + 自动分派
      4. 舰队启动提示
      5. 状态总览
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

    console.print(Panel.fit(
        "[bold cyan]⚓ 舰队部署 — 一体化开发舰队[/]\n"
        f"[dim]项目: {project} | 模板: {template} | 模式: {mode}[/]",
        border_style="cyan",
    ))
    console.print()

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        console=console,
        transient=True,
    )

    with progress:
        # Step 1: 检查团队 — 从模板创建
        t1 = progress.add_task("[cyan]1/4 检查团队状态...", total=100)
        import subprocess as sp
        r = sp.run(
            [sys.executable, "-m", "apex", "team", "template", template],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0:
            progress.update(t1, completed=60, description="[green]✅ 团队已创建[/]")
        else:
            progress.update(t1, completed=60, description="[yellow]⚠️ 团队创建跳过 (可能已存在)[/]")
        time.sleep(0.3)
        progress.update(t1, completed=100)

        # Step 2: 分析拆解需求
        t2 = progress.add_task("[cyan]2/4 AI 分析拆解需求...", total=100)
        from apex.orchestration.task_decomposer import decompose_requirement, dispatch_tasks
        from apex.orchestration.task_manager import get_task_manager

        tm = get_task_manager()
        result = decompose_requirement(requirement, project)
        progress.update(t2, completed=60, description=f"[green]📋 {result.epic_title}[/]")
        time.sleep(0.2)
        progress.update(t2, completed=100)

        # Step 3: 创建任务并分派
        t3 = progress.add_task("[cyan]3/4 创建任务并分派...", total=100)
        dispatch_result = dispatch_tasks(result, tm)
        task_count = dispatch_result.get("dispatched", 0)
        progress.update(t3, completed=80, description=f"[green]✅ {task_count} 个任务已创建并分派[/]")
        time.sleep(0.2)
        progress.update(t3, completed=100)

        # Step 4: 舰队启动就绪
        t4 = progress.add_task("[cyan]4/4 舰队就绪检查...", total=100)
        # Check squad agents
        squad_profiles = ["frontend-dev", "backend-dev", "fullstack-dev", "architect", "devops"]
        squad_dir = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))) / "profiles"
        existing = [p for p in squad_profiles if (squad_dir / p).exists()]
        progress.update(t4, completed=80, description=f"[green]✅ {len(existing)}/{len(squad_profiles)} 开发Agent就绪[/]")
        time.sleep(0.2)
        progress.update(t4, completed=100)

    console.print()

    # ── 结果展示 ──
    from rich.table import Table

    # 分解结果表
    table = Table(title=f"📋 任务清单 — {result.epic_title}", box=box.ROUNDED, border_style="cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("任务", width=38)
    table.add_column("分派至", width=18)
    table.add_column("工时", width=6, justify="right")
    table.add_column("优先级", width=8, justify="center")

    prio_icons = {0: "🔴 阻塞", 1: "🟠 高", 2: "🟡 中", 3: "🟢 低"}
    for i, t in enumerate(result.tasks, 1):
        table.add_row(
            str(i),
            t.title[:36],
            t.assignee or "[dim]待分配[/]",
            f"{t.estimated_hours:.0f}h",
            prio_icons.get(t.priority, "⚪"),
        )
    console.print(table)

    # 舰队状况
    from apex.interface.agent_monitor import get_monitor
    monitor = get_monitor()
    snapshot = monitor.snapshot()

    fleet_table = Table(title="🤖 舰队状况", box=box.ROUNDED, border_style="cyan")
    fleet_table.add_column("", width=4, justify="center")
    fleet_table.add_column("Agent", width=22)
    fleet_table.add_column("状态", width=12)
    fleet_table.add_column("技能", width=6, justify="center")
    fleet_table.add_column("级别", width=4, justify="center")
    fleet_table.add_column("已完任务", width=10, justify="center")

    from apex.cli.commands.squad_cmds import DEV_SQUAD
    for name, info in DEV_SQUAD.items():
        agent = snapshot.agents.get(name)
        if agent:
            state_str = f"[green]● 在线[/]" if agent.state.value == "working" else (
                f"[yellow]● 待命[/]" if agent.state.value == "idle" else
                f"[dim]○ 离线[/]"
            )
            skill_count = len(getattr(agent, 'skills', [])) or (info.get('skill_count', 8))
            level = getattr(agent, 'level', 'L2')
        else:
            state_str = "[dim]○ 未启动[/]"
            skill_count = info.get('skill_count', 8)
            level = "L2"

        badge = info.get("badge", "●")
        fleet_table.add_row(
            badge,
            name,
            state_str,
            str(skill_count),
            level,
            str(info.get('completed', 0)),
        )

    console.print(fleet_table)

    # 执行建议
    console.print(Panel(
        "[bold]🚀 立即执行[/]\n\n"
        f"[cyan]apex dispatch[/]      — 自动分派等待任务\n"
        f"[cyan]apex task epic[/]     — 查看史诗任务树\n"
        f"[cyan]apex schedule view[/] — 甘特图排期\n"
        f"[cyan]apex squad start[/]   — 启动开发Agent终端\n"
        f"[cyan]apex chain run[/] \"{result.epic_title}\" -p dev  — 序列链开发\n\n"
        f"[dim]授权: 关键节点需PM/Origin审批 — 半自动模式已启用[/]",
        title="⚓ Fleet Deploy Complete",
        border_style="green",
    ))

    return {
        "epic_title": result.epic_title,
        "task_count": task_count,
        "tasks": result.tasks,
        "dispatch": dispatch_result,
    }


# ════════════════════════════════════════════════════════════════
# Multi-Mac Fleet Commands (fleet-init, fleet-join, fleet-sync)
# ════════════════════════════════════════════════════════════════

def fleet_init_cmd(
    fleet_name: str = "老卢舰队",
    repo_url: str = "https://github.com/lcyluke/hermes-fleet-config.git",
    force: bool = False,
):
    """Initialize this Mac as fleet Origin."""
    from apex.interface.fleet_multi_mac import fleet_init

    console.print(Panel(
        f"[bold]⚓ 初始化舰队 Origin[/]\n\n"
        f"舰队: [cyan]{fleet_name}[/]\n"
        f"机器: [green]{fleet_init.__module__}[/]\n"
        f"配置仓库: [dim]{repo_url}[/]",
        title="Fleet Init", border_style="cyan",
    ))

    result = fleet_init(fleet_name=fleet_name, repo_url=repo_url, force=force)

    if "error" in result:
        console.print(f"[red]✗ {result['error']}[/]")
        return

    for step in result["steps"]:
        console.print(f"  {step}")

    console.print(f"\n[bold green]✅ Fleet Origin 就绪！[/]")
    console.print(f"  角色: [cyan]ORIGIN[/] (始祖)")
    console.print(f"  机器: {result['machine_id']}")
    console.print(f"\n[dim]下一步: 在 Worker Mac 上运行 'apex fleet-join'[/]")
    console.print(f"[dim]配置仓库: {repo_url}[/]")


def fleet_join_cmd(
    repo_url: str = "https://github.com/lcyluke/hermes-fleet-config.git",
    force: bool = False,
):
    """Join an existing fleet as Worker node."""
    from apex.interface.fleet_multi_mac import fleet_join, get_machine_id

    console.print(Panel(
        f"[bold]🔗 加入舰队[/]\n\n"
        f"配置仓库: [dim]{repo_url}[/]\n"
        f"机器: [green]{get_machine_id()}[/]",
        title="Fleet Join", border_style="cyan",
    ))

    result = fleet_join(repo_url=repo_url, force=force)

    if "error" in result:
        console.print(f"[red]✗ {result['error']}[/]")
        return

    for step in result["steps"]:
        console.print(f"  {step}")

    console.print(f"\n[bold green]✅ 已加入舰队！[/]")
    console.print(f"  角色: [yellow]WORKER[/] (执行舰)")
    console.print(f"  机器: {result['machine_id']}")
    if "next" in result:
        console.print(f"\n[dim]{result['next']}[/]")


def fleet_sync_cmd(direction: str = "pull"):
    """Sync fleet config with central repo."""
    from apex.interface.fleet_multi_mac import fleet_sync, get_fleet_config

    cfg = get_fleet_config()
    role = cfg.get("role") or "unknown"

    direction_text = "拉取" if direction == "pull" else "推送"
    console.print(f"[bold]🔄 舰队同步 — {direction_text}[/]")
    console.print(f"  角色: [cyan]{role.upper()}[/]")

    result = fleet_sync(direction=direction)

    if "error" in result:
        console.print(f"[red]✗ {result['error']}[/]")
        return

    for step in result["steps"]:
        console.print(f"  {step}")

    if result.get("last_sync"):
        console.print(f"  📅 上次同步: {result['last_sync']}")


def fleet_nodes_cmd():
    """Show all fleet nodes (multi-Mac status) — reads from GitHub-synced nodes/."""
    from apex.interface.fleet_multi_mac import fleet_status as multi_status, get_fleet_config, get_all_nodes
    from rich.table import Table

    cfg = get_fleet_config()
    role = cfg.get("role") or "unconfigured"

    # Pull latest node statuses from GitHub first
    if cfg.get("role"):
        import subprocess
        from pathlib import Path as P
        git_dir = P(os.path.expanduser("~/.hermes/.git"))
        if git_dir.exists():
            subprocess.run(
                ["git", "pull", "--rebase", "origin", "main"],
                cwd=git_dir.parent, capture_output=True, timeout=30,
            )

    all_nodes = get_all_nodes()

    console.print(Panel(
        f"[bold]⚓ 舰队节点状态[/]\n\n"
        f"舰队: [cyan]{cfg.get('fleet_name', 'unknown')}[/]\n"
        f"当前机器: [green]{cfg.get('machine_id', 'unknown')}[/]\n"
        f"角色: [bold]{role.upper()}[/]\n"
        f"已知节点: [yellow]{len(all_nodes)}台[/]",
        title="Fleet Nodes", border_style="blue",
    ))

    if not all_nodes:
        console.print("[dim]暂无远程节点。Worker 运行 'apex fleet report' 后此处可见。[/]")
        return

    t = Table(title="🖥 舰队节点", box=None)
    t.add_column("", style="bold")
    t.add_column("机器", style="cyan", width=22)
    t.add_column("角色", style="bold")
    t.add_column("项目", style="green")
    t.add_column("GPU", style="yellow")
    t.add_column("心跳", style="dim")

    role_icon = {"origin": "⚓", "worker": "🔧", None: "❓"}
    for node in all_nodes:
        nrole = node.get("role")
        icon = role_icon.get(nrole, "❓")
        local_mark = " ◀" if node.get("is_local") else ""
        reported = node.get("reported_at", node.get("last_sync", "?"))
        if reported and len(str(reported)) > 16:
            reported = str(reported)[:16]
        projects_str = ", ".join(node.get("projects", [])[:3]) or "—"

        # GPU info
        gpu = node.get("gpu", {})
        if gpu:
            util = gpu.get("util_pct", 0)
            temp = gpu.get("temp_c", 0)
            mem = gpu.get("mem_pct", 0)
            gpu_str = f"{util:.0f}% {temp}°C"
        else:
            gpu_str = "—"

        t.add_row(
            icon,
            str(node.get("machine_id", "?"))[:20] + local_mark,
            (nrole or "?").upper(),
            projects_str,
            gpu_str,
            str(reported),
        )

    console.print(t)

    # GPU alerts
    for node in all_nodes:
        alerts = node.get("gpu_alerts", [])
        if alerts:
            for alert in alerts:
                console.print(f"  {alert}")

    console.print("\n[dim]Worker 运行 'apex fleet report' 上报心跳+GPU → Origin 全览[/]")
    console.print("[dim]配置中心: https://github.com/lcyluke/hermes-fleet-config[/]")


def fleet_gpu_status_cmd():
    """Show GPU status across all fleet nodes."""
    from apex.interface.fleet_multi_mac import get_fleet_config, get_all_nodes, _probe_gpu
    from rich.table import Table
    from rich.panel import Panel
    import subprocess
    from pathlib import Path as P

    cfg = get_fleet_config()

    # Pull latest
    if cfg.get("role"):
        git_dir = P(os.path.expanduser("~/.hermes/.git"))
        if git_dir.exists():
            subprocess.run(
                ["git", "pull", "--rebase", "origin", "main"],
                cwd=git_dir.parent, capture_output=True, timeout=30,
            )

    all_nodes = get_all_nodes()
    local_gpu = _probe_gpu()

    console.print(Panel(
        f"[bold]🖥 舰队 GPU 资源中心[/]\n\n"
        f"节点: [yellow]{len(all_nodes)}台[/]  |  "
        f"本机 GPU: [green]{local_gpu.get('util_pct', 'N/A')}%[/]" if local_gpu else "本机: 无GPU",
        title="GPU Status", border_style="cyan",
    ))

    if not all_nodes:
        console.print("[dim]暂无节点数据。运行 'apex fleet report' 上报。[/]")
        return

    t = Table(title="GPU 节点详情", box=None)
    t.add_column("节点", style="cyan", width=22)
    t.add_column("GPU", style="white", width=18)
    t.add_column("利用率", style="bold")
    t.add_column("显存", style="yellow")
    t.add_column("温度", style="red")
    t.add_column("状态", style="bold")

    for node in all_nodes:
        gpu = node.get("gpu", {})
        if not gpu:
            t.add_row(
                str(node.get("machine_id", "?"))[:20],
                "—", "—", "—", "—", "⚪ 无GPU"
            )
            continue

        util = gpu.get("util_pct", 0)
        if util >= 90:
            status = "🔴 满载"
            util_style = f"[red]{util:.0f}%[/]"
        elif util < 30:
            status = "🟡 空闲"
            util_style = f"[yellow]{util:.0f}%[/]"
        elif util < 5:
            status = "⚪ 休眠"
            util_style = f"[dim]{util:.0f}%[/]"
        else:
            status = "🟢 正常"
            util_style = f"[green]{util:.0f}%[/]"

        t.add_row(
            str(node.get("machine_id", "?"))[:20],
            ", ".join(gpu.get("gpu_names", ["?"]))[:16],
            util_style,
            f"{gpu.get('mem_used_mb',0)}/{gpu.get('mem_total_mb',0)} MB",
            f"{gpu.get('temp_c',0)}°C",
            status,
        )

    console.print(t)


def fleet_report_cmd():
    """Report node heartbeat to fleet — includes GPU status + alerts."""
    from apex.interface.fleet_multi_mac import fleet_report, get_fleet_config, fleet_status

    cfg = get_fleet_config()
    console.print(f"[bold]📡 上报节点心跳[/]")
    console.print(f"  机器: [cyan]{cfg.get('machine_id')}[/]")
    console.print(f"  角色: [bold]{(cfg.get('role') or '?').upper()}[/]")

    # Show GPU status
    status = fleet_status()
    gpu = status.get("gpu", {})
    if gpu:
        console.print(f"  GPU: [yellow]{gpu.get('util_pct', 0):.0f}%[/] | "
                     f"显存 {gpu.get('mem_pct', 0):.0f}% | "
                     f"{gpu.get('temp_c', 0)}°C | "
                     f"{', '.join(gpu.get('gpu_names', ['?']))}")

    result = fleet_report()

    if "error" in result:
        console.print(f"[red]✗ {result['error']}[/]")
        return

    if result.get("push_ok"):
        console.print(f"  ✅ 状态已推送到 GitHub")

        # GPU alerts
        alerts = status.get("gpu_alerts", [])
        if alerts:
            console.print("")
            for alert in alerts:
                console.print(f"  {alert}")
    else:
        console.print(f"  ⚠️ 推送可能失败，检查网络后重试")
