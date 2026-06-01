"""Apex — Swarm模式（蜂群模式）
并行Worker → Verifier → Synthesizer 三阶段交付。
"""
from __future__ import annotations

import sys
import json
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from .kanban import Kanban, Task, TASK_STATUS_READY, TASK_STATUS_IN_PROGRESS, TASK_STATUS_DONE, TASK_STATUS_FAILED
from ..core.runtime import Agent
from ..core.profile import Profile


@dataclass
class SwarmResult:
    success: bool = False
    worker_outputs: list[dict] = field(default_factory=list)
    verifier_output: str = ""
    synthesizer_output: str = ""
    total_cost: float = 0.0
    error: str = ""


class Swarm:
    """蜂群模式 — 并行Worker → Verifier → Synthesizer"""

    def __init__(self, kanban: Kanban):
        self.kanban = kanban

    def run(
        self,
        goal: str,
        workers: list[tuple[str, Profile, str]],  # (name, profile, task_description)
        verifier: Optional[tuple[str, Profile]] = None,
        synthesizer: Optional[tuple[str, Profile]] = None,
        max_parallel: int = 3,
    ) -> SwarmResult:
        """执行一个Swarm

        Args:
            goal: Swarm目标描述
            workers: [(name, profile, task), ...]
            verifier: (name, profile) — 验证者
            synthesizer: (name, profile) — 合成者
            max_parallel: 最大并行数
        """
        result = SwarmResult()

        # Phase 1: 并行Worker
        print(f"\n{'='*50}")
        print(f"🚀 Apex Swarm: {goal}")
        print(f"{'='*50}")
        print(f"   Worker数: {len(workers)}")
        if verifier:
            print(f"   验证者: {verifier[0]}")
        if synthesizer:
            print(f"   合成者: {synthesizer[0]}")
        print(f"{'='*50}\n")

        # 创建Kanban任务
        kanban_tasks = []
        for name, profile, task_desc in workers:
            t = self.kanban.create_task(
                title=f"[{name}] {task_desc[:50]}",
                assignee=name,
                description=task_desc,
                status=TASK_STATUS_READY,
            )
            kanban_tasks.append(t)

        # 并行执行
        print("📋 Phase 1: Worker并行执行")
        print("-" * 40)

        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            future_map = {}
            for (name, profile, task_desc), kanban_task in zip(workers, kanban_tasks):
                agent = Agent(profile, api_key=self._get_api_key())
                self.kanban.update_task(kanban_task.id, status=TASK_STATUS_IN_PROGRESS)
                future = executor.submit(agent.run, task_desc)
                future_map[future] = (name, kanban_task.id)

            for future in as_completed(future_map):
                name, task_id = future_map[future]
                try:
                    output = future.result()
                    agent_summary = f"Agent[{name}]"  # simplified
                    result.worker_outputs.append({
                        "name": name,
                        "task_id": task_id,
                        "output": output,
                    })
                    self.kanban.update_task(task_id, status=TASK_STATUS_DONE, output=output)
                    print(f"   ✅ {name} — 完成")
                except Exception as e:
                    result.worker_outputs.append({
                        "name": name,
                        "task_id": task_id,
                        "output": f"ERROR: {e}",
                    })
                    self.kanban.update_task(task_id, status=TASK_STATUS_FAILED, output=str(e))
                    print(f"   ❌ {name} — 失败: {e}")

        # Phase 2: Verifier（验证者）
        if verifier and result.worker_outputs:
            print(f"\n🔍 Phase 2: 验证者 ({verifier[0]})")
            print("-" * 40)
            name, profile = verifier
            agent = Agent(profile, api_key=self._get_api_key())
            verifier_task = f"""验证以下工作的质量和完整性。
项目目标: {goal}

各Worker输出:
"""
            for wo in result.worker_outputs:
                verifier_task += f"""
--- {wo['name']}的输出 ---
{wo['output'][:2000]}
"""

            verifier_task += """
请给出:
1. 每个Worker输出的质量评分（1-10）
2. 发现的问题和改进建议
3. 整体质量结论：通过/需要修改/不通过
"""
            try:
                result.verifier_output = agent.run(verifier_task)
                print(f"   ✅ 验证完成")
            except Exception as e:
                result.verifier_output = f"验证失败: {e}"
                print(f"   ❌ 验证失败: {e}")

        # Phase 3: Synthesizer（合成者）
        if synthesizer:
            print(f"\n📦 Phase 3: 合成者 ({synthesizer[0]})")
            print("-" * 40)
            name, profile = synthesizer
            agent = Agent(profile, api_key=self._get_api_key())
            synthesizer_task = f"""请整合以下工作成果为一个完整的交付物。
项目目标: {goal}

各Worker输出:
"""
            for wo in result.worker_outputs:
                synthesizer_task += f"""
--- {wo['name']}的输出 ---
{wo['output'][:2000]}
"""

            if result.verifier_output:
                synthesizer_task += f"""
--- 验证者反馈 ---
{result.verifier_output[:2000]}
"""

            synthesizer_task += """
请产出:
1. 整合后的完整方案/交付物
2. 各模块之间的关系说明
3. 下一步建议
"""
            try:
                result.synthesizer_output = agent.run(synthesizer_task)
                print(f"   ✅ 合成完成")
            except Exception as e:
                result.synthesizer_output = f"合成失败: {e}"
                print(f"   ❌ 合成失败: {e}")

        # 汇总
        result.success = True
        print(f"\n{'='*50}")
        print(f"✅ Swarm 完成! 总成本: ${result.total_cost:.4f}")
        print(f"{'='*50}")

        return result

    def _get_api_key(self) -> str:
        """从环境获取API Key"""
        import os
        return os.environ.get("DEEPSEEK_API_KEY", "")
