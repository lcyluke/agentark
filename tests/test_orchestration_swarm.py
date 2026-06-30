"""
Tests for the Apex Swarm orchestration.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from agentark.orchestration.swarm import Swarm, SwarmResult
from agentark.orchestration.kanban import Kanban


class TestSwarm:
    """Test suite for Swarm mode."""

    def test_swarm_init(self, tmp_agentark_home: Path):
        """Swarm can be initialized with a Kanban instance."""
        kanban = Kanban(db_path=tmp_agentark_home / "kanban.db")
        swarm = Swarm(kanban=kanban)
        assert swarm.kanban is kanban

    def test_swarm_result_dataclass(self):
        """SwarmResult dataclass has correct defaults and can hold data."""
        result = SwarmResult()
        assert result.success is False
        assert result.worker_outputs == []
        assert result.verifier_output == ""
        assert result.synthesizer_output == ""
        assert result.total_cost == 0.0
        assert result.error == ""

        # Populate with data
        result.success = True
        result.worker_outputs = [{"name": "worker-1", "output": "done"}]
        result.verifier_output = "All good"
        result.synthesizer_output = "Integrated result"
        result.total_cost = 0.05
        assert result.success is True
        assert len(result.worker_outputs) == 1
        assert result.total_cost == 0.05
