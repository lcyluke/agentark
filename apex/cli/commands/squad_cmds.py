"""Apex — Developer Squad Commander.

One-command launch for the full development team:
  apex squad start    — Start all 5 dev agents in new windows
  apex squad status  — Show all dev agent statuses
  apex squad attach  — Attach to a specific agent
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from apex.interface.agent_monitor import get_monitor

console = Console()

DEV_SQUAD = {
    "frontend-dev": {
        "emoji": "💻",
        "title": "Frontend Developer",
        "skill": "React/TypeScript/UI",
        "color": "green",
    },
    "backend-dev": {
        "emoji": "⚙️",
        "title": "Backend Developer",
        "skill": "Python/FastAPI/DB",
        "color": "blue",
    },
    "fullstack-dev": {
        "emoji": "👨‍💻",
        "title": "Fullstack Developer",
        "skill": "FE+BE+Deploy",
        "color": "cyan",
    },
    "architect": {
        "emoji": "🏛️",
        "title": "System Architect",
        "skill": "Architecture/Design",
        "color": "yellow",
    },
    "devops": {
        "emoji": "🔧",
        "title": "DevOps Engineer",
        "skill": "CI-CD/Infra/Cloud",
        "color": "magenta",
    },
    "vulnerability-scanner": {
        "emoji": "🛡️",
        "title": "Vulnerability Scanner",
        "skill": "SAST/SCA/SecretScan",
        "color": "red",
    },
    "penetration-tester": {
        "emoji": "🕵️",
        "title": "Penetration Tester",
        "skill": "Web/API/Logic Pentest",
        "color": "red",
    },
    "security-by-design": {
        "emoji": "🔐",
        "title": "Security by Design",
        "skill": "Threat Model/Secure Arch",
        "color": "bright_red",
    },
    "project-manager": {
        "emoji": "📊",
        "title": "Project Manager",
        "skill": "Planning/Risk/Tracking",
        "color": "bright_blue",
    },
    "qa-engineer": {
        "emoji": "🧪",
        "title": "QA Engineer",
        "skill": "Test Strategy/Automation",
        "color": "green",
    },
    "requirements-analyst": {
        "emoji": "🎯",
        "title": "Requirements Analyst",
        "skill": "Multi-Perspective/GStack",
        "color": "bright_yellow",
    },
}

METHODOLOGY_CHAIN_EMOJI = ["🧠", "📝", "🔄", "🔬", "🔍", "👀", "✅"]
METHODOLOGY_CHAIN_NAMES = ["brainstorm", "plan", "TDD", "verify", "debug", "review", "finish"]


def status_cmd():
    """Show dev squad status and readiness."""
    monitor = get_monitor()
    snapshot = monitor.snapshot(force_refresh=True)

    console.print()
    console.print(Panel(
        "[bold cyan]👥 DEV SQUAD[/]  [bold white]— 11 Agents[/]  [dim]Superpowers Methodology[/]",
        border_style="cyan",
    ))
    console.print()

    # Methodology chain — single line
    chain_parts = []
    for e, n in zip(METHODOLOGY_CHAIN_EMOJI, METHODOLOGY_CHAIN_NAMES):
        chain_parts.append(f"{e}[dim]{n}[/]")
    chain_str = " \u2192  ".join(chain_parts)
    console.print(f"  {chain_str}")
    console.print()

    # ── Agent Table ──
    table = Table(
        border_style="blue",
        header_style="bold cyan",
        show_header=True,
        box=box.SQUARE,
        title="",
    )
    table.add_column("", width=4)
    table.add_column("Agent", min_width=22, max_width=22, no_wrap=True)
    table.add_column("Role", min_width=18, max_width=18, no_wrap=True)
    table.add_column("State", width=10, justify="center")
    table.add_column("PID", width=6, justify="right")
    table.add_column("Skills", width=6, justify="center")
    table.add_column("Lvl", width=4, justify="center")
    table.add_column("Done", width=4, justify="right")
    table.add_column("Command", min_width=15, max_width=18, no_wrap=True)

    for agent_name, info in DEV_SQUAD.items():
        agent = snapshot.agents.get(agent_name)

        # Check if running
        pid = ""
        running = False
        try:
            result = subprocess.run(
                ["pgrep", "-f", f"hermes -p {agent_name}"],
                capture_output=True, text=True, timeout=3,
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split("\n")
                pid = pids[0][:6]
                running = True
        except Exception:
            pass

        state_str = f"[green]● 在线[/]" if running else f"[dim]○ 待启动[/]"
        pid_str = f"[dim]{pid}[/]" if pid else "[dim]—[/]"
        skill_str = f"{agent.skill_count}" if agent and agent.skill_count else "[dim]0[/]"
        lvl_str = agent.highest_skill_level if agent else "[dim]—[/]"
        done_str = str(agent.work_stats.total_completed) if agent and agent.work_stats.total_completed else "0"
        cmd_short = {
            "frontend-dev": "fe-dev",
            "backend-dev": "be-dev",
            "fullstack-dev": "fs-dev",
            "architect": "arch",
            "devops": "devops",
            "vulnerability-scanner": "vuln-scan",
            "penetration-tester": "pentest",
            "security-by-design": "sec-design",
            "project-manager": "pm",
            "qa-engineer": "qa",
            "requirements-analyst": "req-analyst",
        }.get(agent_name, agent_name[:12])
        cmd_str = f"[dim]{cmd_short} chat[/]" if not running else f"[green]{cmd_short} chat[/]"

        table.add_row(
            info["emoji"],
            f"[{info['color']}]{agent_name}[/]",
            f"[white]{info['title']}[/]",
            state_str,
            pid_str,
            skill_str,
            lvl_str,
            done_str,
            cmd_str,
        )

    console.print(table)

    # Methodology readiness per agent
    console.print("[bold]📋 Methodology Chain Readiness[/]")
    console.print()

    for agent_name, info in DEV_SQUAD.items():
        agent = snapshot.agents.get(agent_name)
        soul_exists = Path.home() / ".hermes" / "profiles" / agent_name / "SOUL.md"
        has_bootstrap = False
        if soul_exists.exists():
            content = soul_exists.read_text()
            has_bootstrap = "SUPERPOWERS-BOOTSTRAP" in content

        # Readiness check
        checks = []
        checks.append("✅ Profile" if soul_exists.exists() else "❌ Profile")
        checks.append("✅ Bootstrap" if has_bootstrap else "❌ Bootstrap")
        checks.append("✅ Skills" if agent and agent.skill_count >= 14 else f"⚠️ Skills({agent.skill_count if agent else 0})")

        if agent and agent.work_stats.total_completed > 0:
            checks.append("✅ Experienced")
        else:
            checks.append("⚪ Fresh")

        console.print(f"  {info['emoji']} [bold]{agent_name}[/] — {' | '.join(checks)}")

    console.print()
    console.print("[dim]💡 Start squad: apex squad start | Attach agent: <agent-name> chat[/]")


def start_cmd():
    """Launch all 5 dev agents in terminal windows."""
    console.print("[bold]🚀 Launching Dev Squad...[/]")

    results = []
    for agent_name in DEV_SQUAD:
        wrapper = Path.home() / ".local" / "bin" / agent_name
        if not wrapper.exists():
            console.print(f"  [red]✗ {agent_name}: wrapper not found. Run 'apex team sync {agent_name}' first[/]")
            continue

        # Open a new Terminal window
        try:
            script = f'tell application "Terminal" to do script "{wrapper} chat"'
            subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, timeout=5,
            )
            results.append((agent_name, "launched"))
            console.print(f"  ✅ {agent_name} — new Terminal window opened")
            time.sleep(0.5)
        except Exception as e:
            results.append((agent_name, f"error: {e}"))
            console.print(f"  [red]✗ {agent_name}: {e}[/]")

    # Summary
    launched = sum(1 for r in results if r[1] == "launched")
    console.print()
    console.print(Panel(
        f"[bold green]✅ Squad launch: {launched}/{len(DEV_SQUAD)} agents[/]\n"
        f"Each agent opens in its own Terminal window with Superpowers methodology loaded.",
        title="🚢 Dev Squad Deployed",
        border_style="green",
    ))

    console.print(f"\n[dim]Methodology chain active in all agents: "
                  f"{' → '.join(f'{e}{n}' for e, n in zip(METHODOLOGY_CHAIN_EMOJI, METHODOLOGY_CHAIN_NAMES))}[/]")


def attach_cmd(agent_name: str):
    """Show connection info for a specific squad member."""
    if agent_name not in DEV_SQUAD:
        console.print(f"[red]Unknown agent '{agent_name}'. Available: {', '.join(DEV_SQUAD.keys())}[/]")
        return

    info = DEV_SQUAD[agent_name]
    wrapper_path = Path.home() / ".local" / "bin" / agent_name

    # Check running
    pid = ""
    running = False
    try:
        result = subprocess.run(
            ["pgrep", "-f", f"hermes -p {agent_name}"],
            capture_output=True, text=True, timeout=3,
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            pid = pids[0]
            running = True
    except Exception:
        pass

    console.print(Panel(
        f"[bold]{info['emoji']} {agent_name} — {info['title']}[/]\n"
        f"Status: {'🟢 Online' if running else '⚪ Offline'}\n"
        f"{'PID: ' + pid if pid else ''}\n"
        f"Launch: [cyan]{agent_name} chat[/]\n"
        f"Profile: [dim]{wrapper_path}[/]",
        title="🤖 Agent Details",
        border_style=info["color"],
    ))

    # Show SOUL.md status
    soul_path = Path.home() / ".hermes" / "profiles" / agent_name / "SOUL.md"
    if soul_path.exists():
        content = soul_path.read_text()
        has_bootstrap = "SUPERPOWERS-BOOTSTRAP" in content
        has_iron_laws = "Iron Laws" in content
        has_methodology = "Development Methodology" in content
        has_red_flags = "Red Flags" in content
        has_review = "Code Review Protocol" in content

        console.print("[bold]Methodology Status:[/]")
        checks = [
            ("🧠 Bootstrap", has_bootstrap),
            ("📋 Methodology Chain", has_methodology),
            ("🚩 Red Flags", has_red_flags),
            ("🔨 Iron Laws", has_iron_laws),
            ("👀 Review Protocol", has_review),
        ]
        for label, ok in checks:
            console.print(f"  {'✅' if ok else '❌'} {label}")

    # Show skills summary
    try:
        from apex.interface.skill_registry import get_registry
        r = get_registry()
        skills = r.get_agent_skills(agent_name)
        by_level = {}
        for s in skills:
            lvl = s.get("level", "L0")
            by_level.setdefault(lvl, []).append(s["skill_name"])

        console.print(f"\n[bold]Skills ({len(skills)} total):[/]")
        for lvl in ["L4", "L3", "L2", "L1", "L0"]:
            if lvl in by_level:
                names = ", ".join(by_level[lvl][:5])
                if len(by_level[lvl]) > 5:
                    names += f" +{len(by_level[lvl])-5}"
                console.print(f"  [{_level_color(lvl)}]{lvl}[/] {names}")
    except Exception:
        pass

    console.print(f"\n[dim]💡 New Terminal: {agent_name} chat[/]")


def _level_color(lvl: str) -> str:
    return {"L5": "yellow", "L4": "green", "L3": "cyan", "L2": "white", "L1": "dim", "L0": "red"}.get(lvl, "white")
