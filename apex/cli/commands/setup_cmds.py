"""Apex — Setup & Installation Command

First-time setup wizard that:
  - Checks Hermes installation
  - Creates default agent profiles
  - Configures model provider and token budgets
  - Sets up shell wrapper scripts for Hermes terminals
  - Configures prompt display (agent name, multi-line input)

Usage:
  apex setup                        — Full interactive setup
  apex setup --quick                — Quick setup (defaults)
  apex setup --check                — Check installation status
  apex setup --model <model>        — Set default model
  apex setup --token-limit <n>      — Set token limit per session
  apex setup --token-budget <n>     — Set total token budget
  apex setup --input-lines <n>      — Set Hermes TUI input lines (3)
"""

from __future__ import annotations

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm, Prompt
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()

HERMES_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))
HERMES_BIN = shutil.which("hermes") or shutil.which("hermes", path=os.path.expanduser("~/.local/bin"))
APEX_HOME = Path(os.environ.get("APEX_HOME", os.path.expanduser("~/.apex")))

DEFAULT_TOKEN_LIMIT = 8000
DEFAULT_TOKEN_BUDGET = 100000
DEFAULT_INPUT_LINES = 3


def check_cmd():
    """🔍 Check installation status."""
    checks = []

    # Hermes check
    if HERMES_BIN:
        try:
            r = subprocess.run([HERMES_BIN, "--version"], capture_output=True, text=True, timeout=10)
            hermes_ver = r.stdout.strip() or r.stderr.strip() or "installed"
            checks.append(("✅", "Hermes Agent", hermes_ver))
        except:
            checks.append(("❌", "Hermes Agent", "not responding"))
    else:
        checks.append(("❌", "Hermes Agent", "not found in PATH"))

    # Hermes profiles
    profiles_dir = HERMES_HOME / "profiles"
    if profiles_dir.exists():
        profiles = [d.name for d in profiles_dir.iterdir() if d.is_dir()]
        checks.append(("✅", f"Hermes Profiles", f"{len(profiles)} found"))
    else:
        checks.append(("⚠️", "Hermes Profiles", "not created yet"))

    # Apex installation
    checks.append(("✅", "Apex CLI", "installed"))

    # DeepSeek config
    auth_file = HERMES_HOME / "auth.json"
    if auth_file.exists():
        checks.append(("✅", "API Auth", "configured"))
    else:
        checks.append(("⚠️", "API Auth", "not configured"))

    # Display
    table = Table(title="🔍 Apex System Check", box=box.ROUNDED)
    table.add_column("Status", width=4)
    table.add_column("Component", width=20)
    table.add_column("Detail", width=40)
    for status, name, detail in checks:
        table.add_row(status, name, detail)
    console.print(table)

    # Summary
    ok = sum(1 for s, _, _ in checks if s == "✅")
    warn = sum(1 for s, _, _ in checks if s == "⚠️")
    fail = sum(1 for s, _, _ in checks if s == "❌")
    console.print(f"\n[dim]{ok} OK  {warn} warnings  {fail} issues[/]")

    if fail > 0 or warn > 0:
        console.print("\n[yellow]Run [bold]apex setup[/bold] to fix issues.[/]")

    return {"ok": ok, "warn": warn, "fail": fail}


