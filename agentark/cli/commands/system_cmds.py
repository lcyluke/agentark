"""Apex — System Command Group

All system management under one roof: skill, economy, evolution, knowledge, autonomous

Usage:
  apex system skill list              — List skills
  apex system economy status          — Economy status
  apex system evolution status        — Evolution status  
  apex system knowledge query <q>     — Query knowledge graph
  apex system autonomous status       — Autonomous engine status
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


# ── Skill subcommands ──

def skill_list_cmd(category: str = "", show_agent: bool = False):
    """List all skills or agent skill levels."""
    from agentark.cli.commands.skill_mgmt import list_cmd as _l
    _l(category=category, agent=show_agent)


def skill_show_cmd(agent_name: str):
    """Show agent skill levels with evidence chain."""
    from agentark.cli.commands.skill_mgmt import show_cmd as _s
    _s(agent_name)


def skill_assess_cmd(agent_name: str, skill_spec: str, confidence: str = ""):
    """Assess/update agent skill level."""
    from agentark.cli.commands.skill_mgmt import assess_cmd as _a
    _a(agent_name, skill_spec, confidence)


def skill_match_cmd(task: str, difficulty: str = "L2", required_skills: str = ""):
    """Find best agent for a task by skill matching."""
    from agentark.cli.commands.skill_mgmt import match_cmd as _m
    _m(task, difficulty, required_skills)


def skill_evaluate_cmd():
    """Run skill evaluation pipeline."""
    from agentark.cli.commands.skill_mgmt import evaluate_cmd as _e
    _e()


def skill_sync_cmd(agent_name: str):
    """Generate SKILL.md for agent's Hermes profile."""
    from agentark.cli.commands.skill_mgmt import sync_cmd as _s
    _s(agent_name)


# ── Economy subcommands ──

def economy_status_cmd():
    """View economy status."""
    from agentark.cli.commands.economy import status_cmd as _es
    _es()


def economy_classify_cmd(task: str):
    """Test task classification and routing."""
    from agentark.cli.commands.economy import classify_cmd as _ec
    _ec(task)


# ── Evolution subcommands ──

def evolution_status_cmd():
    """Evolution engine status."""
    from agentark.cli.commands.evolution import status_cmd as _es
    _es()


def evolution_agent_cmd(name: str):
    """Agent evolution report."""
    from agentark.cli.commands.evolution import agent_cmd as _ea
    _ea(name)


# ── Knowledge subcommands ──

def knowledge_query_cmd(question: str):
    """Query knowledge graph."""
    from agentark.core.knowledge import KnowledgeGraph
    kg = KnowledgeGraph()
    result = kg.query(question)
    console.print(Panel(
        result.answer,
        title=f"🔍 Knowledge Graph: {question[:40]}",
        border_style="cyan",
    ))
    console.print(
        f"[dim]Confidence: {result.confidence:.1%} | "
        f"Evidence: {len(result.evidence)} items | "
        f"Reasoning paths: {len(result.reasoning_path)}[/]"
    )


def knowledge_stats_cmd():
    """Knowledge graph statistics."""
    from agentark.core.knowledge import KnowledgeGraph
    kg = KnowledgeGraph()
    stats = kg.stats()
    table = Table(title="📊 Knowledge Graph Statistics", box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    for k, v in stats.items():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                table.add_row(f"  {k2}", str(v2))
        else:
            table.add_row(k, str(v))
    console.print(table)


# ── Autonomous subcommands ──

def autonomous_status_cmd():
    """Show full autonomous engine report."""
    from agentark.cli.commands.autonomous import status_cmd as _as
    _as()


def autonomous_start_cmd():
    """Start the autonomous engine (7x24 mode)."""
    from agentark.cli.commands.autonomous import start_cmd as _as
    _as()


def autonomous_stop_cmd():
    """Stop the autonomous engine."""
    from agentark.cli.commands.autonomous import stop_cmd as _as
    _as()


def autonomous_pause_cmd():
    """Pause task dispatch (heartbeat continues)."""
    from agentark.cli.commands.autonomous import pause_cmd as _ap
    _ap()


def autonomous_resume_cmd():
    """Resume task dispatch."""
    from agentark.cli.commands.autonomous import resume_cmd as _ar
    _ar()


def autonomous_schedule_cmd(name: str, cron: str, task: str, agent: str = ""):
    """Schedule a recurring task."""
    from agentark.cli.commands.autonomous import schedule_cmd as _asc
    _asc(name, cron, task, agent)


def autonomous_unschedule_cmd(task_id: str):
    """Remove a scheduled task."""
    from agentark.cli.commands.autonomous import unschedule_cmd as _auc
    _auc(task_id)


def autonomous_alerts_cmd():
    """Show unresolved alerts."""
    from agentark.cli.commands.autonomous import alerts_cmd as _aac
    _aac()
