"""Apex — status command"""
from __future__ import annotations

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from agentark.core.profile import ProfileManager, AGENTARK_HOME
from agentark.core.skills import SkillManager
from agentark.orchestration.kanban import Kanban


def show_status(console: Console):
    """Display Apex status"""

    pm = ProfileManager()
    profiles = pm.list()

    # Profile status table
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
            table.add_row(name, "[red]Failed to load[/]", "", "")

    console.print(table)

    # Skills status
    skills_db = AGENTARK_HOME / "skills.db"
    if skills_db.exists():
        sm = SkillManager(skills_db)
        skills = sm.list()
        if skills:
            skill_table = Table(title="🧠 Registered Skills", box=None)
            skill_table.add_column("Name", style="cyan")
            skill_table.add_column("Success Rate", style="green")
            skill_table.add_column("Use Count", style="yellow")
            for s in skills[:10]:
                skill_table.add_row(
                    s.name,
                    f"{s.success_rate():.0%}",
                    str(s.use_count),
                )
            console.print(skill_table)

    # Kanban status
    kanban_db = AGENTARK_HOME / "kanban.db"
    if kanban_db.exists():
        k = Kanban(kanban_db)
        tasks = k.list_tasks()
        if tasks:
            board = Table(title="📋 Task Board", box=None)
            board.add_column("ID", style="dim")
            board.add_column("Task", style="white")
            board.add_column("Assignee", style="cyan")
            board.add_column("Status", style="green")
            board.add_column("Priority")
            for t in tasks[:15]:
                status_icon = {
                    "todo": "📋", "ready": "🟡", "in_progress": "🚧",
                    "blocked": "🚫", "done": "✅", "failed": "❌",
                }.get(t.status, "◻️")
                board.add_row(t.id, t.title[:40], t.assignee, f"{status_icon} {t.status}", str(t.priority))
            console.print(board)

    # Apex info
    info = Panel.fit(
        f"[bold]Apex v0.1.0[/] — One person, infinite capacity.\n"
        f"Profiles: {len(profiles)} | Skills: Ready | Kanban: {'❌' if not kanban_db.exists() else '✅'}\n"
        f"Home: {AGENTARK_HOME}\n"
        f"Provider: deepseek (chat)"
    )
    console.print(info)
