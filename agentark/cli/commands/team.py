"""Apex — team command"""
from __future__ import annotations

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
import click

from agentark.core.profile import ProfileManager


def create_cmd(name: str):
    """Create a new Agent"""
    console = Console()
    pm = ProfileManager()

    if name in pm.list():
        console.print(f"[yellow]⚠ Profile '{name}' already exists[/]")
        return

    role = Prompt.ask("Role name", default=name)
    expertise_str = Prompt.ask("Expertise (comma-separated)", default="")
    expertise = [e.strip() for e in expertise_str.split(",") if e.strip()]

    pm.create_default(name, role=role, expertise=expertise)
    console.print(f"[green]✅ Profile '{name}' created successfully (Role: {role})[/]")


def list_cmd():
    """List all Agents"""
    console = Console()
    pm = ProfileManager()
    profiles = pm.list()

    table = Table(title="Agent List", box=None)
    table.add_column("Name", style="cyan")
    table.add_column("Role", style="green")
    table.add_column("Model", style="yellow")
    table.add_column("Skills", style="magenta")

    for name in profiles:
        try:
            p = pm.load(name)
            table.add_row(name, p.soul.role or "-", p.model.default, ", ".join(p.skills[:3]) or "-")
        except Exception:
            table.add_row(name, "[red]Failed to load[/]", "", "")
    console.print(table)


def show_cmd(name: str):
    """Show Agent details"""
    console = Console()
    pm = ProfileManager()

    try:
        p = pm.load(name)
        info = Panel.fit(
            f"[bold]Name:[/] {p.name}\n"
            f"[bold]Display:[/] {p.display}\n"
            f"[bold]Role:[/] {p.soul.role}\n"
            f"[bold]Expertise:[/] {', '.join(p.soul.expertise)}\n"
            f"[bold]Personality:[/] {p.soul.personality}\n"
            f"[bold]Model:[/] {p.model.default} (fallback: {p.model.fallback})\n"
            f"[bold]Token Budget:[/] {p.token_budget:,}\n"
            f"[bold]Skills:[/] {', '.join(p.skills) or '-'}\n"
            f"[bold]Auto Improve:[/] {'✅' if p.auto_improve else '❌'}",
            title=f"📋 {name}",
        )
        console.print(info)
    except FileNotFoundError:
        console.print(f"[red]✗ Profile '{name}' does not exist[/]")
