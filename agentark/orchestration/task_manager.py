"""Apex — Project & Task Management Extension

Extends OpsManager with:
  - Task hierarchy (Epic → Story → Task → Subtask)
  - PM approval workflow (Request → Review → Approve → Assign → Execute → Verify)
  - Agent capacity-aware auto-dispatch
  - Cross-agent help requests
  - Progress rollup from sub-tasks to parent
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from agentark.orchestration.ops import get_ops, OpsTask, TaskStatus
from agentark.orchestration.kanban import Kanban
from agentark.core.profile import ProfileManager, AGENTARK_HOME


# ════════════════════════════════════════════════════════════════
# Enums
# ════════════════════════════════════════════════════════════════

class TaskType(str, Enum):
    """Hierarchical task types."""
    EPIC = "epic"          # Large initiative, multiple stories
    STORY = "story"        # User story, multiple tasks
    TASK = "task"          # Single unit of work
    SUBTASK = "subtask"    # Sub-division of a task


class WorkflowStatus(str, Enum):
    """Full workflow lifecycle status."""
    DRAFT = "draft"                    # Just created, not submitted
    REQUESTED = "requested"            # Submitted to PM for review
    PM_REVIEW = "pm_review"            # Under PM review
    APPROVED = "approved"              # PM approved
    REJECTED = "rejected"              # PM rejected with feedback
    ASSIGNED = "assigned"              # Assigned to an agent
    IN_PROGRESS = "in_progress"        # Agent is working on it
    BLOCKED = "blocked"               # Blocked by dependency
    COMPLETED = "completed"            # Agent finished
    PM_VERIFY = "pm_verify"            # Awaiting PM verification
    VERIFIED = "verified"              # PM verified
    CLOSED = "closed"                  # Done and closed


class HelpRequestStatus(str, Enum):
    """Cross-agent help request status."""
    PENDING = "pending"
    PM_REVIEW = "pm_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


# ════════════════════════════════════════════════════════════════
# Data Models
# ════════════════════════════════════════════════════════════════

@dataclass
class ProjectTask:
    """Extended task with hierarchy, workflow, and tracking."""
    id: str
    title: str
    description: str = ""
    task_type: TaskType = TaskType.TASK
    workflow_status: WorkflowStatus = WorkflowStatus.DRAFT
    phase: str = "development"
    priority: int = 2  # 0=urgent, 1=high, 2=medium, 3=low

    # Assignment
    assignee: str = ""
    requested_by: str = ""  # Who requested this task
    reviewed_by: str = ""   # PM who reviewed

    # Hierarchy
    parent_id: Optional[str] = None
    epic_id: Optional[str] = None  # Top-level epic for rollup
    depends_on: list[str] = field(default_factory=list)
    sub_task_ids: list[str] = field(default_factory=list)

    # Progress
    progress_pct: float = 0.0  # Auto-calculated from sub-tasks
    estimated_hours: float = 0.0
    actual_hours: float = 0.0

    # Workflow
    pm_notes: str = ""
    rejection_reason: str = ""
    completion_notes: str = ""
    verification_notes: str = ""

    # Cross-agent
    help_requests: list[str] = field(default_factory=list)

    # Timing
    created_at: float = 0.0
    assigned_at: Optional[float] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    verified_at: Optional[float] = None

    # Cost
    estimated_cost: float = 0.0
    actual_cost: float = 0.0

    # Tags
    project: str = ""       # Project name for grouping
    tags: list[str] = field(default_factory=list)

    @property
    def is_leaf(self) -> bool:
        """Leaf task with no sub-tasks (actually executable)."""
        return len(self.sub_task_ids) == 0

    @property
    def duration_days(self) -> float:
        if self.completed_at and self.started_at:
            return round((self.completed_at - self.started_at) / 86400, 1)
        return 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "title": self.title, "description": self.description[:100],
            "task_type": self.task_type.value, "workflow_status": self.workflow_status.value,
            "phase": self.phase, "priority": self.priority,
            "assignee": self.assignee, "requested_by": self.requested_by,
            "parent_id": self.parent_id, "epic_id": self.epic_id,
            "depends_on": self.depends_on, "sub_task_ids": self.sub_task_ids,
            "progress_pct": self.progress_pct,
            "estimated_hours": self.estimated_hours, "actual_hours": self.actual_hours,
            "pm_notes": self.pm_notes[:100] if self.pm_notes else "",
            "project": self.project, "tags": self.tags,
            "is_leaf": self.is_leaf, "duration_days": self.duration_days,
            "created_at": self.created_at, "assigned_at": self.assigned_at,
            "started_at": self.started_at, "completed_at": self.completed_at,
        }


@dataclass
class HelpRequest:
    """Cross-agent help/assistance request."""
    id: str
    requesting_agent: str         # Who needs help
    title: str
    description: str = ""
    status: HelpRequestStatus = HelpRequestStatus.PENDING
    source_task_id: str = ""     # The task that triggered this request
    assigned_agent: str = ""     # Who PM assigned to help
    pm_notes: str = ""
    created_at: float = 0.0
    resolved_at: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id, "requesting_agent": self.requesting_agent,
            "title": self.title, "description": self.description[:100],
            "status": self.status.value, "source_task_id": self.source_task_id,
            "assigned_agent": self.assigned_agent,
            "pm_notes": self.pm_notes[:100] if self.pm_notes else "",
            "created_at": self.created_at, "resolved_at": self.resolved_at,
        }


# ════════════════════════════════════════════════════════════════
# Agent Capacity Manager
# ════════════════════════════════════════════════════════════════

@dataclass
class AgentCapacity:
    """Track how many tasks each agent has assigned."""
    agent_name: str
    active_tasks: int = 0      # Tasks in progress
    max_concurrent: int = 3    # Default max parallel tasks
    total_completed: int = 0
    total_failed: int = 0

    @property
    def available_slots(self) -> int:
        return max(0, self.max_concurrent - self.active_tasks)

    @property
    def load_pct(self) -> float:
        return round(self.active_tasks / self.max_concurrent * 100, 1)

    def to_dict(self) -> dict:
        return {
            "agent": self.agent_name,
            "active": self.active_tasks,
            "max": self.max_concurrent,
            "available": self.available_slots,
            "load_pct": self.load_pct,
            "completed": self.total_completed,
            "failed": self.total_failed,
        }


class TaskManager:
    """Complete task management system — wraps OpsManager with workflow."""

    def __init__(self):
        self.ops = get_ops()
        self.pm = ProfileManager()
        self.kanban = Kanban(AGENTARK_HOME / "kanban.db")
        self._db = self.ops._conn  # Reuse OpsManager's connection

    # ════════════════════════════════════════════════════════════
    # Task CRUD with Hierarchy
    # ════════════════════════════════════════════════════════════

    def create_task(self, title: str, description: str = "",
                    task_type: str = "task", phase: str = "development",
                    priority: int = 2, assignee: str = "",
                    parent_id: str = "", depends_on: list[str] = None,
                    project: str = "", estimated_hours: float = 0.0) -> ProjectTask:
        """Create a hierarchical task. If parent_id is set, auto-link to parent."""
        task_id = f"PT{int(time.time())}{uuid.uuid4().hex[:4]}".upper()
        now = time.time()

        task = ProjectTask(
            id=task_id, title=title, description=description,
            task_type=TaskType(task_type), phase=phase, priority=priority,
            assignee=assignee, parent_id=parent_id or None,
            depends_on=depends_on or [],
            project=project, estimated_hours=estimated_hours,
            created_at=now,
        )

        # Auto-set assignee if not specified — skill-match from available agents
        if not assignee:
            task.assignee = self._pick_best_agent(
                phase=phase, task_title=title, task_description=description
            )

        # If task has an assignee, set status to assigned
        if task.assignee:
            task.workflow_status = WorkflowStatus.ASSIGNED
        else:
            task.workflow_status = WorkflowStatus.REQUESTED

        # Link to parent
        if parent_id:
            parent = self.get_task(parent_id)
            if parent:
                parent.sub_task_ids.append(task_id)
                self._update_parent_progress(parent)

        # Also create in underlying OpsManager for cross-compatibility
        self.ops.create_task(
            title=title, description=description, phase=phase,
            priority=priority, agent_id=assignee,
            parent_id=parent_id, depends_on=depends_on or [],
        )

        # Save to local task store
        self._save_task(task)
        return task

    def get_task(self, task_id: str) -> Optional[ProjectTask]:
        """Get a task by ID."""
        cursor = self._db.execute(
            "SELECT * FROM project_tasks WHERE id=?", (task_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_task(row)

    def get_task_tree(self, task_id: str, depth: int = 3) -> dict:
        """Get a task and all its sub-tasks (recursive) as a tree."""
        task = self.get_task(task_id)
        if not task:
            return {}
        result = task.to_dict()
        if depth > 0 and task.sub_task_ids:
            result["children"] = []
            for sub_id in task.sub_task_ids:
                child = self.get_task_tree(sub_id, depth - 1)
                if child:
                    result["children"].append(child)
        return result

    def get_epic_tree(self, epic_title: str = "") -> list[dict]:
        """Get all epics with their full sub-task trees."""
        if epic_title:
            cursor = self._db.execute(
                "SELECT * FROM project_tasks WHERE task_type='epic' AND title LIKE ? ORDER BY priority, created_at",
                (f"%{epic_title}%",)
            )
        else:
            cursor = self._db.execute(
                "SELECT * FROM project_tasks WHERE task_type='epic' ORDER BY priority, created_at"
            )
        epics = []
        for row in cursor.fetchall():
            task = self._row_to_task(row)
            epics.append(self.get_task_tree(task.id, depth=3))
        return epics

    def list_tasks(self, project: str = "", assignee: str = "",
                   task_type: str = "", workflow_status: str = "",
                   phase: str = "", limit: int = 50) -> list[ProjectTask]:
        """List tasks with filters."""
        conditions = []
        params = []
        if project:
            conditions.append("project=?")
            params.append(project)
        if assignee:
            conditions.append("assignee=?")
            params.append(assignee)
        if task_type:
            conditions.append("task_type=?")
            params.append(task_type)
        if workflow_status:
            conditions.append("workflow_status=?")
            params.append(workflow_status)
        if phase:
            conditions.append("phase=?")
            params.append(phase)

        where = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM project_tasks WHERE {where} ORDER BY priority, created_at DESC LIMIT ?"
        params.append(limit)
        cursor = self._db.execute(query, params)
        return [self._row_to_task(row) for row in cursor.fetchall()]

    def update_task_status(self, task_id: str, new_status: str,
                            notes: str = "", reviewer: str = "") -> ProjectTask:
        """Advance a task through the workflow with PM gates."""
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        old = task.workflow_status.value
        new = WorkflowStatus(new_status)
        now = time.time()

        # Workflow transition rules
        transitions = {
            WorkflowStatus.DRAFT: [WorkflowStatus.REQUESTED],
            WorkflowStatus.REQUESTED: [WorkflowStatus.PM_REVIEW, WorkflowStatus.CLOSED],
            WorkflowStatus.PM_REVIEW: [WorkflowStatus.APPROVED, WorkflowStatus.REJECTED],
            WorkflowStatus.REJECTED: [WorkflowStatus.DRAFT, WorkflowStatus.CLOSED],
            WorkflowStatus.APPROVED: [WorkflowStatus.ASSIGNED],
            WorkflowStatus.ASSIGNED: [WorkflowStatus.IN_PROGRESS, WorkflowStatus.BLOCKED],
            WorkflowStatus.IN_PROGRESS: [WorkflowStatus.COMPLETED, WorkflowStatus.BLOCKED],
            WorkflowStatus.BLOCKED: [WorkflowStatus.IN_PROGRESS, WorkflowStatus.CLOSED],
            WorkflowStatus.COMPLETED: [WorkflowStatus.PM_VERIFY, WorkflowStatus.IN_PROGRESS],
            WorkflowStatus.PM_VERIFY: [WorkflowStatus.VERIFIED, WorkflowStatus.IN_PROGRESS],
            WorkflowStatus.VERIFIED: [WorkflowStatus.CLOSED],
        }

        allowed = transitions.get(task.workflow_status, [])
        if new not in allowed:
            raise ValueError(
                f"Cannot transition from {task.workflow_status.value} to {new_status}. "
                f"Allowed: {[s.value for s in allowed]}"
            )

        # Update fields based on transition
        task.workflow_status = new
        if notes:
            task.pm_notes = notes

        if new == WorkflowStatus.IN_PROGRESS:
            task.started_at = now
        elif new == WorkflowStatus.COMPLETED:
            task.completed_at = now
            if notes:
                task.completion_notes = notes
        elif new == WorkflowStatus.VERIFIED:
            task.verified_at = now
            if notes:
                task.verification_notes = notes
        elif new == WorkflowStatus.REJECTED and notes:
            task.rejection_reason = notes

        if reviewer:
            task.reviewed_by = reviewer
        if new == WorkflowStatus.ASSIGNED:
            task.assigned_at = now
        elif new == WorkflowStatus.APPROVED:
            if notes:
                task.pm_notes = notes

        # If parent, update parent progress
        if task.parent_id:
            parent = self.get_task(task.parent_id)
            if parent:
                self._update_parent_progress(parent)

        # Update underlying OpsManager
        try:
            self.ops.update_task(task_id, status=new.value, output=notes[:500] if notes else "")
        except Exception:
            pass

        self._save_task(task)
        return task

    def request_help(self, requesting_agent: str, title: str,
                     description: str = "", source_task_id: str = "") -> HelpRequest:
        """An agent requests help from PM. PM can approve and assign a helper."""
        req_id = f"HR{int(time.time())}{uuid.uuid4().hex[:4]}".upper()
        request = HelpRequest(
            id=req_id, requesting_agent=requesting_agent,
            title=title, description=description,
            source_task_id=source_task_id, created_at=time.time(),
        )
        # Save to DB
        self._db.execute("""
            INSERT INTO help_requests (id, requesting_agent, title, description,
                status, source_task_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (request.id, request.requesting_agent, request.title, request.description,
              request.status.value, request.source_task_id, request.created_at))
        self._db.commit()
        return request

    def approve_help(self, request_id: str, assigned_agent: str,
                     pm_notes: str = "") -> HelpRequest:
        """PM approves a help request and assigns a helper agent."""
        cursor = self._db.execute(
            "SELECT * FROM help_requests WHERE id=?", (request_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Help request {request_id} not found")

        request = self._row_to_help_request(row)
        request.status = HelpRequestStatus.APPROVED
        request.assigned_agent = assigned_agent
        if pm_notes:
            request.pm_notes = pm_notes

        self._db.execute(
            "UPDATE help_requests SET status=?, assigned_agent=?, pm_notes=? WHERE id=?",
            (request.status.value, assigned_agent, pm_notes, request_id)
        )
        self._db.commit()

        # Auto-create a task for the assigned helper
        self.create_task(
            title=request.title,
            description=request.description,
            assignee=assigned_agent,
            task_type="subtask",
            parent_id=request.source_task_id or "",
            project="help-request",
        )
        return request

    def list_help_requests(self, status: str = "") -> list[HelpRequest]:
        """List help requests."""
        if status:
            cursor = self._db.execute(
                "SELECT * FROM help_requests WHERE status=? ORDER BY created_at DESC",
                (status,)
            )
        else:
            cursor = self._db.execute(
                "SELECT * FROM help_requests ORDER BY created_at DESC"
            )
        return [self._row_to_help_request(row) for row in cursor.fetchall()]

    def get_agent_capacity(self, agent_name: str = "") -> list[AgentCapacity]:
        """Get capacity for all agents or a specific one."""
        profiles = self.pm.list()
        capacities = []

        for name in profiles:
            if agent_name and name != agent_name:
                continue
            # Count active tasks
            active = self._db.execute(
                "SELECT COUNT(*) FROM project_tasks WHERE assignee=? AND workflow_status IN ('assigned','in_progress')",
                (name,)
            ).fetchone()[0]
            done = self._db.execute(
                "SELECT COUNT(*) FROM project_tasks WHERE assignee=? AND workflow_status='closed'",
                (name,)
            ).fetchone()[0]
            failed = self._db.execute(
                "SELECT COUNT(*) FROM project_tasks WHERE assignee=? AND workflow_status='rejected'",
                (name,)
            ).fetchone()[0]
            capacities.append(AgentCapacity(
                agent_name=name, active_tasks=active,
                total_completed=done, total_failed=failed,
            ))

        return capacities

    # ════════════════════════════════════════════════════════════
    # Auto-Dispatch
    # ════════════════════════════════════════════════════════════

    def auto_dispatch(self, max_per_cycle: int = 3) -> list[dict]:
        """Auto-dispatch approved/assigned tasks to agents based on capacity.

        Returns list of dispatch actions taken.
        """
        actions = []

        # Get tasks in 'assigned' status that need capacity check
        pending = self.list_tasks(workflow_status="assigned")
        capacities = {c.agent_name: c for c in self.get_agent_capacity()}

        for task in pending[:max_per_cycle]:
            cap = capacities.get(task.assignee)
            if cap and cap.available_slots > 0:
                self.update_task_status(task.id, "in_progress",
                                        notes="Auto-dispatched by capacity manager")
                actions.append({
                    "task_id": task.id, "title": task.title[:40],
                    "agent": task.assignee, "action": "dispatched",
                })

        # Also check for tasks that no assigned agent — assign by skill match
        unassigned = self.list_tasks(workflow_status="requested")
        for task in unassigned[:max_per_cycle]:
            best = self._pick_best_agent(phase=task.phase, task_title=task.title,
                                          task_description=task.description)
            if best:
                task.assignee = best
                task.workflow_status = WorkflowStatus.ASSIGNED
                self._save_task(task)
                actions.append({
                    "task_id": task.id, "title": task.title[:40],
                    "agent": best, "action": "assigned",
                })

        return actions

    # ════════════════════════════════════════════════════════════
    # Internal Helpers
    # ════════════════════════════════════════════════════════════

    def _pick_best_agent(self, phase: str = "",
                          task_title: str = "",
                          task_description: str = "",
                          required_skills: list[str] = None) -> str:
        """Pick the best available agent using skill matching + capacity.

        Uses SkillRegistry to match agents by skill, then filters by capacity.
        Falls back to original phase-based matching if registry not available.

        Args:
            phase: Project phase for traditional matching fallback.
            task_title: Task title for skill inference.
            task_description: Task description for skill inference.
            required_skills: Explicit skill requirements (optional).

        Returns:
            Best matching agent name, or empty string.
        """
        capacities = {c.agent_name: c for c in self.get_agent_capacity()}

        # Try skill-based matching first
        try:
            from agentark.interface.skill_registry import get_registry
            registry = get_registry()

            # Build a combined text for skill inference
            search_text = f"{task_title} {task_description} {phase}"

            if search_text.strip() or required_skills:
                results = registry.match_task(
                    description=search_text,
                    required_skills=required_skills,
                    difficulty="L2",
                )

                if results:
                    # Score: skill match (0-1) × available slots (capped at 3)
                    scored = []
                    for r in results[:5]:  # Top 5 skill matches
                        cap = capacities.get(r.agent_name)
                        if cap and cap.available_slots > 0:
                            # skill score (0-1) + capacity bonus
                            score = r.match_score * 10 + min(cap.available_slots, 3) * 0.5
                            scored.append((score, r.agent_name, r.match_score, r.details))

                    if scored:
                        scored.sort(reverse=True)
                        best = scored[0][1]
                        return best
        except ImportError:
            pass
        except Exception:
            pass

        # Fallback to original phase-based matching
        role_map = {
            "frontend": ["frontend-dev", "frontend"],
            "backend": ["backend", "developer", "architect"],
            "design": ["pm"],
            "ops": ["devops"],
            "content": ["writer", "content", "copywriter"],
        }
        preferred = role_map.get(phase.lower(), [])

        scored = []
        for cap in self.get_agent_capacity():
            preference_bonus = 10 if cap.agent_name in preferred else 0
            scored.append((cap.available_slots + preference_bonus, cap.agent_name))

        scored.sort(reverse=True)
        if scored and scored[0][0] > 0:
            return scored[0][1]
        return ""

    def _update_parent_progress(self, parent: ProjectTask):
        """Recalculate parent progress from sub-tasks."""
        if not parent.sub_task_ids:
            return
        completed = 0
        total = len(parent.sub_task_ids)
        for sub_id in parent.sub_task_ids:
            sub = self.get_task(sub_id)
            if sub:
                if sub.workflow_status in (WorkflowStatus.VERIFIED, WorkflowStatus.CLOSED, WorkflowStatus.COMPLETED):
                    completed += 1
        parent.progress_pct = round(completed / total * 100, 1)
        self._save_task(parent)

    def _save_task(self, task: ProjectTask):
        """Save task to project_tasks table."""
        self._db.execute("""
            INSERT OR REPLACE INTO project_tasks
            (id, title, description, task_type, workflow_status, phase, priority,
             assignee, requested_by, reviewed_by,
             parent_id, epic_id, depends_on, sub_task_ids,
             progress_pct, estimated_hours, actual_hours,
             pm_notes, rejection_reason, completion_notes, verification_notes,
             help_requests, project, tags,
             created_at, assigned_at, started_at, completed_at, verified_at,
             estimated_cost, actual_cost)
            VALUES (?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?)
        """, (
            task.id, task.title, task.description, task.task_type.value,
            task.workflow_status.value, task.phase, task.priority,
            task.assignee, task.requested_by, task.reviewed_by,
            task.parent_id, task.epic_id,
            json.dumps(task.depends_on), json.dumps(task.sub_task_ids),
            task.progress_pct, task.estimated_hours, task.actual_hours,
            task.pm_notes, task.rejection_reason, task.completion_notes,
            task.verification_notes,
            json.dumps(task.help_requests), task.project, json.dumps(task.tags),
            task.created_at, task.assigned_at, task.started_at,
            task.completed_at, task.verified_at,
            task.estimated_cost, task.actual_cost,
        ))
        self._db.commit()

    def _row_to_task(self, row) -> ProjectTask:
        """Convert a DB row to ProjectTask."""
        return ProjectTask(
            id=row[0], title=row[1], description=row[2] or "",
            task_type=TaskType(row[3]), workflow_status=WorkflowStatus(row[4]),
            phase=row[5] or "development", priority=row[6] or 2,
            assignee=row[7] or "", requested_by=row[8] or "",
            reviewed_by=row[9] or "",
            parent_id=row[10], epic_id=row[11],
            depends_on=json.loads(row[12]) if row[12] else [],
            sub_task_ids=json.loads(row[13]) if row[13] else [],
            progress_pct=row[14] or 0.0,
            estimated_hours=row[15] or 0.0, actual_hours=row[16] or 0.0,
            pm_notes=row[17] or "", rejection_reason=row[18] or "",
            completion_notes=row[19] or "", verification_notes=row[20] or "",
            help_requests=json.loads(row[21]) if row[21] else [],
            project=row[22] or "", tags=json.loads(row[23]) if row[23] else [],
            created_at=row[24] or 0.0, assigned_at=row[25],
            started_at=row[26], completed_at=row[27], verified_at=row[28],
            estimated_cost=row[29] or 0.0, actual_cost=row[30] or 0.0,
        )

    @staticmethod
    def _row_to_help_request(row) -> HelpRequest:
        return HelpRequest(
            id=row[0], requesting_agent=row[1], title=row[2],
            description=row[3] or "", status=HelpRequestStatus(row[4]),
            source_task_id=row[5] or "", assigned_agent=row[6] or "",
            pm_notes=row[7] or "", created_at=row[8] or 0.0,
            resolved_at=row[9],
        )

    def _init_db(self):
        """Initialize the project_tasks and help_requests tables."""
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS project_tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                task_type TEXT DEFAULT 'task',
                workflow_status TEXT DEFAULT 'draft',
                phase TEXT DEFAULT 'development',
                priority INTEGER DEFAULT 2,
                assignee TEXT DEFAULT '',
                requested_by TEXT DEFAULT '',
                reviewed_by TEXT DEFAULT '',
                parent_id TEXT,
                epic_id TEXT,
                depends_on TEXT DEFAULT '[]',
                sub_task_ids TEXT DEFAULT '[]',
                progress_pct REAL DEFAULT 0.0,
                estimated_hours REAL DEFAULT 0.0,
                actual_hours REAL DEFAULT 0.0,
                pm_notes TEXT DEFAULT '',
                rejection_reason TEXT DEFAULT '',
                completion_notes TEXT DEFAULT '',
                verification_notes TEXT DEFAULT '',
                help_requests TEXT DEFAULT '[]',
                project TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                created_at REAL,
                assigned_at REAL,
                started_at REAL,
                completed_at REAL,
                verified_at REAL,
                estimated_cost REAL DEFAULT 0.0,
                actual_cost REAL DEFAULT 0.0
            )
        """)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS help_requests (
                id TEXT PRIMARY KEY,
                requesting_agent TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                source_task_id TEXT DEFAULT '',
                assigned_agent TEXT DEFAULT '',
                pm_notes TEXT DEFAULT '',
                created_at REAL,
                resolved_at REAL
            )
        """)
        self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_tasks_assignee ON project_tasks(assignee)
        """)
        self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_tasks_status ON project_tasks(workflow_status)
        """)
        self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_tasks_project ON project_tasks(project)
        """)
        self._db.commit()


# Global singleton
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """Get or create the global TaskManager singleton."""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
        _task_manager._init_db()
    return _task_manager
