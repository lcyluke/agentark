"""Apex — init 命令"""
from __future__ import annotations

import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from apex.core.profile import APEX_HOME, ProfileManager


def init_project(name: str, project_dir: Path, console: Console):
    """初始化Apex项目"""

    project_path = project_dir / name
    if project_path.exists():
        console.print(f"[yellow]⚠ 目录已存在: {project_path}")
        confirm = Prompt.ask("是否覆盖？", choices=["y", "n"], default="n")
        if confirm != "y":
            console.print("[red]✗ 取消初始化")
            return

    project_path.mkdir(parents=True, exist_ok=True)

    # 创建项目配置
    config = {
        "project": name,
        "apex_version": "0.1.0",
        "default_provider": "deepseek",
        "default_model": "deepseek-chat",
    }
    import yaml
    with open(project_path / "apex.yaml", "w") as f:
        yaml.dump(config, f)

    # 创建默认teams目录
    (project_path / "teams").mkdir(exist_ok=True)

    # 初始化ProfileManager，创建默认Profile
    pm = ProfileManager()
    pm.create_default("default", role="通用助手", expertise=["general"])

    console.print()
    console.print(Panel.fit(
        f"[bold green]✅ Apex项目初始化完成![/]\n\n"
        f"  项目: [bold]{project_path}[/]\n"
        f"  Default Profile: [bold]default[/]\n"
        f"  Provider: [bold]deepseek[/]\n"
        f"  Model: [bold]deepseek-chat[/]\n\n"
        f"  下一步:\n"
        f"  [bold]cd {name}[/]\n"
        f"  [bold]apex run \"你的任务\"[/]\n"
        f"  [bold]apex team create \"做一个AI网站\"[/]",
        title="🎯 Apex Ready",
    ))
