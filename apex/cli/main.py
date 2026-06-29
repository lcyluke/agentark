"""AgentArk — CLI main framework

Designed with 7±2 group principle for intuitive command discovery.

Hierarchy:
  ⚓ apex
  ├── setup         🚀 First-time setup wizard
  ├── init          🚀 Initialize workspace/project
  ├── run           ▶️  Execute a task
  ├── chat          💬 Chat with an agent
  ├── dashboard     📊 Web Dashboard
  ├── demo          🎮 One-click demo
  │
  ├── task          📋 Task management (dispatch/list/epic/schedule/status)
  ├── team          👥 Agent team management (create/list/start/stop/template/sync)
  ├── fleet         🤖 Fleet monitoring (status/show/history/inspect/deploy)
  ├── mode          🔧 Collaboration modes (chain/debate/supervise/pipeline)
  ├── project       📦 Project management (create/analyze/list/sprint)
  ├── system        ⚙️  System management (skill/economy/evolution/knowledge/autonomous)
  ├── help          ❓ Help system (request/approve/list)
  ├── origin        ⚓ Origin Agent — portfolio commander
  └── integrate     🔗 Integrations (hermes/bridge/router/company)

Backward compatibility: old flat commands kept as hidden aliases.
"""

from __future__ import annotations

import sys
import os
import time
from pathlib import Path
from typing import Optional

# 🛑 Suppress macOS malloc stack logging noise in subprocesses
for _v in ("MallocStackLogging", "MallocStackLoggingNoCompact"):
    if _v in os.environ:
        del os.environ[_v]

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

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
from .commands import setup_cmds
from apex.orchestration.crew import crew as crew_group
from .commands import autonomous as autonomous_cmds
from .commands import ops as ops_cmds
from .commands import task_mgmt as task_cmds
from .commands import skill_mgmt as skill_cmds
from .commands import fleet_cmds
from .commands import schedule_cmds
from .commands import squad_cmds
from .commands import sprint as sprint_cmds
from .commands import chat_cmds

# NEW command module wrappers
from .commands import mode_cmds
from .commands import system_cmds as sys_cmds
from .commands import help_cmds
from .commands import survey_cmds

# New mode CLIs
from apex.orchestration import (
    Router, Debate, Supervisor, Monitor, Chain
)
from apex.core.profile import ProfileManager

console = Console()


# ════════════════════════════════════════════════════════════════
# ROOT CLI
# ════════════════════════════════════════════════════════════════


class AliasedGroup(click.Group):
    """Click group that resolves command aliases before failing."""

    def get_command(self, ctx, cmd_name):
        # Try exact match first
        cmd = super().get_command(ctx, cmd_name)
        if cmd is not None:
            return cmd
        # Try alias resolution
        from apex.interface.aliases import resolve_alias
        alias_target = resolve_alias(cmd_name)
        if alias_target:
            # Split "monitor status" → ["monitor", "status"]
            parts = alias_target.split()
            # Walk into subcommands
            current = self
            for part in parts:
                cmd = super(AliasedGroup, current).get_command(ctx, part)
                if cmd is None:
                    return None
                current = cmd
            return current
        return None

    def resolve_command(self, ctx, args):
        # Try alias resolution for the first arg
        if args:
            cmd_name = args[0]
            from apex.interface.aliases import resolve_alias
            alias_target = resolve_alias(cmd_name)
            if alias_target:
                # Replace alias with expanded args
                expanded = alias_target.split() + list(args[1:])
                return super().resolve_command(ctx, expanded)
        return super().resolve_command(ctx, args)


@click.group(cls=AliasedGroup, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version="0.5.1", message="AgentArk v0.5.1 — 46 Agents, 30 commands, infinite capacity.")
@click.pass_context
def cli(ctx):
    """⚓ AgentArk — One person, infinite capacity.

    Manage agents, run tasks, and orchestrate your AI fleet.

    Quick start:  agentark setup --quick
    Help:         apex <command> --help
    Version:      apex --version

    Shortcuts:    apex s (status)  apex p (pm)  apex fs (fleet status)
    """
    pass


# ═══════════════════════════════════════════════════════════════════════
# Custom Help Formatter — Hermes-style output
# ═══════════════════════════════════════════════════════════════════════

import shutil
from datetime import datetime


def format_apex_help(self, ctx, formatter):
    """OpenClaw-inspired help output — clean, colorful, grouped.

    Only applies to the root CLI group; sub-groups use standard Click format.
    """
    if getattr(self, "name", None) is not None and self.name not in (None, "cli"):
        original_format_help(self, ctx, formatter)
        return

    # ── Collect commands ──
    cmd_data = {}
    for name in self.list_commands(ctx):
        cmd = self.get_command(ctx, name)
        if cmd and not cmd.hidden:
            help_text = cmd.help or cmd.short_help or ""
            first_line = help_text.split("\n")[0].strip()
            import unicodedata
            if first_line and unicodedata.category(first_line[0]) == 'So':
                parts = first_line.split(" ", 1)
                first_line = parts[1].strip() if len(parts) > 1 else first_line
            # Mark groups (commands that have subcommands)
            is_group = isinstance(cmd, click.Group)
            cmd_data[name] = (first_line, is_group)

    groups = [
        ("Setup & Start", ["setup", "quickstart", "init", "demo", "model-detect"]),
        ("Local Management", ["fleet", "monitor", "version", "update", "theme", "alias", "tutorial", "doctor"]),
        ("Task Management", ["task", "run", "chat", "status"]),
        ("Team & Agents", ["team", "mode"]),
        ("PM & Project", ["pm", "project", "survey", "dashboard"]),
        ("System", ["system"]),
        ("Integration", ["help", "integrate", "origin"]),
    ]

    all_cmds = []
    for _, cmds in groups:
        all_cmds.extend(c for c in cmds if c in cmd_data)

    # ── Render ──
    # ANSI color helpers
    B = "\033[1m"; D = "\033[2m"; C = "\033[36m"; G = "\033[32m"; Y = "\033[33m"; R = "\033[0m"

    formatter.write("\n")
    formatter.write(f"{B}{C}AgentArk 0.5.1{R} — Multi-Agent Operating System. One person, infinite capacity.\n")
    formatter.write("\n")

    # Usage
    formatter.write(f"{B}Usage:{R} apex [options] [command]\n")
    formatter.write("\n")

    # Options
    formatter.write(f"{B}Options:{R}\n")
    opts = [
        ("-m, --model <model>",
         "Model override (e.g. deepseek-v4-pro). Applies to run/chat/team start."),
        ("-p, --profile <name>",
         "Agent profile to use. Applies to run. E.g. -p backend-dev"),
        ("-s, --swarm",
         "Use Swarm mode for parallel execution. Applies to run."),
        ("-w, --workers <n>",
         "Number of parallel workers for Swarm mode (default: 3)."),
        ("--token-limit <n>",
         "Per-session token cap. Applies to run/chat/team start."),
        ("--input-lines <n>",
         "TUI composer height in lines (default: 3)."),
        ("-h, --help",
         "Display help for command"),
        ("-V, --version",
         "Output the version number"),
    ]
    for flag, desc in opts:
        formatter.write(f"  {G}{flag:<35s}{R} {D}{desc}{R}\n")
    formatter.write("\n")

    # Commands
    formatter.write(f"{B}Commands:{R}\n")
    formatter.write(f"  {D}Hint: commands suffixed with * have subcommands. Run <command> --help for details.{R}\n")

    for group_name, cmd_names in groups:
        present = [n for n in cmd_names if n in cmd_data]
        if not present:
            continue
        formatter.write(f"  {B}{Y}{group_name}:{R}\n")
        for name in present:
            desc, is_group = cmd_data[name]
            suffix = f" {D}*{R}" if is_group else "  "
            marker = f"  {C}{name}{R}{suffix}"
            pad = 28 - len(name) - (2 if is_group else 0)
            formatter.write(f"    {marker}{' ' * max(pad, 1)}{D}{desc}{R}\n")
    formatter.write("\n")

    # Examples
    formatter.write(f"{B}Examples:{R}\n")
    examples = [
        ("agentark init", "Interactive project wizard — 8 steps, agent matching, tech stack"),
        ("agentark init --quick", "Quick project init with smart auto-detection"),
        ("agentark fleet init", "Create agent profiles + launch tmux fleet"),
        ("agentark monitor status", "Agent heartbeat + task status panel"),
        ("agentark chat backend-dev", "Chat with a specific agent"),
        ("agentark run \"Add login\" -p frontend-dev", "Execute a task with an agent"),
        ("agentark team template webapp", "Create a 4-agent development team"),
        ("agentark tutorial", "5-step interactive walkthrough"),
        ("agentark doctor", "System diagnostics + auto-fix"),
        ("agentark version", "Show version + check for updates"),
        ("agentark update", "Self-update to latest GitHub release"),
    ]
    for cmd_example, desc in examples:
        formatter.write(f"  {G}{cmd_example:<52s}{R} {D}{desc}{R}\n")
    formatter.write("\n")

    formatter.write(f"{D}Run 'agentark <command> --help' for more on a specific command.{R}\n")
    formatter.write("\n")


# Patch the help formatter on click.Group
# Save original before patching
original_format_help = click.Group.format_help
click.Group.format_help = format_apex_help

