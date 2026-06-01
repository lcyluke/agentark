"""Apex — One-Click Company (OCC)
一行命令创建一家AI公司。

apex company create "AI SaaS创业公司"
  → 自动创建全部5+个Profile
  → 自动配置Kanban
  → 自动设计SOP
  → 自动生成团队配置
  → 启动

apex company start "帮我写MVP"
  → 2小时后，MVP上线
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from apex.core.profile import ProfileManager, Profile, SoulConfig, APEX_HOME
from apex.core.templates import get_template, TEMPLATES
from apex.orchestration.kanban import Kanban
from apex.orchestration.swarm import Swarm
from apex.orchestration.crew import Crew, DynamicTeamDesigner

console = Console()


@dataclass
class Company:
    """一家AI公司的完整定义"""
    name: str
    description: str = ""
    industry: str = "tech"
    profiles: list[str] = field(default_factory=list)
    kanban_board: str = "default"
    sop: dict = field(default_factory=dict)
    created_at: float = 0.0


COMPANY_TEMPLATES = {
    "saas": {
        "description": "SaaS创业公司 — 从0到1构建产品",
        "profiles": ["pm", "frontend", "backend", "devops", "content"],
        "sop": {
            "name": "SaaS产品开发流程",
            "steps": [
                "需求分析 → PRD",
                "架构设计 → 技术方案",
                "前后端并行开发 → 代码",
                "集成测试 → 测试报告",
                "部署上线 → 生产环境",
                "内容发布 → 官网/文档",
                "监控运维 → 运维报告",
            ]
        }
    },
    "ai_product": {
        "description": "AI产品公司 — 模型+应用一体化",
        "profiles": ["pm", "frontend", "backend", "devops", "content"],
        "sop": {
            "name": "AI产品开发流程",
            "steps": [
                "数据准备 & 标注",
                "模型训练 & 评估",
                "API服务封装",
                "前端应用开发",
                "集成测试",
                "部署上线",
                "用户反馈收集",
            ]
        }
    },
    "content": {
        "description": "内容创作公司 — 多平台内容矩阵",
        "profiles": ["pm", "content", "frontend"],
        "sop": {
            "name": "内容创作流程",
            "steps": [
                "选题策划 → 选题库",
                "内容创作 → 初稿",
                "审核修改 → 终稿",
                "多平台分发 → 发布",
                "数据复盘 → 优化报告",
            ]
        }
    },
    "ecommerce": {
        "description": "电商平台公司 — 从商品到交易",
        "profiles": ["pm", "frontend", "backend", "devops", "content"],
        "sop": {
            "name": "电商平台开发流程",
            "steps": [
                "商品管理系统",
                "购物车 & 订单",
                "支付对接",
                "用户系统",
                "前端店铺",
                "运营后台",
                "部署 & 监控",
            ]
        }
    },
    "freelance": {
        "description": "个人开发者工作室 — 一个人接项目",
        "profiles": ["pm", "frontend", "backend", "devops"],
        "sop": {
            "name": "项目交付流程",
            "steps": [
                "需求沟通 → 报价",
                "技术方案 → 排期",
                "开发实现 → 交付",
                "测试验收 → 上线",
                "后期维护",
            ]
        }
    },
}


class CompanyBuilder:
    """AI公司建造者"""

    def __init__(self):
        self.pm = ProfileManager()
        self.kanban = Kanban(APEX_HOME / "kanban.db")

    def create(self, name: str, industry: str = "saas") -> Company:
        """创建一家AI公司"""

        template = COMPANY_TEMPLATES.get(industry, COMPANY_TEMPLATES["saas"])

        company = Company(
            name=name,
            description=template["description"],
            industry=industry,
            profiles=[],
            created_at=time.time(),
        )

        # Step 1: 创建Profile
        pm = ProfileManager()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"🏗️ 正在组建: {name}...", total=len(template["profiles"]) + 3)

            for tmpl_name in template["profiles"]:
                t = get_template(tmpl_name)
                if t:
                    profile_name = f"{name}_{tmpl_name}"
                    profile = t.to_profile(profile_name)
                    pm.save(profile)
                    company.profiles.append(profile_name)
                    progress.update(task, description=f"  ✅ 创建 {t.display} ({profile_name})", advance=1)
                else:
                    progress.update(task, description=f"  ⚠️ 跳过 {tmpl_name}（模板不存在）", advance=1)

            # Step 2: 创建初始Kanban任务
            progress.update(task, description="  📋 初始化Kanban...", advance=1)
            for i, step in enumerate(template["sop"]["steps"]):
                assignee = company.profiles[i % len(company.profiles)] if company.profiles else ""
                self.kanban.create_task(
                    title=f"[{name}] {step}",
                    assignee=assignee,
                    priority=1 if i == 0 else 2,
                    description=f"SOP步骤{i+1}: {step}",
                    status="todo",
                )

            # Step 3: 保存Company配置
            progress.update(task, description="  💾 保存公司配置...", advance=1)
            config_path = APEX_HOME / "companies" / f"{name}.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                json.dump({
                    "name": company.name,
                    "description": company.description,
                    "industry": company.industry,
                    "profiles": company.profiles,
                    "sop": template["sop"],
                    "created_at": company.created_at,
                }, f, indent=2, ensure_ascii=False)

            progress.update(task, description=f"  ✅ {name} 组建完成!", advance=1)

        # 显示结果
        self._show_company_summary(company, template)

        return company

    def _show_company_summary(self, company: Company, template: dict):
        """显示公司摘要"""
        table = Table(title=f"🏢 {company.name} — AI公司", box=None, border_style="cyan")
        table.add_column("部门", style="cyan")
        table.add_column("角色", style="green")
        table.add_column("职责", style="white")
        table.add_column("已就绪", style="green")

        tmpl_role_map = {
            "pm": ("📋 产品部", "产品经理", "需求分析、PRD"),
            "frontend": ("💻 前端部", "前端开发", "UI实现"),
            "backend": ("⚙️ 后端部", "后端开发", "API/数据库"),
            "content": ("✍️ 内容部", "内容运营", "文案/SEO"),
            "devops": ("🔧 运维部", "DevOps", "部署/监控"),
        }

        for p_name in company.profiles:
            base = p_name.replace(f"{company.name}_", "")
            dept, role, duty = tmpl_role_map.get(base, ("🤖", base, ""))
            table.add_row(dept, role, duty, "✅")

        console.print(table)

        info = Panel.fit(
            f"[bold]行业:[/] {company.industry} | "
            f"[bold]SOP:[/] {template['sop']['name']} "
            f"({len(template['sop']['steps'])}步)\n"
            f"[bold]命令:[/] apex company start \"{company.name}\" \"第一个任务\"\n"
            f"[bold]团队:[/] {', '.join(company.profiles)}",
            title=f"🎯 {company.name} 已上线!",
        )
        console.print(info)

    def start(self, name: str, goal: str):
        """启动公司执行第一个任务"""
        config_path = APEX_HOME / "companies" / f"{name}.json"
        if not config_path.exists():
            console.print(f"[red]✗ 公司 '{name}' 不存在。先用 'apex company create' 创建[/]")
            return

        with open(config_path) as f:
            config = json.load(f)

        console.print(f"\n[bold]🚀 {name} 启动中...")
        console.print(f"   目标: {goal}")
        console.print(f"   SOP: {config['sop']['name']} ({len(config['sop']['steps'])}步)")
        console.print()

        # 用第一个Profile做PM，主导任务分解
        profiles = config.get("profiles", [])
        if not profiles:
            console.print("[red]✗ 公司没有Profile[/]")
            return

        pm_profile = self.pm.load(profiles[0])
        from apex.core.runtime import Agent
        pm_agent = Agent(pm_profile)

        # 自动分解任务
        decomposition_prompt = f"""你是{name}公司的产品经理。
