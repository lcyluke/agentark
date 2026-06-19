"""Apex Hermes integration — project context injection and agent switching.

When Apex launches Hermes from within a project directory, it:
  1. Generates AGENTS.md with project context (injected into Hermes system prompt)
  2. Sets up Hermes profile per agent
  3. Displays a project banner before launching
"""

from __future__ import annotations

import json
import yaml
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# ═══════════════════════════════════════════════════════════════════════════════
# AGENTS.md Generator — injects project context into Hermes
# ═══════════════════════════════════════════════════════════════════════════════

def generate_agents_md(project_path: Path, project_config: dict) -> str:
    """Generate an AGENTS.md file that Hermes will load as project context.

    Hermes auto-detects AGENTS.md (and CLAUDE.md, .cursorrules) in the
    current working directory and injects them into the system prompt.
    """
    name = project_config.get("project", project_path.name)
    ptype = project_config.get("type", "unknown")
    desc = project_config.get("description", "")
    team = project_config.get("team", [])
    provider = project_config.get("default_provider", "deepseek")
    model = project_config.get("default_model", "deepseek-v4-pro")

    start_time = project_config.get("created_at", datetime.now().isoformat())
    scale = project_config.get("scale", "startup")

    doc = f"""# {name} — Apex Project Context

## Project
- **Name:** {name}
- **Type:** {ptype}
- **Scale:** {scale}
- **Description:** {desc}
- **Started:** {start_time}
- **Provider:** {provider} / {model}

## Agent Team
"""
    for agent_id in team:
        doc += f"- **{agent_id}**: Active team member\n"

    doc += """
## Conventions
- This is an Apex-managed project. All agents are coordinated through Apex CLI.
- Use `apex s` for status, `apex p` for PM dashboard.
- Agent profiles are in `teams/` directory.
- Task tracking via `.apex/roadmap.json`.
"""
    return doc


def sync_agents_md(project_path: Path) -> bool:
    """Sync AGENTS.md from apex.yaml if it exists."""
    config_path = project_path / "apex.yaml"
    if not config_path.exists():
        return False

    with open(config_path) as f:
        config = yaml.safe_load(f) or {}

    content = generate_agents_md(project_path, config)
    agents_path = project_path / "AGENTS.md"
    with open(agents_path, "w") as f:
        f.write(content)
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# Project Banner — displayed when entering Apex context
# ═══════════════════════════════════════════════════════════════════════════════

def show_project_banner(console: Console, project_path: Path | None = None):
    """Display the Apex project context banner.

    Shows: project name, agent, start time, token tracking, session time.
    Designed to match Hermes status line format.
    """
    if project_path is None:
        project_path = Path.cwd()

    config_path = project_path / "apex.yaml"
    if not config_path.exists():
        return

    with open(config_path) as f:
        config = yaml.safe_load(f) or {}

    name = config.get("project", project_path.name)
    ptype = config.get("type", "?")
    team = config.get("team", [])
    provider = config.get("default_provider", "deepseek")
    model = config.get("default_model", "deepseek-v4-pro")
    start_time = config.get("created_at", "")

    # Try to load roadmap for progress
    roadmap_path = project_path / ".apex" / "roadmap.json"
    total_tasks = 0
    done_tasks = 0
    if roadmap_path.exists():
        try:
            with open(roadmap_path) as f:
                roadmap = json.load(f)
            tasks = roadmap.get("sprint_tasks", [])
            total_tasks = len(tasks)
            done_tasks = sum(1 for t in tasks if t.get("status") == "done")
        except Exception:
            pass

    # Build banner
    pm_agent = team[0] if team else "default"
    type_icons = {
        "saas-dashboard": "📊", "webapp-fullstack": "🌐", "ecommerce": "🛒",
        "ai-agent": "🤖", "ml-platform": "🧠", "data-platform": "📊",
        "finops": "💰", "cli-tool": "⌨️", "mobile-app": "📱",
        "security-tool": "🔒", "content-platform": "📝",
    }
    icon = type_icons.get(ptype, "📁")

    # Format start time nicely
    try:
        dt = datetime.fromisoformat(start_time)
        start_str = dt.strftime("%m-%d %H:%M")
    except Exception:
        start_str = start_time[:16] if start_time else "?"

    banner_text = (
        f"[bold]{icon} {name}[/]  │  "
        f"[cyan]👤 {pm_agent}[/]  │  "
        f"[dim]📅 {start_str}[/]  │  "
        f"[green]{provider}/{model}[/]"
    )
    if total_tasks > 0:
        pct = int(done_tasks / total_tasks * 100) if total_tasks > 0 else 0
        bar_len = 10
        filled = int(bar_len * done_tasks / total_tasks)
        bar = "█" * filled + "░" * (bar_len - filled)
        banner_text += f"  │  [yellow]📋 {done_tasks}/{total_tasks} {bar} {pct}%[/]"

    console.print()
    console.print(Panel(banner_text, border_style="cyan", padding=(0, 2)))


# ═══════════════════════════════════════════════════════════════════════════════
# Agent Switcher — for ape chat multi-agent conversation
# ═══════════════════════════════════════════════════════════════════════════════

def switch_agent_context(
    console: Console,
    current_agent: str,
    project_path: Path | None = None,
) -> str | None:
    """Interactive agent switcher for ape chat.

    Displays available agents from the project and lets user switch.
    Returns the new agent name, or None if cancelled.
    """
    if project_path is None:
        project_path = Path.cwd()

    config_path = project_path / "apex.yaml"
    if not config_path.exists():
        console.print("[yellow]No apex.yaml found. Run `apex init` first.[/]")
        return None

    with open(config_path) as f:
        config = yaml.safe_load(f) or {}

    team = config.get("team", [])
    if not team:
        console.print("[yellow]No agents in project team.[/]")
        return None

    console.print(f"\n[bold]🔄 切换 Agent 对话[/]")
    console.print(f"  当前: [cyan]{current_agent}[/]")

    table = Table(title="可用 Agent")
    table.add_column("#", style="dim", width=3)
    table.add_column("Agent", style="cyan")
    table.add_column("状态")

    for i, agent_id in enumerate(team, 1):
        marker = " ← 当前" if agent_id == current_agent else ""
        table.add_row(str(i), agent_id, marker)

    console.print(table)
    console.print("[dim]输入编号切换，回车取消[/]")

    choice = input("  > ").strip()
    if not choice:
        return None

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(team):
            new_agent = team[idx]
            console.print(f"\n[green]✓ 已切换到: {new_agent}[/]")
            return new_agent

    # Also accept agent name directly
    if choice in team:
        console.print(f"\n[green]✓ 已切换到: {choice}[/]")
        return choice

    console.print("[red]无效选择[/]")
    return None
