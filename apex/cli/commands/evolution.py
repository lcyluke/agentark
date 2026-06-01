"""Apex — evolution CLI命令"""
from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from apex.core.evolution import EvolutionEngine
from apex.core.profile import APEX_HOME

console = Console()


def status_cmd():
    """查看进化状态"""
    evo = EvolutionEngine()
    summary = evo.summary()

    table = Table(title="🧬 技能进化引擎", box=None)
    table.add_column("指标", style="cyan")
    table.add_column("数值", style="green")

    table.add_row("总执行次数", str(summary["total_executions"]))
    table.add_row("已发现模式", str(summary["patterns_discovered"]))
    table.add_row("有历史Agent", str(summary["agents_with_history"]))
    table.add_row("质量数据可用", "✅" if summary["quality_available"] else "❌")

    console.print(table)


def agent_cmd(name: str):
    """查看Agent进化报告"""
    evo = EvolutionEngine()
    report = evo.get_agent_evolution(name)

    if report["total_executions"] == 0:
        console.print(f"[yellow]Agent '{name}' 还没有执行记录[/]")
        return

    table = Table(title=f"🧬 {name} 进化报告", box=None)
    table.add_column("指标", style="cyan")
    table.add_column("数值", style="green")

    table.add_row("总执行次数", str(report["total_executions"]))
    table.add_row("成功率", report["success_rate"])
    table.add_row("已学习模式", str(report["learned_patterns"]))

    console.print(table)

    # 质量趋势
    if report["quality_trend"]:
        quality_table = Table(title="📈 质量趋势", box=None)
        quality_table.add_column("次数", style="dim")
        quality_table.add_column("质量分", style="green")
        for entry in report["quality_trend"][-10:]:
            bar = "█" * int(entry["score"] * 10)
            quality_table.add_row(str(entry["n"]), f"{entry['score']:.2f} {bar}")
        console.print(quality_table)
