"""CLI renderers for apex pm commands — Rich terminal UI."""

from datetime import datetime, timezone, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.progress import Progress, BarColumn, TextColumn
from rich.text import Text
from rich import box

from apex.interface.pm_engine import PMEngine, CriticalPath, Schedule, Agent, Task

console = Console()
TZ = timezone(timedelta(hours=8))

# ─── Dashboard ────────────────────────────────────────────────────


def render_dashboard(engine: PMEngine, project: str = ""):
    """Full project dashboard: agents, tasks, timeline, health."""
    schedule = engine.generate_schedule(project)
    health = engine.health_check()

    console.print()
    console.print(Panel(
        f"[bold]📊 Apex PM Dashboard[/]  [dim]{datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')}[/]",
        border_style="cyan",
    ))

    # ── Row 1: Summary cards ──
    agents = health["agents"]
    tasks = health["tasks"]

    summary = (
        f"[green]● 活跃Agent: {agents['active']}[/]  "
        f"[yellow]● 警告: {agents['warning']}[/]  "
        f"[red]● 离线: {agents['offline']}[/]  "
        f"[dim]│[/]  "
        f"[cyan]任务: {tasks['total']}[/]  "
        f"[green]✅ {tasks['completed']}[/]  "
        f"[blue]🔄 {tasks['in_progress']}[/]  "
        f"[dim]⏳ {tasks['pending']}[/]  "
        f"[red]🚫 {tasks['blocked']}[/]"
    )
    console.print(Panel(summary, border_style="blue"))
    console.print()

    # ── Row 2: Critical Path + Agents (side by side) ──
    layout = Layout()
    layout.split_row(
        Layout(name="left", ratio=2),
        Layout(name="right", ratio=1),
    )

    # Left: Critical path
    cp = schedule.critical_path
    cp_lines = [f"[bold]⏱ 关键路径 (最长依赖链)[/]"]
    cp_lines.append(f"[dim]总耗时: {cp.total_hours:.1f}h[/]")
    if cp.path:
        cp_lines.append("")
        cp_lines.append("[cyan]▼ 关键链[/]")
        for tid in cp.path:
            task = _find_task(schedule.tasks, tid)
            if task:
                status_icon = _status_icon(task.status)
                cp_lines.append(
                    f"  {status_icon} {tid}: {task.name[:40]} "
                    f"[dim]({task.estimated_hours:.1f}h)[/]"
                )

    layout["left"].update(Panel("\n".join(cp_lines), title="🔗 关键路径", border_style="red"))

    # Right: Agent load
    ag_lines = [f"[bold]👥 Agent负载[/]"]
    ag_lines.append("")
    engine_agents = engine.load_agents()
    for agent in engine_agents[:10]:
        bar_len = 10
        filled = int(bar_len * agent.load_pct)
        bar = "█" * filled + "░" * (bar_len - filled)
        status_dot = {"active": "🟢", "warning": "🟡", "offline": "🔴"}.get(
            agent.status, "⚪"
        )
        ag_lines.append(
            f"{status_dot} {agent.name[:16]:16s} [{bar}] "
            f"[dim]{len(agent.current_tasks)}/{agent.total_tasks}[/]"
        )

    layout["right"].update(Panel("\n".join(ag_lines), title="👥 Agent", border_style="green"))

    console.print(layout)
    console.print()

    # ── Row 3: Parallel groups ──
    if cp.parallel_groups:
        pg_lines = ["[bold]⚡ 可并行执行的任务组[/]"]
        pg_lines.append("")
        for i, group in enumerate(cp.parallel_groups[:5]):
            names = []
            for tid in group:
                t = _find_task(schedule.tasks, tid)
                names.append(f"{tid}" if not t else f"{tid}({t.estimated_hours:.0f}h)")
            pg_lines.append(f"  组{i+1}: {' | '.join(names)}")

        console.print(Panel("\n".join(pg_lines), title="⚡ 并行任务", border_style="yellow"))
        console.print()

    # ── Row 4: Bottlenecks ──
    if cp.bottleneck_tasks:
        bn_lines = []
        for tid in cp.bottleneck_tasks:
            t = _find_task(schedule.tasks, tid)
            if t:
                bn_lines.append(
                    f"  [red]●[/] {tid}: {t.name[:45]} [dim]({t.estimated_hours:.1f}h)[/]"
                )
        console.print(Panel("\n".join(bn_lines), title="🔴 瓶颈任务 (Top 5)", border_style="red"))
        console.print()

    # ── Row 5: Recommendations ──
    if health["recommendations"]:
        rec_lines = []
        for i, rec in enumerate(health["recommendations"], 1):
            rec_lines.append(f"  {i}. {rec}")
        console.print(Panel("\n".join(rec_lines), title="🧠 建议", border_style="cyan"))

    # ── Row 6: Alerts ──
    if health["alerts"]:
        alert_lines = []
        for alert in health["alerts"]:
            alert_lines.append(f"  {alert}")
        console.print(Panel("\n".join(alert_lines), title="🔔 告警", border_style="red"))

    if cp.estimated_completion:
        console.print(f"[dim]预计完成: {cp.estimated_completion[:19]}[/]")


# ─── Schedule ─────────────────────────────────────────────────────


