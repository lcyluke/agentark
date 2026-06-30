"""Apex — Autonomous Engine CLI commands"""
from __future__ import annotations

import time
from datetime import datetime, timedelta

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.progress import BarColumn, Progress, TextColumn
from rich.text import Text
from rich import box

from agentark.orchestration.autonomous import get_engine, AutonomousEngine

console = Console()


def _get_engine() -> AutonomousEngine:
    """Return the global autonomous engine singleton."""
    return get_engine()


def _format_uptime(seconds: float) -> str:
    """Format seconds into human-readable uptime string."""
    delta = timedelta(seconds=int(seconds))
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def _status_emoji(status: str) -> str:
    """Map status string to emoji indicator."""
    mapping = {
        "healthy": "🟢",
        "degraded": "🟡",
        "stalled": "🔴",
        "offline": "⚫",
        "running": "🟢",
        "paused": "🟡",
        "stopped": "🔴",
    }
    return mapping.get(status, "⚪")


def _status_text(status: str, uppercase: bool = True) -> str:
    """Return colored status text."""
    colors = {
        "healthy": "green",
        "degraded": "yellow",
        "stalled": "red",
        "offline": "white",
        "running": "green",
        "paused": "yellow",
        "stopped": "red",
    }
    color = colors.get(status, "white")
    text = status.upper() if uppercase else status
    return f"[{color}]{text}[/]"


# ════════════════════════════════════════════════════════════════════
# start_cmd
# ════════════════════════════════════════════════════════════════════


def start_cmd() -> None:
    """Start the autonomous engine (7x24 mode)."""
    engine = _get_engine()

    if engine.is_running:
        console.print("[yellow]⚠ Autonomous Engine is already running.[/]")
        return

    engine.start()
    console.print("[bold green]✅ Autonomous Engine started — 7x24 operation mode[/]")
    console.print(f"   Uptime tracking began at {datetime.now().strftime('%H:%M:%S')}")


# ════════════════════════════════════════════════════════════════════
# stop_cmd
# ════════════════════════════════════════════════════════════════════


def stop_cmd() -> None:
    """Stop the autonomous engine."""
    engine = _get_engine()

    if not engine.is_running:
        console.print("[yellow]⚠ Autonomous Engine is not running.[/]")
        return

    uptime = _format_uptime(engine.uptime)
    engine.stop()
    console.print("[bold red]⏹  Autonomous Engine stopped[/]")
    console.print(f"   Total uptime this session: {uptime}")


# ════════════════════════════════════════════════════════════════════
# pause_cmd
# ════════════════════════════════════════════════════════════════════


def pause_cmd() -> None:
    """Pause task dispatch (heartbeat continues)."""
    engine = _get_engine()

    if not engine.is_running:
        console.print("[yellow]⚠ Engine is not running. Start it first with 'apex autonomous start'[/]")
        return

    engine.pause()
    console.print("[yellow]⏸  Task dispatch paused[/]")
    console.print("   [dim]Heartbeat monitoring and scheduling continue normally.[/]")


# ════════════════════════════════════════════════════════════════════
# resume_cmd
# ════════════════════════════════════════════════════════════════════


def resume_cmd() -> None:
    """Resume task dispatch."""
    engine = _get_engine()

    if not engine.is_running:
        console.print("[yellow]⚠ Engine is not running. Start it first with 'apex autonomous start'[/]")
        return

    engine.resume()
    console.print("[bold green]▶  Task dispatch resumed[/]")


# ════════════════════════════════════════════════════════════════════
# status_cmd
# ════════════════════════════════════════════════════════════════════


