"""Apex — Help Command Group

Merges: help-request, help-approve, help-list under `apex help <sub>`

Usage:
  apex help request <agent> <title>  — Request help
  apex help approve <id> -a <agent>  — Approve help request
  apex help list                     — List help requests
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agentark.orchestration.task_manager import get_task_manager

console = Console()


def help_request_cmd(agent: str, title: str, description: str = "", task: str = ""):
    """🆘 Request help from PM for another agent."""
    tm = get_task_manager()
    req = tm.request_help(
        requesting_agent=agent,
        title=title,
        description=description,
        source_task_id=task,
    )
    console.print(Panel(
        f"[bold]{req.title}[/]\n"
        f"Request from: [cyan]{agent}[/] | "
        f"ID: [green]{req.id}[/]",
        title="🆘 Help Request Submitted", border_style="yellow",
    ))
    console.print("[dim]PM can approve with: apex help approve <request_id> -a <helper>[/]")


def help_approve_cmd(request_id: str, agent: str, notes: str = ""):
    """✅ PM approves a help request and assigns a helper."""
    tm = get_task_manager()
    req = tm.approve_help(request_id, assigned_agent=agent, pm_notes=notes)
    console.print(Panel(
        f"[bold]✅ Approved: {req.title}[/]\n"
        f"Helper: [green]{req.assigned_agent}[/]",
        title="Help Assignment", border_style="green",
    ))


def help_list_cmd(status_filter: str = ""):
    """📋 List help requests."""
    tm = get_task_manager()
    requests = tm.list_help_requests(status=status_filter or None)
    if not requests:
        console.print("[dim]No help requests found.[/]")
        console.print("[dim]Create one: apex help request <agent> <title>[/]")
        return
    table = Table(title="📋 Help Requests", box=None)
    table.add_column("ID", style="dim", width=10)
    table.add_column("Requester", style="cyan")
    table.add_column("Title", width=30)
    table.add_column("Status", style="yellow")
    table.add_column("Helper", style="green")
    for r in requests:
        table.add_row(
            r.id[:8],
            r.requesting_agent,
            r.title[:28],
            r.status.value,
            r.assigned_agent or "—",
        )
    console.print(table)
