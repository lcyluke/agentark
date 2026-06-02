"""Profile management for agents."""
from __future__ import annotations

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


APEX_HOME = Path(os.environ.get("APEX_HOME", Path.home() / ".apex"))


@dataclass
class ModelConfig:
    default: str = "deepseek-v4-pro"
    fallback: str = "llama3-70b"
    vision: str = "claude-sonnet"


@dataclass
class SoulConfig:
    role: str = ""
    expertise: list[str] = field(default_factory=list)
    personality: str = ""
    communication: str = ""


@dataclass
class MemoryConfig:
    type: str = "hybrid"
    retention_days: int = 30


@dataclass
class ToolConfig:
    mcp_urls: list[str] = field(default_factory=list)
    builtins: list[str] = field(default_factory=list)
    rate_limit: int = 100


@dataclass
class Profile:
    """An Agent's complete Profile definition"""
    name: str
    display: str = ""
    model: ModelConfig = field(default_factory=ModelConfig)
    token_budget: int = 500_000
    soul: SoulConfig = field(default_factory=SoulConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    tools: ToolConfig = field(default_factory=ToolConfig)
    skills: list[str] = field(default_factory=list)
    auto_improve: bool = True

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "Profile":
        m = data.get("model", {})
        s = data.get("soul", {})
        mem = data.get("memory", {})
        t = data.get("tools", {})

        return cls(
            name=name,
            display=data.get("display", name),
            model=ModelConfig(
                default=m.get("default", "deepseek-v4-pro"),
                fallback=m.get("fallback", "llama3-70b"),
                vision=m.get("vision", "claude-sonnet"),
            ),
            token_budget=data.get("token_budget", 500_000),
            soul=SoulConfig(
                role=s.get("role", ""),
                expertise=s.get("expertise", []),
                personality=s.get("personality", ""),
                communication=s.get("communication", ""),
            ),
            memory=MemoryConfig(
                type=mem.get("type", "hybrid"),
                retention_days=mem.get("retention", 30),
            ),
            tools=ToolConfig(
                mcp_urls=t.get("mcp", []),
                builtins=t.get("builtins", []),
                rate_limit=t.get("rate_limit", 100),
            ),
            skills=data.get("skills", []),
            auto_improve=data.get("auto_improve", True),
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "display": self.display,
            "model": {
                "default": self.model.default,
                "fallback": self.model.fallback,
                "vision": self.model.vision,
            },
            "token_budget": self.token_budget,
            "soul": {
                "role": self.soul.role,
                "expertise": self.soul.expertise,
                "personality": self.soul.personality,
                "communication": self.soul.communication,
            },
            "memory": {
                "type": self.memory.type,
                "retention": self.memory.retention_days,
            },
            "tools": {
                "mcp": self.tools.mcp_urls,
                "builtins": self.tools.builtins,
                "rate_limit": self.tools.rate_limit,
            },
            "skills": self.skills,
            "auto_improve": self.auto_improve,
        }


class ProfileManager:
    """Manage the lifecycle of all Profiles"""

    def __init__(self, home: Path = APEX_HOME):
        self.home = home
        self.profiles_dir = home / "profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, Profile] = {}

    def list(self) -> list[str]:
        """List all registered Profiles"""
        names = []
        for f in self.profiles_dir.glob("*.yaml"):
            names.append(f.stem)
        return sorted(names)

    def load(self, name: str) -> Profile:
        """Load a Profile"""
        if name in self._cache:
            return self._cache[name]
        path = self.profiles_dir / f"{name}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Profile '{name}' not found at {path}")
        with open(path) as f:
            data = yaml.safe_load(f)
        profile = Profile.from_dict(name, data)
        self._cache[name] = profile
        return profile

    def save(self, profile: Profile):
        """Save a Profile"""
        path = self.profiles_dir / f"{profile.name}.yaml"
        with open(path, "w") as f:
            yaml.dump(profile.to_dict(), f, default_flow_style=False, allow_unicode=True)
        self._cache[profile.name] = profile

    def create_default(self, name: str, role: str = "", expertise: list[str] = None) -> Profile:
        """Create a default Profile"""
        profile = Profile(
            name=name,
            display=role or name,
            soul=SoulConfig(
                role=role or name,
                expertise=expertise or [],
                personality="Professional, reliable, efficient",
                communication="Direct, with concrete solutions",
            ),
        )
        self.save(profile)
        return profile

    def delete(self, name: str):
        """Delete a Profile"""
        path = self.profiles_dir / f"{name}.yaml"
        if path.exists():
            path.unlink()
        self._cache.pop(name, None)