def status_cmd() -> None:
    """Show full autonomous report with rich visual elements."""
    engine = _get_engine()
    report = engine.generate_report()

    # ── Layout ──────────────────────────────────────────────────
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=6),
        Layout(name="body"),
    )

    # ── Header: Big Colored Indicator ───────────────────────────
    status_icon = _status_emoji(report.engine_status)
    status_color = {
        "running": "bold green",
        "paused": "bold yellow",
        "stopped": "bold red",
        "degraded": "bold yellow",
    }.get(report.engine_status, "bold white")

    uptime_str = _format_uptime(report.uptime_seconds)

    indicator = Panel(
        f"{status_icon}  [bold]ENGINE STATUS: [{status_color}]{report.engine_status.upper()}[/][/]\n"
        f"   [dim]Uptime:[/] {uptime_str}     "
        f"[dim]Queue:[/] {report.pending_queue} pending     "
        f"[dim]Total Exec:[/] {report.tasks_executed_total}     "
        f"[dim]Knowledge:[/] {report.knowledge_nodes} nodes",
        title="🤖 Autonomous Engine",
        border_style=status_color.split()[-1],
        padding=(1, 2),
    )
    console.print(indicator)

    # ── Active Agents Heartbeat Table ───────────────────────────
    if report.active_agents:
        agent_table = Table(
            title="💓 Active Agents — Heartbeat Status",
            box=box.ROUNDED,
            border_style="cyan",
            header_style="bold cyan",
        )
        agent_table.add_column("Agent", style="bold white")
        agent_table.add_column("Status", justify="center")
        agent_table.add_column("Load", justify="center")
        agent_table.add_column("Tasks Done", justify="right")
        agent_table.add_column("Last Active", justify="center")
        agent_table.add_column("Message", style="dim")

        now = time.time()
        for hb in report.active_agents:
            status_dot = _status_emoji(hb.status)
            # Load bar
            load_pct = min(hb.load, 1.0)
            bar_blocks = int(load_pct * 10)
            load_bar = "█" * bar_blocks + "░" * (10 - bar_blocks)
            load_color = "green" if load_pct < 0.5 else ("yellow" if load_pct < 0.8 else "red")
            load_display = f"[{load_color}]{load_bar}[/] {load_pct:.0%}"

            # Last active
            if hb.last_active > 0:
                ago = now - hb.last_active
                if ago < 60:
                    last_active = "just now"
                elif ago < 3600:
                    last_active = f"{int(ago/60)}m ago"
                else:
                    last_active = f"{int(ago/3600)}h ago"
            else:
                last_active = "—"

            agent_table.add_row(
                hb.agent_name,
                status_dot,
                load_display,
                str(hb.tasks_completed),
                last_active,
                hb.message,
            )

        console.print()
        console.print(agent_table)
    else:
        console.print()
        console.print(Panel(
            "[dim]No active agents reporting heartbeats yet.[/]",
            title="💓 Active Agents",
            border_style="dim",
        ))

    # ── Scheduled Tasks Table ───────────────────────────────────
    if report.scheduled_tasks:
        sched_table = Table(
            title="📅 Scheduled Tasks",
            box=box.ROUNDED,
            border_style="blue",
            header_style="bold blue",
        )
        sched_table.add_column("Name", style="bold white")
        sched_table.add_column("Cron", style="cyan")
        sched_table.add_column("Next Run", justify="center")
        sched_table.add_column("Last Result", style="dim", max_width=40)
        sched_table.add_column("Success Rate", justify="center")

        now = time.time()
        for st in report.scheduled_tasks:
            if not st.enabled:
                continue

            # Next run
            if st.next_run > 0:
                remaining = st.next_run - now
                if remaining <= 0:
                    next_str = "[yellow]due now[/]"
                elif remaining < 60:
                    next_str = f"[dim]{int(remaining)}s[/]"
                elif remaining < 3600:
                    next_str = f"[dim]{int(remaining/60)}m[/]"
                else:
                    next_str = f"[dim]{int(remaining/3600)}h[/]"
            else:
                next_str = "—"

            # Success rate
            if st.run_count > 0:
                rate = st.success_count / st.run_count
                rate_color = "green" if rate >= 0.8 else ("yellow" if rate >= 0.5 else "red")
                rate_str = f"[{rate_color}]{rate:.0%}[/] ({st.success_count}/{st.run_count})"
            else:
                rate_str = "[dim]—[/]"

            # Last result (truncate)
            last_res = (st.last_result or "—")[:40]

            sched_table.add_row(
                st.name,
                st.cron_expr,
                next_str,
                last_res,
                rate_str,
            )

        console.print()
        console.print(sched_table)
    else:
        console.print()
        console.print(Panel(
            "[dim]No scheduled tasks configured.[/]",
            title="📅 Scheduled Tasks",
            border_style="dim",
        ))

    # ── Alert Feed ──────────────────────────────────────────────
    if report.alerts:
        alert_panel_lines = []
        for alert in report.alerts[:5]:
            if "ERROR" in alert or "FAIL" in alert:
                prefix = "[red]🔴[/]"
            elif "WARN" in alert:
                prefix = "[yellow]🟡[/]"
            else:
                prefix = "[cyan]🔵[/]"
            alert_panel_lines.append(f"  {prefix} {alert[:90]}")

        console.print()
        console.print(Panel(
            "\n".join(alert_panel_lines),
            title="🔔 Alert Feed (last 5)",
            border_style="yellow",
        ))
    else:
        console.print()
        console.print(Panel(
            "[green]✅ No unresolved alerts[/]",
            title="🔔 Alert Feed",
            border_style="green",
        ))

    # ── AI-Powered Recommendations ──────────────────────────────
    if report.recommendations:
        rec_lines = []
        for i, rec in enumerate(report.recommendations, 1):
            rec_lines.append(f"  [bold cyan]{i}.[/] {rec}")
        console.print()
        console.print(Panel(
            "\n".join(rec_lines),
            title="🧠 AI-Powered Recommendations",
            border_style="cyan",
        ))
    else:
        console.print()
        console.print(Panel(
            "[dim]No recommendations at this time. Everything looks healthy.[/]",
            title="🧠 Recommendations",
            border_style="dim",
        ))

    # ── Summary Footer ──────────────────────────────────────────
    console.print()
    console.print(
        f"[dim]Knowledge Graph:[/] {report.knowledge_nodes} nodes  "
        f"[dim]Evolution Patterns:[/] {report.evolution_patterns}  "
        f"[dim]Failed Tasks:[/] {'[red]' if report.tasks_failed > 0 else '[green]'}{report.tasks_failed}[/]  "
        f"[dim]Queue Wait:[/] {report.average_queue_wait_ms:.0f}ms"
    )


