"""
Tests for the Apex Profile system.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from apex.core.profile import ProfileManager, Profile, APEX_HOME, ModelConfig, SoulConfig, ToolConfig, MemoryConfig
from apex.core.templates import get_template


class TestProfileDefaults:
    """Test creating profiles with default values."""

    def test_create_profile_defaults(self, tmp_apex_home: Path):
        """ProfileManager.create_default creates a profile with sensible defaults."""
        pm = ProfileManager(home=tmp_apex_home)
        profile = pm.create_default(name="default-agent", role="Assistant")
        assert profile.name == "default-agent"
        assert profile.display == "Assistant"
        assert profile.model.default == "deepseek-v4-pro"
        assert profile.token_budget == 500_000
        assert profile.auto_improve is True
        # Verify it was saved
        assert "default-agent" in pm.list()

    def test_create_profile_custom(self, tmp_apex_home: Path):
        """Can create a Profile with all custom fields."""
        pm = ProfileManager(home=tmp_apex_home)
        profile = Profile(
            name="custom-agent",
            display="Custom Agent",
            model=ModelConfig(default="gpt-4", fallback="gpt-3.5", vision="gpt-4-vision"),
            token_budget=1_000_000,
            soul=SoulConfig(
                role="Specialist",
                expertise=["rust", "systems-programming"],
                personality="Precise",
                communication="Technical",
            ),
            memory=MemoryConfig(type="vector", retention_days=90),
            tools=ToolConfig(mcp_urls=["http://mcp.local"], builtins=["filesystem"], rate_limit=200),
            skills=["async", "ffi"],
            auto_improve=False,
        )
        pm.save(profile)
        loaded = pm.load("custom-agent")
        assert loaded.name == "custom-agent"
        assert loaded.token_budget == 1_000_000
        assert loaded.auto_improve is False
        assert loaded.soul.expertise == ["rust", "systems-programming"]
        assert loaded.tools.rate_limit == 200

    def test_save_and_load(self, sample_profile_manager: ProfileManager):
        """Saving a profile persists it to disk, and loading returns the same data."""
        pm = sample_profile_manager
        # Already saved by fixture
        loaded = pm.load("test-agent")
        assert loaded.name == "test-agent"
        assert loaded.display == "Test Agent"
        assert loaded.model.default == "deepseek-v4-pro"
        assert loaded.memory.type == "ephemeral"

    def test_profile_to_dict_roundtrip(self):
        """Profile.to_dict() and Profile.from_dict() are inverses."""
        original = Profile(
            name="roundtrip",
            display="Round Trip",
            model=ModelConfig(default="gpt-4", fallback="gpt-3.5", vision="claude"),
            token_budget=250_000,
            soul=SoulConfig(role="Validator", expertise=["qa"], personality="Strict", communication="Brief"),
            memory=MemoryConfig(type="hybrid", retention_days=60),
            tools=ToolConfig(mcp_urls=[], builtins=["fs"], rate_limit=75),
            skills=["testing"],
            auto_improve=False,
        )
        data = original.to_dict()
        restored = Profile.from_dict(name="roundtrip", data=data)
        assert restored.name == original.name
        assert restored.display == original.display
        assert restored.model.default == original.model.default
        assert restored.token_budget == original.token_budget
        assert restored.soul.role == original.soul.role
        assert restored.memory.type == original.memory.type
        assert restored.tools.rate_limit == original.tools.rate_limit
        assert restored.skills == original.skills

    def test_from_dict(self):
        """Profile.from_dict correctly parses a raw dictionary."""
        data = {
            "display": "From Dict",
            "model": {"default": "custom-model", "fallback": "fb", "vision": "v"},
            "token_budget": 999,
            "soul": {"role": "Parser", "expertise": ["data"], "personality": "Analytical", "communication": "Report"},
            "memory": {"type": "short", "retention": 1},
            "tools": {"mcp": ["http://t"], "builtins": ["ls"], "rate_limit": 5},
            "skills": ["parsing"],
            "auto_improve": True,
        }
        profile = Profile.from_dict(name="from-dict", data=data)
        assert profile.name == "from-dict"
        assert profile.display == "From Dict"
        assert profile.model.default == "custom-model"
        assert profile.token_budget == 999
        assert profile.soul.expertise == ["data"]
        assert profile.tools.rate_limit == 5

    def test_from_template(self):
        """Profile.from_template (via AgentTemplate.to_profile) creates a proper profile."""
        template = get_template("devops")
        assert template is not None, "devops template should exist"
        profile = template.to_profile(name="infra-agent")
        assert profile.name == "infra-agent"
        assert profile.display == "DevOps Engineer"
        assert "ci-cd-pipeline" in profile.skills
        assert profile.soul.personality != ""

    def test_list_profiles(self, sample_profile_manager: ProfileManager):
        """ProfileManager.list() returns all saved profile names."""
        pm = sample_profile_manager
        pm.create_default("agent-two", role="Second")
        pm.create_default("agent-three", role="Third")
        names = pm.list()
        assert "test-agent" in names
        assert "agent-two" in names
        assert "agent-three" in names

    def test_delete_profile(self, sample_profile_manager: ProfileManager):
        """ProfileManager.delete() removes a profile from disk and cache."""
        pm = sample_profile_manager
        assert "test-agent" in pm.list()
        pm.delete("test-agent")
        assert "test-agent" not in pm.list()

    def test_load_nonexistent_raises(self, tmp_apex_home: Path):
        """Loading a non-existent profile raises FileNotFoundError."""
        pm = ProfileManager(home=tmp_apex_home)
        with pytest.raises(FileNotFoundError, match="nonexistent"):
            pm.load("nonexistent")
