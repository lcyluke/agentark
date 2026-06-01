"""Apex — Crew模式（班组模式）
角色组队实时协作 + 动态组队引擎 + 零点击组队。

Crew vs Swarm:
  Swarm = 并行独立Worker + 验证 + 合成（适合独立任务分解）
  Crew  = 角色之间实时对话协作（适合需要讨论反馈的任务）
"""
from __future__ import annotations

import json
import click
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text

from apex.core.profile import Profile, ProfileManager
from apex.core.runtime import Agent
from apex.core.templates import TEMPLATES, get_template, list_templates
from apex.providers import registry as provider_registry


console = Console()


@dataclass
class CrewMember:
    """Crew中的一名成员"""
    name: str
    profile: Profile
    role_description: str
    output: str = ""


@dataclass
class CrewResult:
    """Crew执行结果"""
    goal: str
    members: list[CrewMember] = field(default_factory=list)
    discussion_log: list[dict] = field(default_factory=list)
    final_output: str = ""
    total_cost: float = 0.0


class DynamicTeamDesigner:
    """动态组队引擎 — 零点击组队核心"""

    def __init__(self):
        pass

    def design_team(self, goal: str) -> dict:
        """根据任务自动设计最优团队"""
        goal_lower = goal.lower()

        # 关键词匹配规则
        team_designs = {
            "web": {
                "goal": f"构建Web应用: {goal}",
                "members": [
                    ("pm", "产品经理", "需求分析和PRD"),
                    ("frontend", "前端开发工程师", "UI组件和页面实现"),
                    ("backend", "后端架构师", "API和数据库设计"),
                ],
                "verifier": ("devops", "架构审查"),
            },
            "app": {
                "goal": f"开发应用: {goal}",
                "members": [
                    ("pm", "产品经理", "定义MVP范围"),
                    ("frontend", "前端开发工程师", "界面开发"),
                    ("backend", "后端架构师", "API开发"),
                ],
                "verifier": ("devops", "部署方案审查"),
            },
            "deploy": {
                "goal": f"部署上线: {goal}",
                "members": [
                    ("devops", "DevOps运维工程师", "部署方案和CI/CD"),
                    ("backend", "后端架构师", "环境配置确认"),
                ],
                "verifier": ("pm", "验证"),
            },
            "content": {
                "goal": f"内容创作: {goal}",
                "members": [
                    ("content", "内容运营专家", "文案撰写"),
                    ("pm", "产品经理", "内容策略对齐"),
                ],
                "verifier": None,
            },
            "api": {
                "goal": f"API开发: {goal}",
                "members": [
                    ("backend", "后端架构师", "API设计和实现"),
                    ("devops", "DevOps运维工程师", "部署和监控"),
                ],
                "verifier": ("pm", "API文档审查"),
            },
            "data": {
                "goal": f"数据分析: {goal}",
                "members": [
                    ("backend", "后端架构师", "数据管道设计"),
                    ("pm", "产品经理", "数据指标定义"),
                ],
                "verifier": None,
            },
        }

        # 智能匹配
        for key, design in team_designs.items():
            if key in goal_lower:
                return design

        # 默认：用AI推理组队（如果有DeepSeek）
        default = {
            "goal": f"项目: {goal}",
            "members": [
                ("pm", "产品经理", "需求分析和项目管理"),
                ("frontend", "前端开发工程师", "前端开发"),
                ("backend", "后端架构师", "后端开发"),
            ],
            "verifier": ("devops", "质量审查"),
        }
        return default

    def design_team_from_scratch(self, goal: str) -> dict:
        """用AI推理组队（更精确，但耗时）"""
        # Phase 2: 调用LLM做更精准的团队设计
        return self.design_team(goal)


