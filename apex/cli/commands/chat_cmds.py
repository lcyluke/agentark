"""Apex Chat — Unified CLI launcher for all Apex agents.

Usage:
    apex chat <agent_name>            Launch chat with a specific agent
    apex chat <agent_name> --context "..."  Add project context
    apex chat list                    List all available agents

Every Apex agent gets auto-synced to Hermes on first launch.
Project context is injected so agents share awareness.
"""

from __future__ import annotations

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
PROJECT_CONTEXT_FILE = Path(".apex/project_context.md")
AGENTS_MD = Path("AGENTS.md")


# ══════════════════════════════════════════
# Agent Discovery
# ══════════════════════════════════════════

def list_all_agents() -> list[dict]:
    """Discover all agents: Apex profiles + Hermes profiles + pre-built souls"""
    agents = {}

    # 1. Hermes profiles (already synced)
    hermes_profiles_dir = HERMES_HOME / "profiles"
    if hermes_profiles_dir.exists():
        for pdir in sorted(hermes_profiles_dir.iterdir()):
            if not pdir.is_dir():
                continue
            name = pdir.name
            soul_file = pdir / "SOUL.md"
            role = name
            if soul_file.exists():
                content = soul_file.read_text()
                first_line = content.split("\n")[0] if content else ""
                role = first_line.replace("# ", "").strip().lstrip("🤖📋💻⚙️🔧✍️🖊️📝📤🗄️📊🧪🤖🚀👨‍💻🎨📈🔬📐📚👁️🛡️🔍 ")

            agents[name] = {
                "name": name,
                "role": role,
                "source": "hermes",
                "has_soul": soul_file.exists() if soul_file else False,
            }

    # 2. Apex profiles (not yet synced)
    try:
        from apex.core.profile import ProfileManager
        pm = ProfileManager()
        for name in pm.list():
            if name not in agents:
                try:
                    p = pm.load(name)
                    agents[name] = {
                        "name": name,
                        "role": p.soul.role if p.soul else name,
                        "source": "apex",
                        "has_soul": True,
                    }
                except Exception:
                    agents[name] = {
                        "name": name,
                        "role": name,
                        "source": "apex",
                        "has_soul": False,
                    }
    except Exception:
        pass

    # 3. Pre-built role souls
    try:
        from apex.interface.hermes_sync import ROLE_SOULS
        for name, soul_data in ROLE_SOULS.items():
            if name not in agents:
                agents[name] = {
                    "name": name,
                    "role": soul_data.get("role", name),
                    "source": "template",
                    "has_soul": True,
                }
    except Exception:
        pass

    return list(agents.values())


def find_agent(name: str) -> Optional[dict]:
    """Find an agent by name across all sources."""
    all_agents = list_all_agents()
    for a in all_agents:
        if a["name"] == name:
            return a
    return None


# ══════════════════════════════════════════
# Context Injection
# ══════════════════════════════════════════

def collect_project_context() -> str:
    """Collect project context for shared awareness among agents.

    Reads from:
        1. ./AGENTS.md — project overview (if exists)
        2. ./.apex/project_context.md — Apex-specific project context
        3. ./.apex/kanban.db — current task summary
    """
    parts = []

    # 1. AGENTS.md
    if AGENTS_MD.exists():
        content = AGENTS_MD.read_text()
        # Trim to first 2000 chars as context preamble
        parts.append(content[:2000])
        parts.append("")

    # 2. Apex project context
    if PROJECT_CONTEXT_FILE.exists():
        content = PROJECT_CONTEXT_FILE.read_text()
        parts.append(content[:2000])
        parts.append("")

    # 3. Current Kanban summary
    kanban_db = Path.home() / ".apex" / "kanban.db"
    if kanban_db.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(kanban_db))
            conn.row_factory = sqlite3.Row
            tasks = conn.execute(
                "SELECT title, assignee, status, priority FROM tasks "
                "WHERE status IN ('in_progress', 'ready', 'todo') "
                "ORDER BY priority ASC LIMIT 15"
            ).fetchall()
            conn.close()

            if tasks:
                parts.append("## Current Project Tasks (Kanban)")
                parts.append("")
                for t in tasks:
                    status_icon = {"in_progress": "🔄", "ready": "📋", "todo": "⏳"}.get(t["status"], "▪")
                    parts.append(
                        f"- {status_icon} [{t['priority']}] **{t['assignee'] or 'unassigned'}**: "
                        f"{t['title'][:80]}"
                    )
                parts.append("")
        except Exception:
            pass

    # 4. Fleet teams (cross-agent awareness)
    teams_file = HERMES_HOME / "fleet_teams.json"
    if teams_file.exists():
        try:
            import json
            with open(teams_file) as f:
                data = json.load(f)
            teams = data.get("teams", {})
            if teams:
                parts.append("## Project Teams & Agents")
                parts.append("")
                for tname, team in teams.items():
                    members = team.get("members", [])
                    member_str = ", ".join(
                        f"{m['agent_id']} ({m.get('role', 'member')})"
                        for m in members[:5]
                    )
                    parts.append(f"- **{tname}**: {member_str}")
                parts.append("")
        except Exception:
            pass

    return "\n".join(parts) if parts else ""


