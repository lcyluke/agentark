"""Apex — init command (interactive project setup with agent matching)"""
from __future__ import annotations

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from agentark.core.profile import ProfileManager

# Project type → recommended agent roles + descriptions
PROJECT_PRESETS = {
    "webapp": {
        "label": "🌐 Web 应用",
        "agents": [
            ("product-manager", "需求分析 & 路线图"),
            ("architect", "系统架构设计"),
            ("backend-dev", "后端 API & 数据库"),
            ("frontend-dev", "前端 UI & 交互"),
            ("devops", "部署 & CI/CD"),
            ("qa-engineer", "测试 & 质量保证"),
        ],
    },
    "cli": {
        "label": "⌨️  CLI 工具",
        "agents": [
            ("backend-dev", "核心逻辑开发"),
            ("devops", "发布 & 包管理"),
            ("qa-engineer", "测试 & 边缘用例"),
        ],
    },
    "library": {
        "label": "📦 库 / SDK",
        "agents": [
            ("backend-dev", "API 设计 & 实现"),
            ("qa-engineer", "单元测试 & 文档测试"),
            ("devops", "CI / 发布流水线"),
        ],
    },
    "data": {
        "label": "📊 数据 / ML 项目",
        "agents": [
            ("data-engineer", "数据管道 & ETL"),
            ("data-analyst", "分析 & 可视化"),
            ("ml-engineer", "模型训练 & 部署"),
            ("devops", "基础设施 & GPU 管理"),
        ],
    },
    "finops": {
        "label": "💰 FinOps / 成本优化",
        "agents": [
            ("finops-architect", "成本架构设计"),
            ("finops-backend", "后端成本分析"),
            ("finops-devops", "基础设施成本优化"),
            ("finops-frontend", "Dashboard & 可视化"),
        ],
    },
    "agent": {
        "label": "🤖 多 Agent 系统",
        "agents": [
            ("apex-pm", "项目管理 & 调度"),
            ("architect", "Agent 架构设计"),
            ("backend-dev", "Agent 工具开发"),
            ("devops", "部署 & 监控"),
            ("fleet-commander", "Agent 舰队管理"),
        ],
    },
    "other": {
        "label": "🎯 通用项目",
        "agents": [
            ("product-manager", "需求定义"),
            ("architect", "技术方案"),
            ("backend-dev", "核心开发"),
            ("qa-engineer", "质量把关"),
        ],
    },
}


def _pick_preset(console: Console, description: str = "") -> str:
    """Match project type from description or let user choose."""
    desc_lower = description.lower()

    # Auto-detect from keywords
    keywords = {
        "webapp": ["web", "网站", "前端", "后端", "fullstack", "app", "saas", "dashboard", "看板"],
        "cli": ["cli", "命令行", "terminal", "终端", "tool", "脚本"],
        "library": ["sdk", "库", "lib", "package", "包", "api", "framework", "框架"],
        "data": ["data", "数据", "ml", "机器学习", "训练", "模型", "pipeline", "etl", "analytics"],
        "finops": ["finops", "成本", "cost", "cloud", "云", "billing", "计费"],
        "agent": ["agent", "multi-agent", "多agent", "swarm", "fleet", "舰队", "ai agent"],
    }

    for ptype, kws in keywords.items():
        if any(kw in desc_lower for kw in kws):
            return ptype

    # Manual selection
    console.print("\n[bold]选择项目类型:[/]")
    for i, (ptype, preset) in enumerate(PROJECT_PRESETS.items(), 1):
        console.print(f"  [{i}] {preset['label']}")

    choice = Prompt.ask("输入编号", default="7")
    idx = int(choice) - 1 if choice.isdigit() else 6
    keys = list(PROJECT_PRESETS.keys())
    return keys[min(idx, len(keys) - 1)]