class Crew:
    """班组模式执行器 — 多角色实时协作"""

    def __init__(self, members: list[CrewMember], verifier: Optional[CrewMember] = None):
        self.members = members
        self.verifier = verifier
        self.discussion_log = []
        self.total_cost = 0.0

    @classmethod
    def from_template_names(cls, names: list[str], goal: str) -> "Crew":
        """从模板名列表创建Crew"""
        pm = ProfileManager()
        members = []
        for name in names:
            template = get_template(name)
            if template:
                profile = template.to_profile(f"crew_{name}")
                members.append(CrewMember(
                    name=name,
                    profile=profile,
                    role_description=template.display,
                ))
            else:
                # 尝试直接加载Profile
                try:
                    profile = pm.load(name)
                    members.append(CrewMember(
                        name=name,
                        profile=profile,
                        role_description=profile.soul.role or name,
                    ))
                except FileNotFoundError:
                    console.print(f"[red]✗ 找不到Agent '{name}'[/]")
        return cls(members=members)

    @classmethod
    def auto_design(cls, goal: str) -> "Crew":
        """零点击组队 — 自动设计团队"""
        designer = DynamicTeamDesigner()
        design = designer.design_team(goal)
        pm = ProfileManager()
        members = []

        for template_name, role, task in design["members"]:
            template = get_template(template_name)
            if template:
                profile = template.to_profile(f"crew_{template_name}")
                pm.save(profile)
                member = CrewMember(name=template_name, profile=profile, role_description=role)
            else:
                try:
                    profile = pm.load(template_name)
                    member = CrewMember(name=template_name, profile=profile, role_description=role)
                except FileNotFoundError:
                    console.print(f"[yellow]⚠ 跳过: {template_name}[/]")
                    continue
            members.append(member)

        verifier = None
        if design.get("verifier"):
            v_name, v_role = design["verifier"]
            v_template = get_template(v_name)
            if v_template:
                v_profile = v_template.to_profile(f"crew_{v_name}")
                verifier = CrewMember(name=v_name, profile=v_profile, role_description=v_role)

        return cls(members=members, verifier=verifier)

    def run(self, goal: str) -> CrewResult:
        """执行Crew协作"""
        result = CrewResult(goal=goal, members=self.members)

        console.print(f"\n[bold]🎭 Crew组建完成![/]")
        console.print(f"   目标: [bold]{goal[:80]}{'...' if len(goal) > 80 else ''}[/]")
        console.print(f"   成员: {', '.join(f'{m.name}({m.role_description})' for m in self.members)}")
        if self.verifier:
            console.print(f"   验证: {self.verifier.name}({self.verifier.role_description})")
        console.print()

        # Phase 1: 各成员独立工作（分头调研/设计）
        console.print("[bold]📋 Phase 1: 各成员分头工作[/]")
        console.print("-" * 40)

        with ThreadPoolExecutor(max_workers=len(self.members)) as executor:
            future_map = {}
            for member in self.members:
                agent = Agent(member.profile)
                task_prompt = f"""你是{member.role_description}（{member.name}）。
项目目标: {goal}

请从你的专业角度完成以下工作：
1. 分析任务需求中与你专业相关的部分
2. 给出专业方案和建议
3. 列出你需要其他角色配合的事项

请输出完整、专业、可直接使用的方案。"""
                future = executor.submit(agent.run, task_prompt)
                future_map[future] = member

            for future in as_completed(future_map):
                member = future_map[future]
                try:
                    member.output = future.result()
                    console.print(f"   ✅ {member.name} — 完成")
                except Exception as e:
                    member.output = f"错误: {e}"
                    console.print(f"   ❌ {member.name} — 失败: {e}")

        # Phase 2: 圆桌讨论（每个成员看到其他人的输出，互相反馈）
        if len(self.members) >= 2:
            console.print(f"\n[bold]💬 Phase 2: 圆桌讨论[/]")
            console.print("-" * 40)

            for i, member in enumerate(self.members):
                others_output = "\n\n".join(
                    f"=== {m.name}({m.role_description})的方案 ===\n{m.output[:1500]}"
                    for j, m in enumerate(self.members)
                    if j != i
                )

                agent = Agent(member.profile)
                review_prompt = f"""你是{member.role_description}（{member.name}）。
项目目标: {goal}

以下是你的团队成员的方案。请阅读并给出：
1. 你赞同的部分
2. 你发现的问题或风险
3. 你建议的修改
4. 需要你配合才能实现的部分

其他人的方案:
{others_output}

请输出你的反馈意见（专业、直接、可执行）。"""
                try:
                    feedback = agent.run(review_prompt)
                    self.discussion_log.append({
                        "from": member.name,
                        "type": "feedback",
                        "content": feedback,
                    })
                    result.discussion_log = self.discussion_log
                    console.print(f"   💬 {member.name} — 反馈完成")
                except Exception as e:
                    console.print(f"   ⚠️ {member.name} — 反馈失败: {e}")

        # Phase 3: 最终整合（PM或第一个成员做最终输出）
        console.print(f"\n[bold]📦 Phase 3: 最终整合[/]")
        console.print("-" * 40)

        lead = max(self.members, key=lambda m: len(m.output))
        agent = Agent(lead.profile)

        all_outputs = "\n\n".join(
            f"=== {m.name}({m.role_description}) ===\n{m.output}"
            for m in self.members
        )

        feedback_section = ""
        if self.discussion_log:
            feedback_section = "\n\n=== 讨论反馈 ===\n" + "\n\n".join(
                f"来自 {log['from']}: {log['content'][:1000]}"
                for log in self.discussion_log
            )

        synthesis_prompt = f"""你是项目整合负责人。
项目目标: {goal}

请整合以下各角色的方案为一份完整的交付方案：

{all_outputs}
{feedback_section}

请以{lead.role_description}的视角输出一份结构化的整合方案：
1. 整体架构/方案概述
2. 各模块详细设计
3. 模块间关系
4. 实施建议和优先级
5. 风险点和应对"""
        try:
            result.final_output = agent.run(synthesis_prompt)
            console.print(f"   ✅ 整合完成")
        except Exception as e:
            result.final_output = f"整合失败: {e}"
            console.print(f"   ❌ 整合失败: {e}")

        # Phase 4: 验证（可选）
        if self.verifier:
            console.print(f"\n[bold]🔍 Phase 4: 验证 ({self.verifier.name})[/]")
            console.print("-" * 40)

            v_agent = Agent(self.verifier.profile)
            verify_prompt = f"""请审查以下项目方案的质量和完整性。
项目目标: {goal}

方案:
{result.final_output[:4000]}

请给出:
1. 整体质量评分（1-10）
2. 发现的问题（严重/中等/轻微）
3. 必须修改的事项
4. 总体结论：批准/有条件批准/打回"""
            try:
                verify_output = v_agent.run(verify_prompt)
                self.discussion_log.append({
                    "from": self.verifier.name,
                    "type": "verification",
                    "content": verify_output,
                })
                console.print(f"   ✅ 验证完成")
            except Exception as e:
                console.print(f"   ⚠️ 验证失败: {e}")

        console.print(f"\n[bold green]✅ Crew协作完成![/]")
        return result


