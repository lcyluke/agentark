"""AgentArk — Unified Management Commands (v2 CLI)

Command system:
  agentark create project --name <name> [--desc <desc>]
  agentark create team -p <project> [-r <roles>] [--preset <preset>]
  agentark delete -p <project> [-a <agent>] [--force]
  agentark run hermes -a <agent> -f <project>
  agentark stop hermes -a <agent>
  agentark stop agent -a <agent>
  agentark view project -n <name>
  agentark view team -p <project>
  agentark view agent -a <name>
  agentark view tasks -p <project>
  agentark add agent -p <project> -r <role> [--model <model>]
  agentark change model -a <agent> -m <model>
  agentark change role -a <agent> -r <new_role>
  agentark update --self
  agentark update project -p <project>

Naming convention: <project>-<role> (e.g. finops-pm, finops-architect)
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import box

from agentark.core.profile import ProfileManager
from agentark.cli.commands.project_team import (
    AGENT_ROLES, ROLE_PRESETS, _agent_name, _role_exists,
    _list_project_agents, _interactive_role_selection,
)

console = Console()
pm = ProfileManager()
AGENTARK_HOME = Path(os.environ.get("AGENTARK_HOME", Path.home() / ".apex"))


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

def _load_project_registry() -> dict:
    """Load project registry from ~/.agentark/projects.json"""
    registry_file = AGENTARK_HOME / "projects.json"
    if registry_file.exists():
        import json
        return json.loads(registry_file.read_text())
    return {}


def _save_project_registry(data: dict) -> None:
    """Save project registry."""
    import json
    AGENTARK_HOME.mkdir(parents=True, exist_ok=True)
    (AGENTARK_HOME / "projects.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _ensure_project(name: str) -> None:
    """Ensure a project exists in registry. Create if not."""
    registry = _load_project_registry()
    key = name.lower().strip().replace(" ", "-").replace("_", "-")
    if key not in registry:
        registry[key] = {
            "name": name,
            "key": key,
            "created_at": time.strftime("%Y-%m-%d %H:%M"),
            "agents": [],
        }
        _save_project_registry(registry)


def _register_agent_to_project(project: str, agent_name: str) -> None:
    """Register an agent to a project in the registry."""
    registry = _load_project_registry()
    key = project.lower().strip().replace(" ", "-").replace("_", "-")
    if key in registry:
        if agent_name not in registry[key].setdefault("agents", []):
            registry[key]["agents"].append(agent_name)
            _save_project_registry(registry)


def _unregister_agent_from_project(project: str, agent_name: str) -> None:
    """Unregister an agent from a project."""
    registry = _load_project_registry()
    key = project.lower().strip().replace(" ", "-").replace("_", "-")
    if key in registry and agent_name in registry.get("agents", []):
        registry[key]["agents"].remove(agent_name)
        _save_project_registry(registry)


# ══════════════════════════════════════════════════════════════════
# CREATE
# ══════════════════════════════════════════════════════════════════

def create_project_cmd(name: str, desc: str = "") -> None:
    """Create a new project.

    Usage: agentark create project --name <name> [--desc <desc>]
    """
    key = name.lower().strip().replace(" ", "-").replace("_", "-")

    registry = _load_project_registry()
    if key in registry:
        console.print()
        console.print(Panel(
            f"[yellow]⚠ Project '[bold]{key}[/]' already exists[/]\n"
            f"[dim]Created: {registry[key].get('created_at', 'unknown')}[/]\n"
            f"[dim]Agents: {len(registry[key].get('agents', []))}[/]",
            border_style="yellow",
            title="Already Exists",
        ))
        console.print()
        return

    _ensure_project(name)

    if desc:
        registry = _load_project_registry()
        registry[key]["description"] = desc
        _save_project_registry(registry)

    console.print()
    console.print(Panel(
        f"[bold green]✅ Project Created[/]\n\n"
        f"  [cyan]Name:[/]       {name}\n"
        f"  [cyan]Key:[/]        {key}\n"
        f"  [cyan]Directory:[/]  {AGENTARK_HOME}\n\n"
        f"[dim]Next: agentark create team -p {key} --preset saas[/]",
        border_style="green",
        title="Success",
    ))
    console.print()


def create_team_cmd(project: str, roles: str = "", preset: str = "",
                    model_name: str = "deepseek-v4-pro") -> None:
    """Create a team of agents for a project.

    Usage: agentark create team -p <project> [-r <roles>] [--preset <preset>]

    Shows each agent's name, role, badge, and responsibilities after creation.
    """
    key = project.lower().strip().replace(" ", "-").replace("_", "-")

    # Ensure project exists
    _ensure_project(project)

    # Resolve roles
    selected_roles: list[str] = []
    if preset and preset in ROLE_PRESETS:
        selected_roles = list(ROLE_PRESETS[preset])
    elif roles:
        selected_roles = [r.strip() for r in roles.split(",") if r.strip() in AGENT_ROLES]
    else:
        selected_roles = _interactive_role_selection(key)

    if not selected_roles:
        console.print("[yellow]⚠ No valid roles selected[/]")
        return

    # Create agents
    created = []
    for role_key in selected_roles:
        if not _role_exists(role_key):
            continue

        info = AGENT_ROLES[role_key]
        agent_name = _agent_name(key, role_key)

        try:
            profile = pm.load(agent_name)
            # Update if exists
            profile.soul.role = info["name"]
            profile.soul.expertise = info["desc"]
            profile.skills = info["default_skills"]
            pm.save(profile)
            status = "updated"
        except (FileNotFoundError, Exception):
            # Create new
            profile = pm.create_default(agent_name)
            profile.soul.role = info["name"]
            profile.soul.expertise = info["desc"]
            profile.skills = info["default_skills"]
            profile.model.default = model_name
            pm.save(profile)
            status = "created"

        _register_agent_to_project(key, agent_name)
        created.append((agent_name, info, role_key, status))

    # Display team
    console.print()
    table = Table(
        box=box.ROUNDED,
        title=f"🤖 Agent Team — [bold cyan]{project}[/] [dim]({preset or 'custom'})[/]",
    )
    table.add_column("Agent Name", style="cyan bold")
    table.add_column("Badge", style="")
    table.add_column("Role", style="green")
    table.add_column("Responsibilities", style="dim")
    table.add_column("Status", style="yellow")

    for agent_name, info, role_key, status in created:
        table.add_row(
            agent_name,
            info["badge"],
            info["name"],
            info["desc"],
            "🆕" if status == "created" else "♻️",
        )

    console.print(table)
    console.print()

    # Show next steps
    console.print(Panel(
        f"[bold]🚀 Quick Start[/]\n\n"
        f"  [green]View team:[/]    agentark view team -p {key}\n"
        f"  [green]Launch PM:[/]    agentark run hermes -a {key}-pm -f {key}\n"
        f"  [green]Launch all:[/]   agentark team launch {key}",
        border_style="cyan",
    ))
    console.print()


# ══════════════════════════════════════════════════════════════════
# DELETE
# ══════════════════════════════════════════════════════════════════

def delete_cmd(project: str, agent: str = "", force: bool = False) -> None:
    """Delete a project or individual agent.

    Usage: agentark delete -p <project> [-a <agent>] [--force]
    """
    key = project.lower().strip().replace(" ", "-").replace("_", "-")

    if agent:
        # Delete individual agent
        agent_name = _agent_name(key, agent) if "-" not in agent else agent

        try:
            profile = pm.load(agent_name)
        except (FileNotFoundError, Exception):
            console.print(f"[red]✗ Agent '[bold]{agent_name}[/]' not found[/]")
            return

        if not force:
            console.print()
            console.print(Panel(
                f"[yellow]⚠ Delete agent '[bold]{agent_name}[/]'?[/]\n"
                f"  Role: {profile.soul.role}\n"
                f"  Model: {profile.model.default}",
                border_style="yellow",
                title="Confirm Delete",
            ))
            if not Confirm.ask("  Delete?", default=False):
                console.print("[dim]Cancelled[/]")
                return

        pm.delete(agent_name)
        _unregister_agent_from_project(key, agent_name)
        console.print(f"[green]✅ Deleted agent: [bold]{agent_name}[/][/]")

    else:
        # Delete entire project
        agents = _list_project_agents(key)

        if not force:
            console.print()
            console.print(Panel(
                f"[yellow]⚠ Delete project '[bold]{project}[/]' + [bold]{len(agents)} agents[/]?[/]\n"
                + "\n".join(f"  • {a}" for a in agents),
                border_style="yellow",
                title="Confirm Delete",
            ))
            if not Confirm.ask("  Delete everything?", default=False):
                console.print("[dim]Cancelled[/]")
                return

        deleted = 0
        for a in agents:
            try:
                pm.delete(a)
                deleted += 1
            except Exception:
                pass

        _unregister_agent_from_project(key, agent_name=None)
        registry = _load_project_registry()
        registry.pop(key, None)
        _save_project_registry(registry)

        console.print(
            f"[green]✅ Deleted project [bold]{project}[/] + {deleted} agents[/]"
        )


# ══════════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════════

def run_hermes_cmd(agent: str, project: str) -> None:
    """Launch Hermes with a project agent.

    Usage: agentark run hermes -a <agent> -f <project>

    Dialog title: "hermes-<agent> for <project>"
    """
    from agentark.interface.hermes_sync import sync_profile_to_hermes, start_hermes_profile

    # Determine agent name
    key = project.lower().strip().replace(" ", "-").replace("_", "-")
    if "-" not in agent:
        agent_name = f"{key}-{agent}"
    else:
        agent_name = agent

    # Sync to Hermes
    display_name = f"hermes-{agent_name} for {project}"

    console.print()
    with console.status(f"[cyan]Syncing [bold]{agent_name}[/]...[/]"):
        result = sync_profile_to_hermes(
            agent_name,
            hermes_profile_name=agent_name,
            hermes_display_name=display_name,
        )

    console.print(f"[green]✅ Synced: [bold]{agent_name}[/][/]")
    console.print(f"  Title: [cyan]{display_name}[/]")
    console.print()

    # Launch
    start_hermes_profile(agent_name)


# ══════════════════════════════════════════════════════════════════
# STOP
# ══════════════════════════════════════════════════════════════════

def stop_hermes_cmd(agent: str) -> None:
    """Stop a Hermes session for an agent.

    Usage: agentark stop hermes -a <agent>
    """
    import subprocess

    # Find and kill Hermes process with this profile
    try:
        result = subprocess.run(
            ["pgrep", "-f", f"hermes.*-p.*{agent}"],
            capture_output=True, text=True, timeout=5,
        )
        pids = [p.strip() for p in result.stdout.split("\n") if p.strip()]
        if pids:
            for pid in pids:
                subprocess.run(["kill", pid], timeout=5)
            console.print(f"[green]✅ Stopped Hermes sessions for [bold]{agent}[/] ({len(pids)} process(es))[/]")
        else:
            console.print(f"[yellow]⚠ No running Hermes session found for '{agent}'[/]")
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/]")


# ══════════════════════════════════════════════════════════════════
# VIEW
# ══════════════════════════════════════════════════════════════════

def view_project_cmd(name: str) -> None:
    """View project overview.

    Usage: agentark view project -n <name>
    """
    key = name.lower().strip().replace(" ", "-").replace("_", "-")
    registry = _load_project_registry()

    if key not in registry:
        console.print(f"[red]✗ Project '{name}' not found[/]")
        return

    proj = registry[key]
    agents = _list_project_agents(key)

    console.print()
    console.print(Panel(
        f"[bold cyan]{proj['name']}[/] [dim]({proj['key']})[/]\n"
        f"  Created: {proj.get('created_at', 'unknown')}\n"
        f"  Agents:  {len(agents)}\n"
        + (f"  Desc:    {proj.get('description', '')}" if proj.get('description') else ""),
        border_style="cyan",
        title="📋 Project Overview",
    ))

    if agents:
        console.print()
        table = Table(box=box.ROUNDED, title="Team Members")
        table.add_column("Agent", style="cyan")
        table.add_column("Role", style="green")
        table.add_column("Model", style="yellow")
        table.add_column("Skills", style="dim")

        for a in sorted(agents):
            try:
                p = pm.load(a)
                table.add_row(
                    a,
                    p.soul.role or "-",
                    p.model.default or "default",
                    ", ".join(p.skills[:3]) if p.skills else "-",
                )
            except Exception:
                table.add_row(a, "[dim]—[/]", "[dim]—[/]", "[dim]—[/]")

        console.print(table)

    console.print()


def view_team_cmd(project: str) -> None:
    """View team members for a project.

    Usage: agentark view team -p <project>
    """
    key = project.lower().strip().replace(" ", "-").replace("_", "-")
    agents = _list_project_agents(key)

    if not agents:
        console.print(f"[yellow]⚠ No agents found for project '{project}'[/]")
        console.print(f"[dim]Create: agentark create team -p {key} --preset saas[/]")
        return

    console.print()
    console.print(Panel(
        f"[bold cyan]🤖 {project} Team[/]  [dim]{len(agents)} agents[/]",
        border_style="cyan",
    ))

    table = Table(box=box.ROUNDED)
    table.add_column("Agent Name", style="cyan bold")
    table.add_column("Role", style="green")
    table.add_column("Model", style="yellow")
    table.add_column("Responsibilities", style="dim")
    table.add_column("Skills")

    for a in sorted(agents):
        try:
            p = pm.load(a)
            table.add_row(
                a,
                p.soul.role or "-",
                p.model.default or "default",
                p.soul.expertise or "-",
                ", ".join(p.skills[:3]) if p.skills else "-",
            )
        except Exception:
            table.add_row(a, "[dim]—[/]", "[dim]—[/]", "[dim]—[/]", "[dim]—[/]")

    console.print(table)

    # Show launch commands
    console.print()
    console.print(f"[dim]Launch: agentark run hermes -a {key}-pm -f {key}[/]")
    console.print(f"[dim]View:   agentark view agent -a {key}-pm[/]")
    console.print()


def view_agent_cmd(name: str) -> None:
    """View detailed agent information.

    Usage: agentark view agent -a <name>
    """
    try:
        p = pm.load(name)
    except (FileNotFoundError, Exception):
        console.print(f"[red]✗ Agent '{name}' not found[/]")
        return

    console.print()
    console.print(Panel(
        f"[bold cyan]{name}[/]\n"
        f"  Role:         {p.soul.role or '—'}\n"
        f"  Expertise:    {p.soul.expertise or '—'}\n"
        f"  Personality:  {p.soul.personality or '—'}\n"
        f"  Comm Style:   {p.soul.communication or '—'}\n"
        f"  Model:        {p.model.default or 'default'}\n"
        f"  Skills:       {', '.join(p.skills) if p.skills else '—'}",
        border_style="cyan",
        title=f"👤 Agent Detail",
    ))
    console.print()


def view_tasks_cmd(project: str) -> None:
    """View tasks for a project.

    Usage: agentark view tasks -p <project>
    """
    key = project.lower().strip().replace(" ", "-").replace("_", "-")

    # Check for task DB
    task_db = AGENTARK_HOME / "tasks.json"
    if not task_db.exists():
        console.print(f"[yellow]⚠ No tasks database found[/]")
        return

    import json
    tasks = json.loads(task_db.read_text())
    project_tasks = [t for t in tasks if t.get("project", "").startswith(key)]

    if not project_tasks:
        console.print(f"[dim]No tasks for project '{project}'[/]")
        return

    console.print()
    table = Table(box=box.ROUNDED, title=f"📋 Tasks — {project}")
    table.add_column("ID", style="dim")
    table.add_column("Title", style="bold")
    table.add_column("Status", style="green")
    table.add_column("Assignee", style="cyan")
    table.add_column("Priority", style="yellow")
    table.add_column("Due", style="dim")

    status_color = {
        "todo": "dim", "in_progress": "yellow",
        "done": "green", "blocked": "red", "cancelled": "dim",
    }

    for t in project_tasks[:20]:
        s = t.get("status", "todo")
        table.add_row(
            t.get("id", "")[:8],
            t.get("title", "")[:40],
            f"[{status_color.get(s, '')}]{s}[/]",
            t.get("assignee", "-"),
            t.get("priority", "-"),
            t.get("due", "-"),
        )

    console.print(table)
    console.print(f"\n[dim]{len(project_tasks)} tasks total | agentark view tasks -p {key}[/]\n")


# ══════════════════════════════════════════════════════════════════
# ADD
# ══════════════════════════════════════════════════════════════════

def add_agent_cmd(project: str, role: str, model_name: str = "deepseek-v4-pro") -> None:
    """Add a new agent to an existing project.

    Usage: agentark add agent -p <project> -r <role> [--model <model>]
    """
    key = project.lower().strip().replace(" ", "-").replace("_", "-")

    if not _role_exists(role):
        console.print(f"[red]✗ Unknown role: '{role}'[/]")
        console.print(f"[dim]Run: agentark team list-roles[/]")
        return

    info = AGENT_ROLES[role]
    agent_name = _agent_name(key, role)

    try:
        pm.load(agent_name)
        console.print(f"[yellow]⚠ Agent '[bold]{agent_name}[/]' already exists[/]")
        return
    except Exception:
        pass

    # Create agent
    profile = pm.create_default(agent_name)
    profile.soul.role = info["name"]
    profile.soul.expertise = info["desc"]
    profile.skills = info["default_skills"]
    profile.model.default = model_name
    pm.save(profile)
    _register_agent_to_project(key, agent_name)

    console.print()
    console.print(f"[green]✅ Added: [bold]{info['badge']} {agent_name}[/] — {info['name']}[/]")
    console.print(f"  Role:  {info['desc']}")
    console.print(f"  Model: {model_name}")
    console.print(f"  Skills: {', '.join(info['default_skills'][:4])}")
    console.print()


# ══════════════════════════════════════════════════════════════════
# CHANGE
# ══════════════════════════════════════════════════════════════════

def change_model_cmd(agent: str, model: str) -> None:
    """Change the model for an agent.

    Usage: agentark change model -a <agent> -m <model>
    """
    try:
        profile = pm.load(agent)
    except Exception:
        console.print(f"[red]✗ Agent '{agent}' not found[/]")
        return

    old_model = profile.model.default
    profile.model.default = model
    pm.save(profile)

    console.print(
        f"[green]✅ Model changed: [bold]{agent}[/] "
        f"[dim]{old_model} → [/][cyan]{model}[/]"
    )


def change_role_cmd(agent: str, role: str) -> None:
    """Change the role of an agent.

    Usage: agentark change role -a <agent> -r <new_role>
    """
    if not _role_exists(role):
        console.print(f"[red]✗ Unknown role: '{role}'[/]")
        return

    try:
        profile = pm.load(agent)
    except Exception:
        console.print(f"[red]✗ Agent '{agent}' not found[/]")
        return

    info = AGENT_ROLES[role]
    old_role = profile.soul.role
    profile.soul.role = info["name"]
    profile.soul.expertise = info["desc"]
    profile.skills = info["default_skills"]
    pm.save(profile)

    console.print(
        f"[green]✅ Role changed: [bold]{agent}[/] "
        f"[dim]{old_role} → [/][cyan]{info['badge']} {info['name']}[/]"
    )


# ══════════════════════════════════════════════════════════════════
# UPDATE
# ══════════════════════════════════════════════════════════════════

def update_self_cmd() -> None:
    """Update AgentArk to latest version."""
    from agentark.interface.version import get_current_version, get_latest_version, cmd_update

    current = get_current_version()
    latest = get_latest_version()

    console.print()
    console.print(f"[bold]AgentArk[/] v{current}")
    if latest["version"] != current:
        console.print(f"[yellow]Update available: v{latest['version']}[/]")
        cmd_update()
    else:
        console.print("[green]✅ Already latest[/]")


def update_project_cmd(project: str) -> None:
    """Refresh project agent configurations.

    Usage: agentark update project -p <project>
    """
    key = project.lower().strip().replace(" ", "-").replace("_", "-")
    agents = _list_project_agents(key)

    if not agents:
        console.print(f"[yellow]⚠ No agents for '{project}'[/]")
        return

    updated = 0
    for agent_name in agents:
        try:
            profile = pm.load(agent_name)
            pm.save(profile)
            updated += 1
        except Exception:
            pass

    console.print(f"[green]✅ Refreshed {updated}/{len(agents)} agents for [bold]{project}[/][/]")


# ══════════════════════════════════════════════════════════════════
# CLICK GROUPS — registered in main.py
# ══════════════════════════════════════════════════════════════════

import click as _click

@_click.group(name="create")
def create_group():
    """🆕 Create projects and agent teams"""
    pass

@create_group.command(name="project")
@_click.option("--name", "-n", required=True, help="Project name")
@_click.option("--desc", "-d", default="", help="Project description")
def _create_project(name, desc):
    create_project_cmd(name, desc)

@create_group.command(name="team")
@_click.option("--project", "-p", required=True, help="Project name")
@_click.option("--roles", "-r", default="", help="Comma-separated role keys (e.g. pm,architect,backend)")
@_click.option("--preset", default="", help=f"Role preset: {', '.join(list(ROLE_PRESETS.keys())[:6])}")
@_click.option("--model", "-m", default="deepseek-v4-pro", help="Default model")
def _create_team(project, roles, preset, model):
    create_team_cmd(project, roles, preset, model)


@_click.group(name="delete")
def delete_group():
    """🗑️ Delete projects and agents"""
    pass

@delete_group.command(name="project")
@_click.option("--project", "-p", required=True, help="Project name")
@_click.option("--agent", "-a", default="", help="Specific agent to delete (omit to delete entire project)")
@_click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def _delete(project, agent, force):
    delete_cmd(project, agent, force)


@_click.group(name="run")
def run_group():
    """▶️ Run agents and Hermes sessions"""
    pass

@run_group.command(name="hermes")
@_click.option("--agent", "-a", required=True, help="Agent name or role key")
@_click.option("--for", "-f", "project_name", required=True, help="Project name")
def _run_hermes(agent, project_name):
    run_hermes_cmd(agent, project_name)


@_click.group(name="stop")
def stop_group():
    """⏹️ Stop agents and Hermes sessions"""
    pass

@stop_group.command(name="hermes")
@_click.option("--agent", "-a", required=True, help="Agent name")
def _stop_hermes(agent):
    stop_hermes_cmd(agent)


@_click.group(name="view")
def view_group():
    """👁️ View projects, teams, agents, and tasks"""
    pass

@view_group.command(name="project")
@_click.option("--name", "-n", required=True, help="Project name")
def _view_project(name):
    view_project_cmd(name)

@view_group.command(name="team")
@_click.option("--project", "-p", required=True, help="Project name")
def _view_team(project):
    view_team_cmd(project)

@view_group.command(name="agent")
@_click.option("--agent", "-a", required=True, help="Agent name")
def _view_agent(agent):
    view_agent_cmd(agent)

@view_group.command(name="tasks")
@_click.option("--project", "-p", required=True, help="Project name")
def _view_tasks(project):
    view_tasks_cmd(project)


@_click.group(name="add")
def add_group():
    """➕ Add agents and roles"""
    pass

@add_group.command(name="agent")
@_click.option("--project", "-p", required=True, help="Project name")
@_click.option("--role", "-r", required=True, help="Role key (e.g. pm, architect, devops)")
@_click.option("--model", "-m", default="deepseek-v4-pro", help="Default model")
def _add_agent(project, role, model):
    add_agent_cmd(project, role, model)


@_click.group(name="change")
def change_group():
    """🔄 Change agent models and roles"""
    pass

@change_group.command(name="model")
@_click.option("--agent", "-a", required=True, help="Agent name")
@_click.option("--model", "-m", required=True, help="New model name")
def _change_model(agent, model):
    change_model_cmd(agent, model)

@change_group.command(name="role")
@_click.option("--agent", "-a", required=True, help="Agent name")
@_click.option("--role", "-r", required=True, help="New role key")
def _change_role(agent, role):
    change_role_cmd(agent, role)


@_click.group(name="update")
def update_group():
    """🔄 Update AgentArk or project configurations"""
    pass

@update_group.command(name="self")
def _update_self():
    update_self_cmd()

@update_group.command(name="project")
@_click.option("--project", "-p", required=True, help="Project name")
def _update_project(project):
    update_project_cmd(project)