# ════════════════════════════════════════════════════════════════
# SETUP — 🚀 安装配置
# ════════════════════════════════════════════════════════════════

@cli.command()
@click.option("--quick", is_flag=True, help="Quick setup with defaults")
@click.option("--check", "check_mode", is_flag=True, help="Check installation status")
@click.option("--model", default=None, help="Default model (e.g. deepseek-v4-pro)")
@click.option("--token-limit", type=int, default=None, help="Token limit per session")
@click.option("--token-budget", type=int, default=None, help="Total token budget")
@click.option("--input-lines", type=int, default=None, help="Hermes TUI input lines (default: 3)")
def setup(quick: bool, check_mode: bool, model: Optional[str],
          token_limit: Optional[int], token_budget: Optional[int],
          input_lines: Optional[int]):
    """🚀 First-time setup: install, configure, launch your AI fleet

    Examples:

      agentark setup --quick            Quick setup (all defaults)

      apex setup --model deepseek-v4-pro

      apex setup --check            Check installation status
    """
    from apex.interface.setup_wizard import run_setup
    run_setup(quick=quick, check=check_mode, model=model or "",
              interactive=not quick)


# ════════════════════════════════════════════════════════════════
# TOP-LEVEL COMMANDS (daily use, no nesting)
# ════════════════════════════════════════════════════════════════

@cli.command()
@click.argument("name", default="my-project", required=False)
@click.option("--dir", "-d", default=".", help="Project directory")
@click.option("--quick", is_flag=True, help="Skip wizard, use smart defaults")
@click.option("--type", "-t", "project_type", help="Project type (saas-dashboard, webapp-fullstack, etc.)")
def init(name: str, dir: str, quick: bool, project_type: str):
    """🚀 Initialize a new Apex project — interactive wizard or quick mode

    8-step wizard: Identity → Type → Scale → Tech Stack → Agent Team
    → Integrations → Roadmap → Create

    Examples:

      apex init                          Full interactive wizard

      apex init my-saas                  Named project with wizard

      apex init --quick                  Bypass wizard, auto-detect from cwd

      apex init my-app --type cli-tool   Quick init as CLI tool project
    """
    if quick:
        from apex.interface.project_factory import quick_init
        quick_init(name, Path(dir).resolve(), console)
    else:
        from apex.interface.project_factory import ProjectFactory
        factory = ProjectFactory(name, Path(dir).resolve(), console)
        factory.run()


@cli.command()
@click.argument("task")
@click.option("--profile", "-p", default="default", help="Agent profile to use")
@click.option("--model", "-m", help="Override model (e.g. deepseek-v4-pro)")
@click.option("--token-limit", type=int, default=0, help="Max tokens per turn")
@click.option("--swarm", "-s", is_flag=True, help="Use Swarm mode")
@click.option("--workers", "-w", default=3, help="Number of parallel Swarm workers")
def run(task: str, profile: str, model: str, token_limit: int, swarm: bool, workers: int):
    """▶️  Execute a task

    Examples:

      apex run 'Add login page' --profile frontend-dev

      apex run 'Test API' --profile backend-dev --model deepseek-v4-pro --token-limit 5000
    """
    _configure_token_limit(profile, token_limit)
    run_task(task, profile, model, swarm, workers, console)


@cli.command()
def status():
    """📊 View current Apex status"""
    show_status(console)


@cli.command()
@click.argument("topic")
@click.option("--github-only", is_flag=True, help="Only open-source GitHub projects")
@click.option("--saas-only", is_flag=True, help="Only commercial/SaaS products")
@click.option("--quick", is_flag=True, help="Quick overview (less depth)")
@click.option("--output", "-o", default="rich", type=click.Choice(["rich", "markdown"]), help="Output format")
@click.option("--workers", "-w", default=3, type=int, help="Parallel research workers")
def survey(topic: str, github_only: bool, saas_only: bool, quick: bool, output: str, workers: int):
    """🔍 Competitive survey & market research

    \b
    Researches open-source (GitHub) and commercial products for any topic,
    comparing features, popularity, pricing, and community health.

    \b
    Examples:

      apex survey "AI FinOps"                           Full competitive analysis

      apex survey "multi-agent framework" --quick       Quick overview

      apex survey "Kubernetes cost" --github-only       Only open-source

      apex survey "project management" --saas-only      Only commercial

      apex survey "LLM agent tools" --output markdown   Markdown output
    """
    survey_cmds.survey_cmd(
        topic=topic,
        github_only=github_only,
        saas_only=saas_only,
        quick=quick,
        output=output,
        workers=workers,
    )


@cli.command()
@click.option("--port", "-p", default=8080, help="Port")
@click.option("--host", default="127.0.0.1", help="Bind address")
def dashboard(host: str, port: int):
    """📊 Start Web Dashboard"""
    try:
        from apex.interface.web import run_dashboard
        run_dashboard(host=host, port=port)
    except ImportError as e:
        console.print(f"[red]✗ Failed to start: {e}[/]")
        console.print("Run [bold]pip install flask[/bold] to install dependencies")


@cli.command()
@click.option("--port", "-p", default=8080, help="Dashboard port")
@click.option("--host", default="127.0.0.1", help="Bind address")
@click.option("--no-browser", is_flag=True, help="Don't open browser")
@click.option("--skip-tasks", is_flag=True, help="Don't create demo tasks")
@click.option("--overwrite", is_flag=True, help="Kill existing process on port and restart")
def demo(port: int, host: str, no_browser: bool, skip_tasks: bool, overwrite: bool):
    """🎮 Run AgentArk demo — create AI fleet and open Command Center"""
    try:
        from apex.cli.commands.demo import run_demo
        run_demo(console=console, port=port, host=host,
                 no_browser=no_browser, skip_tasks=skip_tasks,
                 overwrite=overwrite)
    except Exception as e:
        console.print(f"[red]✗ Demo failed: {e}[/]")


# ─── model detect command ───
@cli.command("model-detect")
def model_detect():
    """🔍 Auto-detect available AI models from environment, tools, and cloud"""
    try:
        from apex.cli.commands.model_detect import detect_models, auto_configure
        from rich.table import Table
        from rich.panel import Panel

        result = detect_models()
        console.print(Panel("🔍 Model Auto-Discovery", subtitle=f"Found {result['available']} providers", border_style="cyan"))
        
        # Tools detected
        if result["tools_detected"]:
            t = Table(title="📦 Detected AI Tools", show_header=True)
            t.add_column("Tool", style="cyan")
            t.add_column("Model Hint", style="green")
            t.add_column("Path")
            for tool in result["tools_detected"]:
                t.add_row(tool["name"], tool["model_hint"], tool["path"])
            console.print(t)
        
        # Available models
        providers = result.get("providers", {})
        if providers:
            t2 = Table(title="🤖 Available Models", show_header=True)
            t2.add_column("Provider", style="cyan")
            t2.add_column("Models", style="green")
            t2.add_column("Auth", style="dim")
            for p, info in providers.items():
                t2.add_row(p, ", ".join(info["models"]), info["auth_method"])
            console.print(t2)
            console.print(f"\n[bold green]→ Recommended:[/] {result['recommendation']}")
            console.print("\n[dim]To auto-configure: apex model-detect --apply <provider>[/dim]")
        else:
            console.print("[yellow]⚠ No model providers detected.[/]")
            console.print("[dim]Set API keys as env vars: DEEPSEEK_API_KEY / ANTHROPIC_API_KEY / OPENAI_API_KEY[/dim]")
    except Exception as e:
        console.print(f"[red]✗ Detection failed: {e}[/]")


# ════════════════════════════════════════════════════════════════
# TASK — 📋 任务管理
# ════════════════════════════════════════════════════════════════

@cli.group()
def task():
    """📋 Task Management — create, dispatch, schedule, track progress"""


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
    task_cmds.task_create_cmd(title, description, task_type, phase, priority,
                              assignee, parent, project, hours)


@task.command(name="list")
@click.option("--project", help="Filter by project")
@click.option("--assignee", "-a", help="Filter by assignee")
@click.option("--type", "-t", "task_type", help="Filter by task type")
@click.option("--status", "-s", help="Filter by workflow status")
@click.option("--phase", "-p", help="Filter by phase")
def task_list(project: str, assignee: str, task_type: str, status: str, phase: str):
    """List hierarchical tasks"""
    task_cmds.task_list_cmd(project or "", assignee or "", task_type or "",
                            status or "", phase or "")


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
    """Transition task workflow status"""
    task_cmds.task_status_cmd(task_id, new_status, notes)


@task.command(name="epic")
@click.argument("epic_title", required=False, default="")
def task_epic(epic_title: str):
    """Show epic tree overview"""
    task_cmds.epic_cmd(epic_title or "")


@task.command(name="dispatch")
def task_dispatch():
    """📨 Auto-dispatch tasks to agents by capacity"""
    task_cmds.dispatch_cmd()


@task.command(name="dispatch-smart")
@click.argument("requirement")
@click.option("--project", "-p", default="finopsai", help="Project key")
def task_dispatch_smart(requirement: str, project: str):
    """🧠 Smart dispatch: requirement → AI decompose → create tasks → auto-assign"""
    task_cmds.dispatch_smart_cmd(requirement, project)


