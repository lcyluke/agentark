"""AgentArk — Session CLI commands.

Bridge AgentArk fleet identities into live Hermes terminal sessions.

Commands:
  agentark session list          — List available fleet agents
  agentark session attach <N>    — Create Hermes profile from SOUL.md
  agentark session attach-all    — Attach all available agents
  agentark session detach <N>    — Remove Hermes profile
  agentark session activate <N>  — Set active agent persona
  agentark session deactivate    — Return to default profile
  agentark session show <N>      — Preview generated persona
  agentark session status        — Current session state

Design (方案三 — Hermes Profile Orchestration):
  AgentArk maintains full SOUL.md → persona pipeline.
  Hermes side is zero-change — uses native profile system.
  State file (~/.agentark/active_session) bridges shell sessions.
"""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

# Lazy import to keep CLI startup fast
_UNSET = object()
_manager = _UNSET


def _get_manager():
    global _manager
    if _manager is _UNSET:
        from agentark.interface.session_bridge import SessionManager
        _manager = SessionManager()
    return _manager


console = Console()


# ── CLI Group ───────────────────────────────────────────────────────────


@click.group(name="session")
def session():
    """🪪 Session bridge — activate AgentArk personas in your terminal.

    Three-step workflow:
      1. attach <agent>     — create Hermes profile from fleet SOUL.md
      2. activate <agent>   — set as your active persona
      3. deactivate         — return to default

    Hermes picks up the active identity automatically.
    """
    pass


# ── attach ──────────────────────────────────────────────────────────────


@session.command(name="attach")
@click.argument("agent", required=True)
def session_attach(agent: str):
    """🔗 Attach an agent — create Hermes profile from SOUL.md.

    Reads fleet/profiles/<agent>/SOUL.md and creates a Hermes profile
    at ~/.hermes/profiles/agentark-<agent>/ with the agent's persona.

    AGENT: Name of the fleet agent (e.g. devops, backend-dev, pm)
    """
    mgr = _get_manager()
    result = mgr.attach(agent)
    if result.startswith("Unknown"):
        console.print(f"[red]✗ {result}[/]")
    else:
        console.print(f"[green]✅ {result}[/]")


@session.command(name="attach-all")
def session_attach_all():
    """🔗 Attach all available fleet agents at once."""
    mgr = _get_manager()
    available = mgr.list_available()
    if not available:
        console.print("[yellow]No fleet agents found.[/]")
        return

    results = []
    for name in available:
        result = mgr.attach(name)
        status = "✅" if not result.startswith("Unknown") else "❌"
        results.append((status, name, result[:80]))
        console.print(f"  {status} {name}")

    console.print(f"\n[green]Attached {sum(1 for s,_,_ in results if s=='✅')}/{len(results)} agents.[/]")


# ── detach ──────────────────────────────────────────────────────────────


@session.command(name="detach")
@click.argument("agent", required=True)
def session_detach(agent: str):
    """🗑️  Detach an agent — remove its Hermes profile.

    Deletes ~/.hermes/profiles/agentark-<agent>/.
    Deactivates the agent first if it's currently active.

    AGENT: Name of the fleet agent to detach
    """
    mgr = _get_manager()
    result = mgr.detach(agent)
    console.print(f"[green]✅ {result}[/]" if "removed" in result.lower() else f"[yellow]ℹ️  {result}[/]")


# ── activate / deactivate ───────────────────────────────────────────────


@session.command(name="activate")
@click.argument("agent", required=True)
def session_activate(agent: str):
    """🎭 Activate an agent — set as your terminal persona.

    Writes the active identity to ~/.agentark/active_session.
    Hermes picks this up if your shell rc sources it.

    AGENT: Name of an already-attached fleet agent
    """
    mgr = _get_manager()
    result = mgr.activate(agent)
    if result.startswith("Agent") and "not attached" in result:
        console.print(f"[red]✗ {result}[/]")
        return
    console.print(f"[green]🎭 {result}[/]")


@session.command(name="deactivate")
def session_deactivate():
    """🔄 Deactivate — return to default Hermes profile.

    Clears ~/.agentark/active_session.
    """
    mgr = _get_manager()
    result = mgr.deactivate()
    console.print(f"[dim]{result}[/]")


# ── list / show / status ───────────────────────────────────────────────


@session.command(name="list")
def session_list():
    """📋 List all fleet agents and their attachment status."""
    mgr = _get_manager()
    available = mgr.list_available()
    attached = set(mgr.list_attached())

    if not available:
        console.print("[yellow]No fleet agents with SOUL.md found.[/]")
        return

    table = Table(title="🪪 AgentArk Fleet — Session Agents", box=box.ROUNDED)
    table.add_column("Status", width=8)
    table.add_column("Agent", style="cyan")
    table.add_column("Profile Name", style="dim")

    for name in available:
        if name in attached:
            table.add_row("✅", name, f"agentark-{name}")
        else:
            table.add_row("⬜", name, "—")

    console.print(table)
    console.print("\n[dim]attach: agentark session attach <name>   activate: agentark session activate <name>[/]")


@session.command(name="show")
@click.argument("agent", required=True)
def session_show(agent: str):
    """🔍 Preview the persona content for an agent.

    Shows what will be written to agent_persona.md when you attach.

    AGENT: Fleet agent name
    """
    mgr = _get_manager()
    content = mgr.show(agent)
    if content is None:
        available = ", ".join(mgr.list_available()[:10])
        console.print(f"[red]Unknown agent '{agent}'. Available: {available}[/]")
        return

    # Show first 30 lines with a panel
    lines = content.split("\n")
    preview = "\n".join(lines[:30])
    if len(lines) > 30:
        preview += f"\n\n[dim]... ({len(lines)} lines total)[/]"

    console.print(Panel.fit(
        preview,
        title=f"🎭 {agent} — Persona Preview",
        border_style="cyan",
    ))


@session.command(name="status")
def session_status():
    """📊 Show current session state."""
    mgr = _get_manager()
    s = mgr.status()

    # Active identity
    active_display = f"[green]🎭 {s.active}[/]" if s.active else "[dim]None (using default)[/]"
    console.print(f"[bold]Active:[/] {active_display}")

    # State file location
    from agentark.interface.session_bridge import STATE_FILE
    if STATE_FILE.exists():
        console.print(f"[dim]State:  {STATE_FILE} → {STATE_FILE.read_text().strip()}[/]")
    else:
        console.print(f"[dim]State:  {STATE_FILE} (not set)[/]")

    # Counts
    console.print(f"[bold]Attached:[/] {len(s.attached)}  [bold]Available:[/] {len(s.available)}")

    # Shell integration hint
    if s.active:
        console.print(f"\n[dim]Shell: export HERMES_PROFILE=agentark-{s.active}[/]")
    console.print("[dim]Persist: add 'export HERMES_PROFILE=$(cat ~/.agentark/active_session 2>/dev/null)' to shell rc[/]")
