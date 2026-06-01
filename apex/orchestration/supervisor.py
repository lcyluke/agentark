"""Apex — Supervisor / Hierarchy Mode
Enterprise delegation and review workflow:
1. Decompose — Supervisor breaks task into sub-tasks
2. Delegate — Assign each sub-task to a worker agent
3. Execute — Workers run in parallel (ThreadPoolExecutor)
4. Review — Supervisor reviews each output (approve/revision/reject)
5. Iterate — Rejected/revision items go back to worker with feedback (max 2 rounds)
6. Merge — Approved outputs merged into final deliverable
"""
from __future__ import annotations

import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from apex.core.runtime import Agent
from apex.core.profile import Profile, ProfileManager


# ─── Status Enum ──────────────────────────────────────────────────────────────

class WorkStatus(str, Enum):
    """Status of a WorkItem through the supervisor pipeline."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REVISION = "revision"
    REJECTED = "rejected"


# ─── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class WorkItem:
    """A single sub-task unit managed by the Supervisor.

    Attributes:
        id: Unique identifier for the work item.
        title: Short description of the sub-task.
        description: Detailed instructions for the worker agent.
        assignee: Name/profile reference of the assigned worker agent.
        status: Current lifecycle status.
        output: Raw output produced by the worker.
        review_feedback: Feedback from the supervisor review.
        revision_count: How many times this item has been sent back for revision.
        max_revisions: Maximum allowed revision rounds (default 2).
    """
    id: str
    title: str
    description: str
    assignee: str
    status: WorkStatus = WorkStatus.PENDING
    output: str = ""
    review_feedback: str = ""
    revision_count: int = 0
    max_revisions: int = 2

    @property
    def is_final(self) -> bool:
        """Whether this item has reached a terminal status."""
        return self.status in (WorkStatus.APPROVED, WorkStatus.REJECTED)


@dataclass
class SupervisorResult:
    """The final result produced by a Supervisor run.

    Attributes:
        goal: The original high-level goal / task description.
        work_items: All WorkItem records produced during the run.
        approved_items: Items that passed supervisor review.
        rejected_items: Items that were ultimately rejected.
        merged_output: The final merged deliverable from all approved items.
        iteration_log: Chronological log of review/iteration events.
        total_cost: Cumulative cost estimate across all agent calls.
        success: Whether the overall workflow completed with any approved output.
    """
    goal: str
    work_items: list[WorkItem] = field(default_factory=list)
    approved_items: list[WorkItem] = field(default_factory=list)
    rejected_items: list[WorkItem] = field(default_factory=list)
    merged_output: str = ""
    iteration_log: list[dict] = field(default_factory=list)
    total_cost: float = 0.0
    success: bool = False


# ─── Supervisor ───────────────────────────────────────────────────────────────

class Supervisor:
    """Enterprise Supervisor agent — Hierarchy Mode orchestrator.

    Breaks a high-level goal into sub-tasks, delegates them to worker agents
    in parallel, reviews each output with approve/revision/reject decisions,
    iterates on rejected/revision items with feedback (up to ``max_revisions``
    rounds), and finally merges all approved outputs into a single deliverable.
    """

    def __init__(
        self,
        supervisor_profile: Profile,
        worker_profiles: dict[str, Profile],
        max_parallel: int = 3,
        max_revisions: int = 2,
    ):
        """Initialise the Supervisor.

        Args:
            supervisor_profile: Profile for the supervising agent (the reviewer).
            worker_profiles: Mapping of worker name -> Profile for each worker.
            max_parallel: Maximum number of worker agents to run in parallel.
            max_revisions: Maximum revision rounds per WorkItem (default 2).
        """
        self.supervisor_agent = Agent(supervisor_profile)
        self.worker_profiles = worker_profiles
        self.max_parallel = max_parallel
        self.max_revisions = max_revisions
        self._iteration_log: list[dict] = []
        self._total_cost: float = 0.0

    # ── Public API ────────────────────────────────────────────────────────

    def run(self, goal: str) -> SupervisorResult:
        """Execute the full supervisor workflow.

        Steps:
            1. Decompose  —  Supervisor breaks *goal* into sub-tasks.
            2. Delegate   —  Each sub-task is assigned to a worker agent.
            3. Execute    —  Workers run in parallel.
            4. Review     —  Supervisor reviews each output.
            5. Iterate    —  Rejected/revision items go back with feedback.
            6. Merge      —  Approved outputs are merged into a final deliverable.

        Args:
            goal: The high-level task or project goal.

        Returns:
            A SupervisorResult with all work items, logs, and the merged output.
        """
        self._log("start", f"Supervisor workflow started for: {goal}")

        # Step 1: Decompose
        sub_tasks = self._decompose(goal)
        work_items = [
            WorkItem(
                id=f"task_{i}",
                title=st["title"],
                description=st["description"],
                assignee=st.get("assignee", list(self.worker_profiles.keys())[0]),
                max_revisions=self.max_revisions,
            )
            for i, st in enumerate(sub_tasks)
        ]
        self._log("decompose", f"Decomposed goal into {len(work_items)} sub-tasks")

        # Step 2-3: Delegate & Execute (parallel with review loop)
        self._execute_work_items(work_items, goal)

        # Step 6: Merge
        merged = self._merge(work_items, goal)

        # Assemble result
        approved = [w for w in work_items if w.status == WorkStatus.APPROVED]
        rejected = [w for w in work_items if w.status == WorkStatus.REJECTED]

        result = SupervisorResult(
            goal=goal,
            work_items=work_items,
            approved_items=approved,
            rejected_items=rejected,
            merged_output=merged,
            iteration_log=self._iteration_log,
            total_cost=round(self._total_cost, 6),
            success=len(approved) > 0,
        )

        self._log("complete", f"Workflow complete. Approved: {len(approved)}, "
                  f"Rejected: {len(rejected)}, Cost: ${result.total_cost:.6f}")
        return result

    # ── Step 1: Decompose ─────────────────────────────────────────────────

    def _decompose(self, goal: str) -> list[dict]:
        """Ask the supervisor agent to decompose *goal* into structured sub-tasks.

        Returns:
            A list of dicts with keys: ``title``, ``description``, ``assignee``.
        """
        prompt = f"""You are a senior project supervisor. Decompose the following goal into
