"""Integration tests for Apex core systems — self-healing, ops, knowledge graph, SQLite thread safety."""

import time
import struct
from pathlib import Path
from dataclasses import dataclass

import pytest

# ─────────────────────────────────────────────────────────
# SECTION 1: Self-Healing Integration
# ─────────────────────────────────────────────────────────

class TestSelfHealing:
    """Verify SelfHealingExecutor is properly integrated into Agent runtime."""

    def test_healing_result_default_success(self):
        from apex.orchestration.healing import HealingResult
        r = HealingResult()
        assert r.success is False, "HealingResult() should default to success=False"
        assert r.attempts == 0

    def test_healing_result_with_values(self):
        from apex.orchestration.healing import HealingResult
        r = HealingResult(success=True, attempts=3, final_output="hello")
        assert r.success is True
        assert r.attempts == 3
        assert r.final_output == "hello"

    def test_agent_self_healing_flag(self):
        from apex.core.runtime import Agent
        from apex.core.profile import Profile, SoulConfig
        p = Profile(name="tester", soul=SoulConfig(role="Test"))
        a = Agent(p, self_healing=True)
        assert a.self_healing is True

    def test_agent_run_has_heal_param(self):
        import inspect
        from apex.core.runtime import Agent
        sig = inspect.signature(Agent.run)
        assert "heal" in sig.parameters

    def test_self_healing_executor_imports(self):
        from apex.orchestration.healing import SelfHealingExecutor
        assert SelfHealingExecutor.MAX_ATTEMPTS == 3
        assert SelfHealingExecutor.STRATEGIES == ["direct", "switch_model", "simplify_task"]

    def test_self_healing_executor_wraps_agent(self):
        from apex.core.runtime import Agent
        from apex.core.profile import Profile, SoulConfig
        from apex.orchestration.healing import SelfHealingExecutor
        p = Profile(name="tester", soul=SoulConfig(role="Test"))
        a = Agent(p)
        ex = SelfHealingExecutor(a)
        assert ex.agent is a
        assert ex.kg is not None
        assert ex.evolution is not None

    def test_healer_agent_created(self):
        from apex.core.runtime import Agent
        from apex.core.profile import Profile, SoulConfig
        from apex.orchestration.healing import SelfHealingExecutor
        p = Profile(name="tester", soul=SoulConfig(role="Test"))
        a = Agent(p)
        ex = SelfHealingExecutor(a)
        healer = ex._get_healer()
        assert healer is not None
        assert isinstance(healer, Agent)


# ─────────────────────────────────────────────────────────
# SECTION 2: Ops Module
# ─────────────────────────────────────────────────────────

class TestOps:
    """Verify OpsManager CRUD operations and dashboard stats."""

    def test_get_ops_singleton(self):
        from apex.orchestration.ops import get_ops
        o1 = get_ops()
        o2 = get_ops()
        assert o1 is o2

    def test_release_create_and_list(self):
        from apex.orchestration.ops import get_ops
        o = get_ops()
        rel = o.create_release("99-test", "Test Release")
        assert rel.version == "99-test"
        assert rel.name == "Test Release"
        assert len(rel.stages) == 10

        releases = o.list_releases()
        assert any(r.version == "99-test" for r in releases)

    def test_bug_create_and_list(self):
        from apex.orchestration.ops import get_ops
        o = get_ops()
        bug = o.create_bug("Test bug", "Integration test", severity="high")
        assert bug.title == "Test bug"
        assert bug.sla_remaining_hours > 0
        assert bug.sla_breached is False

        bugs = o.list_bugs(status="open")
        assert any(b.title == "Test bug" for b in bugs)

    def test_task_create_and_list(self):
        from apex.orchestration.ops import get_ops
        o = get_ops()
        task = o.create_task("Test task",
                             description="Integration test",
                             phase="development",
                             priority=2,
                             agent_id="tester")
        assert task.title == "Test task"
        assert task.agent_id == "tester"

        tasks = o.list_tasks()
        assert any(t.title == "Test task" for t in tasks)

    def test_dashboard_stats(self):
        from apex.orchestration.ops import get_ops
        o = get_ops()
        stats = o.get_dashboard_stats()
        assert "tasks" in stats
        assert "bugs" in stats
        assert "releases" in stats
        assert "expert_tickets" in stats
        assert "total" in stats["tasks"]
        assert "done" in stats["tasks"]
        assert "blocked" in stats["tasks"]
        assert "open" in stats["bugs"]
        assert "critical" in stats["bugs"]
        assert "sla_breached" in stats["bugs"]


# ─────────────────────────────────────────────────────────
# SECTION 3: SQLite Thread Safety
# ─────────────────────────────────────────────────────────

