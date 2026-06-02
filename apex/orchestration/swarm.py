"""Parallel workers, verifier, and synthesizer three-stage delivery."""
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
    """Swarm mode — Parallel Workers -> Verifier -> Synthesizer"""

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
        """Execute a Swarm

        Args:
            goal: Swarm goal description
            workers: [(name, profile, task), ...]
            verifier: (name, profile) — verifier
            synthesizer: (name, profile) — synthesizer
            max_parallel: Maximum parallel workers
        """
        result = SwarmResult()

        # Phase 1: Parallel Workers
        print(f"\n{'='*50}")
        print(f"🚀 Apex Swarm: {goal}")
        print(f"{'='*50}")
        print(f"   Workers: {len(workers)}")
        if verifier:
            print(f"   Verifier: {verifier[0]}")
        if synthesizer:
            print(f"   Synthesizer: {synthesizer[0]}")
        print(f"{'='*50}\n")

        # Create Kanban tasks
        kanban_tasks = []
        for name, profile, task_desc in workers:
            t = self.kanban.create_task(
                title=f"[{name}] {task_desc[:50]}",
                assignee=name,
                description=task_desc,
                status=TASK_STATUS_READY,
            )
            kanban_tasks.append(t)

        # Parallel execution
        print("📋 Phase 1: Workers executing in parallel")
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
                    print(f"   ✅ {name} — Completed")
                except Exception as e:
                    result.worker_outputs.append({
                        "name": name,
                        "task_id": task_id,
                        "output": f"ERROR: {e}",
                    })
                    self.kanban.update_task(task_id, status=TASK_STATUS_FAILED, output=str(e))
                    print(f"   ❌ {name} — Failed: {e}")

        # Phase 2: Verifier
        if verifier and result.worker_outputs:
            print(f"\n🔍 Phase 2: Verifier ({verifier[0]})")
            print("-" * 40)
            name, profile = verifier
            agent = Agent(profile, api_key=self._get_api_key())
            verifier_task = f"""Verify the quality and completeness of the following work.
Project Goal: {goal}

Worker Outputs:
"""
            for wo in result.worker_outputs:
                verifier_task += f"""
--- {wo['name']}'s Output ---
{wo['output'][:2000]}
"""

            verifier_task += """
Please provide:
1. Quality score for each Worker output (1-10)
2. Issues found and improvement suggestions
3. Overall quality conclusion: Pass / Needs Revision / Fail
"""
            try:
                result.verifier_output = agent.run(verifier_task)
                print(f"   ✅ Verification completed")
            except Exception as e:
                result.verifier_output = f"Verification failed: {e}"
                print(f"   ❌ Verification failed: {e}")

        # Phase 3: Synthesizer
        if synthesizer:
            print(f"\n📦 Phase 3: Synthesizer ({synthesizer[0]})")
            print("-" * 40)
            name, profile = synthesizer
            agent = Agent(profile, api_key=self._get_api_key())
            synthesizer_task = f"""Please integrate the following work outputs into a complete deliverable.
Project Goal: {goal}

Worker Outputs:
"""
            for wo in result.worker_outputs:
                synthesizer_task += f"""
--- {wo['name']}'s Output ---
{wo['output'][:2000]}
"""

            if result.verifier_output:
                synthesizer_task += f"""
--- Verifier Feedback ---
{result.verifier_output[:2000]}
"""

            synthesizer_task += """
Please produce:
1. Integrated complete solution/deliverable
2. Explanation of relationships between modules
3. Next step recommendations
"""
            try:
                result.synthesizer_output = agent.run(synthesizer_task)
                print(f"   ✅ Synthesis completed")
            except Exception as e:
                result.synthesizer_output = f"Synthesis failed: {e}"
                print(f"   ❌ Synthesis failed: {e}")

        # Summary
        result.success = True
        print(f"\n{'='*50}")
        print(f"✅ Swarm complete! Total cost: ${result.total_cost:.4f}")
        print(f"{'='*50}")

        return result

    def _get_api_key(self) -> str:
        """Get API Key from environment"""
        import os
        return os.environ.get("DEEPSEEK_API_KEY", "")
