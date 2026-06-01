"""Apex — team 命令"""
from __future__ import annotations

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
import click

from apex.core.profile import ProfileManager


def create_cmd(name: str):
    """创建一个新Agent"""
    console = Console()
    pm = ProfileManager()

    if name in pm.list():
        console.print(f"[yellow]⚠ Profile '{name}' 已存在[/]")
        return

    role = Prompt.ask("角色名称", default=name)
    expertise_str = Prompt.ask("专长（逗号分隔）", default="")
    expertise = [e.strip() for e in expertise_str.split(",") if e.strip()]

    pm.create_default(name, role=role, expertise=expertise)
    console.print(f"[green]✅ Profile '{name}' 创建成功 (Role: {role})[/]")


def list_cmd():
    """列出所有Agent"""
    console = Console()
    pm = ProfileManager()
    profiles = pm.list()

    table = Table(title="Agent列表", box=None)
    table.add_column("Name", style="cyan")
    table.add_column("Role", style="green")
    table.add_column("Model", style="yellow")
    table.add_column("Skills", style="magenta")

    for name in profiles:
        try:
            p = pm.load(name)
            table.add_row(name, p.soul.role or "-", p.model.default, ", ".join(p.skills[:3]) or "-")
        except Exception:
            table.add_row(name, "[red]加载失败[/]", "", "")
    console.print(table)


def show_cmd(name: str):
    """显示Agent详情"""
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
        console.print(f"[red]✗ Profile '{name}' 不存在[/]")
