"""Apex — template CLI command"""
from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from agentark.core.templates import list_templates, get_template, TEMPLATES
from agentark.core.profile import ProfileManager


console = Console()


def list_cmd():
    """List all available templates"""
    templates = list_templates()
    
    table = Table(title="📦 Agent Template Library — Ready to Use", box=None)
    table.add_column("", style="dim", width=4)
    table.add_column("Template", style="cyan", width=12)
    table.add_column("Role", style="green", width=20)
    table.add_column("Expertise Highlights", style="white")
    
    for i, t in enumerate(templates, 1):
        expertise_bullets = ", ".join(t.expertise[:4])
        rest = f"... +{len(t.expertise)-4}" if len(t.expertise) > 4 else ""
        table.add_row(
            f"{t.icon}",
            t.name,
            t.display,
            f"{expertise_bullets}{rest}"
        )
    
    console.print(table)
    console.print(f"\n[dim]{len(templates)} templates total · Usage: [bold]apex template use <template-name>[/bold][/dim]")


def show_cmd(name: str):
    """Show template details"""
    t = get_template(name)
    if not t:
        console.print(f"[red]✗ Template '{name}' does not exist. Available: {', '.join(TEMPLATES.keys())}[/]")
        return
    
    info = Panel.fit(
        f"[bold]{t.icon} {t.display}[/] ({t.name})\n\n"
        f"[bold]Description:[/] {t.description}\n\n"
        f"[bold]Personality:[/] {t.personality}\n"
        f"[bold]Communication Style:[/] {t.communication}\n"
        f"[bold]Default Model:[/] {t.default_model}\n\n"
        f"[bold]Expertise ({len(t.expertise)}):[/]\n" + 
        "\n".join(f"  • {e}" for e in t.expertise) + "\n\n"
        f"[bold]Skill Pack ({len(t.skills)}):[/]\n" +
        "\n".join(f"  • {s}" for s in t.skills) + "\n\n"
        f"[bold]Built-in Tools:[/] {', '.join(t.tools)}\n"
        f"[bold]Auto Evolution:[/] ✅",
        title=f"📋 Template Details: {t.name}",
    )
    console.print(info)


def use_cmd(name: str, alias: str = None):
    """Create Agent from template"""
    t = get_template(name)
    if not t:
        console.print(f"[red]✗ Template '{name}' does not exist. Available: {', '.join(TEMPLATES.keys())}[/]")
        return
    
    target_name = alias or t.name
    pm = ProfileManager()
    
    if target_name in pm.list():
        confirm = Confirm.ask(f"[yellow]⚠ Profile '{target_name}' already exists, overwrite?[/]", default=False)
        if not confirm:
            console.print("[yellow]Cancelled[/]")
            return
    
    profile = t.to_profile(target_name)
    pm.save(profile)
    
    console.print(Panel.fit(
        f"[bold green]✅ Agent '{target_name}' is ready![/]\n\n"
        f"[bold]Role:[/] {t.display}\n"
        f"[bold]Expertise:[/] {len(t.expertise)} areas\n"
        f"[bold]Skill Pack:[/] {len(t.skills)} skills\n"
        f"[bold]Model:[/] {t.default_model}\n"
        f"[bold]Auto Evolution:[/] ✅\n\n"
        f"Try: [bold]apex run \"your task\" --profile {target_name}[/]",
        title=f"🎯 {t.icon} {t.display} has joined the fleet"
    ))
