"""
Tests for the Apex Token Economy system.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from apex.economy import (
    classify_task,
    select_model,
    BudgetManager,
    BudgetAccount,
    MODEL_ROUTES,
)


class TestEconomyClassification:
    """Test task classification and model selection."""

    def test_classify_task_architecture(self):
        """'architecture' in task text returns 'architecture'."""
        assert classify_task("Design the system architecture") == "architecture"

    def test_classify_task_code_review(self):
        """'code review' in task text returns 'code-review'."""
        assert classify_task("Please review this pull request") == "code-review"

    def test_classify_task_bug_fix(self):
        """'fix' and 'bug' in task text return 'bug-fix'."""
        assert classify_task("Fix the login bug in production") == "bug-fix"

    def test_classify_task_simple_reply(self):
        """Simple greetings return 'simple-reply'."""
        assert classify_task("Hello, how are you?") == "simple-reply"

    def test_classify_task_default(self):
        """Unknown task types return 'default'."""
        assert classify_task("xyzzy plugh quux unknown task") == "default"

    def test_select_model_code_review(self):
        """Code review tasks select deepseek-v4-pro."""
        route = select_model("Review the code in main.py")
        assert route.model == "deepseek-v4-pro"
        assert route.provider == "deepseek"

    def test_select_model_architecture(self):
        """Architecture tasks select claude-sonnet."""
        route = select_model("Design the cloud architecture")
        assert route.model == "claude-sonnet"
        assert route.provider == "anthropic"

    def test_select_model_falls_back_with_low_budget(self):
        """When budget is very low, fall back to default model."""
        route = select_model("Design the cloud architecture", budget_remaining=0.001)
        # Should fall back to default (deepseek-v4-pro) since claude is too expensive
        assert route.task_type == "default"


class TestBudgetManager:
    """Test BudgetManager CRUD and tracking."""

    def test_budget_manager_init(self, tmp_apex_home: Path):
        """BudgetManager initializes with a SQLite database."""
        db_path = tmp_apex_home / "economy.db"
        bm = BudgetManager(db_path=db_path)
        assert bm.db_path == db_path
        # Should be able to create an account immediately
        account = bm.get_or_create_account("test-project")
        assert account.project == "test-project"
        assert account.monthly_limit == 5.0
        assert account.used == 0.0

    def test_budget_account_create(self, tmp_apex_home: Path):
        """Creating an account with custom limit works."""
        bm = BudgetManager(db_path=tmp_apex_home / "economy.db")
        account = bm.get_or_create_account("big-project", monthly_limit=100.0)
        assert account.project == "big-project"
        assert account.monthly_limit == 100.0
        assert account.used == 0.0

        # Getting the same account again returns existing data
        account2 = bm.get_or_create_account("big-project")
        assert account2.monthly_limit == 100.0

    def test_budget_record_usage(self, tmp_apex_home: Path):
        """Recording usage updates the account balance."""
        bm = BudgetManager(db_path=tmp_apex_home / "economy.db")
        bm.get_or_create_account("my-project", monthly_limit=10.0)
        bm.record_usage("my-project", 2.5, task_type="code-review", model="deepseek-v4-pro")
        used, limit, remaining = bm.get_balance("my-project")
        assert used == 2.5
        assert limit == 10.0
        assert remaining == 7.5

        # Record more usage
        bm.record_usage("my-project", 1.0, task_type="writing", model="deepseek-v4-pro")
        used2, _, remaining2 = bm.get_balance("my-project")
        assert used2 == 3.5
        assert remaining2 == 6.5

    def test_budget_warning(self, tmp_apex_home: Path):
        """check_warning returns a warning string when budget exceeds threshold."""
        bm = BudgetManager(db_path=tmp_apex_home / "economy.db")
        bm.get_or_create_account("tight-project", monthly_limit=10.0)

        # Under threshold — no warning
        assert bm.check_warning("tight-project") is None

        # Use 85% -> over 80% threshold — warning
        bm.record_usage("tight-project", 8.5)
        warning = bm.check_warning("tight-project")
        assert warning is not None
        assert "Budget usage" in warning

        # Use to 100% -> exhausted warning
        bm.record_usage("tight-project", 1.5)
        exhausted = bm.check_warning("tight-project")
        assert exhausted is not None
        assert "exhausted" in exhausted
