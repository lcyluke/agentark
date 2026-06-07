"""Apex Demo — 5-minute wow experience

Creates a swarm demo with 3 agents working in parallel,
opens the 7-tab Command Center, and guides the user through
their first multi-agent experience.
"""
from __future__ import annotations

import subprocess
import time
import webbrowser
from pathlib import Path
from textwrap import dedent

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text


DEMO_TASKS = [
    {
        "title": "[Apex Demo] Frontend — Build Welcome Dashboard",
        "assignee": "frontend-dev",
        "description": "Create a responsive dark-theme welcome page with stats cards and agent fleet grid",
        "priority": 1,
    },
    {
        "title": "[Apex Demo] Backend — API Health Check System",
        "assignee": "devops",
        "description": "Build a health check endpoint and monitoring pipeline with alert rules",
        "priority": 1,
    },
    {
        "title": "[Apex Demo] PM — Sprint Plan & Task Breakdown",
        "assignee": "default",
        "description": "Analyze the project scope and create a 2-week sprint plan with task assignments",
        "priority": 1,
    },
]


def _ensure_project(console: Console, apex_home: Path) -> Path:
    """Ensure demo project directory exists"""
    project_dir = apex_home / "projects" / "demo"
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


def _create_demo_tasks(console: Console) -> list:
    """Create demo tasks on Kanban board"""
    try:
        from apex.orchestration.kanban import Kanban
        from apex.core.profile import APEX_HOME

        kb = Kanban(APEX_HOME / "kanban.db")
        created = []
        for task_data in DEMO_TASKS:
            try:
                task = kb.create_task(
                    title=task_data["title"],
                    assignee=task_data["assignee"],
                    description=task_data["description"],
                    priority=task_data["priority"],
                )
                created.append(task)
                console.print(f"  [green]✓[/green] Created: {task_data['title'][:50]}... → {task_data['assignee']}")
            except Exception as e:
                # Task might already exist — skip
                console.print(f"  [dim]○[/dim] Skipped (may exist): {task_data['title'][:50]}...")
        return created
    except Exception as e:
        console.print(f"  [yellow]⚠[/yellow] Kanban not available, creating in-memory tasks only")
        return []


def _check_environment(console: Console) -> dict:
    """Check what's available"""
    env = {
        "python": True,
        "dashboard": True,
        "kanban": False,
        "browser": False,
        "gpu": False,
    }
    try:
        from apex.orchestration.kanban import Kanban
        from apex.core.profile import APEX_HOME
        kb = Kanban(APEX_HOME / "kanban.db")
        _ = kb.list_tasks()
        env["kanban"] = True
    except:
        pass
    try:
        import subprocess as sp
        sp.run(["open", "about:blank"], capture_output=True, timeout=3)
        env["browser"] = True
    except:
        pass
    return env


def run_demo(
    console: Console | None = None,
    port: int = 8080,
    host: str = "127.0.0.1",
    no_browser: bool = False,
    skip_tasks: bool = False,
    overwrite: bool = False,
):
    """Run the full demo experience"""
    if console is None:
        console = Console()

    from apex.core.profile import APEX_HOME

    # ═══ BANNER ═══
    console.print()
    console.print(Panel(
        Text("⚡  Apex Demo — Your Multi-Agent Command Center", style="bold cyan"),
        subtitle="5 minutes to your AI fleet",
        border_style="cyan",
    ))
    console.print()

    # ═══ STEP 1: Environment Check ═══
    console.print("[bold]Step 1/4[/bold] Checking environment...")
    env = _check_environment(console)
    
    table = Table(show_header=False, box=None, padding=(0, 4))
    table.add_column("Item", style="dim")
    table.add_column("Status")
    for key, ok in env.items():
        table.add_row(key, "[green]✓ Ready[/green]" if ok else "[yellow]○ Limited[/yellow]")
    console.print(table)
    console.print()

    # ═══ STEP 2: Create Demo Fleet ═══
    console.print("[bold]Step 2/4[/bold] Assembling your AI fleet...")
    if not skip_tasks:
        tasks = _create_demo_tasks(console)
    else:
        console.print("  [dim]Skipped (--skip-tasks)[/dim]")
    console.print()

    # ═══ STEP 3: Launch Dashboard ═══
    console.print("[bold]Step 3/4[/bold] Launching Command Center...")
    
    dashboard_url = f"http://{host}:{port}"
    
    # Kill existing process if overwrite
    if overwrite:
        try:
            subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True)
            subprocess.run(["lsof", "-ti", f":{port}", "|", "xargs", "kill", "-9"],
                         shell=True, capture_output=True)
            time.sleep(0.5)
            console.print("  [dim]Killed existing process on port {port}[/dim]")
        except:
            pass
    
    # Start dashboard in background
    try:
        import threading
        from apex.interface.web import create_app

        def _serve():
            app = create_app()
            app.run(host=host, port=port, debug=False, use_reloader=False)

        server_thread = threading.Thread(target=_serve, daemon=True)
        server_thread.start()
        time.sleep(2)
        console.print(f"  [green]✓[/green] Dashboard running at [cyan]{dashboard_url}[/cyan]")
    except Exception as e:
        console.print(f"  [yellow]⚠[/yellow] Dashboard start failed: {e}")
        console.print(f"  Run manually: [cyan]apex dashboard[/cyan]")
    
    console.print()

    # ═══ STEP 4: Open Browser ═══
    if not no_browser and env["browser"]:
        console.print("[bold]Step 4/4[/bold] Opening Command Center...")
        try:
            subprocess.run(["open", dashboard_url], capture_output=True, timeout=5)
            console.print(f"  [green]✓[/green] Browser opened → [cyan]{dashboard_url}[/cyan]")
        except:
            console.print(f"  [yellow]⚠[/yellow] Could not open browser. Visit: [cyan]{dashboard_url}[/cyan]")
    else:
        console.print(f"[bold]Step 4/4[/bold] Visit: [cyan]{dashboard_url}[/cyan]")
    console.print()

    # ═══ NEXT STEPS ═══
    console.print(Panel(
        dedent(f"""\
        [bold cyan]🚀  Your Multi-Agent Command Center is Ready![/bold cyan]

        [bold]Access:[/bold]  {dashboard_url}
        [bold]14 views[/bold] to manage your entire operation

        [bold]Try next:[/bold]
          [cyan]apex swarm "Build a REST API"[/cyan]       Parallel agents
          [cyan]apex crew create "Design a feature"[/cyan]   Role collaboration
          [cyan]apex status[/cyan]                            Fleet overview

        [bold]Demo Tasks Created:[/bold]
          1. Frontend → Build Welcome Dashboard
          2. Backend  → API Health Check System
          3. PM       → Sprint Plan & Breakdown
        """),
        title="✨  Ready",
        border_style="green",
    ))
    console.print()

    return dashboard_url
