"""Apex — Core Agent Runtime
Each Agent is a persistent intelligent agent with its own Profile, Memory, and Skills.
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
    """Agent execution context"""
    session_id: str = ""
    task: str = ""
    messages: list[dict] = field(default_factory=list)
    trace: list[dict] = field(default_factory=list)
    cost: float = 0.0


class Agent:
    """A runnable Agent instance"""

    def __init__(
        self,
        profile: Profile,
        provider_name: str = None,
        api_key: str = None,
        self_healing: bool = False,
    ):
        self.profile = profile
        self.provider_name = provider_name or profile.model.default.split("-")[0]
        self.api_key = api_key
        self.self_healing = self_healing
        self._provider = None
        self.context = AgentContext()

    @property
    def provider(self):
        if self._provider is None:
            config = {"api_key": self.api_key}
            # Check if deepseek provider, has model prefix
            prov_name = self.provider_name
            if prov_name not in provider_registry.list():
                # Try matching - e.g. deepseek-v4-pro maps to deepseek
                for reg_name in provider_registry.list():
                    if prov_name.startswith(reg_name):
                        prov_name = reg_name
                        break
                else:
                    prov_name = "deepseek"  # default
            self._provider = provider_registry.get(prov_name, config)
        return self._provider

    def run(self, task: str, heal: bool = False, **kwargs) -> str:
        """Execute a task"""
        # Self-healing: delegate to SelfHealingExecutor when enabled
        if heal or self.self_healing:
            from apex.orchestration.healing import SelfHealingExecutor
            executor = SelfHealingExecutor(self)
            healer_result = executor.run(task, **kwargs)
            if healer_result.success:
                return healer_result.final_output
            else:
                raise RuntimeError(healer_result.final_output)

        self.context.task = task
        self.context.messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": task},
        ]

        self._trace("start", f"Starting task: {task}")
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
            self._trace("complete", f"Completed (${self.provider.estimate_cost(response):.6f})")

            # Skill evolution (if auto-improve is enabled)
            if self.profile.auto_improve:
                self._auto_learn(task, response.content)

            # Record to evolution engine
            self._record_evolution(task, response.content, True, start_time)

            return response.content

        except Exception as e:
            success = False
            error_msg = str(e)
            # Try fallback model
            if self.profile.model.fallback:
                self._trace("fallback", f"Primary model failed, falling back to {self.profile.model.fallback}")
                try:
                    response = self.provider.chat(
                        self.context.messages,
                        model=self.profile.model.fallback,
                        **kwargs,
                    )
                    self.context.cost += self.provider.estimate_cost(response)
                    self._trace("complete", f"Completed (fallback) (${self.provider.estimate_cost(response):.6f})")
                    self._record_evolution(task, response.content, True, start_time)
                    return response.content
                except Exception as e2:
                    self._trace("error", f"Fallback also failed: {e2}")
                    error_msg = f"{e2}"
            self._record_evolution(task, error_msg, False, start_time, error=error_msg)
            raise

    def _record_evolution(self, task: str, output: str, success: bool,
                          start_time: float, error: str = ""):
        """Record execution to the evolution engine"""
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
            pass  # Evolution record failure does not affect main flow

    def chat(self, messages: list[dict], **kwargs) -> LLMResponse:
        """Direct chat interface (for multi-Agent conversations)"""
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
            f"You are {p.soul.role or p.display}.",
        ]
        if p.soul.expertise:
            parts.append(f"Your expertise: {', '.join(p.soul.expertise)}.")
        if p.soul.personality:
            parts.append(f"Personality: {p.soul.personality}.")
        if p.soul.communication:
            parts.append(f"Communication style: {p.soul.communication}.")
        if p.skills:
            parts.append(f"Skill package: {', '.join(p.skills)}.")
        parts.append("\nPlease complete tasks in a professional, direct, and actionable manner.")
        return "\n".join(parts)

    def _trace(self, event: str, detail: str):
        self.context.trace.append({"event": event, "detail": detail, "cost": self.context.cost})

    def _auto_learn(self, task: str, result: str):
        """Auto-learn from execution (simplified version)"""
        # Phase 2: Implement skill evolution
        pass

    def summarize(self) -> dict:
        """Current session summary"""
        return {
            "agent": self.profile.name,
            "role": self.profile.soul.role,
            "task": self.context.task,
            "total_cost": round(self.context.cost, 6),
            "steps": len(self.context.trace),
            "trace": self.context.trace,
        }
