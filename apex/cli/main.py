"""Apex — CLI 主框架"""
from __future__ import annotations

import sys
import os
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .commands.init import init_project
from .commands.run import run_task
from .commands.status import show_status
from .commands import team as team_cmds
from .commands import template as template_cmds
from .commands import economy as economy_cmds
from .commands import evolution as evolution_cmds
from .commands.company import CompanyBuilder, list_companies
from apex.orchestration.crew import crew as crew_group

console = Console()


@click.group()
@click.version_option(version="0.1.0", message="Apex v0.1.0 — One person, infinite capacity.")
def cli():
    """Apex — 全宇宙最受欢迎的多Agent操作系统"""
    pass


@cli.command()
@click.argument("name")
@click.option("--dir", "-d", default=".", help="项目目录")
def init(name: str, dir: str):
    """初始化一个新的Apex项目"""
    init_project(name, Path(dir).resolve(), console)


@cli.command()
@click.argument("task")
@click.option("--profile", "-p", default="default", help="使用的Agent Profile")
@click.option("--model", "-m", help="覆盖模型名称")
@click.option("--swarm", "-s", is_flag=True, help="是否用Swarm模式")
@click.option("--workers", "-w", default=3, help="Swarm并行Worker数")
def run(task: str, profile: str, model: str, swarm: bool, workers: int):
    """执行一个任务"""
    run_task(task, profile, model, swarm, workers, console)


@cli.command()
def status():
    """查看Apex当前状态"""
    show_status(console)


@cli.group()
def team():
    """管理Agent团队"""
    pass


# ─── team子命令 ───
@team.command(name="create")
@click.argument("name")
def team_create(name: str):
    """创建一个新Agent"""
    team_cmds.create_cmd(name)

@team.command(name="list")
def team_list():
    """列出所有Agent"""
    team_cmds.list_cmd()

@team.command(name="show")
@click.argument("name")
def team_show(name: str):
    """显示Agent详情"""
    team_cmds.show_cmd(name)


# ─── template子命令 ───
@cli.group()
def template():
    """管理Agent模板"""
    pass

@template.command(name="list")
def template_list():
    """列出所有可用模板"""
    template_cmds.list_cmd()

@template.command(name="show")
@click.argument("name")
def template_show(name: str):
    """显示模板详情"""
    template_cmds.show_cmd(name)

@template.command(name="use")
@click.argument("name")
@click.option("--alias", "-a", help="自定义Agent名称")
def template_use(name: str, alias: str):
    """用模板创建Agent"""
    template_cmds.use_cmd(name, alias)


# ─── crew子命令 ───
cli.add_command(crew_group)


# ─── economy命令 ───
@cli.group()
def economy():
    """Token Economy — 预算和成本管理"""
    pass

@economy.command(name="status")
def economy_status():
    """查看经济状态"""
    economy_cmds.status_cmd()

@economy.command(name="classify")
@click.argument("task")
def economy_classify(task: str):
    """测试任务分类和路由"""
    economy_cmds.classify_cmd(task)


# ─── dashboard命令 ───
@cli.command()
@click.option("--port", "-p", default=8080, help="端口")
@click.option("--host", default="127.0.0.1", help="绑定地址")
def dashboard(host: str, port: int):
    """启动Web Dashboard"""
    try:
        from apex.interface.web import run_dashboard
        run_dashboard(host=host, port=port)
    except ImportError as e:
        console.print(f"[red]✗ 启动失败: {e}[/]")
        console.print("运行 [bold]pip install flask[/bold] 安装依赖")


# ─── company命令 ───
@cli.group()
def company():
    """One-Click Company — 创建AI公司"""
    pass

@company.command(name="create")
@click.argument("name")
@click.option("--industry", "-i", default="saas",
              type=click.Choice(["saas", "ai_product", "content", "ecommerce", "freelance"]),
              help="行业类型")
def company_create(name: str, industry: str):
    """创建一家AI公司（一行命令 = 一个团队）"""
    builder = CompanyBuilder()
    builder.create(name, industry)

@company.command(name="start")
@click.argument("name")
@click.argument("goal")
def company_start(name: str, goal: str):
    """启动公司执行任务"""
    builder = CompanyBuilder()
    builder.start(name, goal)

@company.command(name="list")
def company_list():
    """列出所有公司"""
    list_companies()


# ─── knowledge命令 ───
@cli.group()
def knowledge():
    """知识图谱 — 跨Agent共享记忆"""
    pass

@knowledge.command(name="query")
@click.argument("question")
def knowledge_query(question: str):
    """查询知识图谱"""
    from apex.core.knowledge import KnowledgeGraph
    kg = KnowledgeGraph()
    result = kg.query(question)
    console.print(Panel(result.answer, title=f"🔍 知识图谱: {question[:40]}", border_style="cyan"))
    console.print(f"[dim]置信度: {result.confidence:.1%} | 证据: {len(result.evidence)}条 | 推理路径: {len(result.reasoning_path)}条[/]")

@knowledge.command(name="stats")
def knowledge_stats():
    """知识图谱统计"""
    from apex.core.knowledge import KnowledgeGraph
    kg = KnowledgeGraph()
    stats = kg.stats()
    table = Table(title="📊 知识图谱统计", box=None)
    table.add_column("指标", style="cyan")
    table.add_column("数值", style="green")
    for k, v in stats.items():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                table.add_row(f"  {k2}", str(v2))
        else:
            table.add_row(k, str(v))
    console.print(table)


# ─── evolution命令 ───
@cli.group()
def evolution():
    """技能进化引擎 — Agent越用越聪明"""
    pass

@evolution.command(name="status")
def evolution_status():
    """进化引擎状态"""
    evolution_cmds.status_cmd()

@evolution.command(name="agent")
@click.argument("name")
def evolution_agent(name: str):
    """Agent进化报告"""
    evolution_cmds.agent_cmd(name)
