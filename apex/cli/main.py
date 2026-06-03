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
from .commands import bridge as bridge_cmds
from .commands import origin as origin_cmds
from apex.orchestration.crew import crew as crew_group
from .commands import autonomous as autonomous_cmds
from .commands import ops as ops_cmds
from .commands import task_mgmt as task_cmds

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


# ─── demo command ───
@cli.command()
@click.option("--port", "-p", default=8080, help="Dashboard port")
@click.option("--host", default="127.0.0.1", help="Bind address")
@click.option("--no-browser", is_flag=True, help="Don't open browser")
@click.option("--skip-tasks", is_flag=True, help="Don't create demo tasks")
def demo(port: int, host: str, no_browser: bool, skip_tasks: bool):
    """Run Apex demo — create AI fleet and open Command Center"""
    try:
        from apex.cli.commands.demo import run_demo
        run_demo(console=console, port=port, host=host,
                 no_browser=no_browser, skip_tasks=skip_tasks)
    except Exception as e:
        console.print(f"[red]✗ Demo failed: {e}[/]")
        import traceback
        console.print(traceback.format_exc())


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


# ─── autonomous commands ───
@cli.group()
def autonomous():
    """🤖 Autonomous Engine — 7x24 self-aware operation"""
    pass


@autonomous.command(name="start")
def autonomous_start():
    """Start the autonomous engine (7x24 mode)"""
    autonomous_cmds.start_cmd()


@autonomous.command(name="stop")
def autonomous_stop():
    """Stop the autonomous engine"""
    autonomous_cmds.stop_cmd()


@autonomous.command(name="pause")
def autonomous_pause():
    """Pause task dispatch (heartbeat continues)"""
    autonomous_cmds.pause_cmd()


@autonomous.command(name="resume")
def autonomous_resume():
    """Resume task dispatch"""
    autonomous_cmds.resume_cmd()


@autonomous.command(name="status")
def autonomous_status():
    """Show full autonomous engine report"""
    autonomous_cmds.status_cmd()


@autonomous.command(name="schedule")
@click.argument("name")
@click.argument("cron")
@click.argument("task")
@click.option("--agent", "-a", default="", help="Agent profile to assign")
def autonomous_schedule(name: str, cron: str, task: str, agent: str):
    """Schedule a recurring task

    NAME is a human-readable name for this schedule.
    CRON can be a cron expression (e.g. '*/5 * * * *') or human-readable
    interval (e.g. 'every 30m', 'every 2h').
    TASK is the description of the task to execute.
    """
    autonomous_cmds.schedule_cmd(name, cron, task, agent)


@autonomous.command(name="unschedule")
@click.argument("task_id")
def autonomous_unschedule(task_id: str):
    """Remove a scheduled task by its ID"""
    autonomous_cmds.unschedule_cmd(task_id)


# ════════════════════════════════════════════════════════════
# 🌉 BRIDGE — Hermes ↔ Apex 无缝集成
# ════════════════════════════════════════════════════════════

@cli.group()
def bridge():
    """🌉 Hermes Bridge — 6-agent monitor fleet + live sync"""
    pass


@bridge.command(name="init")
def bridge_init():
    """Create/update the 6 default bridge monitoring agents"""
    bridge_cmds.init_bridge_agents(console)


@bridge.command(name="sync")
def bridge_sync():
    """Run one sync cycle — update Kanban from Hermes state.db"""
    bridge_cmds.run_bridge_sync(console)


