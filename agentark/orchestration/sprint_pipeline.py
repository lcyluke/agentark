"""Sprint Pipeline — MVP closed-loop development pipeline.

📝 PLAN ──👤 design-approval ──→ ⚙️ BUILD ──🤖──→ 🧪 VERIFY ──👤 ship-approval ──→ 🚀 SHIP ──🤖──→ 🔄 LEARN

Two manual gates (design approval + ship approval), everything else auto-advances.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

AGENTARK_HOME = Path(os.environ.get("AGENTARK_HOME", os.path.expanduser("~/.apex")))
SPRINTS_DB = AGENTARK_HOME / "sprints.db"

# ═══════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════

PHASES = ["plan", "build", "verify", "ship", "learn"]

PHASE_META = {
    "plan": {
        "display": "📝 PLAN",
        "agent_solo": "product-manager",
        "agent_swarm": ["product-manager", "architect"],
        "description": "需求定义 + 技术设计 + API 契约",
        "gate": "manual",
        "gate_name": "设计审批",
    },
    "build": {
        "display": "⚙️ BUILD",
        "agent_solo": "fullstack-dev",
        "agent_swarm": ["frontend-dev", "backend-dev"],
        "description": "前后端开发",
        "gate": "auto",
        "gate_name": "契约测试",
    },
    "verify": {
        "display": "🧪 VERIFY",
        "agent_solo": "qa-engineer",
        "agent_swarm": ["qa-engineer", "test-agent"],
        "description": "集成测试 + 覆盖率检查",
        "gate": "auto",
        "gate_name": "测试门控",
    },
    "ship": {
        "display": "🚀 SHIP",
        "agent_solo": "devops",
        "agent_swarm": ["devops", "ops-engineer"],
        "description": "部署预览",
        "gate": "manual",
        "gate_name": "发版审批",
    },
    "learn": {
        "display": "🔄 LEARN",
        "agent_solo": "apex-pm",
        "agent_swarm": ["session-scout", "apex-pm"],
        "description": "用户反馈收集 + 下一轮规划",
        "gate": "auto",
        "gate_name": "自动循环",
    },
}


# ═══════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════


@dataclass
class PhaseRecord:
    """One phase in a sprint."""

    name: str
    status: str = "pending"  # pending | active | done | rejected
    agent: str = ""
    started_at: str = ""
    completed_at: str = ""
    hours_spent: float = 0.0
    output: str = ""
    gate: str = "auto"  # auto | manual
    gate_status: str = "pending"  # pending | approved | rejected
    gate_name: str = ""


@dataclass
class Sprint:
    """A complete sprint through the MVP pipeline."""

    id: str = ""
    goal: str = ""
    mode: str = "solo"  # solo | swarm
    current_phase: str = "plan"
    iteration: int = 1
    status: str = "active"  # active | completed | cancelled
    phases: list[PhaseRecord] = field(default_factory=list)
    created_at: str = ""
    completed_at: str = ""

    @property
    def progress_pct(self) -> int:
        """Percentage of phases completed."""
        done = sum(1 for p in self.phases if p.status == "done")
        return int(done / len(PHASES) * 100)

    @property
    def total_hours(self) -> float:
        return sum(p.hours_spent for p in self.phases)

    @property
    def current_gate(self) -> Optional[PhaseRecord]:
        for p in self.phases:
            if p.status == "done" and p.gate == "manual" and p.gate_status == "pending":
                return p
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "mode": self.mode,
            "current_phase": self.current_phase,
            "iteration": self.iteration,
            "status": self.status,
            "progress_pct": self.progress_pct,
            "total_hours": self.total_hours,
            "current_gate": (
                {
                    "name": self.current_gate.name,
                    "gate_name": self.current_gate.gate_name,
                }
                if self.current_gate
                else None
            ),
            "phases": [
                {
                    "name": p.name,
                    "status": p.status,
                    "agent": p.agent,
                    "hours_spent": p.hours_spent,
                    "gate": p.gate,
                    "gate_status": p.gate_status,
                    "gate_name": p.gate_name,
                    "display": PHASE_META.get(p.name, {}).get("display", p.name),
                }
                for p in self.phases
            ],
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


# ═══════════════════════════════════════════════════════════
# Database Layer
# ═══════════════════════════════════════════════════════════


def _get_db() -> sqlite3.Connection:
    """Get or create the sprints database."""
    conn = sqlite3.connect(str(SPRINTS_DB))
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sprints (
            id TEXT PRIMARY KEY,
            goal TEXT NOT NULL,
            mode TEXT DEFAULT 'solo',
            current_phase TEXT DEFAULT 'plan',
            iteration INTEGER DEFAULT 1,
            status TEXT DEFAULT 'active',
            phases_json TEXT DEFAULT '[]',
            created_at TEXT,
            completed_at TEXT
        )
    """
    )
    conn.commit()
    return conn


