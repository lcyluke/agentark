"""AgentArk — Project Team Builder with naming convention.

Creates project agent teams using the naming pattern:
  <project_abbreviation>-<agent_role>

Examples:
  Project "finops" → finops-architect, finops-backend, finops-frontend
  Project "badminton" → badminton-pm, badminton-ml-engineer, badminton-devops

Commands:
  agentark team create-project <name>       Interactive team builder
  agentark team create-project <name> --roles arch,backend,frontend
  agentark team add-role <project> <role>    Add agent to existing project
  agentark team list-roles                   Show available agent roles
  agentark team project-roles <project>      Show agents in a project
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.columns import Columns
from rich import box

from agentark.core.profile import ProfileManager

console = Console()

# ══════════════════════════════════════════════════════════════════
# AGENT ROLE POOL — all available roles for project teams
# ══════════════════════════════════════════════════════════════════

AGENT_ROLES = {
    "pm": {
        "name": "Project Manager",
        "badge": "📊", "group": "PM",
        "desc": "需求管理、Sprint规划、进度追踪、KPI",
        "default_skills": ["PRD撰写", "Sprint规划", "Kanban管理", "利益相关者沟通"],
    },
    "architect": {
        "name": "System Architect",
        "badge": "🏛️", "group": "ARCH",
        "desc": "系统架构设计、技术选型、API设计、安全审计",
        "default_skills": ["微服务架构", "API设计", "数据库建模", "安全方案"],
    },
    "backend": {
        "name": "Backend Developer",
        "badge": "⚙️", "group": "DEV",
        "desc": "API开发、数据库、业务逻辑、性能优化",
        "default_skills": ["FastAPI", "SQL", "缓存策略", "消息队列"],
    },
    "frontend": {
        "name": "Frontend Developer",
        "badge": "💻", "group": "DEV",
        "desc": "UI开发、交互设计、响应式、性能优化",
        "default_skills": ["React", "TypeScript", "Tailwind CSS", "Next.js"],
    },
    "fullstack": {
        "name": "Fullstack Developer",
        "badge": "👨‍💻", "group": "DEV",
        "desc": "前后端全栈开发、快速原型、API+UI",
        "default_skills": ["React", "FastAPI", "PostgreSQL", "Docker"],
    },
    "devops": {
        "name": "DevOps Engineer",
        "badge": "🔧", "group": "OPS",
        "desc": "CI/CD、容器化、基础设施即代码、监控告警",
        "default_skills": ["Docker", "K8s", "GitHub Actions", "Prometheus"],
    },
    "qa": {
        "name": "QA Engineer",
        "badge": "🧪", "group": "QA",
        "desc": "自动化测试、性能测试、安全扫描、质量门禁",
        "default_skills": ["E2E测试", "性能测试", "安全扫描", "回归测试"],
    },
    "ml-engineer": {
        "name": "ML Engineer",
        "badge": "🧠", "group": "ML",
        "desc": "模型训练、推理优化、数据Pipeline、MLOps",
        "default_skills": ["PyTorch", "模型部署", "特征工程", "MLflow"],
    },
    "data-engineer": {
        "name": "Data Engineer",
        "badge": "📊", "group": "DATA",
        "desc": "ETL、数据管道、数据湖、数据仓库",
        "default_skills": ["Spark", "Airflow", "dbt", "ClickHouse"],
    },
    "security": {
        "name": "Security Engineer",
        "badge": "🛡️", "group": "SEC",
        "desc": "安全审计、漏洞扫描、渗透测试、合规",
        "default_skills": ["威胁建模", "OWASP", "渗透测试", "合规审计"],
    },
    "designer": {
        "name": "UX/UI Designer",
        "badge": "🎨", "group": "DESIGN",
        "desc": "用户研究、交互设计、视觉设计、设计系统",
        "default_skills": ["Figma", "用户研究", "设计系统", "原型"],
    },
    "writer": {
        "name": "Technical Writer",
        "badge": "📝", "group": "DOCS",
        "desc": "技术文档、API文档、用户手册、知识库",
        "default_skills": ["Markdown", "API文档", "教程写作", "翻译"],
    },
}

# Quick-start presets for common project types
ROLE_PRESETS = {
    "webapp": ["pm", "architect", "backend", "frontend", "devops", "qa"],
    "saas": ["pm", "architect", "backend", "frontend", "fullstack", "devops", "qa"],
    "cli": ["pm", "backend", "devops", "qa"],
    "ai-agent": ["pm", "architect", "backend", "ml-engineer", "devops", "qa"],
    "ml-platform": ["ml-engineer", "data-engineer", "backend", "devops", "qa"],
    "finops": ["pm", "architect", "backend", "frontend", "devops", "qa"],
    "mobile": ["pm", "architect", "frontend", "backend", "devops", "qa"],
    "security": ["security", "backend", "devops", "qa"],
    "content": ["pm", "frontend", "backend", "writer", "designer", "devops"],
    "minimal": ["pm", "backend", "frontend"],
    "solo": ["fullstack"],
}


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

def _agent_name(project: str, role_key: str) -> str:
    """Generate agent name: <project>-<role>"""
    # Normalize: lowercase, replace spaces/underscores with hyphens
    proj = project.lower().strip().replace(" ", "-").replace("_", "-")
    return f"{proj}-{role_key}"


def _role_exists(role_key: str) -> bool:
    """Check if a role key is valid."""
    return role_key in AGENT_ROLES


def _list_project_agents(project: str) -> list[str]:
    """List all agent profiles matching <project>-* naming pattern."""
    pm = ProfileManager()
    all_profiles = pm.list()

    prefix = f"{project.lower().strip().replace(' ', '-').replace('_', '-')}-"
    return [p for p in all_profiles if p.startswith(prefix)]


# ══════════════════════════════════════════════════════════════════
# COMMANDS
# ══════════════════════════════════════════════════════════════════

def list_roles_cmd():
    """Display all available agent roles."""
    console.print()
    console.print(Panel(
        "[bold cyan]🎭 Available Agent Roles[/]\n"
        f"[dim]{len(AGENT_ROLES)} roles available for project team building[/]",
        border_style="cyan",
    ))
    console.print()

    # Group by category
    groups = {}
    for key, info in AGENT_ROLES.items():
        grp = info["group"]
        groups.setdefault(grp, []).append((key, info))

    for grp_name in ["PM", "ARCH", "DEV", "OPS", "QA", "ML", "DATA", "SEC", "DESIGN", "DOCS"]:
        if grp_name in groups:
            console.print(f"  [bold yellow]{grp_name}[/]")
            for key, info in groups[grp_name]:
                console.print(
                    f"    {info['badge']} [cyan]{key:<14s}[/] "
                    f"[dim]{info['name']:<24s}[/] {info['desc']}"
                )
            console.print()

    # Presets
    console.print(f"  [bold yellow]QUICK PRESETS[/]")
    for preset_name, roles in ROLE_PRESETS.items():
        role_badges = " ".join(
            AGENT_ROLES[r]["badge"] for r in roles if r in AGENT_ROLES
        )
        console.print(
            f"    [dim]{preset_name:<12s}[/] "
            f"{role_badges}  [dim]({len(roles)} agents)[/]"
        )
    console.print()


def create_project_cmd(project_name: str, roles_str: str = "",
                       preset: str = "", quick: bool = False,
                       model: str = "deepseek-v4-pro", provider: str = "deepseek"):
    """Create a project team with <project>-<role> naming.

    Args:
        project_name: Project name (used as prefix for agent names)
        roles_str: Comma-separated role keys (e.g. 'arch,backend,frontend')
        preset: Quick preset name from ROLE_PRESETS
        quick: Skip confirmation prompts
        model: Default model for agents
        provider: Default provider
    """
    # ── Determine roles ──
    selected_roles: list[str] = []

    if preset and preset in ROLE_PRESETS:
        selected_roles = list(ROLE_PRESETS[preset])
    elif roles_str:
        selected_roles = [r.strip() for r in roles_str.split(",") if r.strip()]
    elif quick:
        # Default: webapp preset
        selected_roles = list(ROLE_PRESETS["webapp"])
    else:
        # Interactive mode
        selected_roles = _interactive_role_selection(project_name)

    # Validate roles
    invalid = [r for r in selected_roles if not _role_exists(r)]
    if invalid:
        console.print(f"[red]✗ Unknown roles: {', '.join(invalid)}[/]")
        console.print(f"[dim]Run 'agentark team list-roles' to see available roles[/]")
        return

    if not selected_roles:
        console.print("[yellow]⚠ No roles selected. Use --roles or --preset to specify.[/]")
        return

    # ── Summary ──
    console.print()
    table = Table(title=f"👥 Project Team: [bold]{project_name}[/]", box=box.ROUNDED)
    table.add_column("#", style="dim", width=3)
    table.add_column("Agent Name", style="cyan")
    table.add_column("Role", style="green")
    table.add_column("Skills", style="dim")

    agents_to_create = []
    for i, role_key in enumerate(selected_roles, 1):
        info = AGENT_ROLES[role_key]
        name = _agent_name(project_name, role_key)
        agents_to_create.append((name, role_key, info))
        table.add_row(
            str(i),
            name,
            f"{info['badge']} {info['name']}",
            ", ".join(info["default_skills"][:3]),
        )

    console.print(table)
    console.print()

    if not quick:
        if not Confirm.ask(f"Create {len(agents_to_create)} agents?", default=True):
            console.print("[dim]Cancelled.[/]")
            return

    # ── Create agents ──
    pm = ProfileManager()
    created = 0
    skipped = 0

    for agent_name, role_key, info in agents_to_create:
        if agent_name in pm.list():
            console.print(f"  [yellow]⚠ {agent_name} already exists, skipping[/]")
            skipped += 1
            continue

        try:
            pm.create_default(
                agent_name,
                role=f"{info['name']} — {project_name} 项目",
                expertise=info["default_skills"],
            )
            console.print(f"  [green]✅ {info['badge']} {agent_name}[/] — {info['name']}")
            created += 1
        except Exception as e:
            console.print(f"  [red]✗ {agent_name}: {e}[/]")
            skipped += 1

    # ── Summary ──
    console.print()
    console.print(Panel(
        f"[bold green]✅ Project team created[/]\n"
        f"Project: [cyan]{project_name}[/] | "
        f"Created: [green]{created}[/] | "
        f"Skipped: [yellow]{skipped}[/] | "
        f"Total roles: {len(selected_roles)}",
        border_style="green",
    ))

    # ── Next steps ──
    first_agent = agents_to_create[0][0] if agents_to_create else ""
    console.print()
    console.print("[bold]🚀 Next steps:[/]")
    if first_agent:
        console.print(f"  [cyan]agentark run \"开始第一个任务\" -p {first_agent}[/]")
    console.print(f"  [cyan]agentark team project-roles {project_name}[/]  查看项目团队")
    console.print(f"  [cyan]agentark fleet status[/]                      舰队状态")
    console.print(f"  [cyan]agentark team add-role {project_name} <role>[/] 添加新角色")
    console.print()


def add_role_cmd(project_name: str, role_key: str,
                 model: str = "deepseek-v4-pro", provider: str = "deepseek"):
    """Add a new agent role to an existing project team.

    Args:
        project_name: Existing project name
        role_key: Role key to add (e.g. 'qa', 'security', 'designer')
        model: Default model
        provider: Default provider
    """
    if not _role_exists(role_key):
        console.print(f"[red]✗ Unknown role '{role_key}'[/]")
        console.print(f"[dim]Run 'agentark team list-roles' to see available roles[/]")
        return

    agent_name = _agent_name(project_name, role_key)
    info = AGENT_ROLES[role_key]
    pm = ProfileManager()

    if agent_name in pm.list():
        console.print(f"[yellow]⚠ {agent_name} already exists[/]")
        return

    # Confirm
    console.print()
    console.print(Panel(
        f"[bold]Add role to project [cyan]{project_name}[/]:[/]\n"
        f"  Agent: [cyan]{agent_name}[/]\n"
        f"  Role:  {info['badge']} {info['name']}\n"
        f"  Skills: {', '.join(info['default_skills'][:3])}",
        border_style="cyan",
    ))

    if not Confirm.ask("Create this agent?", default=True):
        console.print("[dim]Cancelled.[/]")
        return

    try:
        pm.create_default(
            agent_name,
            role=f"{info['name']} — {project_name} 项目",
            expertise=info["default_skills"],
        )
        console.print(f"[green]✅ Added {info['badge']} {agent_name} to {project_name}[/]")
    except Exception as e:
        console.print(f"[red]✗ Failed: {e}[/]")


def project_roles_cmd(project_name: str):
    """List all agents in a project team."""
    agents = _list_project_agents(project_name)
    pm = ProfileManager()

    console.print()
    console.print(Panel(
        f"[bold cyan]👥 Project Agents: [white]{project_name}[/][/]",
        border_style="cyan",
    ))
    console.print()

    if not agents:
        console.print(f"[yellow]⚠ No agents found for project '{project_name}'[/]")
        console.print(f"[dim]Create team: agentark team create-project {project_name}[/]")
        console.print()
        return

    table = Table(box=box.ROUNDED)
    table.add_column("Agent", style="cyan")
    table.add_column("Role", style="green")
    table.add_column("Model", style="yellow")
    table.add_column("Skills", style="dim")

    for agent_name in sorted(agents):
        try:
            p = pm.load(agent_name)
            table.add_row(
                agent_name,
                p.soul.role or "-",
                p.model.default,
                ", ".join(p.skills[:3]) or "-",
            )
        except Exception:
            table.add_row(agent_name, "[red]Failed to load[/]", "", "")

    console.print(table)
    console.print(f"\n[dim]Total: {len(agents)} agents | Add role: agentark team add-role {project_name} <role>[/]")
    console.print()


# ══════════════════════════════════════════════════════════════════
# INTERACTIVE ROLE SELECTION
# ══════════════════════════════════════════════════════════════════

def _interactive_role_selection(project_name: str) -> list[str]:
    """Interactive wizard for selecting agent roles."""
    console.print()
    console.print(Panel(
        f"[bold cyan]🎭 Select Agent Roles for: [white]{project_name}[/][/]\n"
        "[dim]Agents will be named as: <project>-<role> (e.g. myapp-backend)[/]",
        border_style="cyan",
    ))

    # Show presets first
    console.print("[bold]Quick Presets:[/]")
    for preset_name, roles in ROLE_PRESETS.items():
        role_badges = " ".join(
            AGENT_ROLES[r]["badge"] for r in roles if r in AGENT_ROLES
        )
        console.print(f"  [dim]{preset_name:<12s}[/] {role_badges}")

    console.print()
    use_preset = Confirm.ask("Use a preset?", default=False)
    if use_preset:
        preset_name = Prompt.ask(
            "  Preset name",
            choices=list(ROLE_PRESETS.keys()),
            default="webapp",
        )
        return list(ROLE_PRESETS[preset_name])

    # Manual selection
    console.print()
    console.print("[bold]Available Roles:[/]")

    role_keys = list(AGENT_ROLES.keys())
    for i, key in enumerate(role_keys, 1):
        info = AGENT_ROLES[key]
        console.print(
            f"  [{i:2d}] {info['badge']} [cyan]{key:<14s}[/] "
            f"[dim]{info['name']:<24s}[/] {info['desc']}"
        )

    console.print()
    console.print("[dim]Enter comma-separated numbers (e.g. '1,3,5,8,10') or role keys (e.g. 'pm,backend,devops')[/]")
    selection = Prompt.ask("Select roles", default="1,3,4,5,6").strip()

    # Parse selection
    parts = [p.strip() for p in selection.split(",")]
    selected = []

    for p in parts:
        if p.isdigit():
            idx = int(p) - 1
            if 0 <= idx < len(role_keys):
                selected.append(role_keys[idx])
        elif p in AGENT_ROLES:
            selected.append(p)
        else:
            console.print(f"  [yellow]⚠ Unknown: {p}, skipping[/]")

    return selected


# ══════════════════════════════════════════════════════════════════
# HERMES LAUNCH — start Hermes sessions for project agents
# ══════════════════════════════════════════════════════════════════


def launch_hermes_cmd(
    project_name: str,
    role: str = "",
    launch_all: bool = False,
) -> None:
    """Launch Hermes conversations for project agents.

    Naming convention: <project>-<role> (e.g. finops-pm, finops-architect)

    Examples:
      agentark team launch finops               Interactive: pick which role
      agentark team launch finops --role pm      Launch finops-pm
      agentark team launch finops --all           Launch all project agents
    """
    pm = ProfileManager()

    # ── Discover project agents ──
    project_prefix = f"{project_name}-"
    all_profiles = pm.list()
    project_agents = sorted([
        p for p in all_profiles if p.startswith(project_prefix)
    ])

    if not project_agents:
        console.print()
        console.print(Panel(
            f"[yellow]⚠ No agents found for project '[bold]{project_name}[/]'[/]\n\n"
            f"[dim]Create a team first:[/]\n"
            f"  agentark team create-project {project_name} --preset saas\n"
            f"  agentark team create-project {project_name} --roles pm,backend,frontend[/]",
            title="Project Not Found",
            border_style="yellow",
        ))
        console.print()
        return

    # ── Resolve target agents ──
    targets: list[str] = []
    if role:
        target_name = f"{project_name}-{role}"
        if target_name in project_agents:
            targets = [target_name]
        else:
            console.print(f"[red]✗ Agent '{target_name}' not found in project '{project_name}'[/]")
            _show_project_agents(project_agents, project_name)
            return
    elif launch_all:
        targets = project_agents
    else:
        # Interactive selection
        targets = _interactive_launch_selection(project_agents, project_name)

    if not targets:
        return

    # ── Sync + Launch ──
    from agentark.interface.hermes_sync import sync_profile_to_hermes, HERMES_PROFILES_DIR

    console.print()
    table = Table(box=box.ROUNDED, title=f"🚀 Launching Hermes — {project_name}")
    table.add_column("Agent", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Command", style="dim")

    for agent_name in targets:
        try:
            # Extract role from agent name (remove project prefix)
            role_name = agent_name[len(project_prefix):]
            display_name = f"{project_name}-{role_name}"

            # Sync to Hermes if needed
            result = sync_profile_to_hermes(
                agent_name,
                hermes_profile_name=agent_name,
                hermes_display_name=display_name,
            )

            table.add_row(agent_name, "✅ Synced", f"hermes -p {agent_name}")

        except Exception as exc:
            table.add_row(agent_name, f"[red]✗ {exc}[/]", "-")

    console.print(table)
    console.print()

    # ── Launch ──
    if len(targets) == 1:
        # Single agent — launch directly in this terminal
        from agentark.interface.hermes_sync import start_hermes_profile
        console.print(f"[cyan]⚡ Launching [bold]{targets[0]}[/] in Hermes...[/]")
        console.print()
        start_hermes_profile(targets[0])
    else:
        # Multiple agents — show launch commands (Hermes takes over terminal)
        console.print("[cyan]📋 Launch commands (one per terminal):[/]")
        console.print()
        for agent_name in targets:
            console.print(f"  [green]agentark team hermes {agent_name}[/]")
        console.print()
        console.print(f"[dim]{len(targets)} agents ready | Hermes profiles at {HERMES_PROFILES_DIR}[/]")
        console.print()


def _interactive_launch_selection(agents: list[str], project_name: str) -> list[str]:
    """Let user pick which agents to launch."""
    console.print()
    console.print(Panel(
        f"[bold cyan]🚀 Launch Hermes — [white]{project_name}[/][/]\n"
        f"[dim]Select agents to start Hermes sessions[/]",
        border_style="cyan",
    ))

    pm = ProfileManager()
    for i, agent_name in enumerate(agents, 1):
        try:
            p = pm.load(agent_name)
            role = p.soul.role or agent_name
            model = p.model.default or "default"
            console.print(f"  [{i:2d}] {agent_name:<25s} [green]{role:<20s}[/] [dim]model: {model}[/]")
        except Exception:
            console.print(f"  [{i:2d}] {agent_name:<25s} [dim](no profile)[/]")

    console.print()
    console.print("[dim]Enter comma-separated numbers, 'all', or press Enter to cancel[/]")
    selection = Prompt.ask("Select", default="").strip()

    if not selection:
        return []

    if selection.lower() == "all":
        return agents

    parts = [p.strip() for p in selection.split(",")]
    selected = []
    for p in parts:
        if p.isdigit():
            idx = int(p) - 1
            if 0 <= idx < len(agents):
                selected.append(agents[idx])
        elif p in agents:
            selected.append(p)

    return selected


def _show_project_agents(agents: list[str], project_name: str) -> None:
    """Display existing project agents."""
    console.print()
    console.print(f"[dim]Available agents in '{project_name}':[/]")
    for a in agents:
        console.print(f"  • {a}")
    console.print()
