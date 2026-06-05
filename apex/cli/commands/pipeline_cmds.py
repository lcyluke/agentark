"""Pipeline CLI commands.

Commands:
  apex pipeline normal <requirement>   — 正常流程: 需求→拆解→分派
  apex pipeline direct <task>          — 专项直达: 指令→Agent
  apex pipeline status <id>            — 查看管线状态
  apex pipeline confirm <id>           — 人工确认继续
"""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from apex.orchestration.pipeline import (
    run_normal_pipeline, run_direct_pipeline, smart_route,
    PipelineMode, Stage, resolve_agent,
)
from apex.orchestration.task_manager import get_task_manager

console = Console()


def pipeline_normal_cmd(requirement: str, project: str = "finopsai", auto_confirm: bool = True):
    """正常流程管线"""
    console.print(f"\n[bold cyan]📋 正常流程管线[/]")
    console.print(f"[dim]项目: {project} | 需求: {requirement[:60]}...[/]\n")

    tm = get_task_manager()

    with console.status("[bold green]🔍 分析拆解中..."):
        run = run_normal_pipeline(
            requirement=requirement,
            project=project,
            auto_confirm=auto_confirm,
            task_manager=tm,
        )

    # 显示Epic
    console.print(Panel(
        f"[bold]{run.epic_title}[/]\n"
        f"[dim]{run.requirement[:100]}[/]",
        title="📋 Epic",
    ))

    # 显示任务列表
    table = Table(title="拆解任务", box=box.SIMPLE)
    table.add_column("#", style="dim", width=3)
    table.add_column("任务", width=40)
    table.add_column("Agent", width=18)
    table.add_column("工时", width=6)
    table.add_column("优先级", width=6)

    for i, t in enumerate(run.tasks, 1):
        p_icon = {0: "🔴", 1: "🟠", 2: "🟡", 3: "🟢"}.get(t.get("priority", 1), "⚪")
        table.add_row(
            str(i), t.get("title", "")[:40],
            t.get("assignee", "-"),
            f"{t.get('hours', 0)}h", p_icon,
        )

    console.print(table)

    # 显示阶段
    console.print(f"\n[bold]当前阶段:[/] {run.stage.value}")
    console.print(f"[bold]管线ID:[/] [dim]{run.id}[/]")

    if run.task_ids:
        console.print(f"\n[bold green]✅ 已创建 {len(run.task_ids)} 个任务[/]")
        for tid in run.task_ids[:5]:
            console.print(f"   • {tid}")

    return run


def pipeline_direct_cmd(task: str, agent: str, project: str = "finopsai", priority: int = 1):
    """专项直达管线"""
    console.print(f"\n[bold yellow]⚡ 专项直达管线[/]")
    console.print(f"[dim]项目: {project} | Agent: {agent} | 优先级: {priority}[/]\n")

    # 解析Agent名称
    resolved = resolve_agent(agent, project)
    if resolved != agent:
        console.print(f"[dim]Agent解析: {agent} → {resolved}[/]")

    tm = get_task_manager()

    with console.status("[bold green]🚀 创建任务..."):
        run = run_direct_pipeline(
            task=task,
            project=project,
            agent=resolved,
            priority=priority,
            task_manager=tm,
        )

    console.print(Panel(
        f"[bold]🎯 {resolved}[/]\n"
        f"任务: {task[:100]}\n"
        f"优先级: {priority} | 阶段: {run.stage.value}",
        title="⚡ 直达任务",
    ))

    if run.task_ids:
        console.print(f"\n[bold green]✅ 任务已创建:[/] {run.task_ids[0]}")
        console.print(f"[bold]管线ID:[/] [dim]{run.id}[/]")
    else:
        console.print(f"\n[bold red]❌ 创建失败[/] — 阶段: {run.stage.value}")

    return run


def pipeline_status_cmd(pipeline_id: str):
    """查看管线状态"""
    console.print(f"\n[bold]管线状态:[/] [dim]{pipeline_id}[/]")
    console.print("[yellow]管线状态查询需要持久化存储，当前版本仅支持内存追踪[/]")
    console.print("[dim]提示: 使用 apex task list --project <name> 查看已创建的任务[/]")


def pipeline_confirm_cmd(pipeline_id: str):
    """人工确认管线"""
    console.print(f"\n[bold]确认管线:[/] [dim]{pipeline_id}[/]")
    console.print("[yellow]人工确认需要持久化存储，当前版本仅支持auto_confirm模式[/]")