# ─── CLI命令 ───
@click.group()
def crew():
    """管理Crew班组"""
    pass


@crew.command(name="create")
@click.argument("goal")
@click.option("--members", "-m", help="成员（逗号分隔模板名）")
def crew_create(goal: str, members: str):
    """创建并执行一个Crew"""
    if members:
        names = [n.strip() for n in members.split(",")]
        c = Crew.from_template_names(names, goal)
    else:
        console.print("[bold]🎯 零点击组队中...[/]")
        c = Crew.auto_design(goal)

    result = c.run(goal)

    if result.final_output:
        console.print(Panel(
            result.final_output[:3000],
            title=f"📦 Crew交付物: {goal[:50]}...",
            border_style="green",
        ))


@crew.command(name="design")
@click.argument("goal")
def crew_design(goal: str):
    """预览自动设计的团队"""
    designer = DynamicTeamDesigner()
    design = designer.design_team(goal)

    table = Table(title=f"🎯 推荐团队: {goal[:50]}", box=None)
    table.add_column("角色", style="cyan")
    table.add_column("模板", style="green")
    table.add_column("职责", style="white")

    for t_name, role, task in design["members"]:
        table.add_row(role, t_name, task)

    console.print(table)
    if design.get("verifier"):
        console.print(f"\n验证者: [bold]{design['verifier'][0]}[/]({design['verifier'][1]})")
    console.print(f"\n[dim]使用: [bold]apex crew create \"{goal}\" --members {'/'.join(m[0] for m in design['members'])}[/][/dim]")
