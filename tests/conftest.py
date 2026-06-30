"""
Pytest fixtures for Apex testing.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from agentark.core.profile import ProfileManager, Profile, SoulConfig, ModelConfig, ToolConfig, MemoryConfig
from agentark.orchestration.kanban import Kanban
from agentark.core.knowledge import KnowledgeGraph
from agentark.providers.base import LLMResponse


@pytest.fixture
def tmp_agentark_home(tmp_path: Path) -> Path:
    """Create a temporary AGENTARK_HOME with profiles directory."""
    home = tmp_path / ".apex"
    profiles_dir = home / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    return home


@pytest.fixture
def sample_profile_manager(tmp_agentark_home: Path) -> ProfileManager:
    """ProfileManager with a pre-created test profile."""
    pm = ProfileManager(home=tmp_agentark_home)
    profile = Profile(
        name="test-agent",
        display="Test Agent",
        model=ModelConfig(default="deepseek-v4-pro", fallback="llama3-70b", vision="claude-sonnet"),
        token_budget=100_000,
        soul=SoulConfig(
            role="Tester",
            expertise=["testing", "automation", "python"],
            personality="Thorough, methodical, detail-oriented",
            communication="Clear and concise",
        ),
        memory=MemoryConfig(type="ephemeral", retention_days=7),
        tools=ToolConfig(
            mcp_urls=["http://localhost:9999"],
            builtins=["filesystem", "shell"],
            rate_limit=50,
        ),
        skills=["pytest", "unittest", "coverage"],
        auto_improve=False,
    )
    pm.save(profile)
    return pm


@pytest.fixture
def sample_kanban(tmp_agentark_home: Path) -> Kanban:
    """Kanban with a few test tasks."""
    kanban = Kanban(db_path=tmp_agentark_home / "kanban.db")
    # Create some tasks
    kanban.create_task("Task A — no dependencies", priority=1)
    kanban.create_task("Task B — depends on A", depends_on=["t_00000001"], priority=2)
    kanban.create_task("Task C — also no deps", priority=3)
    return kanban


@pytest.fixture
def sample_knowledge_graph(tmp_agentark_home: Path) -> KnowledgeGraph:
    """KnowledgeGraph with seed data."""
    kg = KnowledgeGraph(db_path=tmp_agentark_home / "knowledge.db")
    kg.learn("Python", "language", "A high-level programming language", source="fixture")
    kg.learn("FastAPI", "framework", "A modern Python web framework", source="fixture")
    kg.learn("Pydantic", "library", "Data validation library", source="fixture")
    kg.relate("FastAPI", "depends_on", "Python", "built with Python", source="fixture")
    kg.relate("FastAPI", "recommends", "Pydantic", "uses Pydantic for models", source="fixture")
    return kg


@pytest.fixture
def mock_llm_response() -> LLMResponse:
    """Returns a fake LLMResponse for testing."""
    return LLMResponse(
        content="This is a mock LLM response for testing purposes.",
        model="deepseek-v4-pro",
        provider="deepseek",
        usage={"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
    )