@task.command(name="capacity")
@click.option("--agent", "-a", default="", help="Filter by agent name")
def task_capacity(agent: str):
    """🤖 Show agent capacity and load"""
    task_cmds.capacity_cmd(agent)


@task.command(name="schedule")
@click.argument("task_id", required=False)
@click.option("--project", "-p", default=None, help="Filter by project")
def task_schedule(task_id: Optional[str], project: Optional[str]):
    """📊 Show Gantt chart timeline for tasks"""
    schedule_cmds.view_cmd(task_id=task_id, project=project)


# ════════════════════════════════════════════════════════════════
# TEAM — 👥 开发团队管理
# ════════════════════════════════════════════════════════════════

@cli.group()
def team():
    """👥 Team Management — create, list, start, template, sync agents"""


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


@team.command(name="start")
@click.option("--input-lines", type=int, default=3, help="Hermes input lines")
@click.option("--model", "-m", default=None, help="Override default model")
@click.option("--token-limit", type=int, default=0, help="Max tokens per turn")
def team_start(input_lines: int, model: Optional[str], token_limit: int):
    """🚀 Launch all 5 dev agents in new Terminal windows

    Each window shows the agent name (e.g. frontend-dev ⚓ Apex)
    and a 3-line input composer by default.

    Examples:

      apex team start

      apex team start --input-lines 5 --model deepseek-v4-pro
    """
    squad_cmds.start_cmd(input_lines=input_lines, model=model, token_limit=token_limit)


@team.command(name="status")
def team_status():
    """Show dev squad readiness and methodology status"""
    squad_cmds.status_cmd()


@team.command(name="attach")
@click.argument("agent_name",
    type=click.Choice(["frontend-dev", "backend-dev", "fullstack-dev", "architect", "devops",
                       "vulnerability-scanner", "penetration-tester",
                       "security-by-design", "project-manager",
                       "qa-engineer", "requirements-analyst"]))
def team_attach(agent_name: str):
    """Show detailed info for a specific squad member"""
    squad_cmds.attach_cmd(agent_name)


@team.command(name="template")
@click.argument("template_name")
@click.option("--setup-script", is_flag=True, help="Generate setup shell script")
def team_template(template_name: str, setup_script: bool):
    """Create a full agent team from a template (webapp/content/data/startup/research)"""
    from apex.interface.hermes_sync import create_team_from_template, get_team_setup_script, TEAM_TEMPLATES
    if template_name == "list":
        t = Table(title="📋 Available Team Templates", box=None)
        t.add_column("Template", style="cyan")
        t.add_column("Name", style="white")
        t.add_column("Description", style="dim")
        t.add_column("Roles", style="green")
        for name, tmpl in TEAM_TEMPLATES.items():
            t.add_row(name, tmpl["name"], tmpl["description"][:50], ", ".join(tmpl["profiles"]))
        console.print(t)
        return
    if setup_script:
        console.print(get_team_setup_script(template_name, template_name))
        return
    try:
        team = create_team_from_template(template_name)
        console.print(Panel(
            f"[bold]✅ Team Created: {team['name']}[/]\n"
            f"Template: {team['template']}\n"
            f"Agents: {team['total']}",
            title="🚀 Team Ready", border_style="green",
        ))
        t = Table(box=None)
        t.add_column("Profile", style="cyan")
        t.add_column("Role", style="white")
        t.add_column("Wrapper", style="green")
        for p in team["profiles"]:
            t.add_row(p["profile_name"], p["display_name"], p["wrapper_path"])
        console.print(t)
        console.print("\n[bold]Open terminals and run:[/]")
        for p in team["profiles"]:
            console.print(f"  [cyan]{p['profile_name']} chat[/]  # {p['display_name']}")
    except ValueError as e:
        console.print(f"[red]❌ {e}[/]")


@team.command(name="sync")
@click.argument("profile_name")
@click.option("--hermes-name", help="Name for the Hermes profile")
@click.option("--display", help="Display name in SOUL.md")
def team_sync(profile_name: str, hermes_name: str, display: str):
    """Sync an Apex profile to a Hermes profile"""
    from apex.interface.hermes_sync import sync_profile_to_hermes
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
    results = sync_all_profiles()
    t = Table(title="📋 Profile Sync Results", box=None)
    t.add_column("Profile", style="cyan")
    t.add_column("Status", style="green")
    for r in results:
        t.add_row(r["profile_name"], r.get("error", "✅"))
    console.print(t)


@team.command(name="hermes")
@click.argument("profile_name")
@click.option("--query", "-q", default="", help="Initial query (non-interactive)")
@click.option("--input-lines", type=int, default=3, help="Hermes input lines")
@click.option("--model", "-m", default=None, help="Override default model")
@click.option("--token-limit", type=int, default=0, help="Max tokens per turn")
def team_hermes(profile_name: str, query: str, input_lines: int,
                model: Optional[str], token_limit: int):
    """Launch Hermes with a specific agent profile

    Opens a new Hermes chat session showing the agent's badge and name
    in the terminal title, with multi-line input (default: 3 lines).

    Examples:

      apex team hermes frontend-dev

      apex team hermes architect --query "Review this design" --input-lines 5
    """
    _configure_token_limit(profile_name, token_limit)
    _configure_profile_model(profile_name, model)
    _configure_input_lines(profile_name, input_lines)

    from apex.interface.hermes_sync import start_hermes_profile
    start_hermes_profile(profile_name, query)


# ════════════════════════════════════════════════════════════════
# FLEET — 🤖 舰队监控
# ════════════════════════════════════════════════════════════════

@cli.group()
def fleet():
    """🤖 Fleet Monitor — status, inspect, deploy, history"""


@fleet.command(name="status")
@click.option("--live", "-l", is_flag=True, help="Live-updating dashboard")
def fleet_status(live: bool):
    """Show fleet overview dashboard with agent states"""
    fleet_cmds.status_cmd(live=live)


@fleet.command(name="show")
@click.argument("agent_name")
def fleet_show(agent_name: str):
    """Show detailed agent information"""
    fleet_cmds.show_cmd(agent_name)


@fleet.command(name="refresh")
def fleet_refresh():
    """Force refresh all agent states"""
    fleet_cmds.refresh_cmd()


@fleet.command(name="history")
@click.option("--limit", "-n", default=10, help="Number of snapshots to show")
def fleet_history(limit: int):
    """Show fleet snapshot history"""
    fleet_cmds.history_cmd(limit=limit)


@fleet.command(name="inspect")
@click.option("--project", "-p", default="", help="Single project inspection")
@click.option("--pm", default="", help="PM agent for inspection")
def fleet_inspect(project: str, pm: str):
    """⚓ Fleet inspection — project progress + agent task status"""
    fleet_cmds.inspect_cmd(project=project, pm=pm)


@fleet.command(name="monitors")
def fleet_monitors():
    """📊 List all project monitoring agents"""
    from apex.core.project_template import list_all_monitors, get_all_monitor_count
    data = list_all_monitors()
    total = get_all_monitor_count()
    console.print(f"\n[bold cyan]⚓ 全舰队巡检Agent — 共 {total} 个[/]\n")
    t = Table(title="项目巡检Agent矩阵", box=box.SIMPLE)
    t.add_column("项目", width=16)
    t.add_column("PM巡检官", width=16)
    t.add_column("巡检Agent", width=28)
    t.add_column("频率", width=14)
    for key, info in data.items():
        monitors_str = "\n".join(f"{m['emoji']} {m['role']}" for m in info["monitors"])
        schedules_str = "\n".join(m["schedule"] for m in info["monitors"])
        t.add_row(info["project"], info["pm"], monitors_str, schedules_str)
    console.print(t)


@fleet.command(name="deploy")
@click.argument("requirement")
@click.option("--project", "-p", default="default", help="Project key")
@click.option("--template", "-t", default="webapp", help="Team template")
@click.option("--auto/--manual", default=True, help="Auto mode")
@click.option("--mode", "-m", default="pipeline", help="Collaboration mode")
def fleet_deploy(requirement: str, project: str, template: str, auto: bool, mode: str):
    """🚢 One-click fleet deploy: team → decompose → dispatch → status"""
    fleet_cmds.deploy_cmd(
        requirement=requirement, project=project, template=template,
        auto_mode=auto, mode=mode,
    )


# ─── Multi-Mac Fleet Commands ───

@fleet.command(name="init-fleet")
@click.option("--name", "-n", default="老卢舰队", help="Fleet name")
@click.option("--force", "-f", is_flag=True, help="Force re-init")
def fleet_init_fleet(name: str, force: bool):
    """⚓ Initialize this Mac as fleet Origin (Apex repo)"""
    fleet_cmds.fleet_init_cmd(fleet_name=name, force=force)


@fleet.command(name="join-fleet")
@click.option("--force", "-f", is_flag=True, help="Force re-join")
def fleet_join_fleet(force: bool):
    """🔗 Join fleet as Worker (syncs fleet/ from Apex)"""
    fleet_cmds.fleet_join_cmd(force=force)


@fleet.command(name="sync")
@click.option("--push", "direction", flag_value="push", help="Push config (Origin only)")
@click.option("--pull", "direction", flag_value="pull", default=True, help="Pull config (default)")
def fleet_sync_cmd(direction: str):
    """🔄 Sync fleet config — pull (worker) or push (origin)"""
    fleet_cmds.fleet_sync_cmd(direction=direction)


