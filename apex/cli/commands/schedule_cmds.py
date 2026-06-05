"""Apex — Task Schedule & Gantt Chart View

Commands:
  apex schedule view      — Show all tasks in Gantt chart format
  apex schedule view <id> — Show specific epic's tasks in Gantt
  apex schedule list      — List all schedules/epics
"""

from __future__ import annotations

import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from apex.orchestration.task_manager import get_task_manager, ProjectTask, TaskType, WorkflowStatus

console = Console()

# ── Color scheme for Gantt bars ──
STATUS_COLORS = {
    WorkflowStatus.DRAFT: "dim white",
    WorkflowStatus.APPROVED: "cyan",
    WorkflowStatus.ASSIGNED: "blue",
    WorkflowStatus.IN_PROGRESS: "yellow",
    WorkflowStatus.BLOCKED: "red",
    WorkflowStatus.COMPLETED: "green",
    WorkflowStatus.VERIFIED: "green",
    WorkflowStatus.CLOSED: "dim green",
    WorkflowStatus.PM_REVIEW: "bright_yellow",
    WorkflowStatus.PM_VERIFY: "bright_yellow",
    WorkflowStatus.REJECTED: "red",
    WorkflowStatus.REQUESTED: "cyan",
}

STATUS_BAR_FILL = {
    WorkflowStatus.DRAFT: "╌",
    WorkflowStatus.APPROVED: "─",
    WorkflowStatus.ASSIGNED: "━",
    WorkflowStatus.IN_PROGRESS: "█",
    WorkflowStatus.BLOCKED: "░",
    WorkflowStatus.COMPLETED: "▓",
    WorkflowStatus.VERIFIED: "▓",
    WorkflowStatus.CLOSED: "▓",
    WorkflowStatus.PM_REVIEW: "▒",
    WorkflowStatus.PM_VERIFY: "▒",
    WorkflowStatus.REJECTED: "░",
    WorkflowStatus.REQUESTED: "─",
}

# ── Terminal-friendly Gantt renderer ──

CHARS = {
    "bar_start": "├",
    "bar_end": "┤",
    "today": "▼",
    "empty": "·",
    "depend_arrow": "→",
    "milestone": "◆",
}


def _resolve_status(task: ProjectTask) -> WorkflowStatus:
    """Get the most meaningful status for display."""
    return task.workflow_status


def _calc_bar(task: ProjectTask, today_offset: int) -> tuple[int, int, int]:
    """Calculate (start_col, end_col, duration_cols) for a task bar.

    Derives timeline from estimated_hours, priority, and dependencies.
    Start_col = today if not started, positioned based on priority.
    """
    duration_days = max(0.5, task.estimated_hours / 8.0)

    if task.started_at and task.completed_at:
        # Completed task — use actual dates
        start_day = int((task.started_at - today_offset * 86400) / 86400)
        end_day = int((task.completed_at - today_offset * 86400) / 86400)
    elif task.started_at:
        start_day = int((task.started_at - today_offset * 86400) / 86400)
        end_day = start_day + int(duration_days)
    else:
        # Not started — position based on priority
        priority_offset = task.priority  # 0 urgent → sooner
        start_day = priority_offset * 1
        end_day = start_day + int(duration_days)

    duration = max(1, end_day - start_day)
    return start_day, end_day, duration


