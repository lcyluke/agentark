"""Apex PM Engine — project scheduling, critical path, agent assignment.

Core algorithms:
  - Critical Path Method (CPM): longest dependency chain → min project duration
  - Task scheduling: serial/parallel aware, agent-skill matching
  - Agent health: heartbeat + skill level + load assessment

Data flows:
  agent_monitor.json  ─┐
  badminton_tasks.json ─┤
  sprints.json         ─┼──→ PM Engine ──→ dashboard / schedule / assign
  agent skills DB      ─┘
"""

from __future__ import annotations

import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

TZ = timezone(timedelta(hours=8))
FINOPs = Path.home() / "finopsai" / "data"

# ─── Data Models ─────────────────────────────────────────────────


@dataclass
class Task:
    """A unit of work with dependencies, estimates, and assignment."""

    id: str
    name: str
    status: str = "pending"  # pending | in_progress | completed | blocked
    assignee: str = ""
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    dependencies: list[str] = field(default_factory=list)
    priority: int = 2  # 0=P0 critical, 1=P1 high, 2=P2 normal
    project: str = ""
    milestone: str = ""
    skills_required: list[str] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""

    @property
    def is_ready(self) -> bool:
        return self.status == "pending"

    @property
    def is_blocked(self) -> bool:
        return self.status == "blocked"


@dataclass
class Agent:
    """An agent with skills, load, and current assignments."""

    name: str
    status: str = "offline"
    skills: list[str] = field(default_factory=list)
    skill_level: int = 1  # 1-5
    current_tasks: list[str] = field(default_factory=list)
    completed_tasks: int = 0
    total_tasks: int = 0
    last_heartbeat: str = ""
    estimated_free_at: float = 0.0  # timestamp when current work finishes

    @property
    def is_available(self) -> bool:
        return self.status == "active" and len(self.current_tasks) < 3

    @property
    def load_pct(self) -> float:
        if not self.current_tasks:
            return 0.0
        return min(1.0, len(self.current_tasks) / 3.0)


@dataclass
class CriticalPath:
    """Result of critical path analysis."""

    path: list[str]  # task IDs in the critical chain
    total_hours: float
    parallel_groups: list[list[str]]  # tasks that can run in parallel
    bottleneck_tasks: list[str]  # tasks on the critical path
    estimated_completion: str  # ISO datetime


@dataclass
class Schedule:
    """A complete schedule for a project."""

    project: str
    tasks: list[Task]
    critical_path: CriticalPath
    assignments: dict[str, str]  # task_id → agent_name
    total_estimated_hours: float
    serial_hours: float
    parallel_savings: float
    generated_at: str


# ─── PM Engine ────────────────────────────────────────────────────


