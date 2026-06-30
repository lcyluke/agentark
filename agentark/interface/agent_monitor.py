"""Apex — Agent Fleet Monitor.

Real-time agent state tracking, status detection, work log analysis,
and interactive terminal dashboard.

State Machine:
  WORKING  → 有活跃任务，正在执行
  IDLE     → 无任务，可接新任务
  WAITING  → 有任务但长时间无活动 / 被阻塞
  STOPPED  → Hermes Profile 离线 / 无法连接

每个 Agent 状态附带：
  - 角色/技能/等级（来自 Skill Registry）
  - 当前任务列表
  - 工作时间统计
  - 证据链数量
  - 活跃度指标（last_active, task_completion_rate, response_time）
"""

from __future__ import annotations

import os
import time
import enum
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from agentark.core.profile import ProfileManager, AGENTARK_HOME
from agentark.interface.skill_registry import (
    get_registry, LEVELS, LEVEL_LABELS,
)


# ════════════════════════════════════════════════════════════════
# State Enum
# ════════════════════════════════════════════════════════════════


class AgentState(str, enum.Enum):
    WORKING = "working"    # In_progress tasks assigned
    IDLE = "idle"          # No active tasks, ready
    WAITING = "waiting"    # Has tasks but stalled/blocked
    STOPPED = "stopped"    # Profile offline, no heartbeat

    @property
    def emoji(self) -> str:
        return {
            "working": "🟢",
            "idle": "⚪",
            "waiting": "🟡",
            "stopped": "🔴",
        }[self.value]

    @property
    def label_cn(self) -> str:
        return {
            "working": "工作中",
            "idle": "闲置",
            "waiting": "等待",
            "stopped": "停工",
        }[self.value]


# ════════════════════════════════════════════════════════════════
# Data Classes
# ════════════════════════════════════════════════════════════════


@dataclass
class ActiveTask:
    """A task currently assigned to an agent."""
    id: str
    title: str
    type: str
    status: str
    progress_pct: float
    priority: int
    created_at: float
    estimated_hours: float
    project: str

    @property
    def age_hours(self) -> float:
        return (time.time() - self.created_at) / 3600


@dataclass
class WorkStats:
    """Agent work statistics."""
    total_completed: int = 0
    total_failed: int = 0
    total_hours_logged: float = 0.0
    tasks_this_week: int = 0
    tasks_this_month: int = 0
    avg_completion_hours: float = 0.0
    success_rate: float = 1.0
    last_completed_at: float = 0.0
    first_active_at: float = 0.0


@dataclass
class AgentStatus:
    """Complete status snapshot for a single agent."""
    name: str
    state: AgentState = AgentState.STOPPED
    role: str = ""
    emoji: str = "🤖"

    # Connection
    profile_exists: bool = False
    hermes_profile_exists: bool = False
    wrapper_exists: bool = False
    heartbeat_status: str = "unknown"
    last_seen: float = 0.0

    # Work
    active_tasks: list[ActiveTask] = field(default_factory=list)
    work_stats: WorkStats = field(default_factory=WorkStats)

    # Skills
    skill_count: int = 0
    highest_skill_level: str = "L0"
    avg_skill_level: float = 0.0
    top_skills: list[str] = field(default_factory=list)

    # Timing
    current_session_start: float = 0.0
    total_working_minutes_today: float = 0.0
    idle_minutes: float = 0.0  # How long since last activity

    # Extra
    tags: list[str] = field(default_factory=list)

    @property
    def current_session_duration_min(self) -> float:
        if self.state == AgentState.WORKING and self.current_session_start:
            return (time.time() - self.current_session_start) / 60
        return 0.0

    @property
    def idle_duration_min(self) -> float:
        if self.last_seen > 0:
            return (time.time() - self.last_seen) / 60
        return 9999

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "role": self.role,
            "emoji": self.emoji,
            "active_tasks": [asdict(t) for t in self.active_tasks],
            "work_stats": asdict(self.work_stats),
            "skill_count": self.skill_count,
            "highest_skill_level": self.highest_skill_level,
            "avg_skill_level": round(self.avg_skill_level, 1),
            "top_skills": self.top_skills[:5],
            "profile_exists": self.profile_exists,
            "hermes_profile_exists": self.hermes_profile_exists,
            "wrapper_exists": self.wrapper_exists,
            "heartbeat_status": self.heartbeat_status,
            "idle_minutes": round(self.idle_minutes, 1),
            "total_working_minutes_today": round(self.total_working_minutes_today, 1),
            "last_seen": self.last_seen,
        }