# ════════════════════════════════════════════════════════════════════
# schedule_cmd
# ════════════════════════════════════════════════════════════════════


def schedule_cmd(name: str, cron: str, task: str, agent: str = "") -> None:
    """Schedule a recurring task on the autonomous engine.

    Args:
        name: Human-readable name for this schedule.
        cron: Cron expression or human-readable interval
              (e.g. '*/5 * * * *', 'every 30m', 'every 2h').
        task: Description of the task to execute.
        agent: Agent profile to assign (optional, uses default if empty).
    """
    engine = _get_engine()
    scheduled = engine.schedule(
        name=name,
        cron_expr=cron,
        task_description=task,
        assigned_agent=agent,
        priority=2,
    )

    # Format next run for display
    next_run_dt = datetime.fromtimestamp(scheduled.next_run)
    next_run_str = next_run_dt.strftime("%Y-%m-%d %H:%M:%S")
    now = time.time()
    delta = scheduled.next_run - now
    if delta > 0:
        if delta < 60:
            from_now = f"in {int(delta)}s"
        elif delta < 3600:
            from_now = f"in {int(delta/60)}m"
        else:
            from_now = f"in {int(delta/3600)}h"

    console.print(f"[bold green]✅ Scheduled task:[/] [bold]{name}[/]")
    console.print(f"   [dim]ID:[/] {scheduled.id}")
    console.print(f"   [dim]Cron:[/] {cron}")
    console.print(f"   [dim]Agent:[/] {agent or 'default'}")
    console.print(f"   [dim]Next Run:[/] {next_run_str} ({from_now})")


# ════════════════════════════════════════════════════════════════════
# unschedule_cmd
# ════════════════════════════════════════════════════════════════════


