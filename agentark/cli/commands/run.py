"""Apex — run command"""
from __future__ import annotations

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from agentark.core.profile import ProfileManager, AGENTARK_HOME
from agentark.core.runtime import Agent
from agentark.orchestration.swarm import Swarm
from agentark.orchestration.kanban import Kanban


def run_task(task: str, profile_name: str, model: str, swarm: bool, workers: int, console: Console):
    """Execute a task"""

    if not task:
        console.print("[red]✗ Please provide a task description[/]")
        return

    pm = ProfileManager()
    try:
        profile = pm.load(profile_name)
    except FileNotFoundError:
        console.print(f"[red]✗ Profile '{profile_name}' does not exist. Create one with 'apex init' first[/]")
        return

    # Simple single-Agent mode
    if not swarm:
        agent = Agent(profile)
        console.print(f"\n[bold]🤖 Agent: {profile.display or profile.name}[/]")
        console.print(f"   Model: {model or profile.model.default}")
        console.print(f"   Task: {task[:80]}{'...' if len(task) > 80 else ''}\n")

        try:
            result = agent.run(task, model=model) if model else agent.run(task)
            console.print(Panel(result, title=f"✅ {profile.name} completed", border_style="green"))
            console.print(f"[dim]Cost: ${agent.context.cost:.6f} | Steps: {len(agent.context.trace)}[/]")
        except Exception as e:
            console.print(Panel(str(e), title="❌ Execution failed", border_style="red"))

    else:
        # Swarm mode — automatically decompose the task
        console.print(f"\n[bold]🚀 Swarm Mode: {task[:60]}...[/]")
        console.print(f"   Workers: {workers}")

        # Use AI to automatically decompose the task
        planner = Agent(profile)
        decomposition_prompt = f"""Please decompose the following task into {workers} parallel sub-tasks.
Each sub-task should be independent, specific, and actionable.

Task: {task}

Please output in the following format (JSON):
{{
  "goal": "Overall goal description",
  "workers": [
    {{"name": "worker-1", "task": "Sub-task 1 description", "skills": ["Required skill 1"]}},
    {{"name": "worker-2", "task": "Sub-task 2 description", "skills": ["Required skill 1"]}}
  ],
  "verifier_prompt": "What the verifier should check...",
  "synthesizer_prompt": "What the synthesizer should integrate..."
}}

Only output JSON, no other content."""

        try:
            plan_text = planner.run(decomposition_prompt)
            # Parse JSON
            import json
            import re
            json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
            else:
                console.print("[red]✗ Failed to parse task decomposition result[/]")
                return

            # Create Worker Profiles
            worker_configs = []
            for w in plan.get("workers", []):
                w_profile = pm.create_default(
                    name=w["name"],
                    role=w["name"],
                    expertise=w.get("skills", []),
                )
                worker_configs.append((w["name"], w_profile, w["task"]))

            # Verifier, Synthesizer
            verifier = ("verifier", pm.create_default("verifier", role="Quality Verifier"))
            synthesizer = ("synthesizer", pm.create_default("synthesizer", role="Result Synthesizer"))

            # Execute Swarm
            kanban = Kanban(AGENTARK_HOME / "kanban.db")
            swarm = Swarm(kanban)

            result = swarm.run(
                goal=plan.get("goal", task),
                workers=worker_configs,
                verifier=verifier,
                synthesizer=synthesizer,
                max_parallel=workers,
            )

            # Output result
            if result.success:
                if result.synthesizer_output:
                    console.print(Panel(
                        result.synthesizer_output[:3000],
                        title="📦 Swarm Deliverables",
                        border_style="green",
                    ))
            else:
                console.print(f"[red]✗ Swarm execution failed: {result.error}[/]")

        except Exception as e:
            console.print(f"[red]✗ Swarm execution failed: {e}[/]")
            import traceback
            console.print(traceback.format_exc()[:500])
