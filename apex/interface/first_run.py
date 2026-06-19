"""Apex First-Run — detects fresh install and guides user through setup.

Called automatically on first `apex` invocation if no config exists.
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from apex.core.config import config_exists

console = Console()


def check_first_run() -> bool:
    """Check if this is a first run (no config file).

    Returns True if first run detected and setup was triggered.
    """
    if config_exists():
        return False

    console.print()
    console.print(Panel(
        "[bold cyan]⚡ Welcome to Apex![/]\n\n"
        "这看起来是你第一次运行 Apex。\n"
        "安装向导会帮你配置模型、检测工具、启动 Agent 舰队。\n\n"
        "[dim](约需 2 分钟)[/]",
        border_style="cyan",
    ))

    if Confirm.ask("\n开始安装?", default=True):
        from apex.interface.setup_wizard import run_setup
        run_setup(interactive=True)
        return True

    console.print("\n[dim]跳过。可稍后运行: apex setup[/]")
    console.print(f"[dim]配置文件: ~/.apex/config.yaml[/]")
    return False


def show_post_setup_tips():
    """Show helpful tips after setup completes."""
    console.print()
    console.print(Panel(
        "[bold]💡 下一步建议[/]\n\n"
        "  1. [cyan]apex fleet start[/]    启动舰队\n"
        "  2. [cyan]apex monitor status[/] 查看 Agent 状态\n"
        "  3. [cyan]apex pm dashboard[/]   项目管理仪表盘",
        border_style="green",
        title="🚀 开始使用",
    ))


def show_contextual_help(command: str = ""):
    """Show contextual help based on what the user is doing."""
    tips = {
        "fleet": "💡 提示: 用 tmux attach -t apex-fleet 进入舰队\n"
                "    Ctrl+B 0-6 切换 Agent 窗口",
        "monitor": "💡 提示: apex monitor status --watch 60 自动刷新\n"
                   "    apex monitor tools 查看已安装工具",
        "pm": "💡 提示: apex pm assign 自动分配任务\n"
              "    apex pm profile <agent> 查看 Agent 画像",
    }
    if command in tips:
        console.print(f"\n[dim]{tips[command]}[/]")