def render_gantt(tasks: list[ProjectTask], title: str = "Task Schedule") -> None:
    """Render a terminal-friendly Gantt chart using Rich tables."""
    if not tasks:
        console.print("[yellow]No tasks to display.[/]")
        return

    now = datetime.now()
    today_ts = time.mktime(now.timetuple())

    # Determine time window
    all_starts = []
    all_ends = []
    for t in tasks:
        s, e, _ = _calc_bar(t, today_ts)
        all_starts.append(s)
        all_ends.append(e)

    min_day = min(all_starts + [0])
    max_day = max(all_ends + [10])

    # Default: show ±5 days around now, or full range if larger
    if max_day - min_day < 14:
        pad = (14 - (max_day - min_day)) // 2
        min_day = max(0, min_day - pad)
        max_day = max_day + pad

    total_days = max_day - min_day
    if total_days < 10:
        total_days = 10
        max_day = min_day + total_days

    # Header with day markers
    today_col = -min_day  # Column where "today" marker goes

    # Build the Gantt table
    gantt = Table(
        title=f"📊 {title}",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(0, 1),
        show_lines=False,
    )

    gantt.add_column("Task", style="bold white", width=32, no_wrap=True)
    gantt.add_column("Assignee", style="dim", width=14, no_wrap=True)
    gantt.add_column("Status", width=10, no_wrap=True)

    # Timeline columns: show in compact form
    # Show day markers every 2 days to keep it readable
    timeline_cols = []
    for d in range(total_days + 1):
        day_label = f"D{d + min_day}"
        if d % 2 == 0:
            timeline_cols.append(day_label)
        else:
            timeline_cols.append("")

    # We'll use a single timeline column with bars rendered as text
    gantt.add_column(
        Text.assemble(
            ("Timeline", "bold cyan"),
        ),
        width=total_days + 4,
        no_wrap=True,
    )
    gantt.add_column("Hours", style="dim", width=6, justify="right")
    gantt.add_column("Priority", width=6, justify="center")

    # Sort: by priority (urgent first), then by start day
    sorted_tasks = sorted(tasks, key=lambda t: (t.priority, t.estimated_hours))

    # Today marker line
    today_line = [" " * (today_col) + "▼" + " " * (total_days - today_col - 1)]
    gantt.add_row(
        Text("[today]", style="reverse yellow"),
        "",
        "",
        Text(today_line[0], style="reverse yellow"),
        "",
        "",
    )

    for task in sorted_tasks:
        start_day, end_day, duration = _calc_bar(task, today_ts)
        rel_start = start_day - min_day
        rel_end = end_day - min_day

        # Clamp to visible range
        rel_start = max(0, min(rel_start, total_days))
        rel_end = max(0, min(rel_end, total_days))
        duration = max(1, rel_end - rel_start)

        status = _resolve_status(task)
        color = STATUS_COLORS.get(status, "white")
        fill = STATUS_BAR_FILL.get(status, "─")

        # Build bar
        bar_text = ""
        before = rel_start
        after = total_days - rel_end

        bar_text += " " * before
        bar_text += f"[{color}]{''.join([fill] * duration)}[/]"
        bar_text += " " * after

        # Status label
        status_label = status.value.replace("_", " ")
        if len(status_label) > 10:
            status_label = status_label[:9] + "…"

        # Priority indicator
        prio_map = {0: "🔴", 1: "🟠", 2: "🟡", 3: "🟢"}
        prio_icon = prio_map.get(task.priority, "⚪")

        # Dependencies indicator
        name = task.title[:30]
        if task.depends_on:
            deps_short = ",".join(d[:6] for d in task.depends_on)
            name = f"{name} {Text(f'→{deps_short}', style='dim')}"

        gantt.add_row(
            name,
            task.assignee or "—",
            Text(status_label, style=color),
            Text(bar_text),
            f"{task.estimated_hours:.0f}",
            prio_icon,
        )

    console.print(gantt)

    # Legend
    legend = Text.assemble(
        (" Legend: ", "bold"),
        ("█", "green"), " Done  ",
        ("█", "yellow"), " In Progress  ",
        ("░", "red"), " Blocked  ",
        ("─", "cyan"), " Approved  ",
        ("◆", "white"), " Milestone  ",
        ("▼", "reverse yellow"), " Today",
    )
    console.print(legend)
    console.print()


def _get_all_tasks() -> list[ProjectTask]:
    """Get all tasks from the task manager."""
    tm = get_task_manager()
    try:
        return tm.list_tasks()
    except Exception:
        return []


