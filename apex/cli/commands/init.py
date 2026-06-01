"""Apex — init command"""
from __future__ import annotations

import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from apex.core.profile import APEX_HOME, ProfileManager


def init_project(name: str, project_dir: Path, console: Console):
    """Initialize an Apex project"""

    project_path = project_dir / name
    if project_path.exists():
        console.print(f"[yellow]⚠ Directory already exists: {project_path}")
        confirm = Prompt.ask("Overwrite?", choices=["y", "n"], default="n")
        if confirm != "y":
            console.print("[red]✗ Initialization cancelled")
            return

    project_path.mkdir(parents=True, exist_ok=True)

    # Create project config
    config = {
        "project": name,
        "apex_version": "0.1.0",
        "default_provider": "deepseek",
        "default_model": "deepseek-chat",
    }
    import yaml
    with open(project_path / "apex.yaml", "w") as f:
        yaml.dump(config, f)

    # Create default teams directory
    (project_path / "teams").mkdir(exist_ok=True)

    # Initialize ProfileManager, create default Profile
    pm = ProfileManager()
    pm.create_default("default", role="General Assistant", expertise=["general"])

    console.print()
    console.print(Panel.fit(
        f"[bold green]✅ Apex project initialized![/]\n\n"
        f"  Project: [bold]{project_path}[/]\n"
        f"  Default Profile: [bold]default[/]\n"
        f"  Provider: [bold]deepseek[/]\n"
        f"  Model: [bold]deepseek-chat[/]\n\n"
        f"  Next steps:\n"
        f"  [bold]cd {name}[/]\n"
        f"  [bold]apex run \"your task\"[/]\n"
        f"  [bold]apex team create \"Build an AI website\"[/]",
        title="🎯 Apex Ready",
    ))
