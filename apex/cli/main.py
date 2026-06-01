"""Apex — CLI main framework"""
from __future__ import annotations

import sys
import os
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .commands.init import init_project
from .commands.run import run_task
from .commands.status import show_status
from .commands import team as team_cmds
from .commands import template as template_cmds
from .commands import economy as economy_cmds
from .commands import evolution as evolution_cmds
from .commands.company import CompanyBuilder, list_companies
from apex.orchestration.crew import crew as crew_group

# New mode CLIs
from apex.orchestration import (
    Router, Debate, Supervisor, Monitor, Chain
)
from apex.core.profile import ProfileManager

console = Console()


@click.group()
@click.version_option(version="0.1.0", message="Apex v0.1.0 — One person, infinite capacity.")
def cli():
    """Apex — The most popular multi-Agent operating system in the universe"""
    pass


@cli.command()
@click.argument("name")
@click.option("--dir", "-d", default=".", help="Project directory")
def init(name: str, dir: str):
    """Initialize a new Apex project"""
    init_project(name, Path(dir).resolve(), console)


@cli.command()
@click.argument("task")
@click.option("--profile", "-p", default="default", help="Agent Profile to use")
@click.option("--model", "-m", help="Override model name")
@click.option("--swarm", "-s", is_flag=True, help="Use Swarm mode")
@click.option("--workers", "-w", default=3, help="Number of parallel Swarm workers")
def run(task: str, profile: str, model: str, swarm: bool, workers: int):
    """Execute a task"""
    run_task(task, profile, model, swarm, workers, console)


@cli.command()
def status():
    """View current Apex status"""
    show_status(console)


@cli.group()
def team():
    """Manage Agent teams"""
    pass


# ─── team subcommands ───
@team.command(name="create")
@click.argument("name")
def team_create(name: str):
    """Create a new Agent"""
    team_cmds.create_cmd(name)

@team.command(name="list")
def team_list():
    """List all Agents"""
    team_cmds.list_cmd()

@team.command(name="show")
@click.argument("name")
def team_show(name: str):
    """Show Agent details"""
    team_cmds.show_cmd(name)


# ─── template subcommands ───
@cli.group()
def template():
    """Manage Agent templates"""
    pass

@template.command(name="list")
def template_list():
    """List all available templates"""
    template_cmds.list_cmd()

@template.command(name="show")
@click.argument("name")
def template_show(name: str):
    """Show template details"""
    template_cmds.show_cmd(name)

@template.command(name="use")
@click.argument("name")
@click.option("--alias", "-a", help="Custom Agent name")
def template_use(name: str, alias: str):
    """Create Agent from template"""
    template_cmds.use_cmd(name, alias)


# ─── crew subcommands ───
cli.add_command(crew_group)


# ─── economy commands ───
@cli.group()
def economy():
    """Token Economy — Budget and cost management"""
    pass

@economy.command(name="status")
def economy_status():
    """View economy status"""
    economy_cmds.status_cmd()

@economy.command(name="classify")
@click.argument("task")
def economy_classify(task: str):
    """Test task classification and routing"""
    economy_cmds.classify_cmd(task)


# ─── dashboard command ───
@cli.command()
@click.option("--port", "-p", default=8080, help="Port")
@click.option("--host", default="127.0.0.1", help="Bind address")
def dashboard(host: str, port: int):
    """Start Web Dashboard"""
    try:
        from apex.interface.web import run_dashboard
        run_dashboard(host=host, port=port)
    except ImportError as e:
        console.print(f"[red]✗ Failed to start: {e}[/]")
        console.print("Run [bold]pip install flask[/bold] to install dependencies")


# ─── company commands ───
@cli.group()
def company():
    """One-Click Company — Create an AI company"""
    pass

@company.command(name="create")
@click.argument("name")
@click.option("--industry", "-i", default="saas",
              type=click.Choice(["saas", "ai_product", "content", "ecommerce", "freelance"]),
              help="Industry type")
def company_create(name: str, industry: str):
    """Create an AI company (one command = one team)"""
    builder = CompanyBuilder()
    builder.create(name, industry)

@company.command(name="start")
@click.argument("name")
@click.argument("goal")
def company_start(name: str, goal: str):
    """Start a company to execute a task"""
    builder = CompanyBuilder()
    builder.start(name, goal)

@company.command(name="list")
def company_list():
    """List all companies"""
    list_companies()


# ─── knowledge commands ───
@cli.group()
def knowledge():
    """Knowledge Graph — Cross-Agent shared memory"""
    pass

@knowledge.command(name="query")
@click.argument("question")
def knowledge_query(question: str):
    """Query knowledge graph"""
    from apex.core.knowledge import KnowledgeGraph
    kg = KnowledgeGraph()
    result = kg.query(question)
    console.print(Panel(result.answer, title=f"🔍 Knowledge Graph: {question[:40]}", border_style="cyan"))
    console.print(f"[dim]Confidence: {result.confidence:.1%} | Evidence: {len(result.evidence)} items | Reasoning paths: {len(result.reasoning_path)}[/]")

@knowledge.command(name="stats")
def knowledge_stats():
    """Knowledge graph statistics"""
    from apex.core.knowledge import KnowledgeGraph
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


