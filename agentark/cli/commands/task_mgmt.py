"""Apex — Task Management CLI commands.

Commands:
  apex task create          — Create a hierarchical task (epic/story/task/subtask)
  apex task list            — List tasks with filters
  apex task show            — Show task with full tree
  apex task status          — Transition task workflow status
  apex task epic            — Show epic tree
  apex capacity             — Show agent capacity
  apex dispatch             — Auto-dispatch tasks by capacity
  apex help-request         — Request help from another agent
  apex help-approve         — PM approves help request
"""

from __future__ import annotations

import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.columns import Columns
from rich import box

from agentark.orchestration.task_manager import get_task_manager, TaskType, WorkflowStatus

console = Console()


def task_create_cmd(title: str, description: str = "", task_type: str = "task",
                    phase: str = "development", priority: int = 2,
                    assignee: str = "", parent: str = "",
                    project: str = "", hours: float = 0.0):
    """Create a hierarchical task."""
    tm = get_task_manager()
    task = tm.create_task(
        title=title, description=description, task_type=task_type,
        phase=phase, priority=priority, assignee=assignee,
        parent_id=parent, project=project, estimated_hours=hours,
    )
    status_icon = {
        "draft": "📄", "requested": "📨", "assigned": "📌",
        "in_progress": "🔄", "completed": "✅", "verified": "✔️",
    }.get(task.workflow_status.value, "📋")
    console.print(Panel(
        f"[bold]{status_icon} Task created: {task.title}[/]\n"
        f"ID: [cyan]{task.id}[/] | Type: [yellow]{task.task_type.value}[/]\n"
        f"Assignee: [green]{task.assignee or 'unassigned'}[/] | "
        f"Status: [bold]{task.workflow_status.value}[/]\n"
        f"Parent: {task.parent_id or 'none'} | Project: {task.project or 'none'}",
        title="📋 Task Created", border_style="green",
    ))