def _row_to_sprint(row: sqlite3.Row) -> Sprint:
    """Convert a DB row to a Sprint object."""
    phases_data = json.loads(row["phases_json"] or "[]")
    phases = [
        PhaseRecord(
            name=p.get("name", ""),
            status=p.get("status", "pending"),
            agent=p.get("agent", ""),
            started_at=p.get("started_at", ""),
            completed_at=p.get("completed_at", ""),
            hours_spent=p.get("hours_spent", 0.0),
            output=p.get("output", ""),
            gate=p.get("gate", "auto"),
            gate_status=p.get("gate_status", "pending"),
            gate_name=p.get("gate_name", ""),
        )
        for p in phases_data
    ]
    return Sprint(
        id=row["id"],
        goal=row["goal"],
        mode=row["mode"],
        current_phase=row["current_phase"],
        iteration=row["iteration"],
        status=row["status"],
        phases=phases,
        created_at=row["created_at"] or "",
        completed_at=row["completed_at"] or "",
    )


# ═══════════════════════════════════════════════════════════
# Sprint Pipeline Manager
# ═══════════════════════════════════════════════════════════


class SprintManager:
    """Create, manage, and advance sprints through the MVP pipeline."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or SPRINTS_DB
        self.db = self._get_db()

    def _get_db(self) -> sqlite3.Connection:
        """Get or create the sprints database."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sprints (
                id TEXT PRIMARY KEY,
                goal TEXT NOT NULL,
                mode TEXT DEFAULT 'solo',
                current_phase TEXT DEFAULT 'plan',
                iteration INTEGER DEFAULT 1,
                status TEXT DEFAULT 'active',
                phases_json TEXT DEFAULT '[]',
                created_at TEXT,
                completed_at TEXT
            )
        """
        )
        conn.commit()
        return conn

    def create(self, goal: str, mode: str = "solo") -> Sprint:
        """Create a new sprint.

        Args:
            goal: One-sentence description of what to build.
            mode: 'solo' for single fullstack agent, 'swarm' for frontend+backend.

        Returns:
            The newly created Sprint.
        """
        sprint_id = f"sprint_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()

        # Build phase records
        phases = []
        for ph in PHASES:
            meta = PHASE_META[ph]
            agent = meta["agent_solo"] if mode == "solo" else ", ".join(meta["agent_swarm"])
            phases.append(
                {
                    "name": ph,
                    "status": "active" if ph == "plan" else "pending",
                    "agent": agent,
                    "started_at": now if ph == "plan" else "",
                    "completed_at": "",
                    "hours_spent": 0.0,
                    "output": "",
                    "gate": meta["gate"],
                    "gate_status": "pending",
                    "gate_name": meta["gate_name"],
                }
            )

        self.db.execute(
            """
            INSERT INTO sprints (id, goal, mode, current_phase, iteration, status, phases_json, created_at)
            VALUES (?, ?, ?, 'plan', 1, 'active', ?, ?)
            """,
            (sprint_id, goal, mode, json.dumps(phases), now),
        )
        self.db.commit()

        sprint = self.get(sprint_id)
        if not sprint:
            raise RuntimeError(f"Failed to create sprint {sprint_id}")
        return sprint

    def get(self, sprint_id: str) -> Optional[Sprint]:
        """Get a sprint by ID."""
        row = self.db.execute("SELECT * FROM sprints WHERE id = ?", (sprint_id,)).fetchone()
        if not row:
            return None
        return _row_to_sprint(row)

    def list_all(self, status: Optional[str] = None) -> list[Sprint]:
        """List all sprints, optionally filtered by status."""
        if status:
            rows = self.db.execute(
                "SELECT * FROM sprints WHERE status = ? ORDER BY created_at DESC", (status,)
            ).fetchall()
        else:
            rows = self.db.execute("SELECT * FROM sprints ORDER BY created_at DESC").fetchall()
        return [_row_to_sprint(r) for r in rows]

    def approve(self, sprint_id: str) -> dict:
        """Approve the current manual gate and advance to the next phase.

        Returns:
            Dict with 'success', 'message', and 'sprint'.
        """
        sprint = self.get(sprint_id)
        if not sprint:
            return {"success": False, "message": f"Sprint {sprint_id} not found"}

        # Find the current manual gate
        current_phase_idx = PHASES.index(sprint.current_phase)
        phase = sprint.phases[current_phase_idx]

        if phase.gate != "manual":
            return {"success": False, "message": f"Current gate is auto, not manual"}

        if phase.status != "done":
            return {
                "success": False,
                "message": f"Phase '{phase.name}' not done yet, cannot approve",
            }

        # Approve the gate
        phase.gate_status = "approved"
        now = datetime.now(timezone.utc).isoformat()

        # Advance to next phase
        next_idx = current_phase_idx + 1
        if next_idx < len(PHASES):
            next_phase_name = PHASES[next_idx]
            sprint.phases[next_idx].status = "active"
            sprint.phases[next_idx].started_at = now
            sprint.current_phase = next_phase_name
        else:
            # All phases done
            sprint.status = "completed"
            sprint.completed_at = now

        self._save(sprint)
        return {"success": True, "message": f"Approved! Advanced to {sprint.current_phase}", "sprint": sprint.to_dict()}

    def reject(self, sprint_id: str, reason: str = "") -> dict:
        """Reject the current manual gate, resetting the phase to active."""
        sprint = self.get(sprint_id)
        if not sprint:
            return {"success": False, "message": f"Sprint {sprint_id} not found"}

        current_phase_idx = PHASES.index(sprint.current_phase)
        phase = sprint.phases[current_phase_idx]

        if phase.gate != "manual":
            return {"success": False, "message": "Current gate is auto, not manual"}

        phase.gate_status = "rejected"
        phase.status = "active"  # Back to work
        phase.output += f"\n[驳回原因] {reason}" if reason else ""

        self._save(sprint)
        return {"success": True, "message": f"Rejected. Phase '{phase.name}' back to active.", "sprint": sprint.to_dict()}

    def advance_auto(self, sprint_id: str) -> dict:
        """Attempt auto-advance. Only works if current gate is 'auto'.

        Returns:
            Dict with 'success', 'advanced', 'message', 'sprint'.
        """
        sprint = self.get(sprint_id)
        if not sprint:
            return {"success": False, "message": f"Sprint {sprint_id} not found"}

        current_phase_idx = PHASES.index(sprint.current_phase)
        phase = sprint.phases[current_phase_idx]

        if phase.gate != "auto":
            return {
                "success": True,
                "advanced": False,
                "message": f"Gate is manual — waiting for approval: {phase.gate_name}",
                "sprint": sprint.to_dict(),
            }

        if phase.status != "done":
            return {
                "success": True,
                "advanced": False,
                "message": f"Phase '{phase.name}' still active, not ready to advance",
                "sprint": sprint.to_dict(),
            }

        # Auto-approve and advance
        phase.gate_status = "approved"
        now = datetime.now(timezone.utc).isoformat()

        next_idx = current_phase_idx + 1
        if next_idx < len(PHASES):
            next_phase_name = PHASES[next_idx]
            sprint.phases[next_idx].status = "active"
            sprint.phases[next_idx].started_at = now
            sprint.current_phase = next_phase_name
            self._save(sprint)
            return {
                "success": True,
                "advanced": True,
                "message": f"Auto-advanced to {next_phase_name}",
                "sprint": sprint.to_dict(),
            }
        else:
            sprint.status = "completed"
            sprint.completed_at = now
            self._save(sprint)
            return {
                "success": True,
                "advanced": True,
                "message": "Sprint completed! All phases done.",
                "sprint": sprint.to_dict(),
            }

    def complete_phase(self, sprint_id: str, hours: float = 0.0, output: str = "") -> dict:
        """Mark the current phase as done (called by the agent when finished)."""
        sprint = self.get(sprint_id)
        if not sprint:
            return {"success": False, "message": f"Sprint {sprint_id} not found"}

        current_phase_idx = PHASES.index(sprint.current_phase)
        phase = sprint.phases[current_phase_idx]

        if phase.status != "active":
            return {"success": False, "message": f"Phase '{phase.name}' is {phase.status}, not active"}

        phase.status = "done"
        phase.completed_at = datetime.now(timezone.utc).isoformat()
        phase.hours_spent = hours or phase.hours_spent
        phase.output = output or phase.output

        self._save(sprint)
        return {
            "success": True,
            "message": f"Phase '{phase.name}' completed.",
            "gate": phase.gate,
            "gate_name": phase.gate_name,
            "sprint": sprint.to_dict(),
        }

    def add_iteration(self, sprint_id: str, next_goal: str) -> Sprint:
        """Start a new iteration from a completed sprint."""
        sprint = self.get(sprint_id)
        if not sprint or sprint.status != "completed":
            raise ValueError("Can only iterate from a completed sprint")

        return self.create(goal=next_goal, mode=sprint.mode)

    def _save(self, sprint: Sprint):
        """Persist sprint state to DB."""
        phases_json = json.dumps(
            [
                {
                    "name": p.name,
                    "status": p.status,
                    "agent": p.agent,
                    "started_at": p.started_at,
                    "completed_at": p.completed_at,
                    "hours_spent": p.hours_spent,
                    "output": p.output,
                    "gate": p.gate,
                    "gate_status": p.gate_status,
                    "gate_name": p.gate_name,
                }
                for p in sprint.phases
            ]
        )

        self.db.execute(
            """
            UPDATE sprints SET goal=?, mode=?, current_phase=?, iteration=?,
            status=?, phases_json=?, completed_at=?
            WHERE id=?
            """,
            (
                sprint.goal,
                sprint.mode,
                sprint.current_phase,
                sprint.iteration,
                sprint.status,
                phases_json,
                sprint.completed_at,
                sprint.id,
            ),
        )
        self.db.commit()


# ═══════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════

_manager: Optional[SprintManager] = None


def get_manager() -> SprintManager:
    global _manager
    if _manager is None:
        _manager = SprintManager()
    return _manager
