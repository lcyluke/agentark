"""Apex — economy CLI command"""
from __future__ import annotations

import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from apex.core.profile import APEX_HOME
from apex.economy import BudgetManager, classify_task, MODEL_ROUTES

console = Console()


def status_cmd():
    """View economy system status"""
    bm = BudgetManager()
    
    accounts = ["default"]
    
    table = Table(title="💰 Token Economy — Budget Status", box=None)
    table.add_column("Project", style="cyan")
    table.add_column("Monthly Limit", style="yellow")
    table.add_column("Used", style="red")
    table.add_column("Remaining", style="green")
    table.add_column("Usage", style="white")
    
    for proj in accounts:
        used, limit, remaining = bm.get_balance(proj)
        pct = used / limit * 100 if limit > 0 else 0
        pct_str = f"{pct:.1f}%"
        if pct > 80:
            pct_str = f"[red]{pct_str}[/]"
        elif pct > 50:
            pct_str = f"[yellow]{pct_str}[/]"
        else:
            pct_str = f"[green]{pct_str}[/]"
        table.add_row(proj, f"${limit:.2f}", f"${used:.4f}", f"${remaining:.4f}", pct_str)
    
    console.print(table)
    
    # Today's cost
    report = bm.get_daily_report()
    console.print(Panel(report, title="📅 Today's Statistics"))
    
    # Warnings
    for proj in accounts:
        warning = bm.check_warning(proj)
        if warning:
            console.print(f"[yellow]⚠ {warning}[/]")
    
    # Model routing table
    route_table = Table(title="🔄 Smart Routing Rules", box=None)
    route_table.add_column("Task Type", style="cyan")
    route_table.add_column("Model", style="green")
    route_table.add_column("Cost/1K Input", style="yellow")
    route_table.add_column("Quality Score", style="white")
    
    for route in MODEL_ROUTES:
        cost_str = f"${route.cost_per_1k_input:.4f}" if route.cost_per_1k_input > 0 else "[green]Free[/]"
        route_table.add_row(route.task_type, route.model, cost_str, "⭐" * (route.quality_score // 2))
    
    console.print(route_table)


def classify_cmd(task: str):
    """Test task classification"""
    task_type = classify_task(task)
    from apex.economy import select_model
    route = select_model(task)
    
    console.print(f"[bold]Task:[/] {task}")
    console.print(f"[bold]Classification:[/] [cyan]{task_type}[/]")
    console.print(f"[bold]Recommended Model:[/] [green]{route.model}[/] ({route.provider})")
    console.print(f"[bold]Quality Score:[/] {'⭐' * (route.quality_score // 2)}")
    console.print(f"[bold]Estimated Cost:[/] [yellow]${route.cost_per_1k_input:.4f}/1K Input[/]")