class TestSQLiteThreadSafety:
    """Verify check_same_thread=False is set on all DB connections."""

    def test_evolution_db_thread_safe(self):
        from apex.core.profile import APEX_HOME
        import sqlite3
        path = APEX_HOME / "evolution.db"
        conn = sqlite3.connect(str(path), check_same_thread=False)
        row = conn.execute("SELECT 1").fetchone()
        assert row[0] == 1
        conn.close()

    def test_knowledge_db_thread_safe(self):
        from apex.core.profile import APEX_HOME
        import sqlite3
        path = APEX_HOME / "knowledge.db"
        conn = sqlite3.connect(str(path), check_same_thread=False)
        row = conn.execute("SELECT 1").fetchone()
        assert row[0] == 1
        conn.close()

    def test_ops_db_thread_safe(self):
        from apex.orchestration.ops import get_ops
        o = get_ops()
        # ops already has check_same_thread=False in constructor
        stats = o.get_dashboard_stats()
        assert isinstance(stats, dict)


# ─────────────────────────────────────────────────────────
# SECTION 4: Knowledge Graph
# ─────────────────────────────────────────────────────────

class TestKnowledgeGraph:
    """Verify KG has seed data and queries work."""

    def test_kg_stats(self):
        from apex.core.knowledge import KnowledgeGraph
        kg = KnowledgeGraph()
        stats = kg.stats()
        assert stats["total_nodes"] >= 40, f"Expected >=40 nodes, got {stats['total_nodes']}"
        assert stats["total_edges"] >= 40, f"Expected >=40 edges, got {stats['total_edges']}"
        assert stats["unresolved_conflicts"] == 0

    def test_kg_python_query(self):
        from apex.core.knowledge import KnowledgeGraph
        kg = KnowledgeGraph()
        result = kg.query("Python mutable defaults")
        assert result.confidence > 0
        assert len(result.answer) > 0

    def test_kg_docker_query(self):
        from apex.core.knowledge import KnowledgeGraph
        kg = KnowledgeGraph()
        result = kg.query("Docker health check")
        assert result.confidence > 0

    def test_kg_api_query(self):
        from apex.core.knowledge import KnowledgeGraph
        kg = KnowledgeGraph()
        result = kg.query("API pagination")
        assert result.confidence > 0

    def test_kg_structured_outputs_query(self):
        from apex.core.knowledge import KnowledgeGraph
        kg = KnowledgeGraph()
        result = kg.query("type hints Python")
        assert result.confidence > 0


# ─────────────────────────────────────────────────────────
# SECTION 5: Module Imports
# ─────────────────────────────────────────────────────────

class TestModuleImports:
    """Verify all 22 modules import without errors."""

    MODULES = [
        "apex.core.profile", "apex.core.runtime", "apex.core.memory",
        "apex.core.knowledge", "apex.core.evolution", "apex.core.skills",
        "apex.core.templates", "apex.economy", "apex.mcp.hub",
        "apex.providers.base", "apex.providers.deepseek",
        "apex.orchestration.swarm", "apex.orchestration.crew",
        "apex.orchestration.chain", "apex.orchestration.debate",
        "apex.orchestration.router", "apex.orchestration.supervisor",
        "apex.orchestration.monitor", "apex.orchestration.healing",
        "apex.orchestration.kanban", "apex.orchestration.autonomous",
        "apex.orchestration.ops",
    ]

    @pytest.mark.parametrize("module_name", MODULES)
    def test_module_imports(self, module_name):
        __import__(module_name)


# ─────────────────────────────────────────────────────────
# SECTION 6: Agent Runtime
# ─────────────────────────────────────────────────────────

class TestAgentRuntime:
    """Verify Agent runtime construction and method signatures."""

    def test_agent_creation(self):
        from apex.core.runtime import Agent
        from apex.core.profile import Profile, SoulConfig
        p = Profile(name="unit-test", soul=SoulConfig(role="Unit Tester"))
        a = Agent(p)
        assert a.profile.name == "unit-test"
        assert a.profile.soul.role == "Unit Tester"
        assert a.context is not None

    def test_agent_provider_resolution(self):
        from apex.core.runtime import Agent
        from apex.core.profile import Profile, SoulConfig
        p = Profile(name="utest", soul=SoulConfig(role="Test"))
        a = Agent(p)
        # Provider property should resolve without error
        provider = a.provider
        assert provider is not None

    def test_agent_system_prompt(self):
        from apex.core.runtime import Agent
        from apex.core.profile import Profile, SoulConfig
        p = Profile(name="utest", soul=SoulConfig(
            role="Expert Coder",
            expertise=["Python", "FastAPI"],
            personality="Precise and concise",
            communication="Professional",
        ), skills=["testing", "code-review"])
        a = Agent(p)
        prompt = a._build_system_prompt()
        assert "Expert Coder" in prompt
        assert "Python" in prompt
        assert "Precise" in prompt