class PMEngine:
    """Project management engine: scheduling, assignment, health."""

    def __init__(self, data_dir: Path = FINOPs):
        self.data_dir = data_dir

    # ── Data Loading ──────────────────────────────────────────────

    def load_tasks(self, project: str = "") -> list[Task]:
        """Load tasks from badminton_tasks.json or tasks.json."""
        # Try badminton tasks first
        path = self.data_dir / "badminton_tasks.json"
        if not path.exists():
            path = self.data_dir / "tasks.json"
        if not path.exists():
            return []

        with open(path) as f:
            data = json.load(f)

        tasks = []
        raw_tasks = data.get("tasks", data if isinstance(data, list) else [])
        for t in raw_tasks:
            task = Task(
                id=t.get("id", "?"),
                name=t.get("name", t.get("title", "?")),
                status=t.get("status", "pending"),
                assignee=t.get("owner", t.get("assignee", "")),
                estimated_hours=float(t.get("estimated_hours", t.get("est_hours", 2.0))),
                dependencies=t.get("dependencies", t.get("deps", [])),
                priority=t.get("priority", 2),
                project=t.get("project", project or "default"),
                milestone=t.get("milestone", ""),
                skills_required=t.get("skills_required", t.get("skills", [])),
            )
            if not project or task.project == project:
                tasks.append(task)

        return tasks

    def load_agents(self) -> list[Agent]:
        """Load agents from agent_monitor.json."""
        path = self.data_dir / "agent_monitor.json"
        if not path.exists():
            return []

        with open(path) as f:
            data = json.load(f)

        agents = []
        for a in data.get("agents", []):
            name = a.get("name", "?")
            agent = Agent(
                name=name,
                status=a.get("status", "offline"),
                last_heartbeat=a.get("last_heartbeat", ""),
                skills=self._infer_skills(name),
            )

            # Count tasks from badminton_tasks.json
            tasks = self.load_tasks()
            for t in tasks:
                if t.assignee == name:
                    agent.total_tasks += 1
                    if t.status == "completed":
                        agent.completed_tasks += 1
                    elif t.status == "in_progress":
                        agent.current_tasks.append(t.id)
                        # Estimate when they'll be free
                        remaining = t.estimated_hours - t.actual_hours
                        if agent.estimated_free_at == 0:
                            agent.estimated_free_at = time.time() + remaining * 3600
                        else:
                            agent.estimated_free_at += remaining * 3600

            agents.append(agent)

        return agents

    def _infer_skills(self, agent_name: str) -> list[str]:
        """Infer agent skills from name patterns."""
        name_lower = agent_name.lower()
        skills = []

        mapping = {
            "data": ["data-collection", "data-processing", "python"],
            "ml": ["machine-learning", "pytorch", "training"],
            "qa": ["testing", "quality-assurance", "python"],
            "pipeline": ["ci-cd", "devops", "automation"],
            "security": ["security", "audit", "compliance"],
            "frontend": ["react", "ui", "typescript"],
            "backend": ["api", "database", "python"],
            "infra": ["kubernetes", "docker", "terraform"],
            "devops": ["ci-cd", "docker", "monitoring"],
            "ceo": ["management", "decision-making"],
            "coach": ["coordination", "planning"],
        }

        for key, sks in mapping.items():
            if key in name_lower:
                skills.extend(sks)

        return list(set(skills)) if skills else ["general"]

    # ── Critical Path Method (CPM) ────────────────────────────────

    def critical_path_analysis(self, tasks: list[Task]) -> CriticalPath:
        """Calculate the critical path through the task dependency graph.

        Returns the longest chain of dependent tasks that determines
        the minimum project completion time.

        Algorithm:
          1. Build DAG from dependencies
          2. Topological sort
          3. Forward pass: earliest start/finish times
          4. Backward pass: latest start/finish times
          5. Critical path: tasks where early_start == late_start
        """
        if not tasks:
            return CriticalPath(
                path=[], total_hours=0, parallel_groups=[],
                bottleneck_tasks=[], estimated_completion="",
            )

        task_map = {t.id: t for t in tasks}
        in_degree: dict[str, int] = {t.id: 0 for t in tasks}
        adj: dict[str, list[str]] = {t.id: [] for t in tasks}

        for t in tasks:
            for dep_id in t.dependencies:
                if dep_id in task_map:
                    adj.setdefault(dep_id, []).append(t.id)
                    in_degree[t.id] = in_degree.get(t.id, 0) + 1

        # Forward pass
        early_start: dict[str, float] = {}
        early_finish: dict[str, float] = {}
        queue = deque([t.id for t in tasks if in_degree.get(t.id, 0) == 0])

        topo_order = []
        while queue:
            tid = queue.popleft()
            topo_order.append(tid)
            es = 0.0
            task = task_map[tid]
            for dep_id in task.dependencies:
                if dep_id in early_finish:
                    es = max(es, early_finish[dep_id])
            early_start[tid] = es
            early_finish[tid] = es + task.estimated_hours

            for next_id in adj.get(tid, []):
                in_degree[next_id] -= 1
                if in_degree[next_id] == 0:
                    queue.append(next_id)

        # Backward pass
        max_finish = max(early_finish.values()) if early_finish else 0
        late_start: dict[str, float] = {}
        late_finish: dict[str, float] = {}

        for tid in reversed(topo_order):
            lf = max_finish
            for next_id in adj.get(tid, []):
                if next_id in late_start:
                    lf = min(lf, late_start[next_id])
            late_finish[tid] = lf
            task = task_map[tid]
            late_start[tid] = lf - task.estimated_hours

        # Critical path: where early_start == late_start
        critical_ids = [
            tid for tid in topo_order
            if abs(early_start[tid] - late_start.get(tid, early_start[tid])) < 0.01
        ]

        # Parallel groups: tasks at same depth with no interdependencies
        parallel_groups = self._find_parallel_groups(tasks, task_map, adj)

        # Bottlenecks: tasks on critical path sorted by duration
        bottleneck_tasks = sorted(
            critical_ids,
            key=lambda tid: task_map[tid].estimated_hours,
            reverse=True,
        )[:5]

        # Estimated completion
        now = datetime.now(TZ)
        completion_dt = now + timedelta(hours=max_finish)

        return CriticalPath(
            path=critical_ids,
            total_hours=max_finish,
            parallel_groups=parallel_groups,
            bottleneck_tasks=bottleneck_tasks,
            estimated_completion=completion_dt.isoformat(),
        )

    def _find_parallel_groups(
        self, tasks: list[Task],
        task_map: dict[str, Task],
        adj: dict[str, list[str]],
    ) -> list[list[str]]:
        """Identify groups of tasks that can run in parallel."""
        # Tasks at the same topological depth with no mutual dependencies
        depth: dict[str, int] = {}
        for t in tasks:
            if not t.dependencies:
                depth[t.id] = 0
            else:
                depth[t.id] = 1 + max(
                    (depth.get(d, 0) for d in t.dependencies), default=0
                )

        by_depth: dict[int, list[str]] = defaultdict(list)
        for t in tasks:
            by_depth[depth[t.id]].append(t.id)

        parallel_groups = []
        for d, tids in sorted(by_depth.items()):
            if len(tids) > 1:
                # Check no mutual dependencies
                mutually_dependent = False
                for i, a in enumerate(tids):
                    for b in tids[i + 1:]:
                        if b in adj.get(a, []) or a in adj.get(b, []):
                            mutually_dependent = True
                            break
                if not mutually_dependent:
                    parallel_groups.append(tids)

        return parallel_groups

    # ── Agent Assignment ──────────────────────────────────────────

    def auto_assign(self, tasks: list[Task],
                    agents: list[Agent]) -> dict[str, str]:
        """Auto-assign tasks to best-fit available agents.

        Strategy:
          1. Sort tasks by priority (P0 first) then by critical path position
          2. For each ready task, find best agent by skill match + load
          3. Respect dependencies — don't assign blocked tasks
        """
        cp = self.critical_path_analysis(tasks)
        critical_set = set(cp.path)

        # Sort: P0 critical path first, then P0, then P1, then P2
        def sort_key(t: Task) -> tuple:
            return (
                t.priority,                    # P0 < P1 < P2
                t.id not in critical_set,       # critical path tasks first
                t.estimated_hours,              # shorter tasks first
            )

        task_map = {t.id: t for t in tasks}
        ready_tasks = [
            t for t in tasks
            if t.status in ("pending",) and not t.assignee
            and all(
                d in task_map and task_map[d].status == "completed"
                for d in t.dependencies
            )
        ]
        ready_tasks.sort(key=sort_key)

        available = [a for a in agents if a.is_available]
        assignments: dict[str, str] = {}

        for task in ready_tasks:
            best_agent = self._best_fit(task, available)
            if best_agent:
                assignments[task.id] = best_agent.name
                best_agent.current_tasks.append(task.id)
                # Re-sort available by load
                available.sort(key=lambda a: a.load_pct)

        return assignments

    def _best_fit(self, task: Task, agents: list[Agent]) -> Optional[Agent]:
        """Find the best agent for a task based on skill match and load."""
        if not agents:
            return None

        scored = []
        for agent in agents:
            # Skill match score (0-1)
            if task.skills_required:
                matches = sum(
                    1 for s in task.skills_required if s in agent.skills
                )
                skill_score = matches / max(1, len(task.skills_required))
            else:
                skill_score = 0.5  # neutral

            # Load penalty
            load_penalty = agent.load_pct

            # Experience bonus
            exp_bonus = min(1.0, agent.completed_tasks / max(1, agent.total_tasks))

            # Composite score
            score = (skill_score * 0.5) - (load_penalty * 0.3) + (exp_bonus * 0.2)
            scored.append((score, agent))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1] if scored[0][0] > 0.1 else None

    # ── Health Check ──────────────────────────────────────────────

    def health_check(self) -> dict:
        """Run full health check on all agents."""
        agents = self.load_agents()
        tasks = self.load_tasks()

        report = {
            "timestamp": datetime.now(TZ).isoformat(),
            "agents": {
                "total": len(agents),
                "active": sum(1 for a in agents if a.status == "active"),
                "warning": sum(1 for a in agents if a.status == "warning"),
                "offline": sum(1 for a in agents if a.status == "offline"),
            },
            "tasks": {
                "total": len(tasks),
                "completed": sum(1 for t in tasks if t.status == "completed"),
                "in_progress": sum(1 for t in tasks if t.status == "in_progress"),
                "pending": sum(1 for t in tasks if t.status == "pending"),
                "blocked": sum(1 for t in tasks if t.status == "blocked"),
            },
            "alerts": [],
            "recommendations": [],
        }

        # Check offline agents (excluding the 19 that are always offline)
        core_agents = {
            "CEO_LuC", "Data_Agent_LuD", "ML_Agent_LuM",
            "QA_Agent_LuQ", "Pipeline_Agent_LuP", "BadmintonCoach_LuB",
        }
        for agent in agents:
            if agent.name in core_agents and agent.status != "active":
                report["alerts"].append(
                    f"🔴 Core agent {agent.name} is {agent.status}!"
                )

        # Check stalled tasks
        for task in tasks:
            if task.status == "in_progress" and task.estimated_hours > 0:
                if task.actual_hours > task.estimated_hours * 1.5:
                    report["alerts"].append(
                        f"🟡 Task {task.id} is {task.actual_hours/task.estimated_hours:.0%} over estimate"
                    )

        # Check blocked tasks
        blocked = [t for t in tasks if t.status == "blocked"]
        if blocked:
            report["alerts"].append(
                f"🔴 {len(blocked)} tasks BLOCKED: {', '.join(t.id for t in blocked)}"
            )

        # Recommendations
        if report["tasks"]["in_progress"] == 0 and report["tasks"]["pending"] > 0:
            report["recommendations"].append(
                "No tasks in progress. Run 'apex pm assign' to auto-assign pending tasks."
            )

        offline = report["agents"]["offline"]
        if offline > 20:
            report["recommendations"].append(
                f"{offline} agents offline — most are platform agents that need profile creation."
            )

        return report

    # ── Full Schedule Generation ──────────────────────────────────

    def generate_schedule(self, project: str = "") -> Schedule:
        """Generate a complete project schedule."""
        tasks = self.load_tasks(project)
        agents = self.load_agents()
        cp = self.critical_path_analysis(tasks)
        assignments = self.auto_assign(tasks, agents)

        # Calculate serial vs parallel
        serial_hours = sum(t.estimated_hours for t in tasks)
        parallel_savings = serial_hours - cp.total_hours

        return Schedule(
            project=project or "all",
            tasks=tasks,
            critical_path=cp,
            assignments=assignments,
            total_estimated_hours=serial_hours,
            serial_hours=serial_hours,
            parallel_savings=parallel_savings,
            generated_at=datetime.now(TZ).isoformat(),
        )