def setup_cmd(
    quick: bool = False,
    model: Optional[str] = None,
    token_limit: Optional[int] = None,
    token_budget: Optional[int] = None,
    input_lines: Optional[int] = None,
):
    """🚀 First-time setup: install, configure, and launch."""
    console.print(Panel.fit(
        "[bold cyan]🚀 Apex Setup — First-Time Installation[/]\n"
        "[dim]One command to configure your AI fleet[/]",
        border_style="cyan",
    ))

    if not quick:
        console.print("\n[bold]This wizard will:[/]")
        for step in [
            "✅ Check Hermes Agent installation",
            "✅ Create default agent profiles",
            "✅ Configure model provider & token budgets",
            "✅ Set up Hermes terminal wrappers with agent name display",
            "✅ Enable multi-line input (3 lines default)",
        ]:
            console.print(f"  {step}")
        if not Confirm.ask("\nContinue?", default=True):
            console.print("[dim]Setup cancelled.[/]")
            return

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        console=console,
        transient=True,
    )

    results = {}

    with progress:
        # Step 1: Check Hermes
        t1 = progress.add_task("[cyan]1/5 检查 Hermes Agent...", total=100)
        hermes_result = _check_hermes()
        results["hermes"] = hermes_result["status"]
        progress.update(t1, completed=100,
                        description=f"[{'green' if hermes_result['ok'] else 'yellow'}]1/5 {hermes_result['msg']}[/]")

        # Step 2: Create profiles
        t2 = progress.add_task("[cyan]2/5 创建 Agent 配置文件...", total=100)
        profile_result = _create_profiles(quick)
        results["profiles"] = profile_result["count"]
        progress.update(t2, completed=100,
                        description=f"[green]2/5 ✓ {profile_result['count']} 个 Agent 配置文件[/]")

        # Step 3: Configure model
        t3 = progress.add_task("[cyan]3/5 配置模型和 Token 预算...", total=100)
        model_cfg = model or (None if quick else Prompt.ask(
            "Default model", default="deepseek-v4-pro"))
        token_lim = token_limit or (DEFAULT_TOKEN_LIMIT if quick else
                                     int(Prompt.ask("Token limit per session", default=str(DEFAULT_TOKEN_LIMIT))))
        token_bgt = token_budget or (DEFAULT_TOKEN_BUDGET if quick else
                                      int(Prompt.ask("Total token budget", default=str(DEFAULT_TOKEN_BUDGET))))
        input_lns = input_lines or (DEFAULT_INPUT_LINES if quick else
                                     int(Prompt.ask("Input lines in Hermes TUI", default=str(DEFAULT_INPUT_LINES))))
        config_result = _configure_model(model_cfg or "deepseek-v4-pro", token_lim, token_bgt)
        results["config"] = config_result["status"]
        _set_input_lines(input_lns)
        results["input_lines"] = input_lns
        progress.update(t3, completed=100,
                        description=f"[green]3/5 ✓ Model: {model_cfg or 'deepseek-v4-pro'} | Token: {token_lim}/{token_bgt}[/]")

        # Step 4: Setup wrappers
        t4 = progress.add_task("[cyan]4/5 安装 Hermes 终端包装脚本...", total=100)
        wrapper_result = _setup_wrappers(input_lns)
        results["wrappers"] = wrapper_result["count"]
        progress.update(t4, completed=100,
                        description=f"[green]4/5 ✓ {wrapper_result['count']} 个包装脚本已安装[/]")

        # Step 5: Verify
        t5 = progress.add_task("[cyan]5/5 验证配置...", total=100)
        verify_result = _verify_setup()
        results["verify"] = verify_result["ok"]
        progress.update(t5, completed=100,
                        description=f"[{'green' if verify_result['ok'] else 'yellow'}]5/5 {verify_result['msg']}[/]")

    console.print()

    # Summary
    console.print(Panel.fit(
        "[bold green]✅ Setup Complete![/]\n\n"
        f"Hermes Agent:     {results.get('hermes', '?')}\n"
        f"Agent Profiles:   {results.get('profiles', 0)}\n"
        f"Token Limit:      {token_limit or DEFAULT_TOKEN_LIMIT}/session\n"
        f"Token Budget:     {token_budget or DEFAULT_TOKEN_BUDGET} total\n"
        f"Input Lines:      {results.get('input_lines', DEFAULT_INPUT_LINES)}\n"
        f"Shell Wrappers:   {results.get('wrappers', 0)}\n\n"
        "[bold]🚀 快速上手:[/]\n"
        f"  [cyan]apex team template webapp[/]     — 创建开发团队\n"
        f"  [cyan]apex team start[/]               — 启动 Agent 终端\n"
        f"  [cyan]apex chat frontend-dev[/]        — 对话前端 Agent\n"
        f"  [cyan]apex task dispatch <需求>[/]      — 拆解需求执行\n\n"
        "[dim]每打开一个新 Hermes 终端，Agent 名称会显示在标题行，\n"
        f"输入框默认为 {results.get('input_lines', DEFAULT_INPUT_LINES)} 行高度。[/]",
        title="🚀 Apex Fleet Ready",
        border_style="green",
    ))


def _check_hermes() -> dict:
    """Check Hermes Agent installation."""
    if HERMES_BIN:
        try:
            r = subprocess.run([HERMES_BIN, "--version"], capture_output=True, text=True, timeout=10)
            ver = (r.stdout.strip() or r.stderr.strip() or "").split("\n")[0][:40]
            return {"ok": True, "status": "installed", "msg": f"🔍 Hermes Agent: {ver}"}
        except:
            return {"ok": False, "status": "error", "msg": "❌ Hermes Agent not responding"}
    return {"ok": False, "status": "missing", "msg": "❌ Hermes Agent not found"}


