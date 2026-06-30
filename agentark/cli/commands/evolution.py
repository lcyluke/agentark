"""Apex — evolution CLI command"""
from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from agentark.core.evolution import EvolutionEngine
from agentark.core.profile import AGENTARK_HOME

console = Console()


def status_cmd():
    """View evolution status"""
    evo = EvolutionEngine()
    summary = evo.summary()

    table = Table(title="🧬 Skill Evolution Engine", box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Executions", str(summary["total_executions"]))
    table.add_row("Patterns Discovered", str(summary["patterns_discovered"]))
    table.add_row("Agents with History", str(summary["agents_with_history"]))
    table.add_row("Quality Data Available", "✅" if summary["quality_available"] else "❌")

    console.print(table)


def agent_cmd(name: str):
    """View Agent evolution report"""
    evo = EvolutionEngine()
    report = evo.get_agent_evolution(name)

    if report["total_executions"] == 0:
        console.print(f"[yellow]Agent '{name}' has no execution history yet[/]")
        return

    table = Table(title=f"🧬 {name} Evolution Report", box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Executions", str(report["total_executions"]))
    table.add_row("Success Rate", report["success_rate"])
    table.add_row("Learned Patterns", str(report["learned_patterns"]))

    console.print(table)

    # Quality trend
    if report["quality_trend"]:
        quality_table = Table(title="📈 Quality Trend", box=None)
        quality_table.add_column("Run", style="dim")
        quality_table.add_column("Quality Score", style="green")
        for entry in report["quality_trend"][-10:]:
            bar = "█" * int(entry["score"] * 10)
            quality_table.add_row(str(entry["n"]), f"{entry['score']:.2f} {bar}")
        console.print(quality_table)