def unschedule_cmd(task_id: str) -> None:
    """Remove a scheduled task by its ID.

    Args:
        task_id: The ID of the scheduled task to remove.
    """
    engine = _get_engine()
    engine.unschedule(task_id)
    console.print(f"[bold yellow]🗑  Unscheduled task:[/] [bold]{task_id}[/]")


# ════════════════════════════════════════════════════════════════════
# list_scheduled_cmd
# ════════════════════════════════════════════════════════════════════


def list_scheduled_cmd() -> None:
    """List all scheduled tasks with their status."""
    engine = _get_engine()
    tasks = engine.list_scheduled()

    if not tasks:
        console.print("[yellow]⚠ No scheduled tasks found.[/]")
        console.print("   Use [bold]'apex autonomous schedule <name> <cron> <task>'[/] to add one.")
        return

    table = Table(
        title=f"📅 Scheduled Tasks ({len(tasks)} total)",
        box=box.ROUNDED,
        border_style="blue",
        header_style="bold blue",
    )
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name", style="bold white")
    table.add_column("Cron", style="cyan")
    table.add_column("Agent", style="green")
    table.add_column("Enabled", justify="center")
    table.add_column("Runs", justify="right")
    table.add_column("Success %", justify="center")
    table.add_column("Next Run", justify="center")

    now = time.time()
    for st in tasks:
        enabled = "✅" if st.enabled else "❌"

        if st.run_count > 0:
            rate = st.success_count / st.run_count
            rate_color = "green" if rate >= 0.8 else ("yellow" if rate >= 0.5 else "red")
            rate_str = f"[{rate_color}]{rate:.0%}[/]"
        else:
            rate_str = "[dim]—[/]"

        # Next run
        if st.next_run > 0 and st.enabled:
            remaining = st.next_run - now
            if remaining <= 0:
                next_str = "[yellow]due[/]"
            elif remaining < 60:
                next_str = f"[dim]{int(remaining)}s[/]"
            elif remaining < 3600:
                next_str = f"[dim]{int(remaining/60)}m[/]"
            elif remaining < 86400:
                next_str = f"[dim]{int(remaining/3600)}h[/]"
            else:
                next_str = f"[dim]{int(remaining/86400)}d[/]"
        else:
            next_str = "[dim]—[/]"

        table.add_row(
            st.id,
            st.name,
            st.cron_expr,
            st.assigned_agent or "default",
            enabled,
            str(st.run_count),
            rate_str,
            next_str,
        )

    console.print()
    console.print(table)
    console.print()


# ════════════════════════════════════════════════════════════════════
# alerts_cmd
# ════════════════════════════════════════════════════════════════════


def alerts_cmd() -> None:
    """Show unresolved alerts from the autonomous engine."""
    engine = _get_engine()
    alerts = engine.get_alerts(unresolved_only=True, limit=20)

    if not alerts:
        console.print(Panel(
            "[green]✅ No unresolved alerts[/]",
            title="🔔 Alerts",
            border_style="green",
        ))
        return

    table = Table(
        title=f"🔔 Unresolved Alerts ({len(alerts)})",
        box=box.ROUNDED,
        border_style="yellow",
        header_style="bold yellow",
    )
    table.add_column("Severity", justify="center")
    table.add_column("Source", style="cyan")
    table.add_column("Message", style="white")
    table.add_column("Time", style="dim", justify="center")

    for alert in alerts:
        sev = alert["severity"].lower()
        if sev == "error":
            sev_display = "[red]🔴 ERROR[/]"
        elif sev == "warning":
            sev_display = "[yellow]🟡 WARN[/]"
        elif sev == "info":
            sev_display = "[cyan]🔵 INFO[/]"
        else:
            sev_display = f"[white]{sev.upper()}[/]"

        # Format time
        try:
            alert_time = datetime.fromtimestamp(alert["time"])
            time_str = alert_time.strftime("%H:%M:%S")
        except (OSError, ValueError, TypeError):
            time_str = "—"

        table.add_row(
            sev_display,
            alert["source"],
            alert["message"][:80],
            time_str,
        )

    console.print()
    console.print(table)
    console.print()
    console.print("[dim]Use 'apex autonomous resolve <alert_id>' to mark alerts as resolved.[/]")
