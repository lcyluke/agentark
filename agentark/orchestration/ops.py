"""Multi-agent operation management system for task lifecycle, bug tracking, and release pipelines."""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from enum import Enum

from agentark.core.profile import AGENTARK_HOME


# ════════════════════════════════════════════════════════════════════
# Enums
# ════════════════════════════════════════════════════════════════════

class TaskStatus(str, Enum):
    TODO = "todo"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    BLOCKED = "blocked"
    DONE = "done"
    FAILED = "failed"

class BugSeverity(str, Enum):
    CRITICAL = "critical"   # P0: <2h SLA
    HIGH = "high"           # P1: <8h SLA
    MEDIUM = "medium"       # P2: <24h SLA
    LOW = "low"             # P3: <72h SLA

class BugStatus(str, Enum):
    NEW = "new"
    TRIAGED = "triaged"
    ASSIGNED = "assigned"
    FIXING = "fixing"
    FIXED = "fixed"
    VERIFIED = "verified"
    CLOSED = "closed"

class ReleaseStage(str, Enum):
    CODE_FREEZE = "code_freeze"
    BUILD = "build"
    UNIT_TEST = "unit_test"
    INTEGRATION = "integration"
    UAT_DEPLOY = "uat_deploy"
    UAT_TESTING = "uat_testing"
    BUG_FIX = "bug_fix"
    SIGN_OFF = "sign_off"
    RELEASE = "release"
    MONITOR = "monitor"


# ════════════════════════════════════════════════════════════════════
# Data Models
# ════════════════════════════════════════════════════════════════════

@dataclass
class OpsTask:
    """Operational task — basic unit of all work"""
    id: str
    title: str
    description: str
    phase: str = "development"
    status: TaskStatus = TaskStatus.TODO
    priority: int = 2
    agent_id: str = ""
    depends_on: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    parent_id: Optional[str] = None
    subtasks: list[str] = field(default_factory=list)
    estimated_hours: float = 0
    actual_hours: float = 0
    quality_score: float = 0.0
    test_pass_count: int = 0
    test_total_count: int = 0
    output: str = ""
    bugs: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    @property
    def test_pass_rate(self) -> float:
        if self.test_total_count == 0:
            return 0.0
        return self.test_pass_count / self.test_total_count

    @property
    def age_hours(self) -> float:
        start = self.started_at or self.created_at
        return (time.time() - start) / 3600


@dataclass
class Bug:
    """Bug/Issue — full lifecycle tracking"""
    id: str
    title: str
    description: str
    severity: BugSeverity = BugSeverity.MEDIUM
    status: BugStatus = BugStatus.NEW
    source: str = "uat"  # uat / ci / exploration / user_report
    environment: str = "uat"
    steps_to_reproduce: str = ""
    expected_result: str = ""
    actual_result: str = ""
    stack_trace: str = ""
    assigned_agent: str = ""
    related_task: Optional[str] = None
    related_bugs: list[str] = field(default_factory=list)
    fix_attempts: list[dict] = field(default_factory=list)
    resolution: str = ""
    created_at: float = 0.0
    resolved_at: Optional[float] = None
    sla_deadline: float = 0.0
    tags: list[str] = field(default_factory=list)

    @property
    def sla_remaining_hours(self) -> float:
        return max(0, (self.sla_deadline - time.time()) / 3600)

    @property
    def sla_breached(self) -> bool:
        return time.time() > self.sla_deadline and self.status not in (BugStatus.VERIFIED, BugStatus.CLOSED)


@dataclass
class ReleasePipeline:
    """Release pipeline — manage entire release lifecycle"""
    id: str
    version: str
    name: str
    status: str = "planning"
    stages: list[dict] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    changelog: list[dict] = field(default_factory=list)
    blockers: list[dict] = field(default_factory=list)
    signoffs: list[dict] = field(default_factory=list)
    rollback_plan: str = ""
    created_at: float = 0.0
    released_at: Optional[float] = None

    @property
    def progress_pct(self) -> float:
        if not self.stages:
            return 0.0
        done = sum(1 for s in self.stages if s.get("status") == "done")
        return done / len(self.stages)