def view_cmd(task_id: Optional[str] = None, project: Optional[str] = None):
    """Show Gantt chart view for tasks."""
    all_tasks = _get_all_tasks()

    if not all_tasks:
        console.print("[yellow]📭 No tasks found. Create tasks first with: apex dispatch-smart <requirement>[/]")
        return

    # Filter by epic/task ID if provided
    if task_id:
        tasks = [t for t in all_tasks if t.id == task_id or t.epic_id == task_id]
        if not tasks:
            console.print(f"[red]No tasks found for ID: {task_id}[/]")
            return
        title = f"Epic: {task_id}"
    elif project:
        tasks = [t for t in all_tasks if t.project == project]
        if not tasks:
            console.print(f"[yellow]No tasks found for project: {project}[/]")
            return
        title = f"Project: {project}"
    else:
        tasks = all_tasks
        title = "All Tasks"

    # Group as epic tree: show epics first then their subtasks
    epics = [t for t in tasks if t.task_type == TaskType.EPIC]
    non_epics = [t for t in tasks if t.task_type != TaskType.EPIC]

    if epics:
        for epic in sorted(epics, key=lambda t: t.priority):
            children = [t for t in non_epics if t.epic_id == epic.id]
            all_grouped = [epic] + sorted(children, key=lambda t: (t.priority, t.estimated_hours))
            render_gantt(all_grouped, title=f"{title} — {epic.title[:40]}")
    else:
        render_gantt(tasks, title=title)


def list_cmd(project: Optional[str] = None):
    """List all schedules/epics."""
    all_tasks = _get_all_tasks()
    if not all_tasks:
        console.print("[yellow]No tasks found.[/]")
        return

    if project:
        tasks = [t for t in all_tasks if t.project == project]
    else:
        tasks = all_tasks

    epics = [t for t in tasks if t.task_type == TaskType.EPIC]
    stories = [t for t in tasks if t.task_type == TaskType.STORY]
    others = [t for t in tasks if t.task_type not in (TaskType.EPIC, TaskType.STORY)]

    table = Table(title="📋 Task Schedule Overview", border_style="cyan", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=10)
    table.add_column("Title", width=36)
    table.add_column("Type", width=6)
    table.add_column("Status", width=12)
    table.add_column("Assignee", width=14)
    table.add_column("Hours", width=6, justify="right")
    table.add_column("Priority", width=6, justify="center")

    prio_map = {0: "🔴", 1: "🟠", 2: "🟡", 3: "🟢"}

    for t in epics:
        children = [c for c in stories + others if c.epic_id == t.id]
        table.add_row(
            t.id[:8],
            Text(t.title[:34], style="bold"),
            "EPIC",
            t.workflow_status.value,
            t.assignee or "—",
            f"{t.estimated_hours:.0f}",
            prio_map.get(t.priority, "⚪"),
        )
        for c in children:
            table.add_row(
                f"  {c.id[:6]}",
                f"  {c.title[:32]}",
                c.task_type.value[:4],
                c.workflow_status.value,
                c.assignee or "—",
                f"{c.estimated_hours:.0f}",
                prio_map.get(c.priority, "⚪"),
            )
        # Subtotal row
        if children:
            total_h = sum(c.estimated_hours for c in children)
            table.add_row(
                "", f"  [dim]{len(children)} tasks[/]", "", "", "",
                Text(f"{total_h:.0f}", style="dim"),
                "",
            )

    if not epics:
        # Just list all tasks flat
        for t in sorted(tasks, key=lambda x: (x.priority, x.estimated_hours)):
            table.add_row(
                t.id[:8],
                t.title[:34],
                t.task_type.value[:4],
                t.workflow_status.value,
                t.assignee or "—",
                f"{t.estimated_hours:.0f}",
                prio_map.get(t.priority, "⚪"),
            )

    console.print(table)
