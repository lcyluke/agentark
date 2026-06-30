"""CLI renderers for apex pm commands — Rich terminal UI v2.

Enhanced with assignment rationale, agent profiles, and module ownership.
"""

from datetime import datetime, timezone, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box

from agentark.interface.pm_engine import (
    PMEngine, CriticalPath, Schedule, Task, AgentProfile, AssignmentResult,
)

console = Console()
TZ = timezone(timedelta(hours=8))

# ─── Dashboard (enhanced) ─────────────────────────────────────────


def render_dashboard(engine: PMEngine, project: str = ""):
    """Full project dashboard with assignment rationale."""
    schedule = engine.generate_schedule(project)
    health = engine.health_check()

    console.print()
    console.print(Panel(
        f"[bold]📊 Apex PM Dashboard[/]  "
        f"[dim]{datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')}[/]",
        border_style="cyan",
    ))

    # Summary row
    agents = health["agents"]
    tasks = health["tasks"]
    summary = (
        f"[green]● 活跃: {agents['active']}[/]  "
        f"[yellow]● 警告: {agents['warning']}[/]  "
        f"[red]● 离线: {agents['offline']}[/]  "
        f"[dim]│[/]  "
        f"任务: {tasks['total']}  "
        f"[green]✅{tasks['completed']}[/] "
        f"[blue]🔄{tasks['in_progress']}[/] "
        f"[dim]⏳{tasks['pending']}[/] "
        f"[red]🚫{tasks['blocked']}[/]"
    )
    console.print(Panel(summary, border_style="blue"))
    console.print()

    # Layout: critical path + agent load
    layout = Layout()
    layout.split_row(Layout(name="left", ratio=2), Layout(name="right", ratio=1))

    cp = schedule.critical_path
    cp_lines = [f"[bold]⏱ 关键路径[/]  [dim]{cp.total_hours:.1f}h min[/]"]
    if cp.path:
        for tid in cp.path[:12]:
            t = _find_task(schedule.tasks, tid)
            if t:
                icon = _status_icon(t.status)
                cp_lines.append(f"  {icon} {tid}: {t.name[:38]} [dim]({t.estimated_hours:.0f}h)[/]")
    layout["left"].update(Panel("\n".join(cp_lines), border_style="red"))

    # Agent load with skills
    profiles = engine.build_agent_profiles()
    ag_lines = [f"[bold]👥 Agent 负载 & 技能[/]"]
    for agent in profiles[:10]:
        if agent.status != "active":
            continue
        bar = "█" * int(agent.load_pct * 5) + "░" * (5 - int(agent.load_pct * 5))
        ag_lines.append(
            f"🟢 {agent.name[:16]:16s} [{bar}] "
            f"[dim]{', '.join(agent.top_skills[:2])}[/]"
        )
    layout["right"].update(Panel("\n".join(ag_lines), border_style="green"))
    console.print(layout)
    console.print()

    # Parallel groups
    if cp.parallel_groups:
        pg = []
        for i, group in enumerate(cp.parallel_groups[:5]):
            names = ", ".join(group[:4])
            if len(group) > 4:
                names += f" +{len(group)-4}"
            pg.append(f"  组{i+1}: {names}")
        console.print(Panel("\n".join(pg), title="⚡ 可并行执行", border_style="yellow"))
        console.print()

    # Alerts + recommendations
    if health["alerts"]:
        for a in health["alerts"]:
            console.print(f"  {a}")
    if health["recommendations"]:
        for r in health["recommendations"]:
            console.print(f"  💡 {r}")

    if cp.estimated_completion:
        console.print(f"\n[dim]预计完成: {cp.estimated_completion[:19]}[/]")


# ─── Schedule with assignment reasons ────────────────────────────