@fleet.command(name="nodes")
def fleet_nodes():
    """🖥 Show all fleet nodes (multi-Mac)"""
    fleet_cmds.fleet_nodes_cmd()


@fleet.command(name="report")
def fleet_report():
    """📡 Report node heartbeat to fleet (Worker → Origin via GitHub)"""
    fleet_cmds.fleet_report_cmd()


@fleet.command(name="gpu-status")
def fleet_gpu_status():
    """🖥 GPU resource center — all fleet GPUs"""
    fleet_cmds.fleet_gpu_status_cmd()


# ── Tmux-backed fleet runtime ───────────────────────────────────

@fleet.command(name="init")
@click.option("--agents", "-a", default="", help="Comma-separated agent names (default: all squad)")
def fleet_tmux_init(agents: str):
    """⚡ Initialize fleet: create profiles + start tmux session"""
    agent_list = [a.strip() for a in agents.split(",") if a.strip()] if agents else None
    fleet_cmds.fleet_tmux_init(agent_list)


@fleet.command(name="start")
@click.option("--agents", "-a", default="", help="Comma-separated agent names")
def fleet_tmux_start(agents: str):
    """▶️ Start all agents in tmux (auto-inits if needed)"""
    agent_list = [a.strip() for a in agents.split(",") if a.strip()] if agents else None
    fleet_cmds.fleet_tmux_start(agent_list)


@fleet.command(name="stop")
@click.option("--destroy", "-d", is_flag=True, help="Destroy the tmux session entirely")
def fleet_tmux_stop(destroy: bool):
    """⏹ Stop agent windows (--destroy to kill tmux session)"""
    fleet_cmds.fleet_tmux_stop(kill_session=destroy)


@fleet.command(name="attach")
def fleet_tmux_attach():
    """🖥 Show command to attach to fleet tmux session"""
    fleet_cmds.fleet_tmux_attach()


@fleet.command(name="add")
@click.argument("agent_name")
def fleet_tmux_add(agent_name: str):
    """➕ Add an agent to the running fleet"""
    fleet_cmds.fleet_tmux_add(agent_name)


@fleet.command(name="kill")
@click.argument("agent_name")
def fleet_tmux_kill(agent_name: str):
    """🗑 Kill a specific agent window"""
    fleet_cmds.fleet_tmux_kill(agent_name)


@fleet.command(name="log")
@click.argument("agent_name")
@click.option("--lines", "-n", default=30, help="Number of lines to show")
def fleet_tmux_log(agent_name: str, lines: int):
    """📋 Show recent output from an agent"""
    fleet_cmds.fleet_tmux_log(agent_name, lines)


@fleet.command(name="broadcast")
@click.argument("message")
def fleet_tmux_broadcast(message: str):
    """📢 Send a message to all running agents"""
    fleet_cmds.fleet_tmux_broadcast(message)


# ─── LAN Discovery ─────────────────────────────────────────

@fleet.group(name="lan")
def fleet_lan():
    """🔍 LAN Discovery — find fleet peers on local network"""

@fleet_lan.command(name="scan")
def fleet_lan_scan():
    """🔍 Quick scan for LAN peers (4s timeout)"""
    fleet_cmds.fleet_lan_scan_cmd()

@fleet_lan.command(name="discover")
def fleet_lan_discover():
    """📡 Continuous LAN discovery (Ctrl+C to stop)"""
    fleet_cmds.fleet_lan_discover_cmd()


# ─── Resource-Aware Dispatch ───────────────────────────────

@fleet.command(name="probe")
def fleet_probe():
    """🖥 Probe local machine capabilities (CPU/GPU/RAM)"""
    fleet_cmds.fleet_probe_cmd()

@fleet.command(name="dispatch")
@click.argument("task")
@click.option("--gpu", is_flag=True, help="Requires GPU")
@click.option("--gpu-memory-mb", type=int, default=0, help="Minimum GPU memory (MB)")
@click.option("--cpu-cores", type=int, default=1, help="Minimum CPU cores")
@click.option("--ram-mb", type=int, default=512, help="Minimum RAM (MB)")
@click.option("--target", "-t", default="", help="Target specific machine")
@click.option("--profile", "-p", default="", help="Hermes profile to use")
@click.option("--timeout", type=int, default=600, help="Task timeout (seconds)")
@click.option("--dry-run", is_flag=True, help="Preview match without dispatching")
def fleet_dispatch(task: str, gpu: bool, gpu_memory_mb: int, cpu_cores: int,
                   ram_mb: int, target: str, profile: str, timeout: int, dry_run: bool):
    """🚀 Resource-aware task dispatch to best fleet node

    \b
    Examples:
      apex fleet dispatch "Train model" --gpu --gpu-memory-mb 16000
      apex fleet dispatch "Scrape data" --target MacBook-Pro-2.local
      apex fleet dispatch "Build UI" --profile frontend-dev --dry-run
    """
    fleet_cmds.fleet_dispatch_cmd(
        task_description=task, gpu=gpu, gpu_memory_mb=gpu_memory_mb,
        cpu_cores=cpu_cores, ram_mb=ram_mb, target=target,
        profile=profile, timeout=timeout, dry_run=dry_run,
    )

@fleet.command(name="queue")
def fleet_queue():
    """📋 View fleet task dispatch queue"""
    fleet_cmds.fleet_queue_cmd()


# ════════════════════════════════════════════════════════════════
# MODE — 🔧 协作模式
# ════════════════════════════════════════════════════════════════

@cli.group()
def mode():
    """🔧 Collaboration Modes — chain, debate, supervise, pipeline"""


@mode.command(name="chain")
@click.argument("goal")
@click.option("--pipeline", "-p", default="dev",
              type=click.Choice(["dev", "content", "data"]),
              help="Pipeline type")
def mode_chain(goal: str, pipeline: str):
    """⛓️ Sequential chain — agents pass output hand-to-hand"""
    mode_cmds.chain_cmd(goal, pipeline)


@mode.command(name="debate")
@click.argument("topic")
@click.option("--agents", "-a", default=3, help="Number of debating agents")
def mode_debate(topic: str, agents: int):
    """🎯 Multi-agent debate — explore from multiple perspectives"""
    mode_cmds.debate_cmd(topic, agents)


@mode.command(name="supervise")
@click.argument("goal")
@click.option("--workers", "-w", default=3, help="Number of worker agents")
def mode_supervise(goal: str, workers: int):
    """🏛️ Hierarchical supervision — manager delegates, reviews, approves"""
    mode_cmds.supervise_cmd(goal, workers)


@mode.group(name="pipeline")
def mode_pipeline():
    """🔀 Task pipeline — normal flow + direct execution"""


@mode_pipeline.command(name="normal")
@click.argument("requirement")
@click.option("--project", "-p", default="finopsai", help="Project key")
@click.option("--confirm/--no-confirm", default=True, help="Skip manual confirmation")
def mode_pipeline_normal(requirement: str, project: str, confirm: bool):
    """📋 Normal pipeline: requirement → AI decompose → dispatch → monitor"""
    mode_cmds.pipeline_normal_cmd(requirement, project, confirm)


@mode_pipeline.command(name="direct")
@click.argument("task")
@click.option("--agent", "-a", required=True, help="Target agent")
@click.option("--project", "-p", default="finopsai", help="Project key")
@click.option("--priority", "-pr", type=int, default=1, help="Priority 0-3")
def mode_pipeline_direct(task: str, agent: str, project: str, priority: int):
    """⚡ Direct pipeline: command → target agent → execute"""
    mode_cmds.pipeline_direct_cmd(task, agent, project, priority)


@mode_pipeline.command(name="status")
@click.argument("pipeline_id")
def mode_pipeline_status(pipeline_id: str):
    """📊 View pipeline status"""
    mode_cmds.pipeline_status_cmd(pipeline_id)


@mode_pipeline.command(name="confirm")
@click.argument("pipeline_id")
def mode_pipeline_confirm(pipeline_id: str):
    """✅ Confirm pipeline to continue"""
    mode_cmds.pipeline_confirm_cmd(pipeline_id)


# ════════════════════════════════════════════════════════════════
# MONITOR — 📊 状态监控 (Agent状态 + Skills总览)
# ════════════════════════════════════════════════════════════════

@cli.group()
def monitor():
    """📊 Monitor — agent status, skills, tasks dashboard"""


@monitor.command(name="status")
@click.option("--json", "json_output", is_flag=True, help="JSON output for dashboard")
@click.option("--watch", "-w", type=int, default=0, help="Auto-refresh interval (seconds)")
def monitor_status(json_output: bool, watch: int):
    """🤖 Agent task execution status panel"""
    from apex.interface.monitor import cmd_status
    cmd_status(json_output=json_output, watch=watch)


@monitor.command(name="skills")
def monitor_skills():
    """🧠 Agent skills overview — profile skills, SOUL, wrappers"""
    from apex.interface.monitor import cmd_skills
    cmd_skills()


