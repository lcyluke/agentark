"""Apex — Skill Evaluation Pipeline.

Automated skill assessment engine. Scans completed tasks, PRs, and sessions
for evidence, then runs the Skill Evaluator's methodology to grade agents.

This is what the skill-evaluator Hermes profile calls.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from apex.interface.skill_registry import (
    get_registry, SkillRegistry, LEVELS, LEVEL_LABELS,
    MatchResult, TASK_DIFFICULTY_LEVELS,
)


@dataclass
class EvalResult:
    """Result of a single skill evaluation."""
    agent_name: str
    skill_name: str
    current_level: str
    recommended_level: str
    confidence: float
    evidence_added: int
    action: str  # upgrade, downgrade, maintain, review
    reason: str


@dataclass
class EvalReport:
    """Full evaluation cycle report."""
    timestamp: float
    agents_evaluated: int
    skills_evaluated: int
    upgrades: list[EvalResult]
    downgrades: list[EvalResult]
    maintains: list[EvalResult]
    reviews: list[EvalResult]
    errors: list[str]

    def summary(self) -> str:
        total_changes = len(self.upgrades) + len(self.downgrades)
        return (
            f"📊 Evaluation Report\n"
            f"Agents: {self.agents_evaluated} | Skills: {self.skills_evaluated}\n"
            f"Upgrades: {len(self.upgrades)} | Downgrades: {len(self.downgrades)} "
            f"| Maintain: {len(self.maintains)} | Review: {len(self.reviews)}"
        )


def evaluate_completed_task(task_data: dict, registry: SkillRegistry = None) -> Optional[EvalResult]:
    """Evaluate a single completed task and assess skill demonstration.

    Args:
        task_data: Task dict with id, assignee, title, description,
                   completion_notes, actual_hours, etc.
        registry: SkillRegistry instance.

    Returns:
        EvalResult if skill evidence found, None otherwise.
    """
    if registry is None:
        registry = get_registry()

    agent_name = task_data.get("assignee", "")
    title = task_data.get("title", "")
    description = task_data.get("description", "")
    completion_notes = task_data.get("completion_notes", "")
    task_id = task_data.get("id", "")
    priority = task_data.get("priority", 2)

    if not agent_name:
        return None

    # Infer required skills from the task description
    required_skills = registry._infer_skills(f"{title} {description} {completion_notes}")
    if not required_skills:
        return None

    # Determine task difficulty from priority
    # priority 0=urgent(L4), 1=high(L3), 2=medium(L2), 3=low(L1)
    difficulty_map = {0: "L4", 1: "L3", 2: "L2", 3: "L1"}
    task_difficulty = difficulty_map.get(priority, "L2")
    task_diff_idx = LEVELS.index(task_difficulty)

    result = None
    best_skill = None
    best_level_gain = -1

    for sname in required_skills[:3]:  # Check top 3 inferred skills
        current_level = registry.get_skill_level(agent_name, sname)
        if current_level is None:
            continue

        current_idx = LEVELS.index(current_level) if current_level in LEVELS else 0
        level_gap = task_diff_idx - current_idx

        # If task difficulty is at or below agent's current level, add evidence
        # but don't upgrade (maintainance)
        if level_gap <= 0:
            # Add evidence — task completed at expected level
            registry.add_evidence(agent_name, sname, {
                "type": "task",
                "ref": f"Task:{task_id}",
                "description": f"Completed task: {title[:80]}",
                "date": time.strftime("%Y-%m-%d"),
                "assessed_by": "auto",
            })
            best_skill = EvalResult(
                agent_name=agent_name,
                skill_name=sname,
                current_level=current_level,
                recommended_level=current_level,
                confidence=0.6,
                evidence_added=1,
                action="maintain",
                reason=f"Task completed at current skill level ({current_level})",
            )

        # If task difficulty is ABOVE agent's current level AND completed
        # This is a skill demonstration worthy of upgrade consideration
        elif level_gap > 0 and level_gap > best_level_gain:
            best_level_gain = level_gap
            # Register the higher-level evidence
            registry.add_evidence(agent_name, sname, {
                "type": "task",
                "ref": f"Task:{task_id}",
                "description": f"Demonstrated {task_difficulty}-level skill: {title[:60]}",
                "date": time.strftime("%Y-%m-%d"),
                "assessed_by": "auto",
            })

            # Check if cumulative evidence warrants upgrade
            all_skills_dict = registry._data.get("agents", {}).get(agent_name, {}).get("skills", {})
            entry = all_skills_dict.get(sname, {})
            evidence_list = entry.get("evidence", [])
            
            # Count task evidences at or above recommended level
            high_level_tasks = sum(
                1 for ev in evidence_list
                if ev.get("type") == "task"
            )

            recommended = current_level
            # L1→L2: 2 tasks minimum
            if current_level == "L1" and high_level_tasks >= 2:
                recommended = "L2"
            # L2→L3: 3 tasks at difficulty L3+
            elif current_level == "L2" and task_diff_idx >= 2 and high_level_tasks >= 3:
                recommended = "L3"
            # L3→L4: 2 tasks at L4+ 
            elif current_level == "L3" and task_diff_idx >= 3 and high_level_tasks >= 2:
                recommended = "L4"

            confidence = min(0.5 + 0.1 * high_level_tasks, 0.9)

            best_skill = EvalResult(
                agent_name=agent_name,
                skill_name=sname,
                current_level=current_level,
                recommended_level=recommended,
                confidence=round(confidence, 2),
                evidence_added=1,
                action="upgrade" if recommended != current_level else "maintain",
                reason=f"{high_level_tasks} task(s) at ≥{task_difficulty}. " +
                       (f"Recommend {current_level}→{recommended}" if recommended != current_level
                        else f"Need more evidence for {current_level}→{LEVELS[current_idx+1]}"),
            )

    return best_skill


def run_evaluation(registry: SkillRegistry = None) -> EvalReport:
    """Run a full evaluation cycle across all agents and their completed tasks.

    Scans ops.db for completed/verified tasks and evaluates them.
    
    Returns:
        EvalReport with all results.
    """
    if registry is None:
        registry = get_registry()

    report = EvalReport(
        timestamp=time.time(),
        agents_evaluated=0,
        skills_evaluated=0,
        upgrades=[],
        downgrades=[],
        maintains=[],
        reviews=[],
        errors=[],
    )

    try:
        # Get all completed tasks
        from apex.orchestration.task_manager import get_task_manager, WorkflowStatus
        tm = get_task_manager()
        completed_tasks = tm.list_tasks(workflow_status="completed")

        # Also get verified and closed tasks
        verified_tasks = tm.list_tasks(workflow_status="verified")
        closed_tasks = tm.list_tasks(workflow_status="closed")

        all_tasks = completed_tasks + verified_tasks + closed_tasks
        agents_seen = set()

        for task in all_tasks:
            try:
                task_dict = task.to_dict()
                agent_name = task_dict.get("assignee", "")
                if agent_name:
                    agents_seen.add(agent_name)

                result = evaluate_completed_task(task_dict, registry)
                if result:
                    report.skills_evaluated += 1
                    if result.action == "upgrade":
                        report.upgrades.append(result)
                    elif result.action == "downgrade":
                        report.downgrades.append(result)
                    elif result.action == "maintain":
                        report.maintains.append(result)
                    elif result.action == "review":
                        report.reviews.append(result)

            except Exception as e:
                report.errors.append(f"Task {getattr(task, 'id', '?')}: {e}")

        report.agents_evaluated = len(agents_seen)

        # Apply auto-approved upgrades (L1→L2 auto)
        for result in report.upgrades:
            if result.current_level == "L1" and result.recommended_level == "L2":
                registry.assess_skill(
                    agent_name=result.agent_name,
                    skill_name=result.skill_name,
                    new_level=result.recommended_level,
                    assessed_by="skill-evaluator(auto)",
                    confidence=result.confidence,
                )

    except Exception as e:
        report.errors.append(f"Evaluation pipeline failed: {e}")

    return report


def generate_eval_summary(report: EvalReport) -> str:
    """Generate a human-readable summary of evaluation results."""
    lines = [
        "=" * 60,
        "📊 SKILL EVALUATION REPORT",
        "=" * 60,
        f"Time: {time.strftime('%Y-%m-%d %H:%M', time.localtime(report.timestamp))}",
        f"Agents evaluated: {report.agents_evaluated}",
        f"Skills assessed: {report.skills_evaluated}",
        "",
    ]

    if report.upgrades:
        lines.append(f"🔼 UPGRADES ({len(report.upgrades)})")
        lines.append("-" * 40)
        for r in report.upgrades:
            auto_tag = " [auto] " if r.current_level == "L1" else " [pending] "
            lines.append(f"  {r.agent_name}.{r.skill_name}: {r.current_level} → {r.recommended_level}{auto_tag}")
            lines.append(f"    {r.reason}")
        lines.append("")

    if report.downgrades:
        lines.append(f"🔽 DOWNGRADES ({len(report.downgrades)})")
        lines.append("-" * 40)
        for r in report.downgrades:
            lines.append(f"  {r.agent_name}.{r.skill_name}: {r.current_level} → {r.recommended_level}")
        lines.append("")

    if report.maintains:
        lines.append(f"✅ MAINTAINED ({len(report.maintains)})")
        lines.append("-" * 40)
        for r in report.maintains[:5]:
            lines.append(f"  {r.agent_name}.{r.skill_name}: {r.current_level} (evidence added)")
        if len(report.maintains) > 5:
            lines.append(f"  ... and {len(report.maintains) - 5} more")
        lines.append("")

    if report.reviews:
        lines.append(f"🔍 NEEDS REVIEW ({len(report.reviews)})")
        lines.append("-" * 40)
        for r in report.reviews:
            lines.append(f"  {r.agent_name}.{r.skill_name}: {r.reason}")
        lines.append("")

    if report.errors:
        lines.append(f"❌ ERRORS ({len(report.errors)})")
        lines.append("-" * 40)
        for e in report.errors[:5]:
            lines.append(f"  {e}")
        if len(report.errors) > 5:
            lines.append(f"  ... and {len(report.errors) - 5} more")
        lines.append("")

    # Summary stats
    lines.append("=" * 60)
    lines.append(f"Total changes: {len(report.upgrades) + len(report.downgrades)}")
    lines.append(f"  Auto-approved: {sum(1 for r in report.upgrades if r.current_level == 'L1')}")
    lines.append(f"  Pending Origin review: {sum(1 for r in report.upgrades if r.current_level != 'L1')}")
    lines.append("=" * 60)

    return "\n".join(lines)
