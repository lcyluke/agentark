"""Tests for Sprint Pipeline — MVP closed-loop development."""

from __future__ import annotations

from pathlib import Path

import pytest

from apex.orchestration.sprint_pipeline import (
    SprintManager,
    Sprint,
    PhaseRecord,
    PHASES,
    PHASE_META,
)


class TestSprintManager:
    """Test suite for Sprint Pipeline state machine."""

    def test_create_sprint_solo(self, tmp_path: Path):
        """Creating a solo sprint initializes 5 phases starting with plan."""
        db = tmp_path / "sprints.db"
        mgr = SprintManager(db_path=db)
        sprint = mgr.create("Test MVP", mode="solo")

        assert sprint.goal == "Test MVP"
        assert sprint.mode == "solo"
        assert sprint.current_phase == "plan"
        assert sprint.status == "active"
        assert sprint.iteration == 1
        assert sprint.progress_pct == 0
        assert len(sprint.phases) == 5

        # First phase is plan, active, manual gate
        plan = sprint.phases[0]
        assert plan.name == "plan"
        assert plan.status == "active"
        assert plan.gate == "manual"
        assert plan.gate_name == "设计审批"
        assert plan.agent == "product-manager"

        # Other phases are pending
        for p in sprint.phases[1:]:
            assert p.status == "pending"

    def test_create_sprint_swarm(self, tmp_path: Path):
        """Swarm mode assigns two agents to build/test/ship phases."""
        db = tmp_path / "sprints.db"
        mgr = SprintManager(db_path=db)
        sprint = mgr.create("Complex API", mode="swarm")

        build = sprint.phases[1]
        assert build.name == "build"
        assert "frontend-dev" in build.agent
        assert "backend-dev" in build.agent

    def test_complete_phase_then_approve(self, tmp_path: Path):
        """Complete plan → manual gate → approve → advance to build."""
        db = tmp_path / "sprints.db"
        mgr = SprintManager(db_path=db)
        sprint = mgr.create("Login MVP")

        # Complete plan phase
        result = mgr.complete_phase(sprint.id, hours=2.0, output="PRD done")
        assert result["success"]
        assert result["gate"] == "manual"
        assert result["gate_name"] == "设计审批"

        # Verify plan is done, gate pending
        sprint = mgr.get(sprint.id)
        plan = sprint.phases[0]
        assert plan.status == "done"
        assert plan.gate_status == "pending"
        assert plan.hours_spent == 2.0
        assert "PRD done" in plan.output
        assert sprint.progress_pct == 20  # 1/5

        # Approve the manual gate
        result = mgr.approve(sprint.id)
        assert result["success"]
        assert "build" in result["message"].lower()

        # Verify advanced to build
        sprint = mgr.get(sprint.id)
        assert sprint.current_phase == "build"
        assert sprint.phases[0].gate_status == "approved"
        assert sprint.phases[1].status == "active"

    def test_reject_gate(self, tmp_path: Path):
        """Rejecting a gate resets phase to active."""
        db = tmp_path / "sprints.db"
        mgr = SprintManager(db_path=db)
        sprint = mgr.create("Reject test")

        mgr.complete_phase(sprint.id)
        result = mgr.reject(sprint.id, reason="API design wrong")
        assert result["success"]

        sprint = mgr.get(sprint.id)
        assert sprint.phases[0].gate_status == "rejected"
        assert sprint.phases[0].status == "active"
        assert "API design wrong" in sprint.phases[0].output

    def test_auto_advance_on_build_complete(self, tmp_path: Path):
        """After build completes (auto gate), auto-advance to verify."""
        db = tmp_path / "sprints.db"
        mgr = SprintManager(db_path=db)
        sprint = mgr.create("Auto test")

        # Complete plan, approve
        mgr.complete_phase(sprint.id)
        mgr.approve(sprint.id)

        # Now in build phase (auto gate)
        sprint = mgr.get(sprint.id)
        assert sprint.current_phase == "build"
        assert sprint.phases[1].gate == "auto"

        # Complete build
        result = mgr.complete_phase(sprint.id, hours=3.0)
        assert result["success"]
        assert result["gate"] == "auto"

        # Auto-advance should work
        result = mgr.advance_auto(sprint.id)
        assert result["success"]
        assert result["advanced"]

        sprint = mgr.get(sprint.id)
        assert sprint.current_phase == "verify"

    def test_auto_advance_blocked_by_manual(self, tmp_path: Path):
        """Auto-advance should NOT skip a manual gate."""
        db = tmp_path / "sprints.db"
        mgr = SprintManager(db_path=db)
        sprint = mgr.create("Manual gate test")

        # plan phase is still active — auto gate won't advance
        result = mgr.advance_auto(sprint.id)
        assert result["success"]
        assert not result["advanced"]
        # Manual gate blocks even before phase is done
        assert "manual" in result["message"].lower()

        # Complete plan — now at manual gate
        mgr.complete_phase(sprint.id)
        result = mgr.advance_auto(sprint.id)
        assert not result["advanced"]
        assert "manual" in result["message"].lower()
        assert "waiting for approval" in result["message"].lower()

    def test_full_pipeline_flow(self, tmp_path: Path):
        """End-to-end: create → plan → approve → build → auto → ... → completed."""
        db = tmp_path / "sprints.db"
        mgr = SprintManager(db_path=db)
        sprint = mgr.create("Full flow", mode="solo")

        # Phase 1: Plan (manual gate)
        mgr.complete_phase(sprint.id, hours=1.0, output="PRD+API contract")
        mgr.approve(sprint.id)
        sprint = mgr.get(sprint.id)
        assert sprint.current_phase == "build"

        # Phase 2: Build (auto gate)
        mgr.complete_phase(sprint.id, hours=4.0, output="Code committed")
        mgr.advance_auto(sprint.id)
        sprint = mgr.get(sprint.id)
        assert sprint.current_phase == "verify"

        # Phase 3: Verify (auto gate)
        mgr.complete_phase(sprint.id, hours=1.5, output="Tests pass, 85% coverage")
        mgr.advance_auto(sprint.id)
        sprint = mgr.get(sprint.id)
        assert sprint.current_phase == "ship"

        # Phase 4: Ship (manual gate)
        mgr.complete_phase(sprint.id, hours=0.5, output="Deployed to preview")
        mgr.approve(sprint.id)
        sprint = mgr.get(sprint.id)
        assert sprint.current_phase == "learn"

        # Phase 5: Learn (auto gate → completes sprint)
        mgr.complete_phase(sprint.id, hours=1.0, output="Feedback collected")
        mgr.advance_auto(sprint.id)
        sprint = mgr.get(sprint.id)
        assert sprint.status == "completed"
        assert sprint.progress_pct == 100
        assert sprint.total_hours == 8.0

    def test_list_all_sprints(self, tmp_path: Path):
        """List returns all sprints, filterable by status."""
        db = tmp_path / "sprints.db"
        mgr = SprintManager(db_path=db)

        mgr.create("Sprint 1")
        mgr.create("Sprint 2")
        mgr.create("Sprint 3")

        all_sprints = mgr.list_all()
        assert len(all_sprints) == 3

        active = mgr.list_all(status="active")
        assert len(active) == 3

        completed = mgr.list_all(status="completed")
        assert len(completed) == 0

    def test_approve_wrong_gate(self, tmp_path: Path):
        """Cannot approve a gate that isn't manual or isn't done."""
        db = tmp_path / "sprints.db"
        mgr = SprintManager(db_path=db)
        sprint = mgr.create("Wrong gate")

        # Try approving before phase is done
        result = mgr.approve(sprint.id)
        assert not result["success"]
        assert "not done" in result["message"]

    def test_to_dict(self, tmp_path: Path):
        """Sprint.to_dict() produces correct JSON-serializable structure."""
        db = tmp_path / "sprints.db"
        mgr = SprintManager(db_path=db)
        sprint = mgr.create("Dict test")

        d = sprint.to_dict()
        assert d["id"] == sprint.id
        assert d["goal"] == "Dict test"
        assert d["mode"] == "solo"
        assert d["progress_pct"] == 0
        assert d["current_gate"] is None
        assert len(d["phases"]) == 5
        assert d["phases"][0]["display"] == "📝 PLAN"
        assert d["phases"][0]["gate_name"] == "设计审批"

    def test_progress_calculation(self, tmp_path: Path):
        """Progress percentage is correctly calculated."""
        db = tmp_path / "sprints.db"
        mgr = SprintManager(db_path=db)
        sprint = mgr.create("Progress test")

        assert sprint.progress_pct == 0

        mgr.complete_phase(sprint.id)
        mgr.approve(sprint.id)
        sprint = mgr.get(sprint.id)
        assert sprint.progress_pct == 20  # 1/5

        mgr.complete_phase(sprint.id)
        mgr.advance_auto(sprint.id)
        sprint = mgr.get(sprint.id)
        assert sprint.progress_pct == 40  # 2/5

    def test_current_gate_detection(self, tmp_path: Path):
        """current_gate property correctly identifies the pending manual gate."""
        db = tmp_path / "sprints.db"
        mgr = SprintManager(db_path=db)
        sprint = mgr.create("Gate test")

        # No gate pending when phase is active
        assert sprint.current_gate is None

        # After completing plan, gate is pending
        mgr.complete_phase(sprint.id)
        sprint = mgr.get(sprint.id)
        assert sprint.current_gate is not None
        assert sprint.current_gate.name == "plan"
        assert sprint.current_gate.gate_name == "设计审批"


class TestPhaseConstants:
    """Verify phase metadata constants are correct."""

    def test_all_phases_have_meta(self):
        """Every phase in PHASES has corresponding PHASE_META."""
        for ph in PHASES:
            assert ph in PHASE_META
            meta = PHASE_META[ph]
            assert "display" in meta
            assert "gate" in meta
            assert "gate_name" in meta
            assert "agent_solo" in meta
            assert "agent_swarm" in meta

    def test_manual_gates_count(self):
        """Exactly 2 manual gates: plan (design) and ship (release)."""
        manual = [ph for ph in PHASES if PHASE_META[ph]["gate"] == "manual"]
        assert len(manual) == 2
        assert manual[0] == "plan"
        assert manual[1] == "ship"

    def test_auto_gates_count(self):
        """Exactly 3 auto gates: build, verify, learn."""
        auto = [ph for ph in PHASES if PHASE_META[ph]["gate"] == "auto"]
        assert len(auto) == 3
        assert auto == ["build", "verify", "learn"]