@dataclass
class FleetSnapshot:
    """Complete fleet snapshot at a point in time."""
    timestamp: float
    agents: dict[str, AgentStatus]

    @property
    def total_agents(self) -> int:
        return len(self.agents)

    @property
    def working_count(self) -> int:
        return sum(1 for a in self.agents.values() if a.state == AgentState.WORKING)

    @property
    def idle_count(self) -> int:
        return sum(1 for a in self.agents.values() if a.state == AgentState.IDLE)

    @property
    def waiting_count(self) -> int:
        return sum(1 for a in self.agents.values() if a.state == AgentState.WAITING)

    @property
    def stopped_count(self) -> int:
        return sum(1 for a in self.agents.values() if a.state == AgentState.STOPPED)

    @property
    def total_skills(self) -> int:
        return sum(a.skill_count for a in self.agents.values())

    def summary(self) -> str:
        return (
            f"🤖 Fleet: {self.total_agents} agents | "
            f"🟢 {self.working_count} working | "
            f"⚪ {self.idle_count} idle | "
            f"🟡 {self.waiting_count} waiting | "
            f"🔴 {self.stopped_count} stopped | "
            f"📊 {self.total_skills} skills total"
        )


# ════════════════════════════════════════════════════════════════
# Fleet Monitor
# ════════════════════════════════════════════════════════════════