# ─── evolution commands ───
@cli.group()
def evolution():
    """Skill evolution engine — Agents get smarter with use"""
    pass

@evolution.command(name="status")
def evolution_status():
    """Evolution engine status"""
    evolution_cmds.status_cmd()

@evolution.command(name="agent")
@click.argument("name")
def evolution_agent(name: str):
    """Agent evolution report"""
    evolution_cmds.agent_cmd(name)


# ─── chain commands ───
@cli.group()
def chain():
    """Sequential Chain — Pipeline agents with handoff verification"""
    pass

@chain.command(name="run")
@click.argument("goal")
@click.option("--pipeline", "-p", default="dev",
              type=click.Choice(["dev", "content", "data"]),
              help="Pipeline type: dev, content, or data")
def chain_run(goal: str, pipeline: str):
    """Run a sequential chain pipeline"""
    pm = ProfileManager()
    try:
        if pipeline == "content":
            c = Chain.content_pipeline(pm)
        elif pipeline == "data":
            c = Chain.data_pipeline(pm)
        else:
            c = Chain.dev_pipeline(pm)
        result = c.run(goal)
        console.print(Panel(result.assembled_output[:3000] if result.assembled_output else str(result),
                           title=f"📦 Chain Result: {pipeline} pipeline",
                           border_style="green"))
    except Exception as e:
        console.print(f"[red]✗ Chain failed: {e}[/]")


# ─── debate command ───
@cli.command()
@click.argument("topic")
@click.option("--agents", "-a", default=3, help="Number of debating agents")
def debate(topic: str, agents: int):
    """Multi-agent debate — explore a topic from multiple perspectives"""
    try:
        from apex.orchestration.debate import Debate, DebatePosition
        from apex.core.templates import get_template
        pm = ProfileManager()

        positions = []
        stances = ["Pro", "Con", "Neutral"]
        templates = ["pm", "backend", "content"]
        for i in range(min(agents, 3)):
            t = get_template(templates[i])
            profile = t.to_profile(f"debater_{i}")
            pm.save(profile)
            positions.append(DebatePosition(
                agent_name=templates[i],
                profile=profile,
                stance=stances[i],
                expertise=t.expertise[:3],
            ))

        d = Debate(positions=positions)
        result = d.run(topic)
        console.print(Panel(result.synthesis[:3000], title="🎯 Debate Synthesis", border_style="green"))
    except Exception as e:
        console.print(f"[red]✗ Debate failed: {e}[/]")


# ─── router commands ───
@cli.group()
def router():
    """Smart Router — Classify and dispatch tasks to specialized agents"""
    pass

@router.command(name="route")
@click.argument("task")
@click.option("--agents", "-a", default="", help="Comma-separated: category:agent_name pairs")
def router_route(task: str, agents: str):
    """Route a task to the best matching agent"""
    pm = ProfileManager()
    r = Router()
    if agents:
        for pair in agents.split(","):
            if ":" in pair:
                cat, agent_name = pair.split(":", 1)
                r.register_route(cat.strip(), agent_name.strip())
    result = r.route(task)
    if result.success:
        console.print(Panel(result.output[:2000],
                           title=f"📬 Routed to: {result.agent_used} (category: {result.category})",
                           border_style="green"))
    else:
        console.print(f"[red]✗ Routing failed: {result.error}[/]")


# ─── supervisor command ───
@cli.command()
@click.argument("goal")
@click.option("--workers", "-w", default=3, help="Number of worker agents")
def supervisor(goal: str, workers: int):
    """Hierarchical supervision — manager delegates, reviews, approves"""
    try:
        pm = ProfileManager()
        s = Supervisor(pm=pm, max_parallel=workers)
        result = s.run(goal)
        console.print(Panel(result.merged_output[:3000] if result.merged_output else str(result),
                           title=f"✅ Supervisor Complete ({len(result.approved_items)} approved, {len(result.rejected_items)} rejected)",
                           border_style="green"))
    except Exception as e:
        console.print(f"[red]✗ Supervisor failed: {e}[/]")


# ─── monitor commands ───
@cli.group()
def monitor():
    """Reactive Monitor — Watch, detect anomalies, trigger agents"""
    pass

@monitor.command(name="check")
@click.option("--file", "-f", help="Log file path to watch for errors")
@click.option("--url", "-u", help="HTTP URL to health-check")
@click.option("--pattern", "-p", default="error|fail|exception", help="Regex pattern for log monitoring")
def monitor_check(file: str, url: str, pattern: str):
    """Run a single monitoring check"""
    try:
        from apex.orchestration.monitor import Monitor, WatcherRule
        m = Monitor()
        if file:
            m.add_rule(WatcherRule(
                name=f"check-{file}",
                type="file-watcher",
                target=file,
                config={"pattern": pattern},
            ))
        if url:
            m.add_rule(WatcherRule(
                name=f"health-{url[:30]}",
                type="http-health-check",
                target=url,
            ))
        result = m.run_cycle()
        console.print(f"[green]✅ Check complete: {len(result.anomalies)} anomalies[/]")
        for a in result.anomalies[:5]:
            console.print(f"  {'🔴' if a.severity == 'high' else '🟡'} {a.source}: {a.message[:80]}")
    except Exception as e:
        console.print(f"[red]✗ Monitor failed: {e}[/]")
