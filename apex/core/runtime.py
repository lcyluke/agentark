"""Apex — 核心Agent运行时
每个Agent是一个持久化的智能体，有自己的Profile、Memory、Skills。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .profile import Profile, ProfileManager
from apex.providers import LLMResponse, registry as provider_registry
from apex.core.evolution import EvolutionEngine, ExecutionRecord
import time


@dataclass
class AgentContext:
    """Agent的执行上下文"""
    session_id: str = ""
    task: str = ""
    messages: list[dict] = field(default_factory=list)
    trace: list[dict] = field(default_factory=list)
    cost: float = 0.0


class Agent:
    """一个可运行的Agent实例"""

    def __init__(
        self,
        profile: Profile,
        provider_name: str = None,
        api_key: str = None,
    ):
        self.profile = profile
        self.provider_name = provider_name or profile.model.default.split("-")[0]
        self.api_key = api_key
        self._provider = None
        self.context = AgentContext()

    @property
    def provider(self):
        if self._provider is None:
            config = {"api_key": self.api_key}
            # 检查是否deepseek provider、有model前缀
            prov_name = self.provider_name
            if prov_name not in provider_registry.list():
                # 尝试匹配 - 比如 deepseek-chat 对应 deepseek
                for reg_name in provider_registry.list():
                    if prov_name.startswith(reg_name):
                        prov_name = reg_name
                        break
                else:
                    prov_name = "deepseek"  # 默认
            self._provider = provider_registry.get(prov_name, config)
        return self._provider

    def run(self, task: str, **kwargs) -> str:
        """执行一个任务"""
        self.context.task = task
        self.context.messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": task},
        ]

        self._trace("start", f"开始任务: {task}")
        start_time = time.time()
        success = True
        error_msg = ""

        try:
            response = self.provider.chat(
                self.context.messages,
                model=kwargs.get("model", self.profile.model.default),
                **kwargs,
            )
            self.context.cost += self.provider.estimate_cost(response)
            self._trace("complete", f"完成 (${self.provider.estimate_cost(response):.6f})")

            # 技能进化（如果启用自动改进）
            if self.profile.auto_improve:
                self._auto_learn(task, response.content)

            # 记录到进化引擎
            self._record_evolution(task, response.content, True, start_time)

            return response.content

        except Exception as e:
            success = False
            error_msg = str(e)
            # 尝试fallback模型
            if self.profile.model.fallback:
                self._trace("fallback", f"主模型失败，降级到 {self.profile.model.fallback}")
                try:
                    response = self.provider.chat(
                        self.context.messages,
                        model=self.profile.model.fallback,
                        **kwargs,
                    )
                    self.context.cost += self.provider.estimate_cost(response)
                    self._trace("complete", f"完成(fallback) (${self.provider.estimate_cost(response):.6f})")
                    self._record_evolution(task, response.content, True, start_time)
                    return response.content
                except Exception as e2:
                    self._trace("error", f"Fallback也失败: {e2}")
                    error_msg = f"{e2}"
            self._record_evolution(task, error_msg, False, start_time, error=error_msg)
            raise

    def _record_evolution(self, task: str, output: str, success: bool,
                          start_time: float, error: str = ""):
        """记录执行到进化引擎"""
        try:
            evo = EvolutionEngine()
            record = ExecutionRecord(
                agent_name=self.profile.name,
                task=task[:500],
                task_type="general",
                prompt=self._build_system_prompt()[:200],
                output=output[:500],
                success=success,
                duration_ms=int((time.time() - start_time) * 1000),
                quality_score=0.8 if success else 0.1,
                error=error[:200],
                tokens_used=0,
                model=self.profile.model.default,
            )
            evo.record(record)
        except Exception:
            pass  # 进化记录失败不影响主流程

    def chat(self, messages: list[dict], **kwargs) -> LLMResponse:
        """直接聊天接口（用于多Agent对话）"""
        system_prompt = self._build_system_prompt()
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        response = self.provider.chat(
            full_messages,
            model=kwargs.get("model", self.profile.model.default),
            **kwargs,
        )
        self.context.cost += self.provider.estimate_cost(response)
        return response

    def _build_system_prompt(self) -> str:
        p = self.profile
        parts = [
            f"你是{p.soul.role or p.display}。",
        ]
        if p.soul.expertise:
            parts.append(f"你的专长: {', '.join(p.soul.expertise)}。")
        if p.soul.personality:
            parts.append(f"性格: {p.soul.personality}。")
        if p.soul.communication:
            parts.append(f"沟通风格: {p.soul.communication}。")
        if p.skills:
            parts.append(f"技能包: {', '.join(p.skills)}。")
        parts.append("\n请用专业、直接、可执行的方式完成任务。")
        return "\n".join(parts)

    def _trace(self, event: str, detail: str):
        self.context.trace.append({"event": event, "detail": detail, "cost": self.context.cost})

    def _auto_learn(self, task: str, result: str):
        """自动从执行中学习（简化版）"""
        # Phase 2: 实现技能进化
        pass

    def summarize(self) -> dict:
        """当前会话摘要"""
        return {
            "agent": self.profile.name,
            "role": self.profile.soul.role,
            "task": self.context.task,
            "total_cost": round(self.context.cost, 6),
            "steps": len(self.context.trace),
            "trace": self.context.trace,
        }