class FleetMonitor:
    """Collects and analyzes agent status from all available data sources."""

    def __init__(self):
        self.pm = ProfileManager()
        self.registry = get_registry()
        self._hermes_profiles_dir = Path(
            os.environ.get("HERMES_HOME", Path.home() / ".hermes")
        ) / "profiles"
        self._bin_dir = Path.home() / ".local" / "bin"
        self._cache: dict[str, AgentStatus] = {}
        self._last_full_scan: float = 0.0

    # ── Snapshot ────────────────────────────────────────────

    def snapshot(self, force_refresh: bool = False) -> FleetSnapshot:
        """Take a complete fleet snapshot from all data sources."""
        agents: dict[str, AgentStatus] = {}

        # 1. Get all agent names from profiles + registry
        all_agents = set()
        try:
            for name in self.pm.list():
                all_agents.add(name)
        except Exception:
            pass
        try:
            for name in self.registry.list_agents():
                all_agents.add(name)
        except Exception:
            pass

        if not all_agents:
            return FleetSnapshot(timestamp=time.time(), agents={})

        # 2. For each agent, build status
        for agent_name in sorted(all_agents):
            try:
                status = self._build_status(agent_name)
                agents[agent_name] = status
            except Exception as e:
                # Minimal status on error
                status = AgentStatus(name=agent_name)
                status.state = AgentState.STOPPED
                status.heartbeat_status = f"error: {e}"
                agents[agent_name] = status

        self._cache = agents
        self._last_full_scan = time.time()

        return FleetSnapshot(timestamp=time.time(), agents=agents)

    def get_agent(self, agent_name: str, force_refresh: bool = False) -> Optional[AgentStatus]:
        """Get status for a single agent."""
        if force_refresh or agent_name not in self._cache:
            try:
                status = self._build_status(agent_name)
                self._cache[agent_name] = status
                return status
            except Exception:
                return None
        return self._cache.get(agent_name)

    def list_agents(self) -> list[str]:
        """List all known agent names."""
        names = set()
        try:
            for n in self.pm.list():
                names.add(n)
        except Exception:
            pass
        try:
            for n in self.registry.list_agents():
                names.add(n)
        except Exception:
            pass
        return sorted(names)

    # ── Internal ────────────────────────────────────────────

    def _build_status(self, agent_name: str) -> AgentStatus:
        """Build complete status for a single agent."""
        status = AgentStatus(name=agent_name)

        # ── Profile check ──
        status.profile_exists = self._check_apex_profile(agent_name)
        status.hermes_profile_exists = self._check_hermes_profile(agent_name)
        status.wrapper_exists = (self._bin_dir / agent_name).exists()

        # ── Role / Emoji from profile ──
        try:
            profile = self.pm.load(agent_name)
            status.role = profile.soul.role or agent_name
            status.tags = profile.soul.expertise[:3]
        except (FileNotFoundError, Exception):
            # Try SOUL.md
            soul_file = self._hermes_profiles_dir / agent_name / "SOUL.md"
            if soul_file.exists():
                content = soul_file.read_text()
                for line in content.split("\n"):
                    stripped = line.strip()
                    if stripped.startswith("# "):
                        emoji_part = stripped[2:].strip()
                        status.role = emoji_part
                        # Extract emoji
                        import re
                        emoji_match = re.match(r"^([\U0001F300-\U0010FFFF])", emoji_part)
                        if emoji_match:
                            status.emoji = emoji_match.group(1)
                        break
            else:
                status.role = agent_name.replace("-", " ").title()

        # ── Skill data ──
        try:
            skills = self.registry.get_agent_skills(agent_name)
            status.skill_count = len(skills)
            if skills:
                level_indices = []
                for s in skills:
                    lvl = s.get("level", "L0")
                    if lvl in LEVELS:
                        level_indices.append(LEVELS.index(lvl))
                    if s.get("evidence_count", 0) > 0:
                        status.top_skills.append(s["skill_name"])
                if level_indices:
                    status.avg_skill_level = sum(level_indices) / len(level_indices)
                    status.highest_skill_level = LEVELS[max(level_indices)]
                status.top_skills = status.top_skills[:3]
        except Exception:
            pass

        # ── Work data from task_manager ──
        try:
            from agentark.orchestration.task_manager import get_task_manager, WorkflowStatus
            tm = get_task_manager()

            # Active tasks (in_progress)
            active = tm.list_tasks(assignee=agent_name, workflow_status="in_progress")
            for t in active:
                status.active_tasks.append(ActiveTask(
                    id=t.id, title=t.title[:50],
                    type=t.task_type.value,
                    status=t.workflow_status.value,
                    progress_pct=t.progress_pct,
                    priority=t.priority,
                    created_at=t.created_at,
                    estimated_hours=t.estimated_hours,
                    project=t.project,
                ))

            # Completed tasks stats
            completed = tm.list_tasks(assignee=agent_name, workflow_status="closed")
            verified = tm.list_tasks(assignee=agent_name, workflow_status="verified")
            done = tm.list_tasks(assignee=agent_name, workflow_status="completed")

            status.work_stats.total_completed = len(completed) + len(verified) + len(done)

            # Failed/rejected
            rejected = tm.list_tasks(assignee=agent_name, workflow_status="rejected")
            status.work_stats.total_failed = len(rejected)

            # Last activity
            all_statuses = [completed, verified, done]
            last_time = 0.0
            for task_list in all_statuses:
                for t in task_list:
                    ct = getattr(t, "completed_at", 0) or getattr(t, "verified_at", 0) or 0
                    if ct > last_time:
                        last_time = ct
            if last_time > 0:
                status.work_stats.last_completed_at = last_time
                status.last_seen = last_time
                status.idle_minutes = (time.time() - last_time) / 60
            else:
                status.last_seen = 0
                status.idle_minutes = 9999

            # Success rate
            total_tasks = status.work_stats.total_completed + status.work_stats.total_failed
            if total_tasks > 0:
                status.work_stats.success_rate = status.work_stats.total_completed / total_tasks

            # Session start (first task created time)
            all_assigned = tm.list_tasks(assignee=agent_name)
            if all_assigned:
                first = min(t.created_at for t in all_assigned if t.created_at > 0)
                status.work_stats.first_active_at = first
                status.current_session_start = first

        except ImportError:
            pass
        except Exception:
            pass

        # ── Heartbeat from autonomous engine ──
        try:
            from agentark.orchestration.autonomous import AutonomousEngine
            engine = AutonomousEngine()
            heartbeats = engine.get_heartbeats()
            for hb in heartbeats:
                if hb.agent_name == agent_name:
                    status.heartbeat_status = hb.status
                    if hb.last_active > status.last_seen:
                        status.last_seen = hb.last_active
                    break
        except Exception:
            pass

        # ── Determine state ──
        status.state = self._determine_state(status)

        return status

    def _determine_state(self, status: AgentStatus) -> AgentState:
        """Determine agent state from collected data."""
        # If profile doesn't exist and never seen, it's stopped
        if not status.profile_exists and not status.hermes_profile_exists:
            if status.work_stats.total_completed == 0:
                return AgentState.STOPPED

        # If has active tasks
        if status.active_tasks:
            # If tasks are stalled (created > 2h ago, progress < 50%)
            stalled = False
            for task in status.active_tasks:
                if task.age_hours > 2 and task.progress_pct < 50:
                    stalled = True
                    break
            if stalled:
                return AgentState.WAITING
            return AgentState.WORKING

        # No active tasks
        if not status.profile_exists and not status.hermes_profile_exists:
            return AgentState.STOPPED

        # Has profile, no tasks
        if status.work_stats.total_completed > 0:
            # Idle if recently active
            if status.idle_minutes < 60:  # Active within last hour
                return AgentState.IDLE
            elif status.idle_minutes < 1440:  # Active within 24h
                return AgentState.WAITING  # Long idle without tasks = waiting
            else:
                return AgentState.STOPPED  # Not seen in >24h

        return AgentState.IDLE

    def _check_apex_profile(self, name: str) -> bool:
        """Check if Apex profile exists."""
        profile_file = AGENTARK_HOME / "profiles" / f"{name}.yaml"
        return profile_file.exists()

    def _check_hermes_profile(self, name: str) -> bool:
        """Check if Hermes profile exists."""
        return (self._hermes_profiles_dir / name).exists()

    def _check_wrapper(self, name: str) -> bool:
        """Check if wrapper script exists."""
        return (self._bin_dir / name).exists()


# ════════════════════════════════════════════════════════════════
# Convenience
# ════════════════════════════════════════════════════════════════

_monitor_instance: Optional[FleetMonitor] = None


def get_monitor() -> FleetMonitor:
    """Get singleton FleetMonitor."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = FleetMonitor()
    return _monitor_instance
