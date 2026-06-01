"""Apex — 自愈工作流增强版（Self-Healing Workflow v2）
三振出局规则 + 知识积累 + 自动降级 + 进化反馈。

当Agent出错时:
  1. 第一次出错 → 自动修复
  2. 第二次出错 → 切换方案
  3. 第三次出错 → 降级模型 → 通知人类
  4. 无论结果 → 知识写入KG → 进化引擎记录
"""
from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from typing import Optional

from apex.core.runtime import Agent
from apex.core.profile import Profile
from apex.core.knowledge import KnowledgeGraph
from apex.core.evolution import EvolutionEngine, ExecutionRecord
from apex.orchestration.kanban import Kanban, TASK_STATUS_FAILED


@dataclass
class HealingResult:
    success: bool
    attempts: int = 0
    errors: list[str] = field(default_factory=list)
    fixes: list[str] = field(default_factory=list)
    final_output: str = ""
    strategy_used: str = "direct"
    model_downgraded: bool = False


class SelfHealingExecutor:
    """自愈执行器 v2 — 完整生命周期"""

    MAX_ATTEMPTS = 3
    STRATEGIES = [
        "direct",           # 第一次：直接重试
        "switch_model",     # 第二次：切换模型/参数
        "simplify_task",    # 第三次：简化任务再重试
    ]

    def __init__(self, agent: Agent, kanban: Kanban = None):
        self.agent = agent
        self.kanban = kanban
        self.kg = KnowledgeGraph()
        self.evolution = EvolutionEngine()
        self._healer = None

    def _get_healer(self) -> Agent:
        if not self._healer:
            from apex.core.templates import get_template
            template = get_template("devops")
            if template:
                healer_profile = template.to_profile("healer")
            else:
                from apex.core.profile import Profile, SoulConfig
                healer_profile = Profile(
                    name="healer",
                    soul=SoulConfig(
                        role="故障修复专家",
                        expertise=["debugging", "error-analysis", "system-recovery", "root-cause"],
                        personality="冷静、系统化思维、永不放弃",
                    ),
                )
            self._healer = Agent(healer_profile)
        return self._healer

    def run(self, task: str, max_attempts: int = MAX_ATTEMPTS, **kwargs) -> HealingResult:
        """自愈执行 — 三振出局规则"""
        result = HealingResult()
        start_time = time.time()
        strategy_idx = 0

        # 1. 查知识图谱看有没有已知修复
        kg_hint = self.kg.query(f"修复 {task[:60]}")
        if kg_hint.confidence > 0.5:
            result.fixes.append(f"📚 知识图谱建议: {kg_hint.answer[:200]}")

        for attempt in range(1, max_attempts + 1):
            result.attempts = attempt
            strategy = self.STRATEGIES[min(strategy_idx, len(self.STRATEGIES) - 1)]
            result.strategy_used = strategy

            try:
                # 应用策略
                if strategy == "direct":
                    output = self.agent.run(task, **kwargs)

                elif strategy == "switch_model":
                    # 切到fallback模型
                    fallback = self.agent.profile.model.fallback
                    output = self.agent.run(task, model=fallback, **kwargs)
                    result.model_downgraded = True

                elif strategy == "simplify_task":
                    # 简化任务
                    healer = self._get_healer()
                    simplified = healer.run(
                        f"将以下任务拆解为更简单的子任务（一次只做一件事）:\n\n{task}"
                    )
                    output = self.agent.run(f"请完成以下简化版任务:\n{simplified}", **kwargs)

                # 成功！
                result.success = True
                result.final_output = output
                duration_ms = int((time.time() - start_time) * 1000)

                # 记录到进化引擎
                self._record_evolution(task, output, True, duration_ms, strategy)
                return result

            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                result.errors.append(error_msg)
                strategy_idx += 1

                # 自动诊断
                fix = self._diagnose(error_msg, task, attempt)
                if fix:
                    result.fixes.append(fix)

                # 知识图谱积累
                self.kg.learn_from_experience(
                    agent_name=self.agent.profile.name,
                    task=task,
                    error=error_msg,
                    fix=fix,
                )

                # 更新Kanban
                if self.kanban:
                    tasks = self.kanban.list_tasks()
                    for t in tasks:
                        if task[:30] in t.title:
                            self.kanban.update_task(t.id, status=f"healing_a{attempt}")
                            break

                time.sleep(1)

        # 三振出局
        result.success = False
        duration_ms = int((time.time() - start_time) * 1000)
        result.final_output = (
            f"❌ 执行失败（已自动修复{max_attempts}次均无效）\n"
            f"最后错误: {result.errors[-1] if result.errors else '未知'}\n"
            f"尝试策略: {', '.join(self.STRATEGIES[:strategy_idx+1])}\n"
            f"建议: 联系人类确认"
        )

        # 记录失败到进化引擎
        self._record_evolution(task, result.final_output, False, duration_ms, "failed")

        # 更新Kanban为失败
        if self.kanban:
            tasks = self.kanban.list_tasks()
            for t in tasks:
                if task[:30] in t.title:
                    self.kanban.update_task(t.id, status=TASK_STATUS_FAILED, output=result.final_output)
                    break

        return result

    def _diagnose(self, error: str, task: str, attempt: int) -> str:
        """诊断错误 — 先查KG再问LLM"""
        # 先查知识图谱
        kg_result = self.kg.query(f"如何修复 {error[:60]}")
        if kg_result.confidence > 0.5 and "没有找到" not in kg_result.answer:
            return f"📚 知识图谱: {kg_result.answer[:300]}"

        # 再问LLM
        healer = self._get_healer()
        try:
            diag_prompt = f"""一个Agent执行任务时出错。请一键诊断并给出最直接的修复方案。

任务: {task[:200]}
错误: {error[:300]}
第{attempt}次重试

输出格式（简洁）:
根因: ...
修复: ...
"""
            return healer.run(diag_prompt)[:500]
        except Exception:
            return f"简单重试（第{attempt}次）"

    def _record_evolution(self, task: str, output: str, success: bool,
                          duration_ms: int, strategy: str):
        """记录到进化引擎"""
        record = ExecutionRecord(
            agent_name=self.agent.profile.name,
            task=task,
            task_type="healing" if "修复" in task else "general",
            prompt=task[:200],
            output=output[:500],
            success=success,
            duration_ms=duration_ms,
            quality_score=0.8 if success else 0.2,
            error="" if success else (output[:200] if not success else ""),
        )
        self.evolution.record(record)