def task_list_cmd(project: str = "", assignee: str = "",
                  task_type: str = "", status: str = "",
                  phase: str = ""):
    """List tasks with filters."""
    tm = get_task_manager()
    tasks = tm.list_tasks(
        project=project, assignee=assignee,
        task_type=task_type, workflow_status=status, phase=phase,
    )
    if not tasks:
        console.print("[yellow]No tasks found[/]")
        return

    table = Table(title=f"📋 Tasks ({len(tasks)})", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=14)
    table.add_column("Title", style="white")
    table.add_column("Type", style="yellow")
    table.add_column("Status", style="cyan")
    table.add_column("Assignee", style="green")
    table.add_column("Progress", style="blue")

    type_icons = {"epic": "🏗️", "story": "📖", "task": "📋", "subtask": "🔹"}
    for t in tasks:
        type_icon = type_icons.get(t.task_type.value, "📋")
        tree_indent = "  " if t.parent_id else ""
        bar = "█" * int(t.progress_pct // 10) + "░" * (10 - int(t.progress_pct // 10))
        table.add_row(
            t.id, f"{tree_indent}{t.title[:40]}", f"{type_icon} {t.task_type.value}",
            t.workflow_status.value, t.assignee or "—", f"{bar} {t.progress_pct:.0f}%",
        )
    console.print(table)


def task_show_cmd(task_id: str):
    """Show task with full tree."""
    tm = get_task_manager()
    task = tm.get_task(task_id)
    if not task:
        console.print(f"[red]Task {task_id} not found[/]")
        return

    # Task info panel
    info = Panel.fit(
        f"[bold]Title:[/] {task.title}\n"
        f"[bold]Type:[/] {task.task_type.value} | "
        f"[bold]Status:[/] {task.workflow_status.value} | "
        f"[bold]Priority:[/] {task.priority}\n"
        f"[bold]Assignee:[/] {task.assignee or 'unassigned'} | "
        f"[bold]Phase:[/] {task.phase}\n"
        f"[bold]Parent:[/] {task.parent_id or 'none'} | "
        f"[bold]Project:[/] {task.project or 'none'}\n"
        f"[bold]Progress:[/] {task.progress_pct:.0f}% | "
        f"[bold]Est Hours:[/] {task.estimated_hours}\n"
        f"[bold]Created:[/] {time.strftime('%Y-%m-%d %H:%M', time.localtime(task.created_at)) if task.created_at else 'N/A'}\n"
        f"[bold]Description:[/] {task.description[:200]}",
        title=f"📋 {task.id}", border_style="cyan",
    )
    console.print(info)

    # Show tree
    tree_data = tm.get_task_tree(task_id, depth=5)
    if tree_data.get("children"):
        t = Tree(f"[bold cyan]{task.title}[/] ({task.workflow_status.value})")
        _build_task_tree(t, tree_data.get("children", []))
        console.print(t)

    # PM notes
    if task.pm_notes:
        console.print(Panel(task.pm_notes[:300], title="📝 PM Notes", border_style="yellow"))


def _build_task_tree(tree: Tree, children: list[dict]):
    """Recursively build Rich tree from task children."""
    icons = {"epic": "🏗️", "story": "📖", "task": "📋", "subtask": "🔹"}
    for child in children:
        icon = icons.get(child.get("task_type", "task"), "📋")
        status = child.get("workflow_status", "draft")
        assignee = child.get("assignee", "")
        label = f"{icon} {child.get('title', '')[:40]} [{status}]"
        if assignee:
            label += f" @{assignee}"
        if child.get("progress_pct", 0) > 0:
            label += f" ({child['progress_pct']:.0f}%)"
        branch = tree.add(label)
        if child.get("children"):
            _build_task_tree(branch, child["children"])


def task_status_cmd(task_id: str, new_status: str, notes: str = ""):
    """Transition task workflow status."""
    tm = get_task_manager()
    try:
        task = tm.update_task_status(task_id, new_status, notes=notes)
        console.print(f"[green]✅ Task {task_id}: {task.workflow_status.value}[/]")
        if notes:
            console.print(Panel(notes[:200], title="📝 Notes", border_style="yellow"))
    except ValueError as e:
        console.print(f"[red]❌ {e}[/]")


def epic_cmd(epic_title: str = ""):
    """Show epic tree overview."""
    tm = get_task_manager()
    epics = tm.get_epic_tree(epic_title)
    if not epics:
        console.print("[yellow]No epics found. Create one with 'apex task create --type epic'[/]")
        return

    for epic in epics:
        t = Tree(f"[bold cyan]🏗️ {epic['title']}[/] ({epic.get('workflow_status', 'draft')})")
        _build_task_tree(t, epic.get("children", []))
        progress = epic.get("progress_pct", 0)
        bar = "█" * int(progress // 10) + "░" * (10 - int(progress // 10))
        console.print(t)
        console.print(f"  Overall: {bar} {progress:.0f}%")
        console.print()


def capacity_cmd(agent: str = ""):
    """Show agent capacity."""
    tm = get_task_manager()
    capacities = tm.get_agent_capacity(agent_name=agent)

    table = Table(title="🤖 Agent Capacity", box=box.ROUNDED)
    table.add_column("Agent", style="cyan")
    table.add_column("Active", style="yellow")
    table.add_column("Max", style="blue")
    table.add_column("Available", style="green")
    table.add_column("Load", style="magenta")
    table.add_column("Done", style="green")
    table.add_column("Failed", style="red")

    for cap in capacities:
        load_icon = "🟢" if cap.load_pct < 50 else ("🟡" if cap.load_pct < 80 else "🔴")
        table.add_row(
            cap.agent_name, str(cap.active_tasks), str(cap.max_concurrent),
            str(cap.available_slots), f"{load_icon} {cap.load_pct}%",
            str(cap.total_completed), str(cap.total_failed),
        )
    console.print(table)


def dispatch_cmd():
    """Auto-dispatch tasks to agents based on capacity."""
    tm = get_task_manager()
    actions = tm.auto_dispatch()
    if not actions:
        console.print("[yellow]No tasks to dispatch[/]")
        return
    for action in actions:
        console.print(f"  ✅ {action['title'][:50]} → {action['agent']} ({action['action']})")


def dispatch_smart_cmd(requirement: str, project: str = "finopsai"):
    """智能分派：需求文本 → AI拆解 → 创建Task → 自动分配Agent"""
    from agentark.orchestration.task_decomposer import decompose_requirement, dispatch_tasks

    console.print(f"\n[bold cyan]🔍 分析需求:[/] {requirement[:60]}...")
    console.print(f"[bold cyan]📦 项目:[/] {project}")

    # 1. 拆解
    with console.status("[bold green]拆解需求中..."):
        result = decompose_requirement(requirement, project)

    console.print(f"\n[bold]📋 {result.epic_title}[/]")
    console.print(f"[dim]{result.analysis}[/]\n")

    # 显示任务
    table = Table(title="拆解结果", box=box.SIMPLE)
    table.add_column("#", style="dim")
    table.add_column("任务")
    table.add_column("分配")
    table.add_column("工时")
    table.add_column("优先级")

    for i, t in enumerate(result.tasks, 1):
        priority_icon = {0: "🔴", 1: "🟠", 2: "🟡", 3: "🟢"}.get(t.priority, "⚪")
        table.add_row(
            str(i), t.title, t.assignee or "(待分配)",
            f"{t.estimated_hours}h", priority_icon,
        )

    console.print(table)

    # 2. 确认后创建
    console.print("\n[bold yellow]创建以上任务并分派? [y/N][/] ", end="")
    # (CLI模式下自动确认)
    tm = get_task_manager()
    dispatch_result = dispatch_tasks(result, tm)

    console.print(f"\n[bold green]✅ 已创建 {dispatch_result['dispatched']} 个任务[/]")
    if dispatch_result.get("epic_id"):
        console.print(f"   Epic: {dispatch_result['epic_id']}")
    for tid in dispatch_result.get("task_ids", []):
        console.print(f"   Task: {tid}")


def help_request_cmd(agent: str, title: str, description: str = "", task: str = ""):
    """Request help from PM for another agent."""
    tm = get_task_manager()
    req = tm.request_help(requesting_agent=agent, title=title,
                          description=description, source_task_id=task)
    console.print(Panel(
        f"[bold]{req.title}[/]\n"
        f"Request from: [cyan]{agent}[/] | "
        f"ID: [green]{req.id}[/]",
        title="🆘 Help Request Submitted", border_style="yellow",
    ))
    console.print("[dim]PM can approve with: apex help-approve <request_id> --agent <helper>[/]")


def help_approve_cmd(request_id: str, agent: str, notes: str = ""):
    """PM approves a help request and assigns a helper."""
    tm = get_task_manager()
    req = tm.approve_help(request_id, assigned_agent=agent, pm_notes=notes)
    console.print(Panel(
        f"[bold]✅ Help request approved![/]\n"
        f"Request: {req.title}\n"
        f"Helper: [green]{agent}[/]",
        title="🆗 Approved", border_style="green",
    ))


def help_list_cmd(status: str = ""):
    """List help requests."""
    tm = get_task_manager()
    requests = tm.list_help_requests(status=status)
    if not requests:
        console.print("[green]✅ No help requests[/]")
        return
    table = Table(title="🆘 Help Requests", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=14)
    table.add_column("From", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Status", style="yellow")
    table.add_column("Helper", style="green")
    for r in requests:
        table.add_row(
            r.id, r.requesting_agent, r.title[:40],
            r.status.value, r.assigned_agent or "—",
        )
    console.print(table)
