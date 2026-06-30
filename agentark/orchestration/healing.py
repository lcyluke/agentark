"""Three-strike self-healing workflow with knowledge accumulation and auto-degradation."""
from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from typing import Optional

from agentark.core.runtime import Agent
from agentark.core.profile import Profile
from agentark.core.knowledge import KnowledgeGraph
from agentark.core.evolution import EvolutionEngine, ExecutionRecord
from agentark.orchestration.kanban import Kanban, TASK_STATUS_FAILED


@dataclass
class HealingResult:
    success: bool = False
    attempts: int = 0
    errors: list[str] = field(default_factory=list)
    fixes: list[str] = field(default_factory=list)
    final_output: str = ""
    strategy_used: str = "direct"
    model_downgraded: bool = False


class SelfHealingExecutor:
    """Self-Healing Executor v2 — Full lifecycle"""

    MAX_ATTEMPTS = 3
    STRATEGIES = [
        "direct",           # First: direct retry
        "switch_model",     # Second: switch model/parameters
        "simplify_task",    # Third: simplify task then retry
    ]

    def __init__(self, agent: Agent, kanban: Kanban = None):
        self.agent = agent
        self.kanban = kanban
        self.kg = KnowledgeGraph()
        self.evolution = EvolutionEngine()
        self._healer = None

    def _get_healer(self) -> Agent:
        if not self._healer:
            from agentark.core.templates import get_template
            template = get_template("devops")
            if template:
                healer_profile = template.to_profile("healer")
            else:
                from agentark.core.profile import Profile, SoulConfig
                healer_profile = Profile(
                    name="healer",
                    soul=SoulConfig(
                        role="Fault Repair Expert",
                        expertise=["debugging", "error-analysis", "system-recovery", "root-cause"],
                        personality="Calm, systematic thinker, never gives up",
                    ),
                )
            self._healer = Agent(healer_profile)
        return self._healer

    def run(self, task: str, max_attempts: int = MAX_ATTEMPTS, **kwargs) -> HealingResult:
        """Self-healing execution — Three-strike rule"""
        result = HealingResult()
        start_time = time.time()
        strategy_idx = 0

        # 1. Check knowledge graph for known fixes
        kg_hint = self.kg.query(f"Fix {task[:60]}")
        if kg_hint.confidence > 0.5:
            result.fixes.append(f"📚 Knowledge Graph Suggestion: {kg_hint.answer[:200]}")

        for attempt in range(1, max_attempts + 1):
            result.attempts = attempt
            strategy = self.STRATEGIES[min(strategy_idx, len(self.STRATEGIES) - 1)]
            result.strategy_used = strategy

            try:
                # Apply strategy
                if strategy == "direct":
                    output = self.agent.run(task, **kwargs)

                elif strategy == "switch_model":
                    # Switch to fallback model
                    fallback = self.agent.profile.model.fallback
                    output = self.agent.run(task, model=fallback, **kwargs)
                    result.model_downgraded = True

                elif strategy == "simplify_task":
                    # Simplify task
                    healer = self._get_healer()
                    simplified = healer.run(
                        f"Break down the following task into simpler sub-tasks (one thing at a time):\n\n{task}"
                    )
                    output = self.agent.run(f"Please complete the following simplified task:\n{simplified}", **kwargs)

                # Success!
                result.success = True
                result.final_output = output
                duration_ms = int((time.time() - start_time) * 1000)

                # Record to evolution engine
                self._record_evolution(task, output, True, duration_ms, strategy)
                return result

            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                result.errors.append(error_msg)
                strategy_idx += 1

                # Auto-diagnose
                fix = self._diagnose(error_msg, task, attempt)
                if fix:
                    result.fixes.append(fix)

                # Knowledge graph accumulation
                self.kg.learn_from_experience(
                    agent_name=self.agent.profile.name,
                    task=task,
                    error=error_msg,
                    fix=fix,
                )

                # Update Kanban
                if self.kanban:
                    tasks = self.kanban.list_tasks()
                    for t in tasks:
                        if task[:30] in t.title:
                            self.kanban.update_task(t.id, status=f"healing_a{attempt}")
                            break

                time.sleep(1)

        # Three strikes out
        result.success = False
        duration_ms = int((time.time() - start_time) * 1000)
        result.final_output = (
            f"❌ Execution failed (auto-fix attempted {max_attempts} times, all ineffective)\n"
            f"Last error: {result.errors[-1] if result.errors else 'Unknown'}\n"
            f"Strategies attempted: {', '.join(self.STRATEGIES[:strategy_idx+1])}\n"
            f"Suggestion: Contact human for confirmation"
        )

        # Record failure to evolution engine
        self._record_evolution(task, result.final_output, False, duration_ms, "failed")

        # Update Kanban as failed
        if self.kanban:
            tasks = self.kanban.list_tasks()
            for t in tasks:
                if task[:30] in t.title:
                    self.kanban.update_task(t.id, status=TASK_STATUS_FAILED, output=result.final_output)
                    break

        return result

    def _diagnose(self, error: str, task: str, attempt: int) -> str:
        """Diagnose error — check KG first, then ask LLM"""
        # Check knowledge graph first
        kg_result = self.kg.query(f"How to fix {error[:60]}")
        if kg_result.confidence > 0.5 and "not found" not in kg_result.answer.lower():
            return f"📚 Knowledge Graph: {kg_result.answer[:300]}"

        # Then ask LLM
        healer = self._get_healer()
        try:
            diag_prompt = f"""An Agent encountered an error while executing a task. Please diagnose and provide the most direct fix.

Task: {task[:200]}
Error: {error[:300]}
Attempt #{attempt}

Output format (concise):
Root Cause: ...
Fix: ...
"""
            return healer.run(diag_prompt)[:500]
        except Exception:
            return f"Simple retry (Attempt #{attempt})"

    def _record_evolution(self, task: str, output: str, success: bool,
                          duration_ms: int, strategy: str):
        """Record to evolution engine"""
        record = ExecutionRecord(
            agent_name=self.agent.profile.name,
            task=task,
            task_type="healing" if "fix" in task.lower() else "general",
            prompt=task[:200],
            output=output[:500],
            success=success,
            duration_ms=duration_ms,
            quality_score=0.8 if success else 0.2,
            error="" if success else (output[:200] if not success else ""),
        )
        self.evolution.record(record)