def _create_profiles(quick: bool = False) -> dict:
    """Create default agent profiles if not exist."""
    import subprocess
    templates = ["webapp", "content", "data"]
    count = 0
    for t in templates:
        try:
            r = subprocess.run(
                [sys.executable, "-m", "apex", "team", "template", t],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode == 0:
                count += 4  # Each template creates 4 agents
        except:
            pass
    return {"count": count, "ok": count > 0}


def _configure_model(model_name: str, token_limit: int, token_budget: int) -> dict:
    """Write per-profile model config with token budgets."""
    profiles_dir = HERMES_HOME / "profiles"
    if not profiles_dir.exists():
        return {"status": "no_profiles"}

    count = 0
    for pdir in profiles_dir.iterdir():
        if not pdir.is_dir():
            continue
        config_file = pdir / "config.yaml"
        if not config_file.exists():
            continue

        # Read existing config
        try:
            import yaml
            with open(config_file) as f:
                cfg = yaml.safe_load(f) or {}
        except:
            cfg = {}

        # Ensure model section
        if "model" not in cfg:
            cfg["model"] = {}
        cfg["model"]["default"] = model_name

        # Add token budget section
        if "agent" not in cfg:
            cfg["agent"] = {}
        cfg["agent"]["max_tokens_per_turn"] = token_limit
        cfg["agent"]["max_tokens_session"] = token_budget

        # Add display config with agent name prefix
        if "display" not in cfg:
            cfg["display"] = {}
        cfg["display"]["agent_name_prefix"] = True
        cfg["display"]["show_apex_badge"] = True

        # Write back
        with open(config_file, "w") as f:
            yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
        count += 1

    return {"status": f"configured {count} profiles", "count": count}


def _set_input_lines(lines: int = 3):
    """Set multi-line input height in Hermes config."""
    config_file = HERMES_HOME / "config.yaml"
    if not config_file.exists():
        return

    try:
        import yaml
        with open(config_file) as f:
            cfg = yaml.safe_load(f) or {}
    except:
        cfg = {}

    # Add TUI config for input lines
    if "display" not in cfg:
        cfg["display"] = {}
    cfg["display"]["composer_lines"] = lines
    cfg["display"]["multi_line_composer"] = True

    with open(config_file, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)


def _setup_wrappers(input_lines: int = 3) -> dict:
    """Create shell wrapper scripts that show agent name + multi-line input."""
    bindir = Path(os.path.expanduser("~/.local/bin"))
    bindir.mkdir(parents=True, exist_ok=True)

    profiles_dir = HERMES_HOME / "profiles"
    if not profiles_dir.exists():
        return {"count": 0}

    count = 0
    for pdir in profiles_dir.iterdir():
        if not pdir.is_dir():
            continue
        name = pdir.name
        wrapper_path = bindir / name

        # Create wrapper that:
        # 1. Sets terminal title to agent name
        # 2. Sets HERMES input lines config
        # 3. Exports DEEPSEEK_API_KEY
        # 4. Launches Hermes with profile
        wrapper_content = f"""#!/bin/bash
# Apex Agent Wrapper: {name}
# Auto-generated by 'apex setup'
# Provides: agent name in title, multi-line input ({input_lines} lines)

# Terminal title
echo -ne "\\033]0;{name} ⚓ Apex\\007"

# Export config for Hermes
export HERMES_COMPOSER_LINES={input_lines}
export HERMES_PROFILE="{name}"

# Agent prompt prefix in status bar
export APEX_AGENT_NAME="{name}"

# Launch Hermes with profile
exec hermes -p "{name}" "$@"
"""
        with open(wrapper_path, "w") as f:
            f.write(wrapper_content)
        wrapper_path.chmod(0o755)
        count += 1

    # Also create an "apex-chat" command that combines them
    apex_chat_path = bindir / "apex-chat"
    apex_chat_content = f"""#!/bin/bash
# Apex Chat Launcher — multi-line input + agent name display
# Usage: apex-chat <profile-name> [query]

if [ -z "$1" ]; then
    echo "Usage: apex-chat <profile-name> [query]"
    echo "Available profiles:"
    ls -1 {HERMES_HOME}/profiles/ 2>/dev/null || echo "(no profiles)"
    exit 1
fi

AGENT="$1"
shift

echo -ne "\\033]0;${{AGENT}} ⚓ Apex\\007"
export HERMES_COMPOSER_LINES={input_lines}
export APEX_AGENT_NAME="$AGENT"

exec hermes -p "$AGENT" "$@"
"""
    with open(apex_chat_path, "w") as f:
        f.write(apex_chat_content)
    apex_chat_path.chmod(0o755)
    count += 1

    return {"count": count}


def _verify_setup() -> dict:
    """Verify the setup worked."""
    profiles_dir = HERMES_HOME / "profiles"
    bindir = Path(os.path.expanduser("~/.local/bin"))

    profile_count = len([d for d in profiles_dir.iterdir() if d.is_dir()]) if profiles_dir.exists() else 0
    wrapper_count = len([f for f in bindir.iterdir()
                         if f.is_file() and not f.name.startswith(".")]) if bindir.exists() else 0

    return {
        "ok": profile_count > 0,
        "msg": f"✓ {profile_count} profiles, {wrapper_count} wrappers ready",
    }
