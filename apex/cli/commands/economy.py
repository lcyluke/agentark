"""Apex — economy CLI命令"""
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
    """查看经济系统状态"""
    bm = BudgetManager()
    
    accounts = ["default"]
    
    table = Table(title="💰 Token Economy — 预算状态", box=None)
    table.add_column("项目", style="cyan")
    table.add_column("月度限额", style="yellow")
    table.add_column("已用", style="red")
    table.add_column("剩余", style="green")
    table.add_column("使用率", style="white")
    
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
    
    # 今日成本
    report = bm.get_daily_report()
    console.print(Panel(report, title="📅 今日统计"))
    
    # 预警
    for proj in accounts:
        warning = bm.check_warning(proj)
        if warning:
            console.print(f"[yellow]⚠ {warning}[/]")
    
    # 模型路由表
    route_table = Table(title="🔄 智能路由规则", box=None)
    route_table.add_column("任务类型", style="cyan")
    route_table.add_column("模型", style="green")
    route_table.add_column("成本/1K输入", style="yellow")
    route_table.add_column("质量分", style="white")
    
    for route in MODEL_ROUTES:
        cost_str = f"${route.cost_per_1k_input:.4f}" if route.cost_per_1k_input > 0 else "[green]免费[/]"
        route_table.add_row(route.task_type, route.model, cost_str, "⭐" * (route.quality_score // 2))
    
    console.print(route_table)


def classify_cmd(task: str):
    """测试任务分类"""
    task_type = classify_task(task)
    from apex.economy import select_model
    route = select_model(task)
    
    console.print(f"[bold]任务:[/] {task}")
    console.print(f"[bold]分类:[/] [cyan]{task_type}[/]")
    console.print(f"[bold]推荐模型:[/] [green]{route.model}[/] ({route.provider})")
    console.print(f"[bold]质量分:[/] {'⭐' * (route.quality_score // 2)}")
    console.print(f"[bold]预估成本:[/] [yellow]${route.cost_per_1k_input:.4f}/1K输入[/]")
