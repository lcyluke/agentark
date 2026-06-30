"""Apex Setup Wizard — interactive first-run guided setup.

5-step flow:
  1/5 Welcome        — greet, detect environment
  2/5 Model          — auto-detect + pick model
  3/5 Tools          — scan installed tools (Hermes/Claude/Codex/OpenClaw)
  4/5 Fleet          — create profiles + init tmux fleet
  5/5 Done           — summary + next steps

Usage:
  apex setup                    # Full interactive wizard
  apex setup --quick            # All defaults, skip prompts
  apex setup --check            # Diagnostic mode
  apex setup --model X --provider Y  # Quick model config only
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm
from rich import box

from agentark.core.config import get_config, save_config, config_exists, config_path
from agentark.interface.model_selector import ModelSelector
from agentark.interface.tool_discovery import ToolDiscovery

console = Console()

STEPS = ["Welcome", "Model", "Tools", "Fleet", "Done"]
STEP_ICONS = ["👋", "🤖", "🔧", "🚀", "✅"]


def run_setup(
    quick: bool = False,
    check: bool = False,
    model: str = "",
    provider: str = "",
    interactive: bool = True,
):
    """Main entry point for the setup wizard."""

    if check:
        _run_diagnostics()
        return

    if model:
        # Quick model-only config
        ms = ModelSelector()
        ms.set_default(model)
        if provider:
            cfg = get_config()
            cfg.model.provider = provider
            cfg.save()
        return

    console.print()
    console.print(Panel(
        "[bold cyan]⚡ Welcome to Apex Setup[/]\n\n"
        "[dim]Multi-Agent Operating System — one person, infinite capacity.[/]",
        border_style="cyan",
    ))

    if quick:
        _quick_setup()
        return

    # ── Step 1/5: Welcome & Environment Detection ──
    _step_header(1)
    _detect_environment()

    if not interactive:
        return

    if not Prompt.ask("\n[bold]按 Enter 继续[/]", default="", show_default=False):
        pass

    # ── Step 2/5: Model Selection ──
    _step_header(2)
    ms = ModelSelector()
    chosen = ms.interactive_pick()
    if chosen:
        ms.set_default(chosen)
    else:
        console.print("[dim]跳过模型配置，使用默认值。[/]")

    if not interactive:
        return

    # ── Step 3/5: Tool Discovery ──
    _step_header(3)
    _run_tool_discovery()

    # ── Step 4/5: Fleet Init ──
    _step_header(4)
    _init_fleet(interactive=interactive)

    # ── Step 5/5: Done ──
    _step_header(5)
    _show_done()


def _step_header(step_num: int):
    """Print a step header with progress indicator."""
    icon = STEP_ICONS[step_num - 1]
    name = STEPS[step_num - 1]
    bar = "█" * step_num + "░" * (5 - step_num)
    console.print(f"\n[bold cyan]{icon} Step {step_num}/5: {name}[/]  [{bar}]")


def _detect_environment():
    """Detect and display system environment."""
    console.print()
    console.print("[bold]🔍 系统环境检测[/]")

    checks = [
        ("macOS", sys.platform == "darwin"),
        ("Python 3.10+", sys.version_info >= (3, 10)),
        ("tmux", _has_tool("tmux")),
        ("Hermes Agent", _has_tool("hermes")),
        ("GitHub CLI (gh)", _has_tool("gh")),
        ("Git", _has_tool("git")),
        ("Docker", _has_tool("docker")),
    ]

    table = Table(box=box.SIMPLE)
    table.add_column("组件", style="bold")
    table.add_column("状态", justify="center")

    all_ok = True
    for name, ok in checks:
        icon = "✅" if ok else "❌"
        table.add_row(name, icon)
        if not ok and name in ("Python 3.10+", "tmux"):
            all_ok = False

    console.print(table)

    if not all_ok:
        console.print("\n[yellow]⚠ 缺少必要组件，请先安装: brew install tmux[/]")
    else:
        console.print("\n[green]✅ 环境就绪[/]")


def _run_tool_discovery():
    """Scan and display installed tools."""
    td = ToolDiscovery()
    inventory = td.scan(force=True)
    summary = td.summary()

    console.print()
    console.print(f"[green]✅ 发现 {summary['found']}/{summary['total']} 个工具[/]")

    for cat, tools in summary["by_category"].items():
        console.print(f"  [{cat}] {', '.join(tools)}")

    if summary["missing"]:
        console.print(f"\n[dim]未安装: {summary['missing']} 个[/]")


def _init_fleet(interactive: bool = True):
    """Initialize the tmux fleet with default agents."""
    console.print()
    console.print("[bold]🚀 初始化 Agent 舰队[/]")

    if interactive and not Confirm.ask("创建 7 个 Agent Profile 并启动 tmux 舰队?", default=True):
        console.print("[dim]跳过。可稍后运行: apex fleet init[/]")
        return

    try:
        from agentark.fleet import ProfileBundler, TmuxFleetManager

        # Init profiles
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task1 = progress.add_task("[cyan]创建 Agent Profiles...", total=7)
            bundler = ProfileBundler()
            results = bundler.init_all()
            progress.update(task1, completed=7, description="[green]✅ Agent Profiles 创建完成")

        # Start fleet
        console.print()
        fm = TmuxFleetManager()
        initialized = bundler.list_initialized()
        if initialized:
            state = fm.init_fleet(initialized)
            console.print(
                f"[green]✅ 舰队启动: {state.total_windows} 个 Agent 窗口[/]"
            )
            console.print(f"[dim]连接: tmux attach -t {state.session_name}[/]")
    except Exception as e:
        console.print(f"[yellow]⚠ 舰队初始化跳过: {e}[/]")
        console.print("[dim]可稍后运行: apex fleet init[/]")


def _show_done():
    """Show completion summary and next steps."""
    console.print()
    console.print(Panel(
        "[bold green]🎉 Apex 安装完成![/]\n\n"
        "[bold]快速开始:[/]\n"
        "  [cyan]apex fleet start[/]        启动 7 个 Agent\n"
        "  [cyan]apex monitor status[/]     Agent 状态面板\n"
        "  [cyan]apex monitor tools[/]      查看已安装工具\n"
        "  [cyan]apex pm dashboard[/]       PM 仪表盘\n"
        "  [cyan]apex version[/]            检查更新\n\n"
        "[dim]配置: ~/.apex/config.yaml[/]\n"
        "[dim]帮助: apex --help[/]",
        border_style="green",
    ))


def _quick_setup():
    """Quick setup with all defaults."""
    console.print("[bold]⚡ 快速安装 (使用默认配置)[/]\n")

    # Step 1
    _step_header(1)
    _detect_environment()

    # Step 2
    _step_header(2)
    ms = ModelSelector()
    result = ms.detect()
    if result.recommended:
        ms.set_default(result.recommended)
    else:
        ms.set_default("deepseek-v4-pro")

    # Step 3
    _step_header(3)
    _run_tool_discovery()

    # Step 4
    _step_header(4)
    _init_fleet(interactive=False)

    # Step 5
    _step_header(5)
    _show_done()


def _run_diagnostics():
    """Run diagnostics check."""
    console.print()
    console.print(Panel("[bold]🔍 Apex 诊断[/]", border_style="cyan"))

    checks = []

    # System checks
    checks.append(("Python >= 3.10", sys.version_info >= (3, 10)))
    checks.append(("macOS/Linux", sys.platform in ("darwin", "linux")))
    checks.append(("tmux", _has_tool("tmux")))

    # Config checks
    has_config = config_exists()
    checks.append(("配置文件", has_config))
    if has_config:
        try:
            cfg = get_config()
            checks.append(("  模型配置", bool(cfg.model.default)))
        except Exception:
            checks.append(("  配置文件有效", False))

    # Tool checks
    checks.append(("Hermes Agent", _has_tool("hermes")))
    checks.append(("Git", _has_tool("git")))
    checks.append(("GitHub CLI", _has_tool("gh")))

    # Fleet checks
    try:
        from agentark.fleet import TmuxFleetManager
        fm = TmuxFleetManager()
        fleet_running = fm.exists
        checks.append(("Fleet 运行中", fleet_running))
    except Exception:
        checks.append(("Fleet 运行中", False))

    for name, ok in checks:
        icon = "✅" if ok else "❌"
        color = "green" if ok else "red"
        console.print(f"  {icon} [{color}]{name}[/]")

    # Recommendations
    console.print()
    issues = [name for name, ok in checks if not ok]
    if issues:
        console.print("[yellow]⚠ 发现问题:[/]")
        for issue in issues:
            if "tmux" in issue:
                console.print("  → brew install tmux")
            elif "配置文件" in issue:
                console.print("  → 运行 apex setup 创建配置")
            elif "Hermes" in issue:
                console.print("  → 安装 Hermes Agent")
    else:
        console.print("[green]✅ 一切正常[/]")


def _has_tool(name: str) -> bool:
    """Check if a CLI tool is installed."""
    import shutil
    return shutil.which(name) is not None
