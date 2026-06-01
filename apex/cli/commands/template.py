"""Apex — template CLI命令"""
from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from apex.core.templates import list_templates, get_template, TEMPLATES
from apex.core.profile import ProfileManager


console = Console()


def list_cmd():
    """列出所有可用模板"""
    templates = list_templates()
    
    table = Table(title="📦 Agent模板库 — 即开即用", box=None)
    table.add_column("", style="dim", width=4)
    table.add_column("模板名", style="cyan", width=12)
    table.add_column("角色", style="green", width=20)
    table.add_column("专长亮点", style="white")
    
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
    console.print(f"\n[dim]共 {len(templates)} 个模板 · 使用: [bold]apex template use <模板名>[/bold][/dim]")


def show_cmd(name: str):
    """显示模板详情"""
    t = get_template(name)
    if not t:
        console.print(f"[red]✗ 模板 '{name}' 不存在. 可用: {', '.join(TEMPLATES.keys())}[/]")
        return
    
    info = Panel.fit(
        f"[bold]{t.icon} {t.display}[/] ({t.name})\n\n"
        f"[bold]描述:[/] {t.description}\n\n"
        f"[bold]性格:[/] {t.personality}\n"
        f"[bold]沟通风格:[/] {t.communication}\n"
        f"[bold]默认模型:[/] {t.default_model}\n\n"
        f"[bold]专长 ({len(t.expertise)}):[/]\n" + 
        "\n".join(f"  • {e}" for e in t.expertise) + "\n\n"
        f"[bold]技能包 ({len(t.skills)}):[/]\n" +
        "\n".join(f"  • {s}" for s in t.skills) + "\n\n"
        f"[bold]内置工具:[/] {', '.join(t.tools)}\n"
        f"[bold]自动进化:[/] ✅",
        title=f"📋 模板详情: {t.name}",
    )
    console.print(info)


def use_cmd(name: str, alias: str = None):
    """使用模板创建Agent"""
    t = get_template(name)
    if not t:
        console.print(f"[red]✗ 模板 '{name}' 不存在. 可用: {', '.join(TEMPLATES.keys())}[/]")
        return
    
    target_name = alias or t.name
    pm = ProfileManager()
    
    if target_name in pm.list():
        confirm = Confirm.ask(f"[yellow]⚠ Profile '{target_name}' 已存在，覆盖？[/]", default=False)
        if not confirm:
            console.print("[yellow]已取消[/]")
            return
    
    profile = t.to_profile(target_name)
    pm.save(profile)
    
    console.print(Panel.fit(
        f"[bold green]✅ Agent '{target_name}' 就绪！[/]\n\n"
        f"[bold]角色:[/] {t.display}\n"
        f"[bold]专长:[/] {len(t.expertise)}项\n"
        f"[bold]技能包:[/] {len(t.skills)}个\n"
        f"[bold]模型:[/] {t.default_model}\n"
        f"[bold]自动进化:[/] ✅\n\n"
        f"试试: [bold]apex run \"你的任务\" --profile {target_name}[/]",
        title=f"🎯 {t.icon} {t.display} 已加入舰队"
    ))