@monitor.command(name="tools")
def monitor_tools():
    """🔧 System tool discovery — what's installed and who can use it"""
    from apex.interface.tool_discovery import ToolDiscovery
    td = ToolDiscovery()
    inventory = td.scan(force=True)

    console.print()
    console.print(Panel("[bold]🔧 Apex Tool Discovery[/]", border_style="cyan"))
    console.print(
        f"[dim]Scanned {inventory.total_tools} tools, "
        f"[green]found {len(inventory.found)}[/], "
        f"[red]missing {len(inventory.missing)}[/][/]"
    )
    console.print()

    # Found tools table
    table = Table(box=box.ROUNDED, border_style="blue", header_style="bold cyan")
    table.add_column("Tool", style="bold")
    table.add_column("Category", style="dim")
    table.add_column("Version", style="green", max_width=25)
    table.add_column("Provides", style="yellow")
    table.add_column("Used By", style="dim", max_width=30)

    for t in inventory.found:
        table.add_row(
            t.display,
            t.category,
            t.version[:24],
            ", ".join(t.provides[:3]),
            ", ".join(t.recommended_agents[:4]),
        )

    console.print(table)
    console.print()

    # Missing tools
    if inventory.missing:
        missing_str = ", ".join(inventory.missing)
        console.print(f"[dim]Not installed: {missing_str}[/]")
        console.print(f"[dim]Install missing tools to unlock more agent capabilities.[/]")

    # Agent tool summary
    console.print()
    console.print("[bold]Agent → Tool Mapping[/]")
    for agent, tools in sorted(inventory.agent_tool_map.items()):
        if agent == "all":
            continue
        console.print(f"  [cyan]{agent:20s}[/] → {', '.join(tools)}")


# ════════════════════════════════════════════════════════════════
# PM — 📊 项目管理 (调度/分配/健康/时间线)
# ════════════════════════════════════════════════════════════════

@cli.group()
def pm():
    """📊 PM — project scheduling, assignment, health, timeline"""


@pm.command(name="dashboard")
@click.option("--project", "-p", default="", help="Filter by project")
def pm_dashboard(project: str):
    """📊 Full project dashboard: agents, tasks, critical path, health"""
    from apex.interface.pm_engine import PMEngine
    from apex.interface.pm_render import render_dashboard
    engine = PMEngine()
    render_dashboard(engine, project)


@pm.command(name="schedule")
@click.option("--project", "-p", default="", help="Filter by project")
def pm_schedule(project: str):
    """📅 Schedule with critical path, parallel groups, assignments"""
    from apex.interface.pm_engine import PMEngine
    from apex.interface.pm_render import render_schedule
    engine = PMEngine()
    render_schedule(engine, project)


@pm.command(name="assign")
@click.option("--project", "-p", default="", help="Filter by project")
def pm_assign(project: str):
    """🤖 Auto-assign pending tasks to best-fit agents"""
    from apex.interface.pm_engine import PMEngine
    from apex.interface.pm_render import render_schedule
    engine = PMEngine()
    schedule = engine.generate_schedule(project)
    console.print(f"[green]✅ Assigned {len(schedule.assignments)} tasks[/]")
    render_schedule(engine, project)


@pm.command(name="health")
def pm_health():
    """🩺 Health check: agent heartbeats, task status, alerts"""
    from apex.interface.pm_engine import PMEngine
    from apex.interface.pm_render import render_health
    engine = PMEngine()
    render_health(engine)


@pm.command(name="timeline")
@click.option("--project", "-p", default="", help="Filter by project")
def pm_timeline(project: str):
    """📊 Gantt-style timeline with critical path highlighting"""
    from apex.interface.pm_engine import PMEngine
    from apex.interface.pm_render import render_timeline
    engine = PMEngine()
    render_timeline(engine, project)


@pm.command(name="profile")
@click.argument("agent_name")
def pm_profile(agent_name: str):
    """🔍 Agent capability profile: skills, history, role, modules"""
    from apex.interface.pm_engine import PMEngine
    from apex.interface.pm_render import render_profile
    engine = PMEngine()
    render_profile(engine, agent_name)


# ════════════════════════════════════════════════════════════════
# PROJECT — 📦 项目管理
# ════════════════════════════════════════════════════════════════

@cli.group()
def project():
    """📦 Project Management — create, analyze, sprint, pipeline"""


@project.command(name="create")
@click.argument("project_key")
@click.option("--name", "-n", required=True, help="项目显示名")
@click.option("--type", "-t", default="auto",
              type=click.Choice(["auto", "webapp", "ai-ml", "mobile", "data", "content", "infra"]),
              help="Project type")
@click.option("--size", "-s", default="auto",
              type=click.Choice(["auto", "small", "medium", "large"]),
              help="Project size")
@click.option("--path", "-p", default="", help="Project directory")
@click.option("--description", "-d", default="", help="Project description")
@click.option("--dry-run", is_flag=True, help="Preview only")
def project_create(project_key: str, name: str, type: str, size: str,
                   path: str, description: str, dry_run: bool):
    """🚀 Smart project creation — auto-detect type/size, assign agent fleet"""
    from apex.core.project_template import (
        build_smart_template, summarize_template,
        ProjectType, ProjectSize,
    )
    from apex.interface.hermes_sync import sync_profile_to_hermes, ROLE_SOULS
    from apex.interface.skill_registry import sync_skill_md
    import subprocess

    console.print("\n[bold cyan]🔍 分析项目...[/]")
    tmpl = build_smart_template(
        project_key=project_key, project_name=name,
        project_type=type, project_size=size,
        project_path=path, description=description,
    )
    summary = summarize_template(tmpl)
    size_colors = {"small": "green", "medium": "yellow", "large": "red"}
    sc = size_colors.get(tmpl.size.value, "white")
    console.print(Panel(
        f"[bold]{summary['name']}[/]\n"
        f"类型: [cyan]{summary['type']}[/]  规模: [{sc}]{summary['size']}[/]\n"
        f"PM: [green]{summary['pm']}[/]\n"
        f"助手: {summary['assistant']}\n"
        f"核心团队: [yellow]{summary['core_count']}人[/] {', '.join(summary['core_agents']) or '—'}\n"
        f"巡检Agent: [magenta]{summary['monitor_count']}个[/]",
        title="📋 智能分析结果", border_style="cyan"
    ))
    if dry_run:
        console.print("\n[dim](dry-run — 未创建任何Agent)[/]")
        return
    if not click.confirm(f"\n🚀 创建 {summary['total_agents']} 个Agent?", default=True):
        console.print("[dim]已取消[/]")
        return
    from apex.core.project_template import create_project
    create_project(tmpl, console)


@project.command(name="analyze")
@click.argument("project_key")
@click.option("--name", "-n", default="", help="Project display name")
def project_analyze(project_key: str, name: str):
    """🔍 Analyze project type and size, give recommendations"""
    from apex.core.project_template import (
        detect_project_type, detect_project_size,
        ProjectType, ProjectSize
    )
    project_type = detect_project_type(project_key, name or project_key)
    project_size = detect_project_size()
    type_emoji = {
        ProjectType.WEBAPP: "🌐", ProjectType.AI_ML: "🤖",
        ProjectType.MOBILE: "📱", ProjectType.DATA: "📊",
        ProjectType.CONTENT: "✍️", ProjectType.INFRA: "🔧",
    }
    size_label = {
        ProjectSize.SMALL: "🟢 小型(萌芽期)",
        ProjectSize.MEDIUM: "🟡 中型(成长期)",
        ProjectSize.LARGE: "🔴 大型(成熟期)",
    }
    console.print(Panel(
        f"类型: {type_emoji.get(project_type, '📦')} {project_type.value}\n"
        f"规模: {size_label.get(project_size, project_size.value)}",
        title=f"🔍 {project_key} 分析", border_style="cyan"
    ))
    if project_size == ProjectSize.SMALL:
        console.print("[dim]建议: PM兼任巡检，1-2核心Agent即可[/]")
    elif project_size == ProjectSize.MEDIUM:
        console.print("[dim]建议: PM + 智能助手 + 3-4核心Agent[/]")
    else:
        console.print("[dim]建议: PM + 智能助手 + 5+核心Agent + 专项监控[/]")


@project.command(name="list")
def project_list():
    """📋 List all registered projects"""
    from apex.core.project_template import LEGACY_TEMPLATES, summarize_template
    templates = LEGACY_TEMPLATES
    if not templates:
        console.print("[dim]暂无项目模板。用 'apex project create' 创建第一个。[/]")
        return
    t = Table(title="📋 已注册项目", box=None)
    t.add_column("项目", style="cyan")
    t.add_column("类型", style="white")
    t.add_column("规模", style="yellow")
    t.add_column("PM", style="green")
    t.add_column("核心Agent", style="white")
    for key, pt in templates.items():
        summary = summarize_template(pt)
        t.add_row(summary['name'], summary['type'], summary['size'], summary['pm'] or '—', str(summary['core_count']))
    console.print(t)


@project.command(name="sprint")
@click.argument("goal")
@click.option("--mode", "-m", default="solo", type=click.Choice(["solo", "swarm"]), help="solo=fullstack, swarm=split FE/BE")
def project_sprint(goal: str, mode: str):
    """🚀 Start a new MVP sprint"""
    sprint_cmds.cmd_create(goal, mode)


# ════════════════════════════════════════════════════════════════
# SYSTEM — ⚙️ 系统管理
# ════════════════════════════════════════════════════════════════

@cli.group()
def system():
    """⚙️ System Management — skills, economy, evolution, knowledge, autonomous"""


