"""Apex PM Engine v2 — intelligent multi-factor agent assignment.

Assignment strategy (4-factor weighted scoring):
  1. Historical success rate on similar tasks  (35%)
  2. Core SKILL matching (Hermes profiles)     (30%)
  3. Role alignment (SOUL.md)                  (20%)
  4. Current load balancing                    (15%)

Data sources:
  - ~/.hermes/profiles/<agent>/SOUL.md        → role, expertise
  - ~/.hermes/profiles/<agent>/skills/        → actual skills
  - finopsai/data/badminton_tasks.json        → task history + completion
  - finopsai/data/agent_monitor.json          → heartbeat + status
  - Project source tree                       → code module ownership
"""

from __future__ import annotations

import json
import re
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

TZ = timezone(timedelta(hours=8))
FINOPs = Path.home() / "finopsai" / "data"
HERMES = Path.home() / ".hermes"
PROFILES_DIR = HERMES / "profiles"

# ─── Extended Data Models ─────────────────────────────────────────


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
    priority: int = 2
    project: str = ""
    milestone: str = ""
    skills_required: list[str] = field(default_factory=list)
    task_type: str = ""  # e.g. "data_collection", "model_training", "api_dev"
    started_at: str = ""
    completed_at: str = ""
    _assignment_reason: str = ""  # internal: why this agent was chosen

    @property
    def is_ready(self) -> bool:
        return self.status == "pending"

    @property
    def is_blocked(self) -> bool:
        return self.status == "blocked"

    def infer_type(self) -> str:
        """Infer task type from name and ID patterns."""
        name_lower = (self.name + self.id).lower()
        patterns = {
            "data_collection": ["采集", "collect", "download", "爬", "scrape", "bilibili"],
            "data_processing": ["处理", "process", "clean", "清洗", "organize", "clip"],
            "model_training": ["训练", "train", "model", "videoMAE", "fine-tune"],
            "model_integration": ["集成", "integrate", "track", "face", "insight"],
            "api_development": ["api", "服务", "server", "endpoint", "web"],
            "deployment": ["部署", "deploy", "gpu", "推理", "inference", "docker"],
            "testing": ["测试", "test", "qa", "验证", "verify", "quality"],
            "infrastructure": ["infra", "ci", "cd", "pipeline", "数据库", "postgres"],
            "security": ["安全", "security", "auth", "权限", "vulnerability"],
            "documentation": ["文档", "doc", "readme", "wiki"],
        }
        for task_type, keywords in patterns.items():
            if any(kw in name_lower for kw in keywords):
                return task_type
        return "general"


@dataclass
class AgentProfile:
    """Rich agent profile for intelligent assignment."""

    name: str
    status: str = "offline"

    # Role (from SOUL.md)
    role: str = ""
    expertise: list[str] = field(default_factory=list)

    # Skills (from Hermes profile skills directory)
    skills: list[str] = field(default_factory=list)
    skill_count: int = 0
    top_skills: list[str] = field(default_factory=list)  # top 5 by level

    # Historical performance
    completed_tasks: int = 0
    total_tasks: int = 0
    task_type_history: dict[str, dict] = field(default_factory=dict)
    # {task_type: {completed: N, total: N, avg_hours: F, last_at: str}}

    # Current load
    current_tasks: list[str] = field(default_factory=list)
    load_pct: float = 0.0
    estimated_free_at: float = 0.0

    # Code ownership
    owned_modules: list[str] = field(default_factory=list)

    # Meta
    last_heartbeat: str = ""
    model: str = ""

    @property
    def is_available(self) -> bool:
        return self.status == "active" and self.load_pct < 0.8

    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.5  # neutral for new agents
        return self.completed_tasks / self.total_tasks

    def task_type_success(self, task_type: str) -> float:
        """Historical success rate for a specific task type."""
        hist = self.task_type_history.get(task_type)
        if not hist or hist["total"] == 0:
            return 0.5  # neutral
        return hist["completed"] / hist["total"]


# ─── Assignment Result ─────────────────────────────────────────────


@dataclass
class AssignmentResult:
    task_id: str
    agent_name: str
    score: float
    reasons: list[str]


# ─── PM Engine v2 ─────────────────────────────────────────────────