def inject_context_for_profile(profile_name: str, project_context: str):
    """Write project context into the Hermes profile's home directory
    so it's injected into the agent's system prompt automatically.
    """
    profile_dir = HERMES_HOME / "profiles" / profile_name
    if not profile_dir.exists():
        profile_dir.mkdir(parents=True, exist_ok=True)

    home_dir = profile_dir / "home"
    home_dir.mkdir(exist_ok=True)

    context_file = home_dir / "AGENTS.md"
    context_file.write_text(project_context)


# ══════════════════════════════════════════
# Sync & Launch
# ══════════════════════════════════════════

def sync_agent_to_hermes(agent_name: str) -> bool:
    """Ensure the agent has a Hermes profile. Auto-sync if needed."""
    profile_dir = HERMES_HOME / "profiles" / agent_name
    if profile_dir.exists() and (profile_dir / "SOUL.md").exists() and (profile_dir / "config.yaml").exists():
        return True

    console.print(f"[yellow]⚡ Auto-syncing '{agent_name}' to Hermes...[/]")

    try:
        from apex.interface.hermes_sync import sync_profile_to_hermes, ROLE_SOULS
    except ImportError:
        console.print("[red]❌ Cannot import hermes_sync module[/]")
        return False

    # Check if this is a pre-built role
    if agent_name in ROLE_SOULS:
        soul_data = ROLE_SOULS[agent_name]
        display = soul_data.get("role", agent_name)
    else:
        display = None

    try:
        result = sync_profile_to_hermes(
            agent_name,
            hermes_profile_name=agent_name,
            hermes_display_name=display,
        )
        console.print(f"  ✅ Synced → {result['soul_file']}")
        return True
    except Exception as e:
        console.print(f"[red]❌ Sync failed: {e}[/]")
        return False


def launch_hermes_chat(profile_name: str, extra_args: list = None):
    """Launch hermes CLI with the given profile."""
    cmd = ["hermes", "-p", profile_name]

    # Pass any extra args (like initial message)
    if extra_args:
        cmd.extend(extra_args)

    # Use the hermes_sync start function for rich terminal integration
    try:
        from apex.interface.hermes_sync import start_hermes_profile
        query = extra_args[0] if extra_args else ""
        start_hermes_profile(profile_name, query)
    except Exception:
        # Fallback: direct hermes launch
        console.print(f"[dim]Launching: {' '.join(cmd)}[/]")
        subprocess.run(cmd)


# ══════════════════════════════════════════
# CLI Entry Points
# ══════════════════════════════════════════

def chat_list_cmd():
    """List all available agents."""
    agents = list_all_agents()

    table = Table(title="🤖 All Available Agents", box=None)
    table.add_column("Name", style="cyan")
    table.add_column("Role", style="white")
    table.add_column("Source", style="dim")
    table.add_column("Ready", style="green")

    for a in sorted(agents, key=lambda x: x["name"]):
        source_icon = {"hermes": "🔗", "apex": "📦", "template": "📋"}.get(a["source"], "❓")
        ready = "✅" if a["has_soul"] else "⚠️"
        table.add_row(a["name"], a["role"][:40], f"{source_icon} {a['source']}", ready)

    console.print(table)
    console.print("\n[dim]Usage: apex chat <agent_name>[/]")


def chat_launch_cmd(agent_name: str, context: str = "", query: str = ""):
    """Launch a chat session with the specified agent."""
    # 1. Find the agent
    agent = find_agent(agent_name)
    if not agent:
        console.print(f"[red]❌ Agent '{agent_name}' not found.[/]")
        console.print("\n[dim]Use 'apex chat list' to see available agents.[/]")
        return

    # 2. Display agent info
    console.print(Panel(
        f"[bold]{agent['role']}[/]\n"
        f"Profile: [cyan]{agent['name']}[/] · Source: {agent['source']}",
        title=f"🤖 Launching {agent_name}",
        border_style="green",
    ))

    # 3. Sync to Hermes if needed
    if not sync_agent_to_hermes(agent_name):
        console.print("[red]❌ Cannot launch — sync failed.[/]")
        return

    # 4. Collect and inject project context
    project_context = context or collect_project_context()
    if project_context:
        inject_context_for_profile(agent_name, project_context)
        context_lines = project_context.strip().split("\n")
        console.print(f"[dim]📄 Injected project context ({len(context_lines)} lines)[/]")

    # 5. Launch Hermes
    extra_args = []
    if query:
        extra_args = ["-q", query]
    console.print(f"\n[bold cyan]🚀 Starting {agent_name}...[/]\n")
    launch_hermes_chat(agent_name, extra_args)