def render_schedule(engine: PMEngine, project: str = ""):
    """Full schedule with assignments."""
    schedule = engine.generate_schedule(project)

    console.print()
    console.print(Panel(
        f"[bold]📅 项目排期[/]  [dim]{project or 'all'}[/]",
        border_style="cyan",
    ))

    console.print(
        f"[dim]总任务: {len(schedule.tasks)}  │  "
        f"串行: {schedule.serial_hours:.1f}h  │  "
        f"并行优化后: {schedule.critical_path.total_hours:.1f}h  │  "
        f"[green]节省: {schedule.parallel_savings:.1f}h[/]"
    )
    console.print()

    # Task table with assignments
    table = Table(box=box.ROUNDED, border_style="blue", header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("任务", style="bold white", max_width=35)
    table.add_column("状态", justify="center")
    table.add_column("分配", style="green")
    table.add_column("预估", justify="right")
    table.add_column("依赖", style="dim", max_width=20)

    for task in schedule.tasks:
        status_icon = _status_icon(task.status)
        assignee = schedule.assignments.get(task.id, task.assignee or "—")
        deps = ", ".join(task.dependencies[:3])
        if len(task.dependencies) > 3:
            deps += f" +{len(task.dependencies)-3}"

        table.add_row(
            task.id,
            task.name[:33],
            status_icon,
            assignee[:16],
            f"{task.estimated_hours:.0f}h",
            deps,
        )

    console.print(table)

    # Critical path
    cp = schedule.critical_path
    if cp.path:
        console.print()
        console.print(
            f"[bold red]🔗 关键路径:[/] {' → '.join(cp.path)} "
            f"[dim]({cp.total_hours:.1f}h)[/]"
        )


# ─── Health ───────────────────────────────────────────────────────


def render_health(engine: PMEngine):
    """Health check report."""
    report = engine.health_check()

    console.print()
    console.print(Panel("[bold]🩺 Agent健康检查[/]", border_style="cyan"))

    # Agent grid
    agents = engine.load_agents()
    table = Table(box=box.ROUNDED, border_style="blue", header_style="bold cyan")
    table.add_column("Agent", style="bold white")
    table.add_column("状态", justify="center")
    table.add_column("负载", justify="center")
    table.add_column("任务完成", justify="center")
    table.add_column("Skills", style="dim")

    for agent in agents[:15]:
        status_icon = {"active": "🟢", "warning": "🟡", "offline": "🔴"}.get(
            agent.status, "⚪"
        )
        load_bar = "█" * int(agent.load_pct * 5) + "░" * (5 - int(agent.load_pct * 5))
        table.add_row(
            agent.name,
            status_icon,
            f"[{'red' if agent.load_pct > 0.7 else 'green'}]{load_bar}[/]",
            f"{agent.completed_tasks}/{agent.total_tasks}",
            ", ".join(agent.skills[:3]),
        )

    console.print(table)
    console.print()

    # Alerts
    if report["alerts"]:
        for alert in report["alerts"]:
            console.print(f"  {alert}")

    if report["recommendations"]:
        console.print()
        for rec in report["recommendations"]:
            console.print(f"  💡 {rec}")


# ─── Timeline ─────────────────────────────────────────────────────


def render_timeline(engine: PMEngine, project: str = ""):
    """Gantt-like timeline view."""
    schedule = engine.generate_schedule(project)
    tasks = schedule.tasks
    if not tasks:
        console.print("[dim]No tasks to display.[/]")
        return

    cp = schedule.critical_path
    critical_set = set(cp.path)

    console.print()
    console.print(Panel(
        f"[bold]📊 任务时间线[/]  [dim]{project or 'all'}[/]",
        border_style="cyan",
    ))

    # Sort: dependencies first, then by priority
    def sort_key(t: Task) -> int:
        return len(t.dependencies) * 100 + t.priority * 10

    sorted_tasks = sorted(tasks, key=sort_key)

    console.print()
    for task in sorted_tasks[:30]:
        status_icon = _status_icon(task.status)
        is_critical = "🔴" if task.id in critical_set else "  "
        bar_len = min(30, int(task.estimated_hours * 3))
        bar = "▓" * max(1, bar_len)
        assignee = schedule.assignments.get(task.id, task.assignee or "未分配")
        deps = f" ← {', '.join(task.dependencies[:2])}" if task.dependencies else ""

        console.print(
            f"{is_critical} {status_icon} {task.id:10s} "
            f"[{'red' if task.id in critical_set else 'dim'}]{bar}[/] "
            f"{task.estimated_hours:.0f}h "
            f"[dim]{task.name[:30]:30s}[/] "
            f"[green]{assignee[:14]:14s}[/]{deps}"
        )

    console.print()
    console.print(
        f"[dim]🔴 = 关键路径任务  │  {cp.total_hours:.1f}h min duration[/]"
    )


# ─── Helpers ──────────────────────────────────────────────────────


def _find_task(tasks: list[Task], task_id: str) -> Task | None:
    for t in tasks:
        if t.id == task_id:
            return t
    return None


def _status_icon(status: str) -> str:
    return {
        "completed": "✅",
        "in_progress": "🔄",
        "pending": "⏳",
        "blocked": "🚫",
    }.get(status, "❓")
