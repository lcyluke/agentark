"""
Tests for the Apex Self-Healing workflow.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from agentark.orchestration.healing import HealingResult


class TestHealing:
    """Test suite for Self-Healing."""

    def test_healing_init(self):
        """HealingResult can be instantiated with default values."""
        result = HealingResult(success=True)
        assert result.success is True
        assert result.attempts == 0
        assert result.errors == []
        assert result.fixes == []
        assert result.final_output == ""
        assert result.strategy_used == "direct"
        assert result.model_downgraded is False

    def test_healing_result_defaults(self):
        """HealingResult defaults work correctly for a failure scenario."""
        result = HealingResult(
            success=False,
            attempts=3,
            errors=["TimeoutError: connection timed out", "ValueError: invalid response"],
            fixes=["Retry with timeout=60", "Switch to fallback model"],
            strategy_used="simplify_task",
            model_downgraded=True,
        )
        assert result.success is False
        assert result.attempts == 3
        assert len(result.errors) == 2
        assert len(result.fixes) == 2
        assert result.strategy_used == "simplify_task"
        assert result.model_downgraded is True
        assert result.final_output == ""