@system.group(name="skill")
def system_skill():
    """🧠 Skill Registry — levels, assessment, matching"""


@system_skill.command(name="list")
@click.option("--category", "-c", default="", help="Filter by category")
@click.option("--agent", "-a", "show_agent", is_flag=True, help="List agents and their skills")
def system_skill_list(category: str, show_agent: bool):
    """List all skills or agent skill levels"""
    sys_cmds.skill_list_cmd(category=category, show_agent=show_agent)


@system_skill.command(name="show")
@click.argument("agent_name")
def system_skill_show(agent_name: str):
    """Show agent skill levels with evidence chain"""
    sys_cmds.skill_show_cmd(agent_name)


@system_skill.command(name="assess")
@click.argument("agent_name")
@click.argument("skill_spec")
@click.option("--confidence", "-c", default="", help="Confidence 0.0-1.0")
def system_skill_assess(agent_name: str, skill_spec: str, confidence: str):
    """Assess/update agent skill level. Format: skill_name:L3"""
    sys_cmds.skill_assess_cmd(agent_name, skill_spec, confidence)


@system_skill.command(name="match")
@click.argument("task")
@click.option("--difficulty", "-d", default="L2",
              type=click.Choice(["L1", "L2", "L3", "L4", "L5"]),
              help="Minimum difficulty level")
@click.option("--skills", "-s", "required_skills", default="",
              help="Comma-separated required skills")
def system_skill_match(task: str, difficulty: str, required_skills: str):
    """Find best agent for a task by skill matching"""
    sys_cmds.skill_match_cmd(task, difficulty, required_skills)


@system_skill.command(name="evaluate")
def system_skill_evaluate():
    """Run skill evaluation pipeline"""
    sys_cmds.skill_evaluate_cmd()


@system_skill.command(name="sync")
@click.argument("agent_name")
def system_skill_sync(agent_name: str):
    """Generate SKILL.md for agent's Hermes profile"""
    sys_cmds.skill_sync_cmd(agent_name)


@system.group(name="economy")
def system_economy():
    """💰 Token Economy — budget and cost management"""


@system_economy.command(name="status")
def system_economy_status():
    """View economy status"""
    sys_cmds.economy_status_cmd()


@system_economy.command(name="classify")
@click.argument("task")
def system_economy_classify(task: str):
    """Test task classification and routing"""
    sys_cmds.economy_classify_cmd(task)


@system.group(name="evolution")
def system_evolution():
    """🧬 Skill Evolution — agents get smarter with use"""


@system_evolution.command(name="status")
def system_evolution_status():
    """Evolution engine status"""
    sys_cmds.evolution_status_cmd()


@system_evolution.command(name="agent")
@click.argument("name")
def system_evolution_agent(name: str):
    """Agent evolution report"""
    sys_cmds.evolution_agent_cmd(name)


@system.group(name="knowledge")
def system_knowledge():
    """🧠 Knowledge Graph — cross-agent shared memory"""


@system_knowledge.command(name="query")
@click.argument("question")
def system_knowledge_query(question: str):
    """Query knowledge graph"""
    sys_cmds.knowledge_query_cmd(question)


@system_knowledge.command(name="stats")
def system_knowledge_stats():
    """Knowledge graph statistics"""
    sys_cmds.knowledge_stats_cmd()


@system.group(name="autonomous")
def system_autonomous():
    """🤖 Autonomous Engine — 7x24 self-aware operation"""


@system_autonomous.command(name="status")
def system_autonomous_status():
    """Show autonomous engine report"""
    sys_cmds.autonomous_status_cmd()


@system_autonomous.command(name="start")
def system_autonomous_start():
    """Start the autonomous engine"""
    sys_cmds.autonomous_start_cmd()


@system_autonomous.command(name="stop")
def system_autonomous_stop():
    """Stop the autonomous engine"""
    sys_cmds.autonomous_stop_cmd()


@system_autonomous.command(name="pause")
def system_autonomous_pause():
    """Pause task dispatch (heartbeat continues)"""
    sys_cmds.autonomous_pause_cmd()


@system_autonomous.command(name="resume")
def system_autonomous_resume():
    """Resume task dispatch"""
    sys_cmds.autonomous_resume_cmd()


@system_autonomous.command(name="schedule")
@click.argument("name")
@click.argument("cron")
@click.argument("task")
@click.option("--agent", "-a", default="", help="Agent profile to assign")
def system_autonomous_schedule(name: str, cron: str, task: str, agent: str):
    """Schedule a recurring task"""
    sys_cmds.autonomous_schedule_cmd(name, cron, task, agent)


@system_autonomous.command(name="unschedule")
@click.argument("task_id")
def system_autonomous_unschedule(task_id: str):
    """Remove a scheduled task"""
    sys_cmds.autonomous_unschedule_cmd(task_id)


@system_autonomous.command(name="alerts")
def system_autonomous_alerts():
    """Show unresolved alerts"""
    sys_cmds.autonomous_alerts_cmd()


# ════════════════════════════════════════════════════════════════
# HELP — ❓ 帮助系统
# ════════════════════════════════════════════════════════════════

@cli.group()
def help():
    """❓ Help System — request, approve, list cross-agent help"""


@help.command(name="request")
@click.argument("agent")
@click.argument("title")
@click.option("--description", "-d", default="", help="Description of help needed")
@click.option("--task", "-t", default="", help="Source task ID")
def help_request(agent: str, title: str, description: str, task: str):
    """🆘 Request help from PM for another agent"""
    help_cmds.help_request_cmd(agent, title, description, task)


@help.command(name="approve")
@click.argument("request_id")
@click.option("--agent", "-a", required=True, help="Helper agent to assign")
@click.option("--notes", "-n", default="", help="PM notes")
def help_approve(request_id: str, agent: str, notes: str):
    """✅ PM approves help request and assigns helper"""
    help_cmds.help_approve_cmd(request_id, agent, notes)


@help.command(name="list")
@click.option("--status", "-s", default="", help="Filter by status")
def help_list(status: str):
    """📋 List help requests"""
    help_cmds.help_list_cmd(status or "")


# ════════════════════════════════════════════════════════════════
# ORIGIN — ⚓ 始祖Agent
# ════════════════════════════════════════════════════════════════

@cli.group()
def origin():
    """⚓ Origin Agent — portfolio commander, cross-project oversight"""


@origin.command(name="init")
def origin_init():
    """Initialize/deploy the Origin Agent"""
    origin_cmds.init_cmd(console)


@origin.command(name="replicate")
@click.argument("target", required=False)
@click.option("--all", "all_agents", is_flag=True, help="Replicate to all project agents")
@click.option("--strategy", "-s", default="merge",
              type=click.Choice(["merge", "replace", "pm"]),
              help="merge / replace / pm template")
def origin_replicate(target: str, all_agents: bool, strategy: str):
    """Replicate skills to target agent(s)"""
    origin_cmds.replicate_cmd(console, target=target or "", all_agents=all_agents, strategy=strategy)


@origin.group()
def portfolio():
    """📊 Portfolio — multi-project management"""


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
    origin_cmds.portfolio_cmd(console, action="create", name=name, pm_agent=pm or "",
                              strategic_goal=goal, expected_outcome=outcome, description=desc)


@portfolio.command(name="status")
@click.argument("portfolio_id")
def portfolio_status(portfolio_id: str):
    """Show portfolio status + milestones + tasks"""
    origin_cmds.portfolio_cmd(console, action="status", portfolio_id=portfolio_id)


@origin.command(name="overview")
def origin_overview():
    """⚓ Fleet overview — all portfolios status"""
    origin_cmds.overview_cmd(console)


# ════════════════════════════════════════════════════════════════
# INTEGRATE — 🔗 集成
# ════════════════════════════════════════════════════════════════

@cli.group()
def integrate():
    """🔗 Integrations — hermes, bridge, router, monitor, company"""


@integrate.group(name="hermes")
def integrate_hermes():
    """🤖 Hermes Integration — manage & launch Hermes profiles"""


@integrate_hermes.command(name="profiles")
def integrate_hermes_profiles():
    """List all Hermes profiles"""
    from apex.interface.hermes_sync import list_hermes_profiles
    profiles = list_hermes_profiles()
    if not profiles:
        console.print("[yellow]No Hermes profiles found[/]")
        return
    t = Table(title="🤖 Hermes Profiles", box=None)
    t.add_column("Profile", style="cyan")
    t.add_column("Role", style="white")
    t.add_column("Config", style="green")
    t.add_column("SOUL.md", style="green")
    t.add_column("Wrapper", style="green")
    for p in profiles:
        t.add_row(p["name"], p.get("title", "—")[:30],
                  "✅" if p["has_config"] else "❌",
                  "✅" if p["has_soul"] else "❌",
                  "✅" if p["has_wrapper"] else "❌")
    console.print(t)


@integrate.group(name="bridge")
def integrate_bridge():
    """🌉 Apex-Hermes Bridge — sync monitor fleet"""


@integrate_bridge.command(name="init")
def integrate_bridge_init():
    """Create/update the 6 default bridge monitoring agents"""
    bridge_cmds.init_bridge_agents(console)


@integrate_bridge.command(name="sync")
def integrate_bridge_sync():
    """Run one sync cycle — update Kanban from Hermes state.db"""
    bridge_cmds.run_bridge_sync(console)