class PMEngine:
    """Enhanced PM engine with multi-factor agent profiling."""

    def __init__(self, data_dir: Path = FINOPs):
        self.data_dir = data_dir
        self._agent_cache: dict[str, AgentProfile] = {}

    # ══════════════════════════════════════════════════════════════
    # Agent Profiling
    # ══════════════════════════════════════════════════════════════

    def build_agent_profiles(self, force_refresh: bool = False) -> list[AgentProfile]:
        """Build rich AgentProfiles from all data sources."""
        if self._agent_cache and not force_refresh:
            return list(self._agent_cache.values())

        profiles = {}

        # ── Source 1: agent_monitor.json (heartbeat + status) ──
        monitor_data = self._load_json(self.data_dir / "agent_monitor.json")
        for a in monitor_data.get("agents", []):
            name = a.get("name", "?")
            profiles[name] = AgentProfile(
                name=name,
                status=a.get("status", "offline"),
                last_heartbeat=a.get("last_heartbeat", ""),
            )

        # ── Source 2: Hermes profile SOUL.md (role + expertise) ──
        for pdir in PROFILES_DIR.iterdir() if PROFILES_DIR.exists() else []:
            if not pdir.is_dir():
                continue
            name = pdir.name
            if name not in profiles:
                profiles[name] = AgentProfile(name=name)

            soul_file = pdir / "SOUL.md"
            if soul_file.exists():
                content = soul_file.read_text()
                profiles[name].role = self._extract_role(content)
                profiles[name].expertise = self._extract_expertise(content)

            # Skills
            skills_dir = pdir / "skills"
            if skills_dir.exists():
                skill_files = list(skills_dir.rglob("SKILL.md"))
                profiles[name].skill_count = len(skill_files)
                skill_names = [f.parent.name for f in skill_files]
                profiles[name].skills = skill_names[:50]
                profiles[name].top_skills = skill_names[:5]

            # Model
            config_file = pdir / "config.yaml"
            if config_file.exists():
                profiles[name].model = self._extract_model(config_file)

        # ── Source 3: badminton_tasks.json (historical performance) ──
        tasks_data = self._load_json(self.data_dir / "badminton_tasks.json")
        for t in tasks_data.get("tasks", []):
            assignee = t.get("owner", t.get("assignee", ""))
            if not assignee:
                continue

            # Create profile for assignees not in agent_monitor
            if assignee not in profiles:
                profiles[assignee] = AgentProfile(name=assignee)

            p = profiles[assignee]
            p.total_tasks += 1
            if t.get("status") == "completed":
                p.completed_tasks += 1

            task_type = Task(
                id=t.get("id", "?"),
                name=t.get("name", t.get("title", "")),
                status=t.get("status", "?"),
            ).infer_type()

            if task_type not in p.task_type_history:
                p.task_type_history[task_type] = {
                    "completed": 0, "total": 0,
                    "avg_hours": 0.0, "task_ids": [],
                }
            hist = p.task_type_history[task_type]
            hist["total"] += 1
            if t.get("status") == "completed":
                hist["completed"] += 1
            hist["task_ids"].append(t.get("id", "?")[:20])

            # Track in-progress for load
            if t.get("status") == "in_progress":
                p.current_tasks.append(t.get("id", "?"))

        # ── Source 4: Code module ownership ──
        self._assign_module_ownership(profiles)

        # ── Compute load percentage ──
        for p in profiles.values():
            p.load_pct = min(1.0, len(p.current_tasks) / 3.0)

        self._agent_cache = profiles
        return list(profiles.values())

    def get_agent_profile(self, name: str) -> Optional[AgentProfile]:
        """Get a single agent's profile."""
        profiles = self.build_agent_profiles()
        for p in profiles:
            if p.name == name:
                return p
        return None

    # ── SOUL parsing ─────────────────────────────────────────────

    def _extract_role(self, soul_content: str) -> str:
        """Extract role from SOUL.md."""
        # Pattern: "# Role Name — Description" or "You are the Role Name"
        for line in soul_content.split("\n"):
            line = line.strip()
            if line.startswith("# ") and "—" in line:
                return line.replace("# ", "").split("—")[0].strip()
            if "You are the" in line:
                m = re.search(r"You are the (.+?)($|of|\.|,)", line)
                if m:
                    return m.group(1).strip()
        return ""

    def _extract_expertise(self, soul_content: str) -> list[str]:
        """Extract expertise areas from SOUL.md."""
        expertise = []
        for line in soul_content.split("\n"):
            line = line.strip()
            if line.startswith("## ") and "Core " in line:
                expertise.append(line.replace("## ", "").strip())
            if line.startswith("- ") and any(
                kw in line.lower()
                for kw in ["design", "develop", "test", "deploy", "manage",
                           "coordinate", "build", "own", "ensure", "review"]
            ):
                expertise.append(line.replace("- ", "").strip()[:60])
        return expertise[:8]

    def _extract_model(self, config_file: Path) -> str:
        try:
            import yaml
            with open(config_file) as f:
                cfg = yaml.safe_load(f) or {}
            return cfg.get("model", {}).get("default", "?")
        except Exception:
            return "?"

    def _assign_module_ownership(self, profiles: dict[str, AgentProfile]):
        """Map agents to code modules based on their role and skills."""
        module_map = {
            "data_collection": ["collector", "download", "scrape", "crawler", "bilibili"],
            "data_processing": ["clip", "process", "organize", "pipeline", "extract"],
            "model_training": ["train", "model", "videoMAE", "tracknet", "finetune"],
            "api_backend": ["api", "server", "endpoint", "fastapi", "flask"],
            "frontend": ["ui", "dashboard", "react", "component", "html"],
            "devops": ["ci", "cd", "docker", "deploy", "monitor", "pipeline"],
            "testing": ["test", "qa", "verify", "quality", "coverage"],
            "security": ["auth", "security", "vulnerability", "compliance"],
        }

        for name, profile in profiles.items():
            name_lower = name.lower()
            owned = []
            for module, keywords in module_map.items():
                if any(kw in name_lower for kw in keywords):
                    owned.append(module)
                elif any(kw in (profile.role or "").lower() for kw in keywords):
                    owned.append(module)
                elif any(
                    any(kw in skill.lower() for kw in keywords)
                    for skill in profile.skills[:10]
                ):
                    owned.append(module)

            if not owned:
                owned.append("general")
            profile.owned_modules = list(set(owned))

    # ══════════════════════════════════════════════════════════════
    # Intelligent Assignment (4-factor weighted scoring)
    # ══════════════════════════════════════════════════════════════

    def auto_assign(
        self,
        tasks: list[Task] | None = None,
        agents: list[AgentProfile] | None = None,
        explain: bool = True,
    ) -> list[AssignmentResult]:
        """Auto-assign tasks using multi-factor scoring.

        Args:
            tasks: Tasks to assign. If None, loads from data dir.
            agents: Agent profiles. If None, builds from all sources.
            explain: Include assignment reasons in results.

        Returns:
            List of AssignmentResult with scores and reasons.
        """
        if tasks is None:
            tasks = self.load_tasks()
        if agents is None:
            agents = self.build_agent_profiles()

        task_map = {t.id: t for t in tasks}

        # Filter: ready tasks (pending, unassigned, dependencies met)
        ready = [
            t for t in tasks
            if t.status in ("pending",)
            and all(
                d in task_map and task_map[d].status == "completed"
                for d in t.dependencies
            )
        ]

        # Sort by priority then critical path position
        cp = self.critical_path_analysis(tasks)
        critical_set = set(cp.path)

        def sort_key(t: Task) -> tuple:
            return (
                t.priority,
                t.id not in critical_set,
                -t.estimated_hours,
            )

        ready.sort(key=sort_key)

        # Filter available agents
        available = [a for a in agents if a.is_available]
        if not available:
            available = [a for a in agents if a.status == "active"]

        results: list[AssignmentResult] = []

        for task in ready:
            scored = []
            for agent in available:
                score, reasons = self._compute_assignment_score(task, agent)
                scored.append((score, reasons, agent))

            scored.sort(key=lambda x: x[0], reverse=True)

            if scored and scored[0][0] > 0.1:
                best = scored[0]
                agent = best[2]
                task.assignee = agent.name
                task._assignment_reason = " | ".join(best[1][:3])
                agent.current_tasks.append(task.id)
                # Re-sort available by updated load
                available.sort(key=lambda a: a.load_pct)

                results.append(AssignmentResult(
                    task_id=task.id,
                    agent_name=agent.name,
                    score=best[0],
                    reasons=best[1],
                ))

        return results

    def _compute_assignment_score(
        self, task: Task, agent: AgentProfile
    ) -> tuple[float, list[str]]:
        """4-factor weighted scoring for task-agent fit.

        Returns:
            (score 0.0-1.0, list of reason strings)
        """
        task_type = task.infer_type()
        reasons = []
        total = 0.0

        # ── Factor 1: Historical success on similar tasks (35%) ──
        hist_success = agent.task_type_success(task_type)
        hist_weight = 0.35
        total += hist_success * hist_weight
        if agent.task_type_history.get(task_type, {}).get("total", 0) > 0:
            reasons.append(
                f"历史{task_type}: {hist_success:.0%} "
                f"({agent.task_type_history[task_type]['completed']}/"
                f"{agent.task_type_history[task_type]['total']})"
            )
        else:
            reasons.append(f"历史{task_type}: 无记录 (中性评分)")

        # ── Factor 2: Core SKILL match (30%) ──
        if task.skills_required:
            matches = sum(
                1 for s in task.skills_required if s in agent.skills
            )
            skill_score = matches / max(1, len(task.skills_required))
        else:
            # Infer required skills from task type
            inferred = self._infer_skills_for_type(task_type)
            matches = sum(1 for s in inferred if s in agent.skills)
            skill_score = matches / max(1, len(inferred)) if inferred else 0.5

        skill_weight = 0.30
        total += skill_score * skill_weight
        if skill_score > 0.5:
            reasons.append(
                f"技能匹配: {skill_score:.0%} "
                f"(拥有: {', '.join(agent.top_skills[:3])})"
            )
        else:
            reasons.append(f"技能匹配: {skill_score:.0%}")

        # ── Factor 3: Role alignment (20%) ──
        role_score = self._role_task_fit(agent.role, task_type)
        role_weight = 0.20
        total += role_score * role_weight
        if agent.role:
            reasons.append(f"角色匹配: {agent.role[:20]} → {task_type} ({role_score:.0%})")

        # ── Factor 4: Load balancing (15%) ──
        load_score = 1.0 - agent.load_pct
        load_weight = 0.15
        total += load_score * load_weight
        reasons.append(f"负载: {agent.load_pct:.0%} ({len(agent.current_tasks)}个进行中)")

        return min(1.0, total), reasons

    def _role_task_fit(self, role: str, task_type: str) -> float:
        """Score how well an agent's role fits a task type."""
        role_lower = role.lower()
        mapping = {
            "data_collection": ["data", "采集", "collect"],
            "data_processing": ["data", "处理", "process", "backend"],
            "model_training": ["ml", "machine", "训练", "model", "ai"],
            "model_integration": ["ml", "backend", "integrate", "集成"],
            "api_development": ["backend", "api", "fullstack", "dev"],
            "frontend": ["frontend", "前端", "ui"],
            "deployment": ["devops", "运维", "deploy", "infra"],
            "testing": ["qa", "test", "测试", "quality"],
            "infrastructure": ["devops", "infra", "运维", "architect"],
            "security": ["security", "安全", "auth"],
        }

        keywords = mapping.get(task_type, [])
        if not keywords:
            return 0.3  # generic

        matches = sum(1 for kw in keywords if kw in role_lower)
        return min(1.0, 0.3 + matches * 0.23)

    def _infer_skills_for_type(self, task_type: str) -> list[str]:
        """Infer required skills for a task type."""
        mapping = {
            "data_collection": ["python", "data-collection", "web-scraping", "bilibili"],
            "data_processing": ["python", "data-processing", "video-processing", "ffmpeg"],
            "model_training": ["python", "pytorch", "machine-learning", "videoMAE"],
            "model_integration": ["python", "api", "integration", "tracking"],
            "api_development": ["python", "api", "fastapi", "backend", "database"],
            "deployment": ["docker", "kubernetes", "ci-cd", "gpu", "inference"],
            "testing": ["python", "testing", "pytest", "quality-assurance"],
            "infrastructure": ["docker", "terraform", "kubernetes", "ci-cd", "monitoring"],
            "security": ["security", "audit", "compliance", "vulnerability-scanning"],
            "documentation": ["writing", "documentation", "markdown"],
        }
        return mapping.get(task_type, ["python", "general"])

    # ══════════════════════════════════════════════════════════════
    # Data Loading (from v1, kept for compatibility)
    # ══════════════════════════════════════════════════════════════

    def load_tasks(self, project: str = "") -> list[Task]:
        path = self.data_dir / "badminton_tasks.json"
        if not path.exists():
            path = self.data_dir / "tasks.json"
        if not path.exists():
            return []

        try:
            with open(path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

        raw_tasks = data.get("tasks", data if isinstance(data, list) else [])
        tasks = []
        for t in raw_tasks:
            # Handle both naming conventions
            raw_priority = t.get("priority", "P2")
            if isinstance(raw_priority, str) and raw_priority.startswith("P"):
                priority = int(raw_priority[1]) if raw_priority[1].isdigit() else 2
            else:
                priority = int(raw_priority) if raw_priority else 2

            task = Task(
                id=t.get("id", "?"),
                name=t.get("name", t.get("title", "?")),
                status=t.get("status", "pending"),
                assignee=t.get("owner", t.get("assignee", "")),
                estimated_hours=float(t.get("estimated_hours", t.get("est_hours", 2.0))),
                dependencies=t.get("dependencies", t.get("deps", [])),
                priority=priority,
                project=t.get("project", project or "default"),
                milestone=t.get("milestone", ""),
                skills_required=t.get("skills_required", t.get("skills", [])),
            )
            task.task_type = task.infer_type()
            if not project or task.project == project:
                tasks.append(task)
        return tasks

    # ══════════════════════════════════════════════════════════════
    # Critical Path Method (from v1, unchanged)
    # ══════════════════════════════════════════════════════════════

    def critical_path_analysis(self, tasks: list[Task]) -> "CriticalPath":
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

        critical_ids = [
            tid for tid in topo_order
            if abs(early_start[tid] - late_start.get(tid, early_start[tid])) < 0.01
        ]

        parallel_groups = self._find_parallel_groups(tasks, task_map, adj)
        bottleneck_tasks = sorted(
            critical_ids,
            key=lambda tid: task_map[tid].estimated_hours,
            reverse=True,
        )[:5]

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
                mutually_dependent = False
                for i, a in enumerate(tids):
                    for b in tids[i + 1:]:
                        if b in adj.get(a, []) or a in adj.get(b, []):
                            mutually_dependent = True
                            break
                if not mutually_dependent:
                    parallel_groups.append(tids)
        return parallel_groups

    # ══════════════════════════════════════════════════════════════
    # Schedule (from v1)
    # ══════════════════════════════════════════════════════════════

    def generate_schedule(self, project: str = "") -> "Schedule":
        tasks = self.load_tasks(project)
        cp = self.critical_path_analysis(tasks)
        assignments = self.auto_assign(tasks, explain=True)
        serial_hours = sum(t.estimated_hours for t in tasks)
        parallel_savings = serial_hours - cp.total_hours

        assign_map = {a.task_id: a.agent_name for a in assignments}
        return Schedule(
            project=project or "all",
            tasks=tasks,
            critical_path=cp,
            assignments=assign_map,
            total_estimated_hours=serial_hours,
            serial_hours=serial_hours,
            parallel_savings=parallel_savings,
            generated_at=datetime.now(TZ).isoformat(),
        )

    # ══════════════════════════════════════════════════════════════
    # Health (from v1)
    # ══════════════════════════════════════════════════════════════

    def health_check(self) -> dict:
        agents = self.build_agent_profiles()
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

        core_agents = {
            "CEO_LuC", "Data_Agent_LuD", "ML_Agent_LuM",
            "QA_Agent_LuQ", "Pipeline_Agent_LuP", "BadmintonCoach_LuB",
        }
        for agent in agents:
            if agent.name in core_agents and agent.status != "active":
                report["alerts"].append(
                    f"🔴 Core agent {agent.name} is {agent.status}!"
                )

        for task in tasks:
            if task.status == "in_progress" and task.estimated_hours > 0:
                if task.actual_hours > task.estimated_hours * 1.5:
                    report["alerts"].append(
                        f"🟡 {task.id} over estimate "
                        f"({task.actual_hours/task.estimated_hours:.0%})"
                    )

        blocked = [t for t in tasks if t.status == "blocked"]
        if blocked:
            report["alerts"].append(
                f"🔴 {len(blocked)} tasks BLOCKED"
            )

        if report["tasks"]["in_progress"] == 0 and report["tasks"]["pending"] > 0:
            report["recommendations"].append(
                "No tasks in progress. Run 'apex pm assign'."
            )

        return report

    # ── Helpers ──────────────────────────────────────────────────

    def _load_json(self, path: Path) -> dict:
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return {}


# ─── Re-export data classes ──────────────────────────────────────


@dataclass
class CriticalPath:
    path: list[str]
    total_hours: float
    parallel_groups: list[list[str]]
    bottleneck_tasks: list[str]
    estimated_completion: str


@dataclass
class Schedule:
    project: str
    tasks: list[Task]
    critical_path: CriticalPath
    assignments: dict[str, str]
    total_estimated_hours: float
    serial_hours: float
    parallel_savings: float
    generated_at: str
