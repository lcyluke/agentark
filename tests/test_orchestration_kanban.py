"""
Tests for the Apex Kanban orchestration system.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from apex.orchestration.kanban import Kanban, Task
from apex.orchestration.kanban import (
    TASK_STATUS_TODO,
    TASK_STATUS_READY,
    TASK_STATUS_IN_PROGRESS,
    TASK_STATUS_DONE,
    TASK_STATUS_BLOCKED,
    TASK_STATUS_FAILED,
)


class TestKanban:
    """Test suite for the Kanban task board."""

    def test_create_task(self, tmp_apex_home: Path):
        """Creating a task returns a Task with correct fields."""
        kanban = Kanban(db_path=tmp_apex_home / "kanban.db")
        task = kanban.create_task(
            "Implement login",
            description="OAuth2 login flow",
            assignee="dev-1",
            priority=1,
        )
        assert task.title == "Implement login"
        assert task.description == "OAuth2 login flow"
        assert task.assignee == "dev-1"
        assert task.priority == 1
        assert task.status == TASK_STATUS_TODO
        assert task.id.startswith("t_")
        assert task.created_at != ""

    def test_update_task_status(self, tmp_apex_home: Path):
        """Updating a task status works correctly."""
        kanban = Kanban(db_path=tmp_apex_home / "kanban.db")
        task = kanban.create_task("Deploy to production")
        kanban.update_task(task.id, status=TASK_STATUS_IN_PROGRESS)
        updated = kanban.get_task(task.id)
        assert updated is not None
        assert updated.status == TASK_STATUS_IN_PROGRESS

        kanban.update_task(task.id, status=TASK_STATUS_DONE)
        done = kanban.get_task(task.id)
        assert done.status == TASK_STATUS_DONE
        assert done.completed_at is not None

    def test_list_tasks_by_status(self, tmp_apex_home: Path):
        """list_tasks filters correctly by status."""
        kanban = Kanban(db_path=tmp_apex_home / "kanban.db")
        t1 = kanban.create_task("Task 1", status=TASK_STATUS_TODO)
        t2 = kanban.create_task("Task 2", status=TASK_STATUS_IN_PROGRESS)
        t3 = kanban.create_task("Task 3", status=TASK_STATUS_DONE)

        todo_tasks = kanban.list_tasks(status=TASK_STATUS_TODO)
        assert len(todo_tasks) == 1
        assert todo_tasks[0].id == t1.id

        in_prog = kanban.list_tasks(status=TASK_STATUS_IN_PROGRESS)
        assert len(in_prog) == 1
        assert in_prog[0].id == t2.id

        done_tasks = kanban.list_tasks(status=TASK_STATUS_DONE)
        assert len(done_tasks) == 1
        assert done_tasks[0].id == t3.id

    def test_dependency_chain(self, tmp_apex_home: Path):
        """Tasks can depend on other tasks via depends_on."""
        kanban = Kanban(db_path=tmp_apex_home / "kanban.db")
        parent = kanban.create_task("Setup database")
        child = kanban.create_task("Build API", depends_on=[parent.id])
        assert child.depends_on == [parent.id]

        # Verify the dependency is persisted
        loaded_child = kanban.get_task(child.id)
        assert loaded_child is not None
        assert loaded_child.depends_on == [parent.id]

    def test_get_ready_tasks(self, tmp_apex_home: Path):
        """get_ready_tasks returns tasks whose dependencies are met."""
        kanban = Kanban(db_path=tmp_apex_home / "kanban.db")
        t1 = kanban.create_task("Independent task")
        t2 = kanban.create_task("Dependent task", depends_on=[t1.id])

        # t1 has no deps, should be ready. t2 depends on t1 which is not done.
        ready = kanban.get_ready_tasks()
        ready_ids = [t.id for t in ready]
        assert t1.id in ready_ids
        assert t2.id not in ready_ids

        # Complete t1 — now t2 should also be ready
        kanban.update_task(t1.id, status=TASK_STATUS_DONE)
        ready2 = kanban.get_ready_tasks()
        ready2_ids = [t.id for t in ready2]
        assert t2.id in ready2_ids

    def test_get_ready_tasks_blocked(self, tmp_apex_home: Path):
        """get_ready_tasks does NOT return tasks with unmet dependencies."""
        kanban = Kanban(db_path=tmp_apex_home / "kanban.db")
        t1 = kanban.create_task("Blocking task A")
        t2 = kanban.create_task("Blocking task B")
        t3 = kanban.create_task("Blocked task", depends_on=[t1.id, t2.id])

        # Neither A nor B is done, so t3 should NOT be ready
        ready = kanban.get_ready_tasks()
        ready_ids = [t.id for t in ready]
        assert t3.id not in ready_ids

        # Mark A done — t3 still depends on B
        kanban.update_task(t1.id, status=TASK_STATUS_DONE)
        ready2 = kanban.get_ready_tasks()
        ready2_ids = [t.id for t in ready2]
        assert t3.id not in ready2_ids

        # Mark B done too — t3 should now be ready
        kanban.update_task(t2.id, status=TASK_STATUS_DONE)
        ready3 = kanban.get_ready_tasks()
        ready3_ids = [t.id for t in ready3]
        assert t3.id in ready3_ids

    def test_ai_suggestions(self, tmp_apex_home: Path):
        """ai_suggestions returns context-aware suggestions."""
        kanban = Kanban(db_path=tmp_apex_home / "kanban.db")
        # No tasks yet — may return empty or basic suggestion
        suggestions_empty = kanban.ai_suggestions()
        assert isinstance(suggestions_empty, list)

        # Add many in-progress tasks to trigger the parallelism warning
        for i in range(4):
            t = kanban.create_task(f"Busy task {i}")
            kanban.update_task(t.id, status=TASK_STATUS_IN_PROGRESS)

        suggestions_busy = kanban.ai_suggestions()
        # Should warn about too many in-progress tasks
        assert any("in progress" in s.lower() for s in suggestions_busy)

        # Add pending todo tasks
        kanban.create_task("Pending task 1")
        kanban.create_task("Pending task 2")
        suggestions_with_todo = kanban.ai_suggestions()
        assert any("todo" in s.lower() for s in suggestions_with_todo)
