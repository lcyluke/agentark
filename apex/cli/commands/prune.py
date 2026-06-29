"""AgentArk — Fleet Prune: cleanup idle/unused agents.

Detects and removes agents that meet ALL of:
  1. No SKILLs assigned (skill count = 0)
  2. Not assigned to any project team
  3. No tasks completed in the last 7 days

Commands:
  agentark fleet prune              Dry-run: list candidates, ask confirm
  agentark fleet prune --dry-run    Preview only, no deletion
  agentark fleet prune --force      Delete all without confirmation
  agentark fleet prune --older 14   Custom idle threshold (days, default 7)
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm
from rich import box

from apex.core.profile import APEX_HOME, ProfileManager
from apex.interface.skill_registry import get_registry

console = Console()

# ── Paths ────────────────────────────────────────────────────────

HERMES_HOME = Path(os.path.expanduser("~/.hermes"))
PROFILES_DIR = HERMES_HOME / "profiles"
PROJECTS_FILE = APEX_HOME / "projects_registry.json"
KANBAN_DB = APEX_HOME / "kanban.db"
TASK_DB = APEX_HOME / "task_history.json"


def _get_skill_count(agent_name: str) -> int:
    """Get skill count for an agent from the skill registry."""
    try:
        registry = get_registry()
        skills = registry.get_agent_skills(agent_name)
        return len(skills)
    except Exception:
        pass

    # Fallback: count SKILL.md files in agent's skills dir
    skills_dir = Path(os.path.expanduser(f"~/.hermes/profiles/{agent_name}/skills"))
    if skills_dir.exists():
        return len(list(skills_dir.rglob("SKILL.md")))
    return 0


def _get_assigned_projects(agent_name: str) -> list[str]:
    """Get list of project names this agent is assigned to."""
    projects = []
    if not PROJECTS_FILE.exists():
        return projects

    try:
        with open(PROJECTS_FILE) as f:
            data = json.load(f)
        for proj_name, proj_data in data.get("projects", {}).items():
            team = proj_data.get("team", [])
            if agent_name in team:
                projects.append(proj_name)
        # Also check apex.yaml in common project dirs
    except Exception:
        pass

    # Check apex.yaml files in workspace dirs
    workspace = Path(os.path.expanduser("~/Desktop/2026workspace"))
    for apex_yaml in workspace.rglob("apex.yaml"):
        try:
            import yaml
            with open(apex_yaml) as f:
                cfg = yaml.safe_load(f) or {}
            team = cfg.get("team", [])
            if agent_name in team:
                projects.append(cfg.get("project", apex_yaml.parent.name))
        except Exception:
            pass

    return projects


def _get_last_task_time(agent_name: str) -> Optional[datetime]:
    """Get the timestamp of the last completed task for this agent."""
    last_time = None

    # Check task history JSON
    if TASK_DB.exists():
        try:
            with open(TASK_DB) as f:
                history = json.load(f)
            tasks = history if isinstance(history, list) else history.get("tasks", [])
            for task in tasks:
                if task.get("assignee") == agent_name:
                    ts = task.get("completed_at") or task.get("updated_at") or task.get("created_at")
                    if ts:
                        try:
                            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                            if last_time is None or dt > last_time:
                                last_time = dt
                        except Exception:
                            pass
        except Exception:
            pass

    # Check kanban.db SQLite
    if not last_time and KANBAN_DB.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(KANBAN_DB))
            cursor = conn.execute(
                "SELECT MAX(updated_at) FROM tasks WHERE assignee = ? AND status = 'completed'",
                (agent_name,),
            )
            row = cursor.fetchone()
            conn.close()
            if row and row[0]:
                try:
                    last_time = datetime.fromisoformat(row[0].replace("Z", "+00:00"))
                except Exception:
                    pass
        except Exception:
            pass

    return last_time


def _collect_candidates(idle_days: int = 7) -> list[dict]:
    """Collect agent candidates for pruning.

    An agent is a candidate if ALL of:
      1. skill_count == 0
      2. No project assignment
      3. No task in the last `idle_days` days (or never had a task)
    """
    pm = ProfileManager()
    all_profiles = pm.list()

    cutoff = datetime.now() - timedelta(days=idle_days)
    candidates = []

    for agent_name in all_profiles:
        # Skip system/default profiles
        if agent_name in ("default", "system", "origin"):
            continue

        # Check 1: No SKILLs
        skill_count = _get_skill_count(agent_name)
        has_skills = skill_count > 0

        # Check 2: Project assignment
        projects = _get_assigned_projects(agent_name)
        has_project = len(projects) > 0

        # Check 3: Recent tasks
        last_task = _get_last_task_time(agent_name)
        has_recent_tasks = last_task is not None and last_task > cutoff

        # Candidate if ALL three conditions are negative
        if not has_skills and not has_project and not has_recent_tasks:
            candidates.append({
                "name": agent_name,
                "skill_count": skill_count,
                "projects": projects,
                "last_task": last_task,
                "idle_days": (
                    (datetime.now() - last_task).days
                    if last_task else None
                ),
            })

    return candidates


def prune_cmd(dry_run: bool = False, force: bool = False,
              older: int = 7, yes: bool = False):
    """Prune idle/unused agent profiles.

    Args:
        dry_run: Preview only, no deletion
        force: Delete without confirmation
        older: Idle threshold in days (default: 7)
        yes: Auto-confirm each deletion
    """
    idle_days = older

    console.print()
    console.print(Panel(
        f"[bold]🧹 AgentArk Fleet Prune[/]\n"
        f"[dim]Detects agents with: ① no SKILLs  ② no project assignment  ③ idle ≥ {idle_days}d[/]",
        border_style="yellow",
    ))
    console.print()

    candidates = _collect_candidates(idle_days)

    if not candidates:
        console.print("[green]✅ No idle agents found. Fleet is clean![/]")
        console.print()
        return

    # ── Table ──
    table = Table(
        title=f"🧹 Prune Candidates ({len(candidates)} agents — idle ≥ {idle_days}d)",
        border_style="yellow",
        box=box.ROUNDED,
        show_header=True,
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Agent", style="cyan")
    table.add_column("Skills", justify="center")
    table.add_column("Project", style="dim")
    table.add_column("Last Task", style="yellow")
    table.add_column("Idle", justify="right")

    for i, c in enumerate(candidates, 1):
        last_str = c["last_task"].strftime("%Y-%m-%d") if c["last_task"] else "never"
        idle_str = f"{c['idle_days']}d" if c["idle_days"] is not None else "∞"
        proj_str = ", ".join(c["projects"]) if c["projects"] else "[red]none[/]"
        skill_str = str(c["skill_count"]) if c["skill_count"] > 0 else "[red]0[/]"

        table.add_row(
            str(i),
            c["name"],
            skill_str,
            proj_str,
            last_str,
            idle_str,
        )

    console.print(table)
    console.print()

    if dry_run:
        console.print("[dim]💡 Dry-run mode — no agents deleted. Remove --dry-run to prune.[/]")
        console.print()
        return

    # ── Confirmation ──
    if force:
        console.print("[bold red]⚠️  FORCE mode — will delete ALL candidates without confirmation[/]")
        if not Confirm.ask("Proceed with force deletion?", default=False):
            console.print("[dim]Cancelled.[/]")
            return
    else:
        console.print(f"[yellow]⚠️  {len(candidates)} agents will be removed.[/]")
        if not yes and not Confirm.ask("Proceed with deletion?", default=False):
            console.print("[dim]Cancelled.[/]")
            return

    # ── Delete ──
    pm = ProfileManager()
    deleted = 0
    skipped = 0

    for c in candidates:
        agent_name = c["name"]
        profile_dir = PROFILES_DIR / agent_name

        if not force and not yes:
            if not Confirm.ask(f"  Delete [cyan]{agent_name}[/]?", default=True):
                skipped += 1
                continue

        try:
            # Remove Hermes profile directory
            if profile_dir.exists():
                import shutil
                shutil.rmtree(profile_dir)
                console.print(f"  [green]🗑  {agent_name}[/] — profile removed")
                deleted += 1
            else:
                console.print(f"  [dim]  {agent_name} — profile not found, skipping[/]")
                skipped += 1

            # Remove wrapper script
            wrapper = Path(os.path.expanduser(f"~/.local/bin/{agent_name}"))
            if wrapper.exists():
                wrapper.unlink()
        except Exception as e:
            console.print(f"  [red]✗ {agent_name}: {e}[/]")
            skipped += 1

    # ── Summary ──
    console.print()
    console.print(Panel(
        f"[bold green]✅ Prune complete[/]\n"
        f"Deleted: [green]{deleted}[/] | Skipped: [yellow]{skipped}[/] | Total: {len(candidates)}",
        border_style="green",
    ))
    console.print()