公司SOP: {config['sop']['name']}
公司团队: {', '.join(profiles)}

请将以下目标分解为Kanban任务，每个任务指定负责人：

目标: {goal}

输出JSON格式:
{{
  "goal": "目标简述",
  "tasks": [
    {{"title": "任务1", "assignee": "pm_profile_name", "description": "..."}},
    {{"title": "任务2", "assignee": "frontend_profile_name", "description": "..."}}
  ]
}}"""

        try:
            plan_text = pm_agent.run(decomposition_prompt)
            import re
            json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
            else:
                console.print("[red]✗ 无法解析任务分解[/]")
                return

            # 创建Kanban任务
            for t in plan.get("tasks", []):
                self.kanban.create_task(
                    title=f"[{name}] {t['title']}",
                    assignee=t.get("assignee", profiles[0]),
                    description=t.get("description", ""),
                    status="ready",
                )

            console.print(f"\n[bold green]✅ {name} 已启动! {len(plan.get('tasks',[]))}个任务已创建[/]")
            console.print(f"   查看: [bold]apex status[/]")
            console.print(f"   监控: [bold]apex dashboard[/]")

        except Exception as e:
            console.print(f"[red]✗ 启动失败: {e}[/]")


def list_companies():
    """列出所有已创建的公司"""
    companies_dir = APEX_HOME / "companies"
    if not companies_dir.exists():
        console.print("[yellow]还没有创建过公司[/]")
        return

    companies = list(companies_dir.glob("*.json"))
    if not companies:
        console.print("[yellow]还没有创建过公司[/]")
        return

    table = Table(title="🏢 AI公司列表", box=None)
    table.add_column("名称", style="cyan")
    table.add_column("行业", style="green")
    table.add_column("团队规模", style="yellow")
    table.add_column("创建时间")

    for c_path in companies:
        with open(c_path) as f:
            data = json.load(f)
        created = time.strftime("%Y-%m-%d %H:%M", time.localtime(data.get("created_at", 0)))
        table.add_row(data["name"], data["industry"], str(len(data.get("profiles", []))), created)

    console.print(table)