@bridge.command(name="status")
def bridge_status():
    """Show bridge agent fleet health"""
    data = bridge_cmds.get_bridge_status()
    table = Table(title="🌉 Apex-Hermes Bridge — Fleet Status", box=None)
    table.add_column("Agent", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Info", style="dim")

    for a in data.get("agents", []):
        icon = {"done": "✅", "in_progress": "🟡", "blocked": "🔴"}.get(a["status"], "⬜")
        info = (a.get("output", "") or "")[:60].replace("\n", " ")
        table.add_row(f"{icon} {a['assignee']}", a["status"], info)

    console.print(table)
    console.print(f"\n[dim]Healthy: {data['healthy']} | Degraded: {data['degraded']} | Offline: {data['offline']}[/]")


@bridge.command(name="agents")
def bridge_agents():
    """List all 6 bridge monitoring agents"""
    from apex.core.profile import ProfileManager
    pm = ProfileManager()
    table = Table(title="🤖 Bridge Monitoring Agents", box=None)
    table.add_column("Name", style="cyan")
    table.add_column("Role", style="green")
    table.add_column("Expertise", style="yellow")

    for name, cfg in bridge_cmds.BRIDGE_AGENTS.items():
        try:
            pm.load(name)
            icon = "✅"
        except FileNotFoundError:
            icon = "⬜"
        table.add_row(f"{icon} {name}", cfg["role"], ", ".join(cfg["expertise"][:3]))

    console.print(table)
    console.print("\n[dim]Run [bold]apex bridge init[/] to create/update all 6 agents.[/]")


# ════════════════════════════════════════════════════════════
# ⚓ ORIGIN — 始祖Agent · 项目群总指挥官
# ════════════════════════════════════════════════════════════

@cli.group()
def origin():
    """⚓ Origin Agent — 始祖Agent · 项目群总指挥"""
    pass


@origin.command(name="init")
def origin_init():
    """Initialize/deploy the Origin Agent"""
    origin_cmds.init_cmd(console)


@origin.command(name="replicate")
@click.argument("target", required=False)
@click.option("--all", "all_agents", is_flag=True, help="Replicate to all project agents")
@click.option("--strategy", "-s", default="merge",
              type=click.Choice(["merge", "replace", "pm"]),
              help="merge(合并) / replace(替换) / pm(PM模板)")
def origin_replicate(target: str, all_agents: bool, strategy: str):
    """Replicate skills to target agent(s)"""
    origin_cmds.replicate_cmd(console, target=target or "",
                              all_agents=all_agents, strategy=strategy)


@origin.group()
def portfolio():
    """📊 Portfolio — 项目群管理"""
    pass


@portfolio.command(name="list")
def portfolio_list():
    """List all portfolios"""
    origin_cmds.portfolio_cmd(console, action="list")


@portfolio.command(name="create")
@click.argument("name")
@click.option("--pm", "-p", default="", help="PM agent name")
@click.option("--goal", "-g", default="", help="Strategic goal")
@click.option("--outcome", "-o", default="", help="Expected outcome")
@click.option("--desc", "-d", default="", help="Description")
def portfolio_create(name: str, pm: str, goal: str, outcome: str, desc: str):
    """Create a new portfolio"""
    origin_cmds.portfolio_cmd(console, action="create",
                              name=name, pm_agent=pm or "",
                              strategic_goal=goal, expected_outcome=outcome,
                              description=desc)


@portfolio.command(name="status")
@click.argument("portfolio_id")
def portfolio_status(portfolio_id: str):
    """Show portfolio status + milestones + tasks"""
    origin_cmds.portfolio_cmd(console, action="status", portfolio_id=portfolio_id)


@origin.command(name="overview")
def origin_overview():
    """⚓ Fleet overview — all portfolios status"""
    origin_cmds.overview_cmd(console)




@autonomous.command(name="list-scheduled")
def autonomous_list_scheduled():
    """List all scheduled tasks"""
    autonomous_cmds.list_scheduled_cmd()


# ─── ops commands ───
@cli.group()
def ops():
    """📊 Operations — Multi-Agent release & bug management"""
    pass

@ops.command(name="status")
def ops_status():
    """Ops dashboard summary"""
    ops_cmds.status_cmd()

@ops.group()
def release():
    """Release pipeline management"""
    pass

@release.command(name="create")
@click.argument("version")
@click.option("--name", "-n", help="Release name")
def release_create(version: str, name: str):
    """Create a new release pipeline"""
    ops_cmds.release_create_cmd(version, name)

@release.command(name="status")
def release_status():
    """Show current release status"""
    ops_cmds.release_status_cmd()

@release.command(name="list")
def release_list():
    """List all releases"""
    ops_cmds.release_list_cmd()

@ops.group()
def bug():
    """Bug tracking and management"""
    pass

@bug.command(name="list")
@click.option("--status", "-s", default="open", help="Filter by status")
@click.option("--severity", help="Filter by severity (critical/high/medium/low)")
def bug_list(status: str, severity: str):
    """List bugs"""
    ops_cmds.bug_list_cmd(status, severity)

@bug.command(name="create")
@click.argument("title")
@click.argument("description")
@click.option("--severity", "-s", default="medium",
              type=click.Choice(["critical", "high", "medium", "low"]))
@click.option("--steps", help="Steps to reproduce")
@click.option("--expected", help="Expected result")
@click.option("--actual", help="Actual result")
def bug_create(title: str, description: str, severity: str,
               steps: str, expected: str, actual: str):
    """Report a new bug"""
    ops_cmds.bug_create_cmd(title, description, severity, steps or "", expected or "", actual or "")

@bug.command(name="show")
@click.argument("bug_id")
def bug_show(bug_id: str):
    """Show bug details"""
    ops_cmds.bug_show_cmd(bug_id)

@ops.group()
def task():
    """Ops task management"""
    pass

@task.command(name="list")
@click.option("--status", help="Filter by status")
@click.option("--agent", "-a", help="Filter by agent")
def task_list(status: str, agent: str):
    """List ops tasks"""
    ops_cmds.task_list_cmd(status, agent)

@task.command(name="create")
@click.argument("title")
@click.option("--description", "-d", default="", help="Task description")
@click.option("--phase", "-p", default="development",
              type=click.Choice(["requirement", "development", "test", "uat", "release"]))
@click.option("--priority", default=2, type=int, help="Priority (0-3, lower=higher)")
@click.option("--agent", "-a", default="", help="Assigned agent")
def task_create(title: str, description: str, phase: str, priority: int, agent: str):
    """Create an ops task"""
    ops_cmds.task_create_cmd(title, description, phase, priority, agent)

@ops.command(name="expert-list")
def ops_expert_list():
    """List open expert consultation tickets"""
    ops_cmds.expert_list_cmd()


@autonomous.command(name="alerts")
def autonomous_alerts():
    """Show unresolved alerts"""
    autonomous_cmds.alerts_cmd()


# ─── task management commands ───
@cli.group()
def task():
    """📋 Task Management — Hierarchical tasks with PM workflow"""
    pass

@task.command(name="create")
@click.argument("title")
@click.option("--description", "-d", default="", help="Task description")
@click.option("--type", "-t", "task_type", default="task",
              type=click.Choice(["epic", "story", "task", "subtask"]), help="Task type")
@click.option("--phase", "-p", default="development", help="Development phase")
@click.option("--priority", default=2, type=int, help="Priority (0-3)")
@click.option("--assignee", "-a", default="", help="Assign to agent")
@click.option("--parent", default="", help="Parent task ID")
@click.option("--project", default="", help="Project name")
@click.option("--hours", default=0.0, type=float, help="Estimated hours")
def task_create(title: str, description: str, task_type: str, phase: str,
                priority: int, assignee: str, parent: str, project: str, hours: float):
    """Create a hierarchical task"""
    task_cmds.task_create_cmd(title, description, task_type, phase, priority, assignee, parent, project, hours)

@task.command(name="list")
@click.option("--project", help="Filter by project")
@click.option("--assignee", "-a", help="Filter by assignee")
@click.option("--type", "-t", "task_type", help="Filter by task type")
@click.option("--status", "-s", help="Filter by workflow status")
@click.option("--phase", "-p", help="Filter by phase")
def task_list(project: str, assignee: str, task_type: str, status: str, phase: str):
    """List hierarchical tasks"""
    task_cmds.task_list_cmd(project or "", assignee or "", task_type or "", status or "", phase or "")

@task.command(name="show")
@click.argument("task_id")
def task_show(task_id: str):
    """Show task with full tree"""
    task_cmds.task_show_cmd(task_id)

@task.command(name="status")
@click.argument("task_id")
@click.argument("new_status")
@click.option("--notes", "-n", default="", help="PM notes or feedback")
def task_status(task_id: str, new_status: str, notes: str):
    """Transition task workflow status (draft→requested→pm_review→approved→assigned→
    in_progress→completed→pm_verify→verified→closed)"""
    task_cmds.task_status_cmd(task_id, new_status, notes)

@task.command(name="epic")
@click.argument("epic_title", required=False, default="")
def task_epic(epic_title: str):
    """Show epic tree overview"""
    task_cmds.epic_cmd(epic_title or "")

@cli.command()
@click.option("--agent", "-a", default="", help="Filter by agent name")
def capacity(agent: str):
    """🤖 Show agent capacity and load"""
    task_cmds.capacity_cmd(agent)

@cli.command()
def dispatch():
    """📨 Auto-dispatch tasks to agents by capacity"""
    task_cmds.dispatch_cmd()

@cli.command()
@click.argument("agent")
@click.argument("title")
@click.option("--description", "-d", default="", help="Description of help needed")
@click.option("--task", "-t", default="", help="Source task ID")
def help_request(agent: str, title: str, description: str, task: str):
    """🆘 Request help from PM for another agent"""
    task_cmds.help_request_cmd(agent, title, description, task)

@cli.command()
@click.argument("request_id")
@click.option("--agent", "-a", required=True, help="Helper agent to assign")
@click.option("--notes", "-n", default="", help="PM notes")
def help_approve(request_id: str, agent: str, notes: str):
    """✅ PM approves help request and assigns helper"""
    task_cmds.help_approve_cmd(request_id, agent, notes)

@cli.command()
@click.option("--status", "-s", default="", help="Filter by status")
def help_list(status: str):
    """📋 List help requests"""
    task_cmds.help_list_cmd(status or "")


# ─── hermes integration commands ───
@cli.group()
def hermes():
    """🤖 Hermes Integration — Manage & launch Hermes agent profiles"""
    pass

@hermes.command(name="start")
@click.argument("profile_name")
@click.option("--query", "-q", default="", help="Initial query (non-interactive)")
def hermes_start(profile_name: str, query: str):
    """Launch Hermes with a specific agent profile
    
    Opens a new Hermes chat session with the given profile's 
    role, personality, and capabilities pre-configured.
    The terminal will show the agent's role name, not 'Hermes'.
    """
    from apex.interface.hermes_sync import start_hermes_profile
    start_hermes_profile(profile_name, query)

@hermes.command(name="profiles")
def hermes_profiles():
    """List all Hermes profiles"""
    from apex.interface.hermes_sync import list_hermes_profiles
    from rich.console import Console
    from rich.table import Table
    console = Console()
    profiles = list_hermes_profiles()
    if not profiles:
        console.print("[yellow]No Hermes profiles found[/]")
        return
    table = Table(title="🤖 Hermes Profiles", box=None)
    table.add_column("Profile", style="cyan")
    table.add_column("Role", style="white")
    table.add_column("Config", style="green")
    table.add_column("SOUL.md", style="green")
    table.add_column("Wrapper", style="green")
    for p in profiles:
        table.add_row(
            p["name"],
            p.get("title", "—")[:30],
            "✅" if p["has_config"] else "❌",
            "✅" if p["has_soul"] else "❌",
            "✅" if p["has_wrapper"] else "❌",
        )
    console.print(table)


# ─── team template commands ───
@team.command(name="sync")
@click.argument("profile_name")
@click.option("--hermes-name", help="Name for the Hermes profile (default: same)")
@click.option("--display", help="Display name in SOUL.md")
def team_sync(profile_name: str, hermes_name: str, display: str):
    """Sync an Apex profile to a Hermes profile (config + SOUL.md + wrapper)"""
    from apex.interface.hermes_sync import sync_profile_to_hermes
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
    result = sync_profile_to_hermes(
        profile_name,
        hermes_profile_name=hermes_name,
        hermes_display_name=display,
    )
    console.print(Panel(
        f"[bold]✅ Synced: {result['profile_name']}[/]\n"
        f"Role: {result['display_name']}\n"
        f"SOUL.md: {result['soul_file']}\n"
        f"Wrapper: [green]{result['wrapper_path']}[/]\n\n"
        f"Run: [bold cyan]{result['profile_name']} chat[/]",
        title="🤖 → Hermes Profile", border_style="green",
    ))

@team.command(name="sync-all")
def team_sync_all():
    """Sync all Apex profiles to Hermes"""
    from apex.interface.hermes_sync import sync_all_profiles
    from rich.console import Console
    from rich.table import Table
    console = Console()
    results = sync_all_profiles()
    table = Table(title="📋 Profile Sync Results", box=None)
    table.add_column("Profile", style="cyan")
    table.add_column("Status", style="green")
    for r in results:
        status = r.get("error", "✅")
        table.add_row(r["profile_name"], status)
    console.print(table)

@team.command(name="template")
@click.argument("template_name")
@click.option("--setup-script", is_flag=True, help="Generate setup shell script")
def team_template(template_name: str, setup_script: bool):
    """Create a full agent team from a template
    
    Templates: webapp, content, data, startup, research
    """
    from apex.interface.hermes_sync import create_team_from_template, get_team_setup_script, TEAM_TEMPLATES
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    console = Console()

    if template_name == "list":
        table = Table(title="📋 Available Team Templates", box=None)
        table.add_column("Template", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Description", style="dim")
        table.add_column("Roles", style="green")
        for name, tmpl in TEAM_TEMPLATES.items():
            table.add_row(name, tmpl["name"], tmpl["description"][:50], ", ".join(tmpl["profiles"]))
        console.print(table)
        return

    if setup_script:
        script = get_team_setup_script(template_name, template_name)
        console.print(script)
        return

    try:
        team = create_team_from_template(template_name)
        console.print(Panel(
            f"[bold]✅ Team Created: {team['name']}[/]\n"
            f"Template: {team['template']}\n"
            f"Agents: {team['total']}",
            title="🚀 Team Ready", border_style="green",
        ))
        table = Table(box=None)
        table.add_column("Profile", style="cyan")
        table.add_column("Role", style="white")
        table.add_column("Wrapper", style="green")
        for p in team["profiles"]:
            table.add_row(p["profile_name"], p["display_name"], p["wrapper_path"])
        console.print(table)
        console.print("\n[bold]Open terminals and run:[/]")
        for p in team["profiles"]:
            console.print(f"  [cyan]{p['profile_name']} chat[/]  # {p['display_name']}")
    except ValueError as e:
        console.print(f"[red]❌ {e}[/]")
