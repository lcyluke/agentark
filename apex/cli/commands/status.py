"""Apex — status 命令"""
from __future__ import annotations

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from apex.core.profile import ProfileManager, APEX_HOME
from apex.core.skills import SkillManager
from apex.orchestration.kanban import Kanban


def show_status(console: Console):
    """显示Apex状态"""

    pm = ProfileManager()
    profiles = pm.list()

    # Profile状态表
    table = Table(title="🤖 Agent Profiles", box=None)
    table.add_column("Name", style="cyan")
    table.add_column("Role", style="green")
    table.add_column("Model", style="yellow")
    table.add_column("Skills", style="magenta")

    for name in profiles:
        try:
            p = pm.load(name)
            table.add_row(
                name,
                p.soul.role or "-",
                p.model.default,
                ", ".join(p.skills[:3]) or "-",
            )
        except Exception:
            table.add_row(name, "[red]加载失败[/]", "", "")

    console.print(table)

    # Skills状态
    skills_db = APEX_HOME / "skills.db"
    if skills_db.exists():
        sm = SkillManager(skills_db)
        skills = sm.list()
        if skills:
            skill_table = Table(title="🧠 已注册技能", box=None)
            skill_table.add_column("Name", style="cyan")
            skill_table.add_column("成功率", style="green")
            skill_table.add_column("使用次数", style="yellow")
            for s in skills[:10]:
                skill_table.add_row(
                    s.name,
                    f"{s.success_rate():.0%}",
                    str(s.use_count),
                )
            console.print(skill_table)

    # Kanban状态
    kanban_db = APEX_HOME / "kanban.db"
    if kanban_db.exists():
        k = Kanban(kanban_db)
        tasks = k.list_tasks()
        if tasks:
            board = Table(title="📋 任务看板", box=None)
            board.add_column("ID", style="dim")
            board.add_column("任务", style="white")
            board.add_column("负责人", style="cyan")
            board.add_column("状态", style="green")
            board.add_column("优先级")
            for t in tasks[:15]:
                status_icon = {
                    "todo": "📋", "ready": "🟡", "in_progress": "🚧",
                    "blocked": "🚫", "done": "✅", "failed": "❌",
                }.get(t.status, "◻️")
                board.add_row(t.id, t.title[:40], t.assignee, f"{status_icon} {t.status}", str(t.priority))
            console.print(board)

    # Apex信息
    info = Panel.fit(
        f"[bold]Apex v0.1.0[/] — One person, infinite capacity.\n"
        f"Profiles: {len(profiles)} | Skills: 就绪 | Kanban: {'❌' if not kanban_db.exists() else '✅'}\n"
        f"Home: {APEX_HOME}\n"
        f"Provider: deepseek (chat)"
    )
    console.print(info)
