"""Apex — Mode Command Group

All collaboration modes under one roof: chain, debate, supervise, pipeline

Usage:
  apex mode chain <goal> -p <type>     — Sequential chain pipeline
  apex mode debate <topic>              — Multi-agent debate
  apex mode supervise <goal> -w <n>     — Hierarchical supervision
  apex mode pipeline normal <req>       — Normal pipeline flow
  apex mode pipeline direct <task>      — Direct task to agent
  apex mode pipeline status <id>        — Pipeline status
  apex mode pipeline confirm <id>       — Approve pipeline gate
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from agentark.core.profile import ProfileManager

console = Console()


def chain_cmd(goal: str, pipeline_type: str = "dev"):
    """⛓️ Run a sequential chain pipeline."""
    from agentark.orchestration import Chain
    pm = ProfileManager()
    try:
        if pipeline_type == "content":
            c = Chain.content_pipeline(pm)
        elif pipeline_type == "data":
            c = Chain.data_pipeline(pm)
        else:
            c = Chain.dev_pipeline(pm)
        result = c.run(goal)
        console.print(Panel(
            result.assembled_output[:3000] if result.assembled_output else str(result),
            title=f"⛓️ Chain Result: {pipeline_type} pipeline",
            border_style="green",
        ))
    except Exception as e:
        console.print(f"[red]✗ Chain failed: {e}[/]")


def debate_cmd(topic: str, agents: int = 3):
    """🎯 Multi-agent debate — explore a topic from multiple perspectives."""
    try:
        from agentark.orchestration.debate import Debate, DebatePosition
        from agentark.core.templates import get_template
        pm = ProfileManager()
        positions = []
        stances = ["Pro", "Con", "Neutral"]
        templates_list = ["pm", "backend", "content"]
        for i in range(min(agents, 3)):
            t = get_template(templates_list[i])
            profile = t.to_profile(f"debater_{i}")
            pm.save(profile)
            from agentark.orchestration.debate import DebatePosition
            positions.append(DebatePosition(
                agent_name=templates_list[i],
                profile=profile,
                stance=stances[i],
                expertise=t.expertise[:3],
            ))
        d = Debate(positions=positions)
        result = d.run(topic)
        console.print(Panel(
            result.synthesis[:3000],
            title="🎯 Debate Synthesis",
            border_style="green",
        ))
    except Exception as e:
        console.print(f"[red]✗ Debate failed: {e}[/]")


def supervise_cmd(goal: str, workers: int = 3):
    """🏛️ Hierarchical supervision — manager delegates, reviews, approves."""
    try:
        pm = ProfileManager()
        from agentark.orchestration import Supervisor
        s = Supervisor(pm=pm, max_parallel=workers)
        result = s.run(goal)
        approved = getattr(result, 'approved_items', [])
        rejected = getattr(result, 'rejected_items', [])
        console.print(Panel(
            result.merged_output[:3000] if hasattr(result, 'merged_output') and result.merged_output else str(result),
            title=f"✅ Supervisor Complete ({len(approved)} approved, {len(rejected)} rejected)",
            border_style="green",
        ))
    except Exception as e:
        console.print(f"[red]✗ Supervisor failed: {e}[/]")


def pipeline_normal_cmd(requirement: str, project: str = "finopsai", auto_confirm: bool = True):
    """📋 Normal pipeline: requirement → AI decompose → dispatch → monitor."""
    from agentark.cli.commands.pipeline_cmds import pipeline_normal_cmd as _pn
    _pn(requirement, project, auto_confirm)


def pipeline_direct_cmd(task: str, agent: str, project: str = "finopsai", priority: int = 1):
    """⚡ Direct pipeline: command → target agent → execute immediately."""
    from agentark.cli.commands.pipeline_cmds import pipeline_direct_cmd as _pd
    _pd(task, agent, project, priority)


def pipeline_status_cmd(pipeline_id: str):
    """📊 View pipeline status."""
    from agentark.cli.commands.pipeline_cmds import pipeline_status_cmd as _ps
    _ps(pipeline_id)


def pipeline_confirm_cmd(pipeline_id: str):
    """✅ Confirm pipeline to continue."""
    from agentark.cli.commands.pipeline_cmds import pipeline_confirm_cmd as _pc
    _pc(pipeline_id)
