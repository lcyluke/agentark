"""
Origin Agent CLI — 始祖Agent 命令行接口

Commands:
  apex origin init          Initialize/deploy the Origin Agent
  apex origin replicate     Replicate skills to project agents
  apex origin portfolio     Portfolio management (create/list/status)
  apex origin overview      Fleet overview dashboard
  apex origin switch        Switch to Origin mode from any agent
"""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from apex.orchestration.origin import OriginAgent, ORIGIN_PROFILE_NAME


def _get_origin() -> OriginAgent:
    return OriginAgent()


def init_cmd(console: Console):
    """Initialize/deploy the Origin Agent."""
    origin = _get_origin()
    result = origin._ensure_origin_profile()

    if result["status"] == "created":
        console.print(f"[green]⚓ 始祖Agent已创建: {result['name']}[/]")
    else:
        console.print(f"[yellow]⚓ 始祖Agent已升级: {result['name']}[/]")

    # Show capabilities
    table = Table(title="🧭 始祖Agent 核心能力", box=None)
    table.add_column("能力", style="cyan")
    table.add_column("说明", style="green")

    capabilities = [
        ("技能复制迁移", "将skills/expertise注入任何agent的profile"),
        ("权限继承", "被注入agent获得origin授权的command权限"),
        ("项目群管理", "管理多个独立项目的PM agent + 资源平衡"),
        ("战略目标下达", "设定项目OKR + 预期效果 + 追踪进度"),
        ("任意窗口切换", "通过Hermes skill从任何chat切回origin模式"),
    ]
    for cap, desc in capabilities:
        table.add_row(cap, desc)
    console.print(table)

    console.print("\n[dim]运行 [bold]apex origin replicate --all[/] 向所有agent注入PM能力[/]")


def replicate_cmd(console: Console, target: str = "", all_agents: bool = False,
                   strategy: str = "merge"):
    """Replicate skills to target agent(s)."""
    origin = _get_origin()

    if all_agents:
        result = origin.replicate_to_all()
        console.print(f"[green]⚓ 已向 {result['replicated']} 个agent注入PM能力[/]")
        for name in result.get("targets", []):
            console.print(f"   🚢 {name}")
        return

    if not target:
        console.print("[red]请指定目标agent名称 或使用 --all[/]")
        return

    result = origin.replicate_to(target, strategy=strategy)
    if result.get("ok"):
        console.print(f"[green]⚓ {result['message']}[/]")
        console.print(f"   技能数: {result['skills_count']} | 专长数: {result['expertise_count']}")
    else:
        console.print(f"[red]✗ {result.get('error', '未知错误')}[/]")


def portfolio_cmd(console: Console, action: str = "list", **kwargs):
    """Portfolio management."""
    origin = _get_origin()

    if action == "list":
        portfolios = origin.list_portfolios()
        if not portfolios:
            console.print("[dim]暂无项目群。运行 [bold]apex origin portfolio create <name>[/] 创建[/]")
            return

        table = Table(title="📊 项目群管理", box=None)
        table.add_column("ID", style="dim")
        table.add_column("项目名", style="cyan")
        table.add_column("PM Agent", style="green")
        table.add_column("状态", style="yellow")
        table.add_column("战略目标", style="dim")

        for p in portfolios:
            status_icon = {"active": "🟢", "paused": "🟡", "completed": "✅"}.get(p["status"], "⬜")
            goal = (p.get("strategic_goal") or "")[:50]
            table.add_row(
                p["id"][:12], p["name"],
                p.get("pm_agent", "-"),
                f"{status_icon} {p['status']}",
                goal,
            )
        console.print(table)

    elif action == "create":
        name = kwargs.get("name", "")
        desc = kwargs.get("description", "")
        goal = kwargs.get("strategic_goal", "")
        outcome = kwargs.get("expected_outcome", "")
        pm = kwargs.get("pm_agent", "")

        if not name:
            console.print("[red]请提供项目名[/]")
            return

        result = origin.create_portfolio(name, desc, goal, outcome, pm)
        if result.get("ok"):
            console.print(f"[green]⚓ {result['message']}[/]")
        else:
            console.print(f"[red]✗ {result.get('error', '')}[/]")

    elif action == "status":
        pid = kwargs.get("portfolio_id", "")
        if not pid:
            console.print("[red]请提供项目ID[/]")
            return

        pf = origin.get_portfolio_status(pid)
        if "error" in pf:
            console.print(f"[red]✗ {pf['error']}[/]")
            return

        console.print(Panel(
            f"战略目标: {pf.get('strategic_goal', '未设定')}\n"
            f"预期效果: {pf.get('expected_outcome', '未设定')}\n"
            f"PM Agent: {pf.get('pm_agent', '未分配')}",
            title=f"📊 {pf['name']}",
            border_style="cyan",
        ))

        ts = pf.get("task_summary", {})
        console.print(f"  任务: {ts.get('done',0)}✅ / {ts.get('in_progress',0)}🔄 / {ts.get('total',0)}总计")

        milestones = pf.get("milestones", [])
        if milestones:
            console.print("\n  📍 里程碑:")
            for m in milestones:
                icon = {"done": "✅", "in_progress": "🔄", "pending": "⏳"}.get(m["status"], "⬜")
                console.print(f"    {icon} {m['title']}  ({m.get('target_date', '未设日期')})")


def overview_cmd(console: Console):
    """Fleet overview."""
    origin = _get_origin()
    overview = origin.portfolio_overview()

    console.print(Panel(
        f"舰队: {overview['fleets']} | 活跃: {overview['active']} | 完成: {overview['completed']}\n"
        f"任务: {overview['completed_tasks']}/{overview['total_tasks']} "
        f"({overview['completion_rate']}%)",
        title="⚓ 舰队总览 — Fleet Overview",
        border_style="cyan",
    ))

    if overview["portfolios"]:
        table = Table(box=None)
        table.add_column("项目", style="cyan")
        table.add_column("舰长(PM)", style="green")
        table.add_column("状态", style="yellow")
        table.add_column("航向(战略目标)", style="dim")

        for p in overview["portfolios"]:
            status_icon = {"active": "🟢", "completed": "✅"}.get(p["status"], "⬜")
            table.add_row(p["name"], p["pm_agent"], status_icon, p["strategic_goal"])

        console.print(table)
