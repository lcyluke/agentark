"""Apex Ops — CLI Commands for Multi-Agent Operations

Commands:
  apex ops release create <version>  — Start a new release pipeline
  apex ops release status             — Current release status
  apex ops bug list                   — List bugs
  apex ops bug create <title>         — Report a bug
  apex ops bug show <id>              — Bug details
  apex ops task list                  — List ops tasks
  apex ops task create <title>        — Create an ops task
  apex ops status                     — Ops dashboard summary
  apex ops expert list                — Open expert tickets
"""
from __future__ import annotations

import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.layout import Layout
from rich import box

from apex.orchestration.ops import get_ops, BugSeverity, TaskStatus, OpsManager

console = Console()


def status_cmd():
    """Ops dashboard summary"""
    ops = get_ops()
    stats = ops.get_dashboard_stats()

    # Tasks card
    t = stats["tasks"]
    table = Table(title="📋 Tasks", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Total", str(t["total"]))
    table.add_row("Done", str(t["done"]))
    table.add_row("Blocked", f"[red]{t['blocked']}[/red]")
    table.add_row("Completion", f"{t['completion_pct']}%")
    console.print(table)

    # Bugs card
    b = stats["bugs"]
    bug_table = Table(title="🐛 Bugs", box=box.ROUNDED)
    bug_table.add_column("Metric", style="cyan")
    bug_table.add_column("Value", style="green")
    bug_table.add_row("Open", str(b["open"]))
    bug_table.add_row("Critical", f"[red]{b['critical']}[/red]")
    bug_table.add_row("SLA Breached", f"[red]{b['sla_breached']}[/red]")
    console.print(bug_table)

    # Releases card
    r = stats["releases"]
    rel_table = Table(title="🚀 Releases", box=box.ROUNDED)
    rel_table.add_column("Metric", style="cyan")
    rel_table.add_column("Value", style="green")
    rel_table.add_row("Active", str(r["active"]))
    console.print(rel_table)

    # Expert tickets
    e = stats["expert_tickets"]
    console.print(Panel(f"🧠 Open Expert Tickets: {e['open']}",
                        title="Expert Consultation", border_style="yellow"))

    # Active agents
    agents = stats.get("active_agents", [])
    if agents:
        console.print(f"🟢 Active Agents: {', '.join(agents)}")
    else:
        console.print("⚪ No agents currently active")


def release_create_cmd(version: str, name: str = ""):
    """Create a new release pipeline"""
    ops = get_ops()
    release = ops.create_release(version, name)
    console.print(Panel(f"🚀 Release {release.version} created!",
                        subtitle=release.id, border_style="green"))

    # Show stages
    table = Table(title="Pipeline Stages", box=box.ROUNDED)
    table.add_column("Stage", style="cyan")
    table.add_column("Status", style="green")
    for s in release.stages:
        status_icon = {"done": "✅", "in_progress": "🟡", "pending": "⬜"}.get(s["status"], "⬜")
        table.add_row(s["label"], f"{status_icon} {s['status']}")
    console.print(table)


def release_status_cmd():
    """Show current release status"""
    ops = get_ops()
    releases = ops.list_releases()
    if not releases:
        console.print("[yellow]No releases. Create one with 'apex ops release create <version>'[/]")
        return

    for rel in releases[:3]:
        pct = rel.progress_pct * 100
        bar = "█" * int(pct // 10) + "░" * (10 - int(pct // 10))
        console.print(Panel(
            f"Version: [bold]{rel.version}[/]  Status: {rel.status}  Progress: {bar} {pct:.0f}%\n"
            f"ID: {rel.id}  Created: {time.strftime('%Y-%m-%d %H:%M', time.localtime(rel.created_at))}",
            title=f"🚀 {rel.name}", border_style="green" if pct == 100 else "yellow",
        ))

        # Stage details
        stage_table = Table(box=box.SIMPLE)
        stage_table.add_column("Stage", style="cyan")
        stage_table.add_column("Status")
        stage_table.add_column("Agent")
        for s in rel.stages:
            icon = {"done": "✅", "in_progress": "🟡", "pending": "⬜",
                    "failed": "❌", "blocked": "🚫"}.get(s["status"], "⬜")
            stage_table.add_row(s["label"], f"{icon} {s['status']}", s.get("agent", ""))
        console.print(stage_table)


def bug_list_cmd(status: str = "open", severity: str = None):
    """List bugs"""
    ops = get_ops()
    bugs = ops.list_bugs(status=status, severity=severity)

    if not bugs:
        console.print("[green]✅ No bugs found![/]")
        return

    table = Table(title=f"🐛 Bugs ({status})", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=14)
    table.add_column("Title", style="white")
    table.add_column("Severity", style="red")
    table.add_column("Status", style="cyan")
    table.add_column("Agent", style="green")
    table.add_column("SLA", style="yellow")

    for bug in bugs:
        sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        sla_str = f"{bug.sla_remaining_hours:.1f}h" if not bug.sla_breached else "[red]BREACHED[/]"
        table.add_row(
            bug.id, bug.title[:50],
            f"{sev_icon.get(bug.severity.value, '⚪')} {bug.severity.value}",
            bug.status.value, bug.assigned_agent or "—", sla_str,
        )
    console.print(table)


def bug_create_cmd(title: str, description: str, severity: str = "medium",
                    steps: str = "", expected: str = "", actual: str = ""):
    """Create a new bug"""
    ops = get_ops()
    bug = ops.create_bug(
        title=title, description=description, severity=severity,
        steps_to_reproduce=steps, expected_result=expected,
        actual_result=actual,
    )
    console.print(Panel(
        f"[bold]{bug.id}[/] — {bug.title}\n"
        f"Severity: {bug.severity.value} | SLA: {bug.sla_remaining_hours:.1f}h",
        title="🐛 Bug Created", border_style="red" if severity == "critical" else "yellow",
    ))


def bug_show_cmd(bug_id: str):
    """Show bug details"""
    ops = get_ops()
    bug = ops.get_bug(bug_id)
    if not bug:
        console.print(f"[red]Bug {bug_id} not found[/]")
        return

    info = Panel.fit(
        f"[bold]Title:[/] {bug.title}\n"
        f"[bold]Severity:[/] {bug.severity.value} | "
        f"[bold]Status:[/] {bug.status.value} | "
        f"[bold]SLA:[/] {'🔴 BREACHED' if bug.sla_breached else f'⏰ {bug.sla_remaining_hours:.1f}h remaining'}\n"
        f"[bold]Source:[/] {bug.source} | [bold]Environment:[/] {bug.environment}\n"
        f"[bold]Assigned:[/] {bug.assigned_agent or 'Unassigned'}\n"
        f"[bold]Related Task:[/] {bug.related_task or 'None'}\n\n"
        f"[bold]Description:[/]\n{bug.description[:500]}\n\n"
        f"[bold]Steps to Reproduce:[/]\n{bug.steps_to_reproduce[:300]}\n\n"
        f"[bold]Expected:[/] {bug.expected_result[:200]}\n"
        f"[bold]Actual:[/] {bug.actual_result[:200]}\n",
        title=f"🐛 {bug.id}",
    )
    console.print(info)

    if bug.resolution:
        console.print(Panel(bug.resolution[:500], title="Resolution", border_style="green"))


def task_list_cmd(status: str = None, agent: str = None):
    """List ops tasks"""
    ops = get_ops()
    tasks = ops.list_tasks(status=status, agent_id=agent)

    if not tasks:
        console.print("[yellow]No tasks found[/]")
        return

    table = Table(title="📋 Tasks", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=14)
    table.add_column("Title", style="white")
    table.add_column("Phase", style="blue")
    table.add_column("Status")
    table.add_column("Agent", style="green")
    table.add_column("Tests", style="cyan")
    table.add_column("Quality", style="yellow")

    for t in tasks:
        status_icon = {"done": "✅", "in_progress": "🟡", "blocked": "🚫",
                       "todo": "📋", "review": "👀"}.get(t.status.value, "⬜")
        tests = f"{t.test_pass_count}/{t.test_total_count}" if t.test_total_count > 0 else "—"
        quality = f"{t.quality_score:.0%}" if t.quality_score else "—"
        table.add_row(t.id, t.title[:45], t.phase,
                      f"{status_icon} {t.status.value}",
                      t.agent_id or "—", tests, quality)
    console.print(table)


def task_create_cmd(title: str, description: str = "", phase: str = "development",
                     priority: int = 2, agent: str = ""):
    """Create an ops task"""
    ops = get_ops()
    task = ops.create_task(
        title=title, description=description, phase=phase,
        priority=priority, agent_id=agent,
    )
    console.print(f"[green]✅ Task {task.id} created: {task.title}[/]")


def expert_list_cmd():
    """List open expert tickets"""
    ops = get_ops()
    tickets = ops.list_expert_tickets(status="open")

    if not tickets:
        console.print("[green]✅ No open expert tickets[/]")
        return

    table = Table(title="🧠 Open Expert Tickets", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=14)
    table.add_column("Title", style="white")
    table.add_column("Requester", style="cyan")
    table.add_column("Expert", style="green")
    table.add_column("Age", style="yellow")

    for t in tickets:
        age = time.time() - t.created_at
        age_str = f"{age/60:.0f}m" if age < 3600 else f"{age/3600:.1f}h"
        table.add_row(t.id, t.title[:45], t.requester, t.expert, age_str)
    console.print(table)