well-defined sub-tasks that can be worked on independently by different agents.

Goal: {goal}

Available workers: {', '.join(self.worker_profiles.keys())}

For each sub-task, provide:
- title: Short name for the sub-task
- description: Detailed instructions for the worker agent (be specific and actionable)
- assignee: The worker name best suited for this sub-task

Output ONLY a valid JSON array of objects with keys "title", "description", and "assignee".
Example:
[
  {{
    "title": "Design database schema",
    "description": "Design the PostgreSQL schema including tables, indices, and relationships for ...",
    "assignee": "backend"
  }}
]"""

        raw = self.supervisor_agent.run(prompt)
        self._track_cost(self.supervisor_agent)

        sub_tasks = self._parse_json_list(raw)
        if not sub_tasks:
            # Fallback: create one task per worker
            sub_tasks = [
                {
                    "title": f"Task for {name}",
                    "description": goal,
                    "assignee": name,
                }
                for name in self.worker_profiles
            ]
        return sub_tasks

    # ── Steps 2-5: Execute, Review, Iterate ───────────────────────────────

    def _execute_work_items(self, work_items: list[WorkItem], goal: str) -> None:
        """Run the parallel execute-review-iterate loop until all items are final."""
        pending = [w for w in work_items if not w.is_final]

        while pending:
            # Mark as in_progress
            for w in pending:
                w.status = WorkStatus.IN_PROGRESS

            # Parallel execution
            with ThreadPoolExecutor(max_workers=min(self.max_parallel, len(pending))) as executor:
                future_map = {}
                for w in pending:
                    profile = self.worker_profiles.get(w.assignee)
                    if not profile:
                        w.output = f"ERROR: No profile found for worker '{w.assignee}'"
                        w.status = WorkStatus.REJECTED
                        self._log("error", f"No profile for worker '{w.assignee}' on task '{w.title}'")
                        continue
                    agent = Agent(profile)
                    worker_prompt = self._build_worker_prompt(w, goal)
                    future = executor.submit(agent.run, worker_prompt)
                    future_map[future] = w

                for future in as_completed(future_map):
                    w = future_map[future]
                    try:
                        w.output = future.result()
                        self._track_cost(Agent(self.worker_profiles[w.assignee]))
                        w.status = WorkStatus.PENDING_REVIEW
                        self._log("execute", f"Task '{w.title}' completed by {w.assignee}")
                    except Exception as e:
                        w.output = f"EXECUTION_ERROR: {e}"
                        w.status = WorkStatus.REJECTED
                        self._log("error", f"Task '{w.title}' failed execution: {e}")

            # Review all pending_review items
            for w in pending:
                if w.status != WorkStatus.PENDING_REVIEW:
                    continue
                decision = self._review_item(w, goal)
                w.review_feedback = decision.get("feedback", "")
                verdict = decision.get("verdict", "revision").lower()

                if verdict == "approved":
                    w.status = WorkStatus.APPROVED
                    self._log("approve", f"Task '{w.title}' approved")
                elif verdict == "revision" and w.revision_count < w.max_revisions:
                    w.revision_count += 1
                    w.status = WorkStatus.REVISION
                    self._log("revision", f"Task '{w.title}' sent for revision "
                              f"(round {w.revision_count}/{w.max_revisions})")
                else:
                    w.status = WorkStatus.REJECTED
                    self._log("reject", f"Task '{w.title}' rejected after "
                              f"{w.revision_count} revision(s)")

            # Rebuild pending list for next iteration
            pending = [w for w in work_items if w.status in (
                WorkStatus.REVISION, WorkStatus.IN_PROGRESS
            )]

    # ── Step 4: Review ────────────────────────────────────────────────────

    def _review_item(self, item: WorkItem, goal: str) -> dict:
        """Ask the supervisor agent to review a single WorkItem's output.

        Returns:
            Dict with keys ``verdict`` (approved/revision/rejected) and ``feedback``.
        """
        revision_history = ""
        if item.revision_count > 0:
            revision_history = (
                f"\nPrevious revision round: {item.revision_count}\n"
                f"Previous feedback: {item.review_feedback}\n"
            )

        prompt = f"""You are a strict project supervisor reviewing a worker's output.

