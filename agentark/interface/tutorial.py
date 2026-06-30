"""Apex Interactive Tutorial — guided walkthrough for new users.

5-step interactive tutorial:
  1. Welcome    — what Apex is
  2. Fleet      — start agents in tmux
  3. Monitor    — check agent status
  4. PM         — schedule + assign tasks
  5. Done       — next steps

Usage:
  apex tutorial
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()

STEPS = [
    {
        "title": "Welcome",
        "emoji": "👋",
        "content": [
            "Apex 是一个多 Agent 操作系统",
            "让一个人拥有一个公司的能力",
            "",
            "核心概念:",
            "  • Agent = 有独立角色的 AI 助手",
            "  • Fleet = 在 tmux 中运行的 Agent 舰队",
            "  • PM = 项目管理 + 智能调度",
        ],
    },
    {
        "title": "Fleet",
        "emoji": "🚀",
        "content": [
            "启动你的 Agent 舰队:",
            "",
            "  apex fleet init      创建 7 个 Agent + 启动",
            "  apex fleet start     启动所有 Agent",
            "  apex fleet status    查看舰队状态",
            "  apex fleet log pm    查看 PM 输出",
            "",
            "Agent 角色:",
            "  pm         项目经理",
            "  architect  系统架构师",
            "  backend-dev 后端开发",
            "  frontend-dev 前端开发",
            "  devops     运维工程师",
            "  qa-engineer 测试工程师",
            "  github-release 发布工程师",
        ],
    },
    {
        "title": "Monitor",
        "emoji": "📊",
        "content": [
            "监控 Agent 状态和任务:",
            "",
            "  apex monitor status    Agent 状态面板",
            "  apex monitor skills    Skills 总览",
            "  apex monitor tools     系统工具发现",
            "  apex doctor           系统诊断",
            "",
            "快捷别名:",
            "  apex s   = monitor status",
            "  apex fs  = fleet status",
        ],
    },
    {
        "title": "PM",
        "emoji": "📊",
        "content": [
            "项目管理 + 智能调度:",
            "",
            "  apex pm dashboard  完整仪表盘",
            "  apex pm schedule   排期 + 分配",
            "  apex pm assign     自动分配任务",
            "  apex pm health     健康检查",
            "  apex pm timeline   甘特图时间线",
            "",
            "快捷别名:",
            "  apex p  = pm dashboard",
            "  apex ps = pm schedule",
        ],
    },
    {
        "title": "Done",
        "emoji": "✅",
        "content": [
            "你已经掌握了 Apex 的核心功能!",
            "",
            "常用命令速查:",
            "  apex fleet start   启动舰队",
            "  apex s             状态面板 (monitor status)",
            "  apex p             项目管理 (pm dashboard)",
            "  apex up            检查更新",
            "  apex doctor        系统诊断",
            "",
            "配置:",
            "  apex config show       查看配置",
            "  apex config model set  切换模型",
            "  apex theme set ocean   切换主题",
            "",
            "帮助: apex --help",
        ],
    },
]


def run_tutorial():
    """Run the interactive tutorial."""
    console.print()
    console.print(Panel(
        "[bold cyan]🎓 Apex 交互式教程[/]\n"
        "[dim]5 步，约 3 分钟[/]",
        border_style="cyan",
    ))

    for i, step in enumerate(STEPS, 1):
        console.print(f"\n[bold cyan]{step['emoji']} Step {i}/5: {step['title']}[/] [dim]{'█'*i + '░'*(5-i)}[/]")
        console.print()

        for line in step["content"]:
            if line.startswith("  "):
                console.print(f"  [dim]{line}[/]")
            elif line and not line.startswith("•"):
                console.print(f"[bold]{line}[/]")
            else:
                console.print(line)

        if i < len(STEPS):
            if not Confirm.ask(f"\n继续 Step {i+1}?", default=True):
                console.print("[dim]教程已暂停。随时运行 apex tutorial 继续。[/]")
                return

    console.print()
    console.print(Panel(
        "[bold green]🎉 教程完成![/]\n\n"
        "现在试试:\n"
        "  [cyan]apex fleet start[/]    启动舰队\n"
        "  [cyan]apex s[/]              查看状态\n"
        "  [cyan]apex p[/]              项目管理",
        border_style="green",
    ))
