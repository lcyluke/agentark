"""Apex version check and self-update.

Usage:
  apex version             Show current + check latest GitHub release
  apex update              Self-update to latest GitHub release
"""

from __future__ import annotations

import json
import subprocess
import sys
from importlib.metadata import version as pkg_version
from pathlib import Path

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
GITHUB_API = "https://api.github.com/repos/lcyluke/agentark/releases/latest"
GITHUB_TAGS = "https://api.github.com/repos/lcyluke/agentark/tags"


def get_current_version() -> str:
    """Get the installed Apex version."""
    try:
        return pkg_version("apex-multiagent")
    except Exception:
        return "unknown"


def get_latest_version() -> dict:
    """Fetch latest release info from GitHub."""
    try:
        resp = httpx.get(GITHUB_API, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "version": data.get("tag_name", "?").lstrip("v"),
                "published_at": data.get("published_at", "")[:10],
                "name": data.get("name", ""),
                "url": data.get("html_url", ""),
            }
    except Exception:
        pass
    return {"version": "unknown", "published_at": "", "name": "", "url": ""}


def get_recent_versions(count: int = 5) -> list[dict]:
    """Fetch recent version tags."""
    try:
        resp = httpx.get(f"{GITHUB_TAGS}?per_page={count}", timeout=10)
        if resp.status_code == 200:
            tags = resp.json()
            return [
                {"version": t.get("name", "?").lstrip("v"),
                 "commit": (t.get("commit", {}).get("sha", ""))[:7]}
                for t in tags
            ]
    except Exception:
        pass
    return []


def cmd_version():
    """Show current version + check for updates."""
    current = get_current_version()
    latest = get_latest_version()

    console.print()
    console.print(Panel(
        f"[bold]⚡ Apex[/] [cyan]v{current}[/]",
        border_style="cyan",
    ))

    table = Table(box=None, show_header=False)
    table.add_column(style="bold")
    table.add_column()

    table.add_row("Installed", f"v{current}")
    if latest["version"] != "unknown":
        is_newer = latest["version"] != current
        color = "yellow" if is_newer else "green"
        table.add_row(
            "Latest",
            f"[{color}]v{latest['version']}[/] "
            f"[dim]({latest['published_at']})[/]"
        )
        if is_newer:
            table.add_row(
                "",
                f"[yellow]🚀 Update available! Run: apex update[/]"
            )
        else:
            table.add_row("", "[green]✅ Up to date[/]")
    else:
        table.add_row("Latest", "[dim]Could not reach GitHub[/]")

    console.print(table)

    # Recent versions
    recent = get_recent_versions(5)
    if recent:
        console.print()
        console.print("[bold]Recent releases:[/]")
        for r in recent:
            marker = " ← current" if r["version"] == current else ""
            console.print(f"  v{r['version']} [dim]({r['commit']}){marker}[/]")

    console.print()


def cmd_update():
    """Self-update Apex from GitHub."""
    current = get_current_version()
    latest = get_latest_version()

    if latest["version"] == "unknown":
        console.print("[red]Cannot reach GitHub. Check your network.[/]")
        return

    if latest["version"] == current:
        console.print(f"[green]Already up to date (v{current}).[/]")
        return

    console.print(f"[yellow]Updating from v{current} → v{latest['version']}...[/]")

    # Find the venv's pip
    pip_path = Path(sys.executable).parent / "pip"
    if not pip_path.exists():
        pip_path = Path(sys.prefix) / "bin" / "pip"

    try:
        result = subprocess.run(
            [str(pip_path), "install", "--force-reinstall", "--no-deps",
             f"git+https://github.com/lcyluke/agentark.git@v{latest['version']}"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            console.print(f"[green]✅ Updated to v{latest['version']}![/]")
            console.print(f"[dim]Release: {latest['url']}[/]")
        else:
            console.print(f"[red]Update failed:[/]")
            console.print(result.stderr[:300])
    except Exception as e:
        console.print(f"[red]Update error: {e}[/]")
        console.print("[dim]Try manual update: pip install --upgrade git+https://github.com/lcyluke/apex.git[/]")