def init_project(name: str, project_dir: Path, console: Console):
    """Interactive Apex project initialization."""

    # ═══ Step 1: Welcome ═══
    console.print()
    console.print(Panel(
        "[bold cyan]🚀 Apex Project Init[/]\n"
        "[dim]交互式项目设置 — 分析目标 → 推荐团队 → 一键创建[/]",
        border_style="cyan",
    ))

    # ═══ Step 2: Project Info ═══
    console.print(f"\n[bold]📋 Step 1/4: 项目信息[/]")

    if name == "my-project":
        name = Prompt.ask("  项目名称", default="my-apex-project")

    project_path = project_dir / name
    if project_path.exists():
        console.print(f"  [yellow]⚠ 目录已存在: {project_path}[/]")
        if not Confirm.ask("  覆盖?", default=False):
            console.print("[red]✗ 已取消[/]")
            return

    desc = Prompt.ask("  项目描述 (可选)", default="")

    # ═══ Step 3: Goal Analysis + Agent Matching ═══
    console.print(f"\n[bold]🔍 Step 2/4: 目标分析 & Agent 推荐[/]")

    ptype = _pick_preset(console, desc)
    preset = PROJECT_PRESETS[ptype]
    console.print(f"\n  [green]✓ 识别为: {preset['label']}[/]")

    # Show recommended team
    console.print(f"\n  [bold]推荐 Agent 团队:[/]")
    selected_agents = []
    for agent_id, role_desc in preset["agents"]:
        include = Confirm.ask(f"     {agent_id} ({role_desc})?", default=True)
        if include:
            selected_agents.append((agent_id, role_desc))

    if not selected_agents:
        selected_agents = [("default", "通用助手")]

    # ═══ Step 4: Provider & Model ═══
    console.print(f"\n[bold]⚙️  Step 3/4: 模型配置[/]")
    providers = {"1": "deepseek", "2": "openai", "3": "anthropic"}
    console.print("   [1] DeepSeek (推荐)   [2] OpenAI   [3] Anthropic")
    prov_choice = Prompt.ask("  选择 Provider", default="1")
    provider = providers.get(prov_choice, "deepseek")

    default_models = {
        "deepseek": "deepseek-v4-pro",
        "openai": "gpt-4o",
        "anthropic": "claude-sonnet-4-20250514",
    }
    model = Prompt.ask("  模型", default=default_models.get(provider, "deepseek-v4-pro"))

    # ═══ Step 5: Create ═══
    console.print(f"\n[bold]🏗️  Step 4/4: 创建项目[/]")

    project_path.mkdir(parents=True, exist_ok=True)

    # apex.yaml
    import yaml
    config = {
        "project": name,
        "description": desc or f"{preset['label']} 项目",
        "type": ptype,
        "apex_version": "0.5.1",
        "default_provider": provider,
        "default_model": model,
        "team": [agent_id for agent_id, _ in selected_agents],
    }
    with open(project_path / "apex.yaml", "w") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    # teams/ directory
    (project_path / "teams").mkdir(exist_ok=True)

    # Create profiles for selected agents
    pm = ProfileManager()
    for agent_id, role_desc in selected_agents:
        pm.create_default(agent_id, role=role_desc, expertise=[ptype])

    # README stub
    readme = f"# {name}\n\n{desc or preset['label'] + ' 项目'}\n\n"
    readme += "## Team\n\n"
    for agent_id, role_desc in selected_agents:
        readme += f"- **{agent_id}**: {role_desc}\n"
    readme += "\n## Quickstart\n\n"
    readme += f"```bash\ncd {name}\n"
    readme += f"apex run \"your first task\" -p {selected_agents[0][0]}\n"
    readme += "apex pm dashboard\n```\n"
    with open(project_path / "README.md", "w") as f:
        f.write(readme)

    # ═══ Success Summary ═══
    console.print()
    console.print(Panel(
        "[bold green]✅ 项目创建成功![/]\n",
        border_style="green",
    ))

    # Summary table
    table = Table(title="📋 项目摘要", show_header=False, title_style="bold")
    table.add_column(style="dim"); table.add_column(style="bold")
    table.add_row("项目名称", name)
    table.add_row("项目类型", preset["label"])
    table.add_row("目录", str(project_path))
    table.add_row("Provider", provider)
    table.add_row("模型", model)
    console.print(table)

    # Agent team
    agent_table = Table(title="👥 Agent 团队", title_style="bold")
    agent_table.add_column("Agent", style="cyan")
    agent_table.add_column("角色", style="dim")
    for agent_id, role_desc in selected_agents:
        agent_table.add_row(agent_id, role_desc)
    console.print(agent_table)

    # Next steps
    console.print(Panel(
        "[bold]下一步:[/]\n\n"
        f"  [cyan]cd {name}[/]\n"
        f"  [cyan]apex run \"你的第一个任务\" -p {selected_agents[0][0]}[/]\n"
        f"  [cyan]apex pm dashboard[/]         查看项目管理面板\n"
        f"  [cyan]apex fleet status[/]         查看 Agent 状态\n"
        f"  [cyan]apex tutorial[/]             5 分钟交互教程\n",
        title="🚀 开始使用",
        border_style="green",
    ))
    console.print()