@integrate_bridge.command(name="status")
def integrate_bridge_status():
    """Show bridge agent fleet health"""
    data = bridge_cmds.get_bridge_status()
    t = Table(title="🌉 Apex-Hermes Bridge — Fleet Status", box=None)
    t.add_column("Agent", style="cyan")
    t.add_column("Status", style="green")
    t.add_column("Info", style="dim")
    for a in data.get("agents", []):
        icon = {"done": "✅", "in_progress": "🟡", "blocked": "🔴"}.get(a["status"], "⬜")
        info = (a.get("output", "") or "")[:60].replace("\n", " ")
        t.add_row(f"{icon} {a['assignee']}", a["status"], info)
    console.print(t)
    console.print(f"\n[dim]Healthy: {data['healthy']} | Degraded: {data['degraded']} | Offline: {data['offline']}[/]")


@integrate_bridge.command(name="agents")
def integrate_bridge_agents():
    """List all 6 bridge monitoring agents"""
    from apex.core.profile import ProfileManager
    pm = ProfileManager()
    t = Table(title="🤖 Bridge Monitoring Agents", box=None)
    t.add_column("Name", style="cyan")
    t.add_column("Role", style="green")
    t.add_column("Expertise", style="yellow")
    for name, cfg in bridge_cmds.BRIDGE_AGENTS.items():
        try:
            pm.load(name)
            icon = "✅"
        except FileNotFoundError:
            icon = "⬜"
        t.add_row(f"{icon} {name}", cfg["role"], ", ".join(cfg["expertise"][:3]))
    console.print(t)
    console.print("\n[dim]Run [bold]apex integrate bridge init[/] to create/update all 6 agents.[/]")


@integrate.group(name="router")
def integrate_router():
    """🗺️ Smart Router — classify and dispatch tasks"""


@integrate_router.command(name="route")
@click.argument("task")
@click.option("--agents", "-a", default="", help="Comma-separated category:agent pairs")
def integrate_router_route(task: str, agents: str):
    """Route a task to the best matching agent"""
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


@integrate.group(name="monitor")
def integrate_monitor():
    """👁️ Reactive Monitor — watch, detect anomalies, trigger agents"""


@integrate_monitor.command(name="check")
@click.option("--file", "-f", help="Log file path to watch for errors")
@click.option("--url", "-u", help="HTTP URL to health-check")
@click.option("--pattern", "-p", default="error|fail|exception", help="Regex pattern")
def integrate_monitor_check(file: str, url: str, pattern: str):
    """Run a single monitoring check"""
    try:
        from apex.orchestration.monitor import Monitor, WatcherRule
        m = Monitor()
        if file:
            m.add_rule(WatcherRule(name=f"check-{file}", type="file-watcher",
                                   target=file, config={"pattern": pattern}))
        if url:
            m.add_rule(WatcherRule(name=f"health-{url[:30]}", type="http-health-check", target=url))
        result = m.run_cycle()
        console.print(f"[green]✅ Check complete: {len(result.anomalies)} anomalies[/]")
        for a in result.anomalies[:5]:
            console.print(f"  {'🔴' if a.severity == 'high' else '🟡'} {a.source}: {a.message[:80]}")
    except Exception as e:
        console.print(f"[red]✗ Monitor failed: {e}[/]")


@integrate.group(name="company")
def integrate_company():
    """🏢 One-Click Company — create an AI company"""


@integrate_company.command(name="create")
@click.argument("name")
@click.option("--industry", "-i", default="saas",
              type=click.Choice(["saas", "ai_product", "content", "ecommerce", "freelance"]),
              help="Industry type")
def integrate_company_create(name: str, industry: str):
    """Create an AI company (one command = one team)"""
    CompanyBuilder().create(name, industry)


@integrate_company.command(name="start")
@click.argument("name")
@click.argument("goal")
def integrate_company_start(name: str, goal: str):
    """Start a company to execute a task"""
    CompanyBuilder().start(name, goal)


@integrate_company.command(name="list")
def integrate_company_list():
    """List all companies"""
    list_companies()


# ════════════════════════════════════════════════════════════════
# CHAT — 💬 对话
# ════════════════════════════════════════════════════════════════

@cli.group(invoke_without_command=True)
@click.argument("agent_name", required=False)
@click.option("--context", "-c", default="", help="Extra project context")
@click.option("--query", "-q", default="", help="Initial message")
@click.option("--model", "-m", default=None, help="Override default model")
@click.option("--token-limit", type=int, default=0, help="Max tokens per turn")
@click.option("--input-lines", type=int, default=3, help="Input height in TUI")
@click.option("--list", "-l", "list_mode", is_flag=True, help="List all agents")
@click.pass_context
def chat(ctx, agent_name: str, context: str, query: str,
         model: Optional[str], token_limit: int, input_lines: int, list_mode: bool):
    """💬 Chat with an Apex agent.

    Opens a Hermes chat session showing the agent's name in the terminal title
    with multi-line input (default: 3 lines).

    \b
    Examples:
      apex chat frontend-dev                   Talk to frontend dev
      apex chat architect -q "Review this"     Initial query
      apex chat backend-dev --model deepseek-v4-pro --token-limit 5000
      apex chat --list                         List all agents
    """
    if ctx.invoked_subcommand is None:
        if list_mode or not agent_name:
            chat_cmds.chat_list_cmd()
            return
        _configure_token_limit(agent_name, token_limit)
        _configure_profile_model(agent_name, model)
        _configure_input_lines(agent_name, input_lines)
        chat_cmds.chat_launch_cmd(agent_name, context, query)


@chat.command(name="list")
def chat_list():
    """📋 List all available agents"""
    chat_cmds.chat_list_cmd()


# ════════════════════════════════════════════════════════════════
# HELPER: per-command token/model/input config
# ════════════════════════════════════════════════════════════════


def _configure_token_limit(profile_name: str, token_limit: int):
    """Set per-profile token limit if specified."""
    if token_limit <= 0:
        return
    profile_dir = HERMES_HOME / "profiles" / profile_name
    if not profile_dir.exists():
        return
    config_file = profile_dir / "config.yaml"
    if not config_file.exists():
        return
    try:
        import yaml
        with open(config_file) as f:
            cfg = yaml.safe_load(f) or {}
        if "agent" not in cfg:
            cfg["agent"] = {}
        cfg["agent"]["max_tokens_per_turn"] = token_limit
        with open(config_file, "w") as f:
            yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
    except:
        pass


def _configure_profile_model(profile_name: str, model: Optional[str]):
    """Set per-profile model if specified."""
    if not model:
        return
    profile_dir = HERMES_HOME / "profiles" / profile_name
    if not profile_dir.exists():
        return
    config_file = profile_dir / "config.yaml"
    if not config_file.exists():
        return
    try:
        import yaml
        with open(config_file) as f:
            cfg = yaml.safe_load(f) or {}
        if "model" not in cfg:
            cfg["model"] = {}
        cfg["model"]["default"] = model
        with open(config_file, "w") as f:
            yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
    except:
        pass


def _configure_input_lines(profile_name: str, input_lines: int):
    """Set per-profile input line height."""
    if input_lines < 1:
        input_lines = 3
    profile_dir = HERMES_HOME / "profiles" / profile_name
    if not profile_dir.exists():
        return
    config_file = profile_dir / "config.yaml"
    if not config_file.exists():
        return
    try:
        import yaml
        with open(config_file) as f:
            cfg = yaml.safe_load(f) or {}
        if "display" not in cfg:
            cfg["display"] = {}
        cfg["display"]["composer_lines"] = input_lines
        cfg["display"]["multi_line_composer"] = True
        with open(config_file, "w") as f:
            yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
    except:
        pass


HERMES_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))


# ════════════════════════════════════════════════════════════════
# BACKWARD COMPATIBILITY — deprecated flat aliases
# ════════════════════════════════════════════════════════════════

@cli.command(hidden=True)
@click.argument("topic")
@click.option("--agents", "-a", default=3, help="Number of debating agents")
@click.pass_context
def debate(ctx, topic: str, agents: int):
    """[DEPRECATED] Use: apex mode debate"""
    console.print("[dim]⚠️  [bold]deprecated[/] — use [cyan]apex mode debate[/] instead[/]")
    ctx.invoke(mode_debate, topic=topic, agents=agents)


@cli.command(hidden=True)
@click.argument("goal")
@click.option("--workers", "-w", default=3, help="Number of worker agents")
@click.pass_context
def supervisor(ctx, goal: str, workers: int):
    """[DEPRECATED] Use: apex mode supervise"""
    console.print("[dim]⚠️  [bold]deprecated[/] — use [cyan]apex mode supervise[/] instead[/]")
    ctx.invoke(mode_supervise, goal=goal, workers=workers)


@cli.command(hidden=True)
def dispatch():
    """[DEPRECATED] Use: apex task dispatch"""
    console.print("[dim]⚠️  [bold]deprecated[/] — use [cyan]apex task dispatch[/] instead[/]")
    task_cmds.dispatch_cmd()


# Add crew subcommand
cli.add_command(crew_group)


if __name__ == "__main__":
    cli()


# ════════════════════════════════════════════════════════════════
# QUICKSTART — 🚀 快速上手引导
# ════════════════════════════════════════════════════════════════

