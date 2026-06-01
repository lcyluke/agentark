"""Apex — run 命令"""
from __future__ import annotations

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from apex.core.profile import ProfileManager, APEX_HOME
from apex.core.runtime import Agent
from apex.orchestration.swarm import Swarm
from apex.orchestration.kanban import Kanban


def run_task(task: str, profile_name: str, model: str, swarm: bool, workers: int, console: Console):
    """执行任务"""

    if not task:
        console.print("[red]✗ 请提供任务描述[/]")
        return

    pm = ProfileManager()
    try:
        profile = pm.load(profile_name)
    except FileNotFoundError:
        console.print(f"[red]✗ Profile '{profile_name}' 不存在. 先用 'apex init' 创建[/]")
        return

    # 简单的单Agent模式
    if not swarm:
        agent = Agent(profile)
        console.print(f"\n[bold]🤖 Agent: {profile.display or profile.name}[/]")
        console.print(f"   模型: {model or profile.model.default}")
        console.print(f"   任务: {task[:80]}{'...' if len(task) > 80 else ''}\n")

        try:
            result = agent.run(task, model=model) if model else agent.run(task)
            console.print(Panel(result, title=f"✅ {profile.name} 完成", border_style="green"))
            console.print(f"[dim]成本: ${agent.context.cost:.6f} | 步骤: {len(agent.context.trace)}[/]")
        except Exception as e:
            console.print(Panel(str(e), title="❌ 执行失败", border_style="red"))

    else:
        # Swarm模式 — 自动拆解任务
        console.print(f"\n[bold]🚀 Swarm模式: {task[:60]}...[/]")
        console.print(f"   Worker数: {workers}")

        # 用AI自动拆解任务
        planner = Agent(profile)
        decomposition_prompt = f"""请将以下任务拆解为{workers}个可并行执行的子任务。
每个子任务应该独立、具体、可执行。

任务: {task}

请按以下格式输出（JSON）:
{{
  "goal": "整体目标描述",
  "workers": [
    {{"name": "worker-1", "task": "子任务1描述", "skills": ["所需技能1"]}},
    {{"name": "worker-2", "task": "子任务2描述", "skills": ["所需技能1"]}}
  ],
  "verifier_prompt": "验证者应该检查什么...",
  "synthesizer_prompt": "合成者应该整合什么..."
}}

只输出JSON，不要其他内容。"""

        try:
            plan_text = planner.run(decomposition_prompt)
            # 解析JSON
            import json
            import re
            json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
            else:
                console.print("[red]✗ 无法解析任务拆解结果[/]")
                return

            # 创建Worker Profiles
            worker_configs = []
            for w in plan.get("workers", []):
                w_profile = pm.create_default(
                    name=w["name"],
                    role=w["name"],
                    expertise=w.get("skills", []),
                )
                worker_configs.append((w["name"], w_profile, w["task"]))

            # 验证者、合成者
            verifier = ("verifier", pm.create_default("verifier", role="质量验证者"))
            synthesizer = ("synthesizer", pm.create_default("synthesizer", role="结果整合者"))

            # 执行Swarm
            kanban = Kanban(APEX_HOME / "kanban.db")
            swarm = Swarm(kanban)

            result = swarm.run(
                goal=plan.get("goal", task),
                workers=worker_configs,
                verifier=verifier,
                synthesizer=synthesizer,
                max_parallel=workers,
            )

            # 输出结果
            if result.success:
                if result.synthesizer_output:
                    console.print(Panel(
                        result.synthesizer_output[:3000],
                        title="📦 Swarm交付物",
                        border_style="green",
                    ))
            else:
                console.print(f"[red]✗ Swarm执行失败: {result.error}[/]")

        except Exception as e:
            console.print(f"[red]✗ Swarm执行失败: {e}[/]")
            import traceback
            console.print(traceback.format_exc()[:500])
