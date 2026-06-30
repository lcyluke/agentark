"""Apex Sprint Pipeline CLI — MVP closed-loop development.

Commands:
  apex sprint create <goal>   — Start a new sprint
  apex sprint status [id]     — View sprint progress
  apex sprint approve [id]    — Approve current manual gate
  apex sprint reject [id]     — Reject current manual gate
  apex sprint list            — List all sprints
  apex sprint complete [id]   — Mark current phase as done
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich import box

from agentark.orchestration.sprint_pipeline import SprintManager, PHASES, PHASE_META

console = Console()


def _get_active_sprint(mgr: SprintManager):
    """Get the most recent active sprint."""
    sprints = mgr.list_all(status="active")
    return sprints[0] if sprints else None


def cmd_create(goal: str, mode: str = "solo"):
    """Create a new sprint."""
    mgr = SprintManager()
    sprint = mgr.create(goal, mode=mode)

    console.print()
    console.print(
        Panel.fit(
            f"[bold green]🏃 Sprint Created![/]\n"
            f"  ID: [cyan]{sprint.id}[/]\n"
            f"  Goal: {sprint.goal}\n"
            f"  Mode: [yellow]{sprint.mode}[/]\n"
            f"  Iteration: #{sprint.iteration}",
            title="Sprint Pipeline",
        )
    )

    # Show phase plan
    table = Table(title="Phases", box=box.SIMPLE)
    table.add_column("Phase", style="bold")
    table.add_column("Agent(s)")
    table.add_column("Gate")
    table.add_column("Status")

    for p in sprint.phases:
        meta = PHASE_META.get(p.name, {})
        icon = "👤" if p.gate == "manual" else "🤖"
        status_icon = "🔄" if p.status == "active" else "⏳"
        table.add_row(
            f"{status_icon} {meta.get('display', p.name)}",
            p.agent,
            f"{icon} {p.gate_name}",
            p.status,
        )

    console.print(table)
    console.print(f"\n[dim]Next: PLAN phase active. Work → complete → approve → BUILD[/]")
    console.print(f"[dim]Run: apex sprint status {sprint.id}[/]")


def cmd_status(sprint_id=None):
    """Show sprint progress."""
    mgr = SprintManager()

    if sprint_id:
        sprint = mgr.get(sprint_id)
    else:
        sprint = _get_active_sprint(mgr)

    if not sprint:
        console.print("[yellow]No active sprint found. Create one with: apex sprint create <goal>[/]")
        return

    # Progress bar
    done = sum(1 for p in sprint.phases if p.status == "done")
    pct = sprint.progress_pct

    console.print()
    console.print(
        Panel.fit(
            f"[bold]🏃 Sprint: {sprint.goal}[/]\n"
            f"  ID: [cyan]{sprint.id}[/] | Mode: [yellow]{sprint.mode}[/] | Iteration: #{sprint.iteration}",
            title=f"Sprint #{sprint.id.split('_')[1][:6]}",
        )
    )

    # Progress
    bar_width = 30
    filled = int(pct / 100 * bar_width)
    bar = "█" * filled + "░" * (bar_width - filled)
    console.print(f"  [{pct}%] {bar}  {done}/{len(PHASES)} phases")

    # Phases table
    table = Table(box=box.SIMPLE)
    table.add_column("Phase")
    table.add_column("Hours")
    table.add_column("Gate")
    table.add_column("Output")

    for p in sprint.phases:
        meta = PHASE_META.get(p.name, {})
        icon_map = {"done": "✅", "active": "🔄", "pending": "⏳", "rejected": "❌"}
        icon = icon_map.get(p.status, "?")
        gate_icon = "👤" if p.gate == "manual" else "🤖"

        output_preview = (p.output or "")[:40] + ("..." if len(p.output or "") > 40 else "")

        table.add_row(
            f"{icon} {meta.get('display', p.name)}",
            f"{p.hours_spent:.1f}h" if p.hours_spent else "—",
            f"{gate_icon} {p.gate_name} ({p.gate_status})",
            output_preview or "—",
        )

    console.print(table)

    # Current gate
    gate = sprint.current_gate
    if gate:
        console.print(f"\n[bold yellow]🚦 等待审批: 👤 {gate.gate_name}[/]")
        console.print(f"[dim]Run: apex sprint approve {sprint.id}[/]")

    console.print(f"\n📊 累计工时: {sprint.total_hours:.1f}h | 迭代: V{sprint.iteration}")


def cmd_approve(sprint_id=None):
    """Approve the current manual gate."""
    mgr = SprintManager()

    if not sprint_id:
        sprint = _get_active_sprint(mgr)
        sprint_id = sprint.id if sprint else None

    if not sprint_id:
        console.print("[red]No sprint to approve[/]")
        return

    result = mgr.approve(sprint_id)
    if result["success"]:
        console.print(f"[green]✅ {result['message']}[/]")
        cmd_status(sprint_id)
    else:
        console.print(f"[red]❌ {result['message']}[/]")


def cmd_reject(sprint_id=None, reason=""):
    """Reject the current manual gate."""
    mgr = SprintManager()

    if not sprint_id:
        sprint = _get_active_sprint(mgr)
        sprint_id = sprint.id if sprint else None

    if not sprint_id:
        console.print("[red]No sprint to reject[/]")
        return

    result = mgr.reject(sprint_id, reason)
    if result["success"]:
        console.print(f"[yellow]↩️ {result['message']}[/]")
    else:
        console.print(f"[red]❌ {result['message']}[/]")


def cmd_complete(sprint_id=None, hours=0.0, output=""):
    """Mark current phase as done."""
    mgr = SprintManager()

    if not sprint_id:
        sprint = _get_active_sprint(mgr)
        sprint_id = sprint.id if sprint else None

    if not sprint_id:
        console.print("[red]No sprint to complete[/]")
        return

    result = mgr.complete_phase(sprint_id, hours=hours, output=output)
    if result["success"]:
        console.print(f"[green]✅ {result['message']}[/]")
        if result.get("gate") == "auto":
            # Try auto-advance
            auto = mgr.advance_auto(sprint_id)
            console.print(f"[dim]🤖 {auto['message']}[/]")
        else:
            console.print(f"[yellow]🚦 等待审批: 👤 {result.get('gate_name', 'unknown')}[/]")
    else:
        console.print(f"[red]❌ {result['message']}[/]")


def cmd_list():
    """List all sprints."""
    mgr = SprintManager()
    sprints = mgr.list_all()

    if not sprints:
        console.print("[dim]No sprints yet. Create one: apex sprint create <goal>[/]")
        return

    table = Table(title="All Sprints", box=box.SIMPLE)
    table.add_column("ID")
    table.add_column("Goal")
    table.add_column("Mode")
    table.add_column("Phase")
    table.add_column("Progress")
    table.add_column("Status")

    for s in sprints:
        icon = "🟢" if s.status == "active" else "⚪"
        table.add_row(
            s.id,
            s.goal[:40],
            s.mode,
            s.current_phase,
            f"{s.progress_pct}%",
            f"{icon} {s.status}",
        )

    console.print(table)