@cli.command(name="quickstart")
def quickstart():
    """🚀 Show quick start guide — essential commands for beginners"""
    from rich.panel import Panel
    panel = Panel.fit(
        "[bold cyan]🚀 Apex Quick Start Guide[/]\n\n"
        "[bold]FIRST-TIME SETUP[/]\n"
        "  [green]agentark setup --quick[/]         Quick setup with defaults\n"
        "  [green]apex setup --check[/]         Check installation status\n\n"
        "[bold]CREATE YOUR AI TEAM[/]\n"
        "  [green]apex team template webapp[/]  Create 4-agent dev team\n"
        "  [green]apex team start[/]            Launch agent terminals\n\n"
        "[bold]YOUR FIRST TASK[/]\n"
        "  [green]apex task dispatch-smart \"需求\"[/]  AI decomposes\n"
        "  [green]apex task schedule[/]               Gantt chart timeline\n"
        "  [green]apex fleet status[/]                Check agent status\n"
        "  [green]apex chat <agent>[/]                Talk to your agent\n"
        "  [green]apex survey \"topic\"[/]             Competitive analysis\n\n"
        "[bold]COLLABORATION MODES[/]\n"
        "  [green]apex mode chain \"goal\" -p dev[/]    Sequential chain\n"
        "  [green]apex mode supervise \"goal\" -w 3[/] Manager + workers\n\n"
        "[bold]SYSTEM & INTEGRATION[/]\n"
        "  [green]apex system skill list[/]          View agent skills\n"
        "  [green]apex integrate hermes profiles[/]  List Hermes profiles\n"
        "  [green]apex origin overview[/]            Fleet-wide status\n\n"
        "[dim]TIP: --token-limit N  |  --input-lines N  |  --model NAME[/]",
        border_style="cyan",
        title="⚓ Apex Fleet — Quick Start",
    )
    console.print(panel)
    console.print("\\n[dim]Full help: apex --help  |  Command help: apex <command> --help[/]")

# ════════════════════════════════════════════════════════════════
# VERSION & UPDATE
# ════════════════════════════════════════════════════════════════

@cli.group()
def config():
    """⚙️ Apex configuration — model, provider, theme, notifications"""


@config.command(name="show")
def config_show():
    """📋 Show current configuration"""
    from apex.core.config import get_config
    import json
    cfg = get_config()
    console.print(Panel(json.dumps(cfg.to_dict(), indent=2, ensure_ascii=False),
                        title="⚙️ Apex Config", border_style="cyan"))


@config.command(name="set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """✏️ Set a config value (e.g. 'model.default deepseek-v4-pro')"""
    from apex.core.config import get_config, save_config
    parts = key.split(".", 1)
    if len(parts) != 2:
        console.print("[red]Format: apex config set <section>.<key> <value>[/]")
        console.print("[dim]Example: apex config set model.default deepseek-v4-pro[/]")
        return
    cfg = get_config()
    cfg.set(parts[0], parts[1], value)
    console.print(f"[green]✅ {key} = {value}[/]")


@config.command(name="model")
@click.argument("action", default="show")
@click.argument("model_name", default="")
def config_model(action: str, model_name: str):
    """🤖 Model management: show/list/set/detect"""
    from apex.interface.model_selector import ModelSelector
    ms = ModelSelector()
    if action == "show":
        ms.show_current()
    elif action == "set" and model_name:
        ms.set_default(model_name)
    elif action == "detect":
        result = ms.detect()
        console.print(f"[green]Available: {len(result.available)}[/]")
        for dp in result.available:
            console.print(f"  {dp.emoji} {dp.name}: {dp.default_model}")
    elif action == "list":
        result = ms.detect()
        for dp in result.available + result.unavailable:
            icon = "✅" if dp.has_key else "❌"
            console.print(f"  {icon} {dp.emoji} {dp.name}: {', '.join(dp.models)}")
    else:
        ms.show_current()


@config.command(name="path")
def config_path_cmd():
    """📁 Show config file path"""
    from apex.core.config import config_path
    console.print(f"[cyan]{config_path()}[/]")


@config.command(name="profile")
@click.argument("agent_name")
def config_profile(agent_name: str):
    """🔍 Show agent profile configuration"""
    profile_dir = Path.home() / ".hermes" / "profiles" / agent_name
    if not profile_dir.exists():
        console.print(f"[red]Agent '{agent_name}' profile not found.[/]")
        return

    console.print()
    console.print(Panel(f"[bold]Agent Profile: {agent_name}[/]", border_style="cyan"))

    # SOUL.md
    soul_file = profile_dir / "SOUL.md"
    if soul_file.exists():
        content = soul_file.read_text()
        first_line = content.strip().split("\n")[0].replace("# ", "")
        console.print(f"[bold]SOUL:[/] {first_line[:80]}")
        console.print(f"[dim]  {soul_file}[/]")

    # Config
    config_file = profile_dir / "config.yaml"
    if config_file.exists():
        import yaml
        with open(config_file) as f:
            cfg = yaml.safe_load(f) or {}
        model = cfg.get("model", {}).get("default", "?")
        console.print(f"[bold]Model:[/] [green]{model}[/]")
        console.print(f"  [dim]{config_file}[/]")

    # Skills
    skills_dir = profile_dir / "skills"
    if skills_dir.exists():
        count = len([f for f in skills_dir.rglob("SKILL.md") if f.is_file()])
        console.print(f"[bold]Skills:[/] {count}")

    # Wrapper
    wrapper = Path.home() / ".local" / "bin" / agent_name
    console.print(f"[bold]Wrapper:[/] {'✅' if wrapper.exists() else '❌'} [dim]{wrapper}[/]")

    # .env
    env_file = profile_dir / ".env"
    console.print(f"[bold].env:[/] {'✅' if env_file.exists() else '❌'}")


@cli.command(name="doctor")
@click.option("--fix", is_flag=True, help="Auto-fix common issues")
@click.option("--json", "json_output", is_flag=True, help="JSON output")
def doctor_cmd(fix: bool, json_output: bool):
    """🔍 System diagnostics — check environment, tools, config, fleet"""
    from apex.interface.doctor import Doctor, render_diagnostic, render_json
    d = Doctor()
    if fix:
        results = d.auto_fix()
        for r in results:
            console.print(f"  {r}")
        return
    report = d.run_all()
    if json_output:
        render_json(report)
    else:
        render_diagnostic(report)


@cli.command(name="tutorial")
def tutorial_cmd():
    """🎓 Interactive tutorial — 5-step guided walkthrough for new users"""
    from apex.interface.tutorial import run_tutorial
    run_tutorial()


@cli.command(name="version")
def version_cmd():
    """📋 Show version and check for updates"""
    from apex.interface.logo import render_mini
    render_mini(console, "0.5.1")
    from apex.interface.version import cmd_version
    cmd_version()


@cli.command(name="update")
def update_cmd():
    """🚀 Update Apex to the latest version from GitHub"""
    from apex.interface.version import cmd_update
    cmd_update()


@cli.group()
def theme():
    """🎨 Theme management — switch CLI color themes"""


@theme.command(name="list")
def theme_list():
    """List available themes"""
    from apex.interface.skin_engine import SkinEngine
    from rich.table import Table
    engine = SkinEngine()
    current = engine.current
    table = Table(box=None)
    table.add_column("", width=3)
    table.add_column("主题", style="bold")
    table.add_column("说明", style="dim")
    for skin in engine.list_themes():
        marker = "→" if skin.name == current.name else " "
        table.add_row(marker, skin.display, skin.description)
    console.print(table)
    console.print(f"\n[dim]切换: apex theme set <name>[/]")


@theme.command(name="set")
@click.argument("name")
def theme_set(name: str):
    """Set active theme"""
    from apex.interface.skin_engine import get_engine
    engine = get_engine()
    if engine.set_theme(name):
        console.print(f"[green]✅ 主题切换为: {name}[/]")
    else:
        available = ", ".join(engine.themes.keys())
        console.print(f"[red]未知主题: {name}[/]")
        console.print(f"[dim]可用: {available}[/]")


@cli.group()
def alias():
    """🔗 Command aliases — short names for frequent commands"""


@alias.command(name="list")
def alias_list():
    """List all aliases"""
    from apex.interface.aliases import list_aliases
    from rich.table import Table
    aliases = list_aliases()
    table = Table(box=None)
    table.add_column("别名", style="bold cyan")
    table.add_column("命令", style="white")
    table.add_column("来源", style="dim")
    for name, (cmd, marker) in sorted(aliases.items()):
        table.add_row(f"apex {name}", cmd, marker)
    console.print(table)


@alias.command(name="add")
@click.argument("name")
@click.argument("command")
def alias_add(name: str, command: str):
    """Add a custom alias"""
    from apex.interface.aliases import add_alias
    add_alias(name, command)
    console.print(f"[green]✅ apex {name} → {command}[/]")


@alias.command(name="remove")
@click.argument("name")
def alias_remove(name: str):
    """Remove a custom alias"""
    from apex.interface.aliases import remove_alias
    if remove_alias(name):
        console.print(f"[green]✅ 已删除 alias: {name}[/]")
    else:
        console.print(f"[yellow]无法删除: {name} (内置别名或不存在)[/]")