def render_schedule(engine: PMEngine, project: str = ""):
    """Schedule showing assignments with rationale."""
    tasks = engine.load_tasks(project)
    cp = engine.critical_path_analysis(tasks)
    critical_set = set(cp.path)
    assignments = engine.auto_assign(tasks, explain=True)
    assign_map = {a.task_id: a for a in assignments}

    console.print()
    console.print(Panel(
        f"[bold]📅 项目排期[/]  [dim]{project or 'all'}[/]  "
        f"[dim]串行{sum(t.estimated_hours for t in tasks):.0f}h → "
        f"并行优化{cp.total_hours:.0f}h[/]",
        border_style="cyan",
    ))

    serial = sum(t.estimated_hours for t in tasks)
    console.print(
        f"[green]节省 {serial - cp.total_hours:.0f}h "
        f"({(1-cp.total_hours/max(1,serial))*100:.0f}%)[/]  "
        f"[dim]已分配 {len(assignments)}/{len([t for t in tasks if t.status == 'pending'])} 个待处理任务[/]"
    )
    console.print()

    table = Table(box=box.ROUNDED, border_style="blue", header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("任务", style="bold", max_width=22)
    table.add_column("类型", style="dim", width=10)
    table.add_column("状态", justify="center")
    table.add_column("分配", style="green", width=14)
    table.add_column("预估", justify="right")
    table.add_column("评分", justify="right", width=5)
    table.add_column("理由", style="dim", max_width=30)

    for task in tasks:
        icon = _status_icon(task.status)
        critical_mark = "🔴" if task.id in critical_set else "  "
        a = assign_map.get(task.id)
        assignee = a.agent_name if a else (task.assignee or "—")
        score = f"{a.score:.0%}" if a else "—"
        reason = (a.reasons[0] if a.reasons else "")[:28] if a else ""

        table.add_row(
            f"{critical_mark}{task.id}",
            task.name[:20],
            task.task_type[:10],
            icon,
            assignee[:14],
            f"{task.estimated_hours:.0f}h",
            score,
            reason,
        )

    console.print(table)

    if cp.path:
        console.print(f"\n[bold red]🔗 关键路径:[/] {' → '.join(cp.path[:8])}  [dim]({cp.total_hours:.0f}h)[/]")


# ─── Agent Profile (new) ─────────────────────────────────────────


def render_profile(engine: PMEngine, agent_name: str):
    """Show detailed agent capability profile."""
    profile = engine.get_agent_profile(agent_name)
    if not profile:
        console.print(f"[red]Agent '{agent_name}' not found.[/]")
        console.print(f"[dim]Available: {', '.join(p.name for p in engine.build_agent_profiles()[:15])}[/]")
        return

    console.print()
    console.print(Panel(
        f"[bold]{profile.name}[/]  "
        f"{'🟢' if profile.status == 'active' else '🔴'} {profile.status}  "
        f"[dim]{profile.role or 'no role'}[/]",
        border_style="cyan",
    ))

    # Row 1: Core stats
    stats = (
        f"[bold]成功完成:[/] {profile.completed_tasks}/{profile.total_tasks} "
        f"({profile.success_rate:.0%})  "
        f"[bold]Skills:[/] {profile.skill_count}  "
        f"[bold]负载:[/] {profile.load_pct:.0%}  "
        f"[bold]模型:[/] {profile.model or '?'}"
    )
    console.print(Panel(stats, border_style="blue"))
    console.print()

    # Row 2: Skills + History (side by side)
    layout = Layout()
    layout.split_row(Layout(name="left", ratio=1), Layout(name="right", ratio=1))

    # Top skills
    sl = ["[bold]🧠 Top Skills[/]"]
    skill_levels = {"L5": "red", "L4": "yellow", "L3": "green", "L2": "cyan", "L1": "dim"}
    for s in profile.top_skills:
        sl.append(f"  • {s}")
    if profile.owned_modules:
        sl.append("")
        sl.append("[bold]📦 负责模块[/]")
        for m in profile.owned_modules:
            sl.append(f"  • {m}")
    layout["left"].update(Panel("\n".join(sl), border_style="green"))

    # Task type history
    hl = ["[bold]📊 历史任务类型[/]"]
    for ttype, hist in sorted(profile.task_type_history.items(),
                               key=lambda x: x[1]["total"], reverse=True)[:8]:
        rate = hist["completed"] / max(1, hist["total"])
        bar = "█" * int(rate * 8) + "░" * (8 - int(rate * 8))
        hl.append(
            f"  {ttype:18s} [{bar}] "
            f"{hist['completed']}/{hist['total']} ({rate:.0%})"
        )
    layout["right"].update(Panel("\n".join(hl), border_style="yellow"))

    console.print(layout)
    console.print()

    # Expertise
    if profile.expertise:
        exp_lines = ["[bold]🎯 专业领域[/]"]
        for e in profile.expertise[:6]:
            exp_lines.append(f"  • {e}")
        console.print(Panel("\n".join(exp_lines), border_style="dim"))


# ─── Health (enhanced) ───────────────────────────────────────────


def render_health(engine: PMEngine):
    """Health check with detailed agent profiles."""
    report = engine.health_check()

    console.print()
    console.print(Panel("[bold]🩺 Agent 健康检查[/]", border_style="cyan"))

    profiles = engine.build_agent_profiles()

    table = Table(box=box.ROUNDED, border_style="blue", header_style="bold cyan")
    table.add_column("Agent", style="bold")
    table.add_column("状态", justify="center")
    table.add_column("角色", style="dim", max_width=14)
    table.add_column("负载", justify="center")
    table.add_column("完成率", justify="center")
    table.add_column("Skills", justify="center")
    table.add_column("擅长", style="dim", max_width=20)

    for p in profiles[:18]:
        icon = {"active": "🟢", "warning": "🟡", "offline": "🔴"}.get(p.status, "⚪")
        bar = "█" * int(p.load_pct * 4) + "░" * (4 - int(p.load_pct * 4))
        best_type = max(p.task_type_history.items(),
                        key=lambda x: x[1]["total"]) if p.task_type_history else ("—", {})
        best_name = best_type[0] if best_type[0] != "—" else "—"

        table.add_row(
            p.name[:20],
            icon,
            (p.role or "—")[:14],
            bar,
            f"{p.completed_tasks}/{p.total_tasks}",
            str(p.skill_count),
            best_name[:18],
        )

    console.print(table)
    console.print()

    if report["alerts"]:
        for a in report["alerts"]:
            console.print(f"  {a}")
    if report["recommendations"]:
        for r in report["recommendations"]:
            console.print(f"  💡 {r}")


# ─── Timeline (with assignment annotations) ──────────────────────


def render_timeline(engine: PMEngine, project: str = ""):
    """Timeline with assignment annotations."""
    tasks = engine.load_tasks(project)
    if not tasks:
        console.print("[dim]No tasks.[/]")
        return

    cp = engine.critical_path_analysis(tasks)
    critical_set = set(cp.path)
    assignments = engine.auto_assign(tasks, explain=True)
    assign_map = {a.task_id: a for a in assignments}

    console.print()
    console.print(Panel(
        f"[bold]📊 任务时间线[/]  [dim]{project or 'all'}[/]",
        border_style="cyan",
    ))
    console.print()

    for task in tasks[:30]:
        icon = _status_icon(task.status)
        critical = "🔴" if task.id in critical_set else "  "
        bar_len = min(30, int(task.estimated_hours * 3))
        bar = "▓" * max(1, bar_len)
        a = assign_map.get(task.id)
        assignee = a.agent_name if a else (task.assignee or "未分配")
        score = f" [{a.score:.0%}]" if a else ""
        deps = f" ← {','.join(task.dependencies[:2])}" if task.dependencies else ""

        console.print(
            f"{critical} {icon} {task.id:10s} "
            f"[{'red' if task.id in critical_set else 'dim'}]{bar}[/] "
            f"{task.estimated_hours:.0f}h  "
            f"[dim]{task.name[:28]:28s}[/] "
            f"[green]{assignee:14s}{score}[/]{deps}"
        )

    console.print()
    console.print(f"[dim]🔴=关键路径  │  预计 {cp.total_hours:.1f}h[/]")


# ─── Helpers ──────────────────────────────────────────────────────


def _find_task(tasks: list[Task], task_id: str) -> Task | None:
    for t in tasks:
        if t.id == task_id:
            return t
    return None


def _status_icon(status: str) -> str:
    return {
        "completed": "✅", "in_progress": "🔄",
        "pending": "⏳", "blocked": "🚫",
    }.get(status, "❓")