Goal: {goal}

Sub-task: {item.title}
Description: {item.description}
Worker: {item.assignee}

Worker Output:
--- BEGIN OUTPUT ---
{item.output}
--- END OUTPUT ---
{revision_history}

Review the output carefully. Decide one of the following:
- "approved": The output meets requirements and can be merged as-is.
- "revision": The output needs minor corrections or improvements. Provide specific, actionable feedback.
- "rejected": The output is fundamentally wrong or unusable and should be discarded.

Output ONLY a valid JSON object with keys "verdict" (string) and "feedback" (string).
Example:
{{"verdict": "revision", "feedback": "The database schema is missing foreign key constraints on the orders table."}}"""

        raw = self.supervisor_agent.run(prompt)
        self._track_cost(self.supervisor_agent)

        decision = self._parse_json(raw)
        if not decision or "verdict" not in decision:
            decision = {"verdict": "revision", "feedback": "Review parsing failed. Please revise."}
        return decision

    # ── Step 6: Merge ─────────────────────────────────────────────────────

    def _merge(self, work_items: list[WorkItem], goal: str) -> str:
        """Merge all approved work item outputs into a single deliverable."""
        approved = [w for w in work_items if w.status == WorkStatus.APPROVED]
        if not approved:
            return "No approved outputs to merge."

        if len(approved) == 1:
            return approved[0].output

        outputs_section = "\n\n".join(
            f"=== {w.title} (by {w.assignee}) ===\n{w.output}"
            for w in approved
        )

        prompt = f"""You are a senior project integrator. Merge the following approved work
outputs into a single coherent deliverable.

Goal: {goal}

Approved Sub-task Outputs:
{outputs_section}

Produce a consolidated deliverable that:
1. Combines all contributions into a logical, well-structured document
2. Removes duplication while preserving all valuable content
3. Maintains consistent language and formatting throughout
4. Includes a brief summary of what was produced and any recommended next steps

Output the final merged deliverable only."""

        merged = self.supervisor_agent.run(prompt)
        self._track_cost(self.supervisor_agent)
        return merged

    # ── Helpers ───────────────────────────────────────────────────────────

    def _build_worker_prompt(self, item: WorkItem, goal: str) -> str:
        """Build the prompt sent to a worker agent for a given WorkItem."""
        revision_context = ""
        if item.revision_count > 0 and item.review_feedback:
            revision_context = (
                f"\n\n--- REVISION FEEDBACK (Round {item.revision_count}) ---\n"
                f"{item.review_feedback}\n\n"
                f"Please address the feedback above in your revised output. "
                f"Do NOT repeat content unchanged — focus on fixing the issues raised."
            )

        return f"""You are a worker agent contributing to the following project goal:

Goal: {goal}

Your sub-task: {item.title}
Instructions: {item.description}
{revision_context}

Please deliver a complete, high-quality output for your assigned sub-task. Be specific,
professional, and actionable."""

    def _track_cost(self, agent: Agent) -> None:
        """Accumulate cost from an agent's context after a run."""
        self._total_cost += agent.context.cost

    def _log(self, event: str, detail: str) -> None:
        """Append a structured entry to the iteration log."""
        self._iteration_log.append({"event": event, "detail": detail})

    # ── JSON Parsing Helpers ──────────────────────────────────────────────

    @staticmethod
    def _parse_json(raw: str) -> Optional[dict]:
        """Attempt to parse a JSON object from raw text (handles mark fences)."""
        cleaned = raw.strip()
        # Strip common markdown code fences
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _parse_json_list(raw: str) -> list[dict]:
        """Attempt to parse a JSON array from raw text (handles mark fences)."""
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()
        try:
            result = json.loads(cleaned)
            if isinstance(result, list):
                return result
            return []
        except json.JSONDecodeError:
            return []