@dataclass
class ExpertTicket:
    """Expert consultation ticket"""
    id: str
    title: str
    description: str
    requester: str
    expert: str
    status: str = "open"
    knowledge_base_hits: list[str] = field(default_factory=list)
    resolution: str = ""
    created_at: float = 0.0
    resolved_at: Optional[float] = None


# ════════════════════════════════════════════════════════════════════
# Ops Manager — Unified Operations Database
# ════════════════════════════════════════════════════════════════════

class OpsManager:
    """Central operations manager — tasks, bugs, releases, experts"""

    def __init__(self, db_path: Path = AGENTARK_HOME / "ops.db"):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT DEFAULT '',
                phase TEXT DEFAULT 'development', status TEXT DEFAULT 'todo',
                priority INTEGER DEFAULT 2, agent_id TEXT DEFAULT '',
                depends_on TEXT DEFAULT '[]', dependents TEXT DEFAULT '[]',
                parent_id TEXT, subtasks TEXT DEFAULT '[]',
                estimated_hours REAL DEFAULT 0, actual_hours REAL DEFAULT 0,
                quality_score REAL DEFAULT 0,
                test_pass_count INTEGER DEFAULT 0, test_total_count INTEGER DEFAULT 0,
                output TEXT DEFAULT '', bugs TEXT DEFAULT '[]', tags TEXT DEFAULT '[]',
                created_at REAL DEFAULT (julianday('now')),
                started_at REAL, completed_at REAL
            );
            CREATE TABLE IF NOT EXISTS bugs (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT DEFAULT '',
                severity TEXT DEFAULT 'medium', status TEXT DEFAULT 'new',
                source TEXT DEFAULT 'uat', environment TEXT DEFAULT 'uat',
                steps_to_reproduce TEXT DEFAULT '', expected_result TEXT DEFAULT '',
                actual_result TEXT DEFAULT '', stack_trace TEXT DEFAULT '',
                assigned_agent TEXT DEFAULT '', related_task TEXT,
                related_bugs TEXT DEFAULT '[]', fix_attempts TEXT DEFAULT '[]',
                resolution TEXT DEFAULT '', sla_deadline REAL DEFAULT 0,
                created_at REAL DEFAULT (julianday('now')),
                resolved_at REAL, tags TEXT DEFAULT '[]'
            );
            CREATE TABLE IF NOT EXISTS releases (
                id TEXT PRIMARY KEY, version TEXT NOT NULL, name TEXT DEFAULT '',
                status TEXT DEFAULT 'planning', stages TEXT DEFAULT '[]',
                artifacts TEXT DEFAULT '[]', changelog TEXT DEFAULT '[]',
                blockers TEXT DEFAULT '[]', signoffs TEXT DEFAULT '[]',
                rollback_plan TEXT DEFAULT '',
                created_at REAL DEFAULT (julianday('now')), released_at REAL
            );
            CREATE TABLE IF NOT EXISTS expert_tickets (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT DEFAULT '',
                requester TEXT DEFAULT '', expert TEXT DEFAULT '',
                status TEXT DEFAULT 'open', knowledge_base_hits TEXT DEFAULT '[]',
                resolution TEXT DEFAULT '',
                created_at REAL DEFAULT (julianday('now')), resolved_at REAL
            );
            CREATE TABLE IF NOT EXISTS agent_work_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL, task_id TEXT NOT NULL,
                action TEXT DEFAULT '', detail TEXT DEFAULT '',
                duration_ms INTEGER DEFAULT 0, status TEXT DEFAULT 'info',
                created_at REAL DEFAULT (julianday('now'))
            );
        """)
        self._conn.commit()

    # ════════════════════════════════════════════════════════════
    # Tasks
    # ════════════════════════════════════════════════════════════

    def create_task(self, title: str, **kwargs) -> OpsTask:
        task_id = f"T{int(time.time())}{uuid.uuid4().hex[:4]}".upper()
        task = OpsTask(
            id=task_id, title=title,
            description=kwargs.get("description", ""),
            phase=kwargs.get("phase", "development"),
            status=TaskStatus(kwargs.get("status", "todo")),
            priority=kwargs.get("priority", 2),
            agent_id=kwargs.get("agent_id", ""),
            depends_on=kwargs.get("depends_on", []),
            parent_id=kwargs.get("parent_id"),
            estimated_hours=kwargs.get("estimated_hours", 0),
            tags=kwargs.get("tags", []),
            created_at=time.time(),
        )
        self._conn.execute(
            """INSERT INTO tasks (id, title, description, phase, status, priority,
               agent_id, depends_on, parent_id, estimated_hours, tags, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (task.id, task.title, task.description, task.phase, task.status.value,
             task.priority, task.agent_id, json.dumps(task.depends_on),
             task.parent_id, task.estimated_hours, json.dumps(task.tags), task.created_at),
        )
        self._conn.commit()
        self._log_work(kwargs.get("agent_id", "system"), task.id, "created", str(task.id))
        return task

    def update_task(self, task_id: str, **updates):
        allowed = {"status", "agent_id", "priority", "phase", "output",
                   "quality_score", "test_pass_count", "test_total_count",
                   "actual_hours", "completed_at", "started_at"}
        sets = ["status=?", "status=?"]  # placeholder
        sets = []
        values = []
        for k, v in updates.items():
            if k in ("depends_on", "dependents", "subtasks", "bugs", "tags"):
                sets.append(f"{k}=?")
                values.append(json.dumps(v))
            elif k in allowed:
                sets.append(f"{k}=?")
                if isinstance(v, Enum):
                    values.append(v.value)
                else:
                    values.append(v)
        if not sets:
            return
        values.append(task_id)
        self._conn.execute(f"UPDATE tasks SET {', '.join(sets)} WHERE id=?", values)
        self._conn.commit()

    def get_task(self, task_id: str) -> Optional[OpsTask]:
        cursor = self._conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
        row = cursor.fetchone()
        return self._row_to_task(row) if row else None

    def list_tasks(self, status: str = None, agent_id: str = None,
                   phase: str = None, priority: int = None, limit: int = 100) -> list[OpsTask]:
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        if status:
            query += " AND status=?"
            params.append(status)
        if agent_id:
            query += " AND agent_id=?"
            params.append(agent_id)
        if phase:
            query += " AND phase=?"
            params.append(phase)
        if priority is not None:
            query += " AND priority=?"
            params.append(priority)
        query += " ORDER BY priority, created_at ASC LIMIT ?"
        params.append(limit)
        cursor = self._conn.execute(query, params)
        return [self._row_to_task(r) for r in cursor.fetchall()]

    def _row_to_task(self, row) -> OpsTask:
        return OpsTask(
            id=row["id"], title=row["title"], description=row["description"],
            phase=row["phase"], status=TaskStatus(row["status"]),
            priority=row["priority"], agent_id=row["agent_id"],
            depends_on=json.loads(row["depends_on"]) if row["depends_on"] else [],
            dependents=json.loads(row["dependents"]) if row["dependents"] else [],
            parent_id=row["parent_id"],
            subtasks=json.loads(row["subtasks"]) if row["subtasks"] else [],
            estimated_hours=row["estimated_hours"], actual_hours=row["actual_hours"],
            quality_score=row["quality_score"],
            test_pass_count=row["test_pass_count"], test_total_count=row["test_total_count"],
            output=row["output"],
            bugs=json.loads(row["bugs"]) if row["bugs"] else [],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            created_at=row["created_at"], started_at=row["started_at"],
            completed_at=row["completed_at"],
        )

    # ════════════════════════════════════════════════════════════
    # Bugs
    # ════════════════════════════════════════════════════════════

    SLA_HOURS = {"critical": 2, "high": 8, "medium": 24, "low": 72}

    def create_bug(self, title: str, description: str, severity: str = "medium",
                   **kwargs) -> Bug:
        bug_id = f"B{int(time.time())}{uuid.uuid4().hex[:4]}".upper()
        sla = self.SLA_HOURS.get(severity, 24)
        bug = Bug(
            id=bug_id, title=title, description=description,
            severity=BugSeverity(severity), source=kwargs.get("source", "uat"),
            environment=kwargs.get("environment", "uat"),
            steps_to_reproduce=kwargs.get("steps_to_reproduce", ""),
            expected_result=kwargs.get("expected_result", ""),
            actual_result=kwargs.get("actual_result", ""),
            stack_trace=kwargs.get("stack_trace", ""),
            assigned_agent=kwargs.get("assigned_agent", ""),
            related_task=kwargs.get("related_task"),
            sla_deadline=time.time() + sla * 3600,
            tags=kwargs.get("tags", []),
            created_at=time.time(),
        )
        self._conn.execute(
            """INSERT INTO bugs (id, title, description, severity, status, source,
               environment, steps_to_reproduce, expected_result, actual_result,
               stack_trace, assigned_agent, related_task, sla_deadline, tags, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (bug.id, bug.title, bug.description, bug.severity.value, bug.status.value,
             bug.source, bug.environment, bug.steps_to_reproduce, bug.expected_result,
             bug.actual_result, bug.stack_trace, bug.assigned_agent, bug.related_task,
             bug.sla_deadline, json.dumps(bug.tags), bug.created_at),
        )
        self._conn.commit()
        return bug

    def update_bug(self, bug_id: str, **updates):
        allowed = {"status", "severity", "assigned_agent", "resolution",
                   "resolved_at", "environment"}
        sets = []
        values = []
        for k, v in updates.items():
            if k in ("related_bugs", "fix_attempts", "tags"):
                sets.append(f"{k}=?")
                values.append(json.dumps(v))
            elif k in allowed:
                sets.append(f"{k}=?")
                if isinstance(v, Enum):
                    values.append(v.value)
                else:
                    values.append(v)
        if not sets:
            return
        values.append(bug_id)
        self._conn.execute(f"UPDATE bugs SET {', '.join(sets)} WHERE id=?", values)
        self._conn.commit()

    def list_bugs(self, status: str = None, severity: str = None,
                  agent: str = None, limit: int = 50) -> list[Bug]:
        query = "SELECT * FROM bugs WHERE 1=1"
        params = []
        if status:
            if status == "open":
                query += " AND status NOT IN ('verified','closed')"
            else:
                query += " AND status=?"
                params.append(status)
        if severity:
            query += " AND severity=?"
            params.append(severity)
        if agent:
            query += " AND assigned_agent=?"
            params.append(agent)
        query += " ORDER BY CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, created_at ASC LIMIT ?"
        params.append(limit)
        cursor = self._conn.execute(query, params)
        return [self._row_to_bug(r) for r in cursor.fetchall()]

    def _row_to_bug(self, row) -> Bug:
        return Bug(
            id=row["id"], title=row["title"], description=row["description"],
            severity=BugSeverity(row["severity"]),
            status=BugStatus(row["status"]),
            source=row["source"], environment=row["environment"],
            steps_to_reproduce=row["steps_to_reproduce"],
            expected_result=row["expected_result"], actual_result=row["actual_result"],
            stack_trace=row["stack_trace"], assigned_agent=row["assigned_agent"],
            related_task=row["related_task"],
            related_bugs=json.loads(row["related_bugs"]) if row["related_bugs"] else [],
            fix_attempts=json.loads(row["fix_attempts"]) if row["fix_attempts"] else [],
            resolution=row["resolution"],
            sla_deadline=row["sla_deadline"], created_at=row["created_at"],
            resolved_at=row["resolved_at"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
        )

    def get_bug(self, bug_id: str) -> Optional[Bug]:
        cursor = self._conn.execute("SELECT * FROM bugs WHERE id=?", (bug_id,))
        row = cursor.fetchone()
        return self._row_to_bug(row) if row else None

    # ════════════════════════════════════════════════════════════
    # Releases
    # ════════════════════════════════════════════════════════════

    RELEASE_STAGES = [
        {"name": "code_freeze", "label": "Code Freeze", "order": 1},
        {"name": "build", "label": "Build & Version", "order": 2},
        {"name": "unit_test", "label": "Unit Tests", "order": 3},
        {"name": "integration", "label": "Integration Tests", "order": 4},
        {"name": "uat_deploy", "label": "UAT Deploy", "order": 5},
        {"name": "uat_testing", "label": "UAT Testing", "order": 6},
        {"name": "bug_fix", "label": "Bug Fix", "order": 7},
        {"name": "sign_off", "label": "Sign-off", "order": 8},
        {"name": "release", "label": "Release", "order": 9},
        {"name": "monitor", "label": "Post-Release Monitor", "order": 10},
    ]

    def create_release(self, version: str, name: str = "") -> ReleasePipeline:
        rel_id = f"R{int(time.time())}{uuid.uuid4().hex[:4]}".upper()
        stages = [{"name": s["name"], "label": s["label"], "order": s["order"],
                    "status": "pending", "agent": "", "completed_at": None}
                  for s in self.RELEASE_STAGES]
        release = ReleasePipeline(
            id=rel_id, version=version, name=name or f"Release {version}",
            stages=stages, created_at=time.time(),
        )
        self._conn.execute(
            """INSERT INTO releases (id, version, name, stages, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (release.id, release.version, release.name,
             json.dumps(stages), release.created_at),
        )
        self._conn.commit()
        return release

    def update_release_stage(self, release_id: str, stage_name: str,
                              status: str, agent: str = ""):
        cursor = self._conn.execute("SELECT stages FROM releases WHERE id=?",
                                     (release_id,))
        row = cursor.fetchone()
        if not row:
            return
        stages = json.loads(row["stages"])
        for s in stages:
            if s["name"] == stage_name:
                s["status"] = status
                if agent:
                    s["agent"] = agent
                if status == "done":
                    s["completed_at"] = time.time()
                break
        self._conn.execute("UPDATE releases SET stages=? WHERE id=?",
                           (json.dumps(stages), release_id))
        self._conn.commit()

    def get_release(self, release_id: str) -> Optional[ReleasePipeline]:
        cursor = self._conn.execute("SELECT * FROM releases WHERE id=?", (release_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return ReleasePipeline(
            id=row["id"], version=row["version"], name=row["name"],
            status=row["status"],
            stages=json.loads(row["stages"]) if row["stages"] else [],
            artifacts=json.loads(row["artifacts"]) if row["artifacts"] else [],
            changelog=json.loads(row["changelog"]) if row["changelog"] else [],
            blockers=json.loads(row["blockers"]) if row["blockers"] else [],
            signoffs=json.loads(row["signoffs"]) if row["signoffs"] else [],
            rollback_plan=row["rollback_plan"],
            created_at=row["created_at"], released_at=row["released_at"],
        )

    def list_releases(self, limit: int = 10) -> list[ReleasePipeline]:
        cursor = self._conn.execute(
            "SELECT * FROM releases ORDER BY created_at DESC LIMIT ?", (limit,))
        return [self._row_to_release(r) for r in cursor.fetchall()]

    def _row_to_release(self, row) -> ReleasePipeline:
        return ReleasePipeline(
            id=row["id"], version=row["version"], name=row["name"],
            status=row["status"],
            stages=json.loads(row["stages"]) if row["stages"] else [],
            artifacts=json.loads(row["artifacts"]) if row["artifacts"] else [],
            changelog=json.loads(row["changelog"]) if row["changelog"] else [],
            blockers=json.loads(row["blockers"]) if row["blockers"] else [],
            signoffs=json.loads(row["signoffs"]) if row["signoffs"] else [],
            rollback_plan=row["rollback_plan"],
            created_at=row["created_at"], released_at=row["released_at"],
        )

    # ════════════════════════════════════════════════════════════
    # Expert Tickets
    # ════════════════════════════════════════════════════════════

    def create_expert_ticket(self, title: str, description: str,
                              requester: str, expert: str) -> ExpertTicket:
        ticket_id = f"E{int(time.time())}{uuid.uuid4().hex[:4]}".upper()
        ticket = ExpertTicket(
            id=ticket_id, title=title, description=description,
            requester=requester, expert=expert, created_at=time.time(),
        )
        self._conn.execute(
            """INSERT INTO expert_tickets (id, title, description, requester, expert, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (ticket.id, ticket.title, ticket.description, ticket.requester,
             ticket.expert, ticket.created_at),
        )
        self._conn.commit()
        return ticket

    def resolve_expert_ticket(self, ticket_id: str, resolution: str):
        self._conn.execute(
            "UPDATE expert_tickets SET status='resolved', resolution=?, resolved_at=? WHERE id=?",
            (resolution, time.time(), ticket_id),
        )
        self._conn.commit()

    def list_expert_tickets(self, status: str = None, limit: int = 20) -> list[ExpertTicket]:
        query = "SELECT * FROM expert_tickets"
        params = []
        if status:
            query += " WHERE status=?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cursor = self._conn.execute(query, params)
        return [ExpertTicket(
            id=r["id"], title=r["title"], description=r["description"],
            requester=r["requester"], expert=r["expert"],
            status=r["status"],
            knowledge_base_hits=json.loads(r["knowledge_base_hits"]) if r["knowledge_base_hits"] else [],
            resolution=r["resolution"],
            created_at=r["created_at"], resolved_at=r["resolved_at"],
        ) for r in cursor.fetchall()]

    # ════════════════════════════════════════════════════════════
    # Work Log
    # ════════════════════════════════════════════════════════════

    def _log_work(self, agent_id: str, task_id: str, action: str, detail: str = "",
                  duration_ms: int = 0, status: str = "info"):
        self._conn.execute(
            """INSERT INTO agent_work_log (agent_id, task_id, action, detail, duration_ms, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (agent_id, task_id, action, detail[:500], duration_ms, status),
        )
        self._conn.commit()

    def get_agent_log(self, agent_id: str, limit: int = 50) -> list[dict]:
        cursor = self._conn.execute(
            """SELECT * FROM agent_work_log WHERE agent_id=? ORDER BY created_at DESC LIMIT ?""",
            (agent_id, limit),
        )
        return [dict(r) for r in cursor.fetchall()]

    # ════════════════════════════════════════════════════════════
    # Dashboard Stats
    # ════════════════════════════════════════════════════════════

    def get_dashboard_stats(self) -> dict:
        """Aggregate stats for the ops dashboard"""
        tasks_total = self._conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        tasks_done = self._conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE status='done'").fetchone()[0]
        tasks_blocked = self._conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE status='blocked'").fetchone()[0]

        bugs_open = self._conn.execute(
            "SELECT COUNT(*) FROM bugs WHERE status NOT IN ('verified','closed')"
        ).fetchone()[0]
        bugs_critical = self._conn.execute(
            "SELECT COUNT(*) FROM bugs WHERE severity='critical' AND status NOT IN ('verified','closed')"
        ).fetchone()[0]
        bugs_sla_breached = self._conn.execute(
            "SELECT COUNT(*) FROM bugs WHERE sla_deadline < ? AND status NOT IN ('verified','closed')",
            (time.time(),),
        ).fetchone()[0]

        releases_active = self._conn.execute(
            "SELECT COUNT(*) FROM releases WHERE status NOT IN ('released','rollback')"
        ).fetchone()[0]

        experts_open = self._conn.execute(
            "SELECT COUNT(*) FROM expert_tickets WHERE status='open'"
        ).fetchone()[0]

        # Active agents (from tasks)
        cursor = self._conn.execute(
            "SELECT DISTINCT agent_id FROM tasks WHERE status='in_progress'"
        )
        active_agents = [r[0] for r in cursor.fetchall() if r[0]]

        return {
            "tasks": {"total": tasks_total, "done": tasks_done,
                      "blocked": tasks_blocked,
                      "completion_pct": round(tasks_done / tasks_total * 100, 1) if tasks_total else 0},
            "bugs": {"open": bugs_open, "critical": bugs_critical,
                     "sla_breached": bugs_sla_breached},
            "releases": {"active": releases_active},
            "expert_tickets": {"open": experts_open},
            "active_agents": active_agents,
        }


# Global singleton
_ops_instance: Optional[OpsManager] = None

def get_ops() -> OpsManager:
    global _ops_instance
    if _ops_instance is None:
        _ops_instance = OpsManager()
    return _ops_instance
