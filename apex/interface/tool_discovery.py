"""Apex Tool Discovery — auto-detect installed CLI tools during init.

Scans the system for AI/DevOps tools and maps them to agent capabilities.
Runs automatically during `apex fleet init` and stores results for the PM engine.

Architecture:
  ToolDiscovery.scan() → ToolInventory → Agent capability mapping
  Results cached to ~/.apex/tools.json for subsequent use.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

TZ = timezone(timedelta(hours=8))
APEX_HOME = Path.home() / ".apex"
TOOLS_CACHE = APEX_HOME / "tools.json"

# ─── Tool Registry ────────────────────────────────────────────────
#
# Each entry defines: how to find the tool, what it provides,
# and which agent roles benefit from it.
# ───────────────────────────────────────────────────────────────────


@dataclass
class ToolDef:
    """Definition of a discoverable tool."""

    name: str
    display: str
    category: str  # ai_agent | version_control | infrastructure | testing | dev
    search_paths: list[str] = field(default_factory=list)
    search_bins: list[str] = field(default_factory=list)
    version_flag: str = "--version"
    provides: list[str] = field(default_factory=list)  # capabilities
    recommended_agents: list[str] = field(default_factory=list)
    homepage: str = ""


# The canonical tool catalog
TOOL_CATALOG = [
    # ── AI Agent CLI Tools ──
    ToolDef(
        name="hermes",
        display="Hermes Agent",
        category="ai_agent",
        search_bins=["hermes"],
        search_paths=["~/.local/bin/hermes", "/usr/local/bin/hermes"],
        provides=["multi-agent-runtime", "skill-execution", "cron-scheduling", "gateway"],
        recommended_agents=["pm", "architect", "backend-dev", "devops", "github-release"],
        homepage="https://github.com/NousResearch/hermes-agent",
    ),
    ToolDef(
        name="openclaw",
        display="OpenClaw",
        category="ai_agent",
        search_bins=["openclaw"],
        search_paths=["~/.local/bin/openclaw", "~/Library/pnpm/openclaw"],
        provides=["web-automation", "browser-control", "data-scraping"],
        recommended_agents=["backend-dev", "frontend-dev"],
        homepage="https://github.com/nicholasgriffintn/openclaw",
    ),
    ToolDef(
        name="claude",
        display="Claude Code",
        category="ai_agent",
        search_bins=["claude"],
        search_paths=["~/.npm-global/bin/claude", "/usr/local/bin/claude"],
        version_flag="--version",
        provides=["code-generation", "code-review", "debugging", "refactoring"],
        recommended_agents=["backend-dev", "frontend-dev", "architect"],
        homepage="https://docs.anthropic.com/en/docs/claude-code",
    ),
    ToolDef(
        name="codex",
        display="OpenAI Codex CLI",
        category="ai_agent",
        search_bins=["codex"],
        search_paths=["~/.local/bin/codex", "/usr/local/bin/codex"],
        provides=["code-generation", "code-review", "testing"],
        recommended_agents=["backend-dev", "frontend-dev", "qa-engineer"],
        homepage="https://github.com/openai/codex",
    ),
    # ── Evaluation & Testing ──
    ToolDef(
        name="lm_eval",
        display="lm-evaluation-harness",
        category="testing",
        search_bins=["lm_eval"],
        search_paths=["~/.local/bin/lm_eval"],
        version_flag="--help",  # No --version, check with --help
        provides=["model-evaluation", "benchmarking", "accuracy-testing"],
        recommended_agents=["qa-engineer"],
        homepage="https://github.com/EleutherAI/lm-evaluation-harness",
    ),
    # ── Version Control ──
    ToolDef(
        name="gh",
        display="GitHub CLI",
        category="version_control",
        search_bins=["gh"],
        provides=["github-management", "pr-workflow", "release-management"],
        recommended_agents=["github-release", "devops"],
        homepage="https://cli.github.com/",
    ),
    ToolDef(
        name="git",
        display="Git",
        category="version_control",
        search_bins=["git"],
        provides=["version-control", "branching", "collaboration"],
        recommended_agents=["backend-dev", "frontend-dev", "architect"],
    ),
    # ── Infrastructure ──
    ToolDef(
        name="tmux",
        display="tmux",
        category="infrastructure",
        search_bins=["tmux"],
        version_flag="-V",
        provides=["terminal-multiplexing", "session-persistence"],
        recommended_agents=["all"],
    ),
    ToolDef(
        name="docker",
        display="Docker",
        category="infrastructure",
        search_bins=["docker"],
        provides=["containerization", "deployment", "isolation"],
        recommended_agents=["devops", "backend-dev"],
    ),
    ToolDef(
        name="kubectl",
        display="Kubernetes CLI",
        category="infrastructure",
        search_bins=["kubectl"],
        version_flag="version --client",
        provides=["orchestration", "scaling", "service-mesh"],
        recommended_agents=["devops"],
    ),
    ToolDef(
        name="terraform",
        display="Terraform",
        category="infrastructure",
        search_bins=["terraform"],
        provides=["infrastructure-as-code", "provisioning"],
        recommended_agents=["devops"],
    ),
    # ── Development ──
    ToolDef(
        name="python3",
        display="Python 3",
        category="dev",
        search_bins=["python3", "python"],
        provides=["scripting", "data-processing", "ml-training"],
        recommended_agents=["all"],
    ),
    ToolDef(
        name="pip3",
        display="pip",
        category="dev",
        search_bins=["pip3", "pip"],
        provides=["package-management", "dependency-resolution"],
        recommended_agents=["all"],
    ),
    ToolDef(
        name="make",
        display="GNU Make",
        category="dev",
        search_bins=["make"],
        provides=["build-automation", "task-orchestration"],
        recommended_agents=["devops", "backend-dev"],
    ),
    ToolDef(
        name="curl",
        display="curl",
        category="dev",
        search_bins=["curl"],
        provides=["http-client", "api-testing", "file-download"],
        recommended_agents=["all"],
    ),
]

# ─── Discovery Result ─────────────────────────────────────────────


@dataclass
class DiscoveredTool:
    """A tool found on the system."""

    name: str
    display: str
    category: str
    path: str
    version: str
    provides: list[str]
    recommended_agents: list[str]
    homepage: str


@dataclass
class ToolInventory:
    """Complete scan result."""

    scanned_at: str
    total_tools: int
    found: list[DiscoveredTool]
    missing: list[str]
    capabilities: dict[str, list[str]]  # capability → [tool_names]
    agent_tool_map: dict[str, list[str]]  # agent_name → [tool_names]


# ─── Discovery Engine ─────────────────────────────────────────────


class ToolDiscovery:
    """Scans the system for installed tools and maps to agent capabilities."""

    def __init__(self):
        self.catalog = TOOL_CATALOG

    def scan(self, force: bool = False) -> ToolInventory:
        """Scan for all registered tools.

        Args:
            force: Re-scan even if cache exists.

        Returns:
            ToolInventory with all discovered tools.
        """
        if not force and TOOLS_CACHE.exists():
            return self._load_cache()

        found = []
        missing = []
        capabilities: dict[str, list[str]] = {}
        agent_tool_map: dict[str, list[str]] = {}

        for td in self.catalog:
            result = self._discover(td)
            if result:
                found.append(result)
                # Build capability map
                for cap in result.provides:
                    capabilities.setdefault(cap, []).append(result.name)
                # Build agent→tool map
                for agent in result.recommended_agents:
                    agent_tool_map.setdefault(agent, []).append(result.name)
            else:
                missing.append(td.name)

        inventory = ToolInventory(
            scanned_at=datetime.now(TZ).isoformat(),
            total_tools=len(self.catalog),
            found=found,
            missing=missing,
            capabilities=capabilities,
            agent_tool_map=agent_tool_map,
        )

        self._save_cache(inventory)
        return inventory

    def _discover(self, td: ToolDef) -> Optional[DiscoveredTool]:
        """Try to locate and identify a tool."""
        binary_path = None

        # Strategy 1: which
        for bin_name in td.search_bins:
            binary_path = shutil.which(bin_name)
            if binary_path:
                break

        # Strategy 2: known paths
        if not binary_path:
            for p in td.search_paths:
                expanded = Path(os.path.expanduser(p))
                if expanded.exists() and os.access(expanded, os.X_OK):
                    binary_path = str(expanded)
                    break

        if not binary_path:
            return None

        # Get version
        version = self._get_version(binary_path, td.version_flag)

        return DiscoveredTool(
            name=td.name,
            display=td.display,
            category=td.category,
            path=binary_path,
            version=version,
            provides=td.provides,
            recommended_agents=td.recommended_agents,
            homepage=td.homepage,
        )

    def _get_version(self, binary_path: str, version_flag: str) -> str:
        """Try to get tool version safely (3s timeout)."""
        try:
            parts = version_flag.split()
            cmd = [binary_path] + parts
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=3,
            )
            # Combine stdout+stderr, take first meaningful line
            output = (result.stdout + result.stderr).strip()
            lines = [l for l in output.split("\n") if l.strip()]
            return lines[0][:80] if lines else "installed"
        except Exception:
            return "installed"

    # ── Cache ─────────────────────────────────────────────────────

    def _save_cache(self, inventory: ToolInventory):
        APEX_HOME.mkdir(parents=True, exist_ok=True)
        data = {
            "scanned_at": inventory.scanned_at,
            "total_tools": inventory.total_tools,
            "found": [
                {
                    "name": t.name, "display": t.display,
                    "category": t.category, "path": t.path,
                    "version": t.version, "provides": t.provides,
                }
                for t in inventory.found
            ],
            "missing": inventory.missing,
            "capabilities": inventory.capabilities,
            "agent_tool_map": inventory.agent_tool_map,
        }
        with open(TOOLS_CACHE, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_cache(self) -> ToolInventory:
        with open(TOOLS_CACHE) as f:
            data = json.load(f)

        found = [
            DiscoveredTool(
                name=t["name"], display=t["display"],
                category=t["category"], path=t["path"],
                version=t["version"], provides=t["provides"],
                recommended_agents=[], homepage="",
            )
            for t in data["found"]
        ]

        return ToolInventory(
            scanned_at=data["scanned_at"],
            total_tools=data["total_tools"],
            found=found,
            missing=data["missing"],
            capabilities=data["capabilities"],
            agent_tool_map=data["agent_tool_map"],
        )

    # ── Query ─────────────────────────────────────────────────────

    def get_agent_tools(self, agent_name: str) -> list[str]:
        """Get tools available to a specific agent."""
        inventory = self.scan()
        direct = inventory.agent_tool_map.get(agent_name, [])
        all_tools = inventory.agent_tool_map.get("all", [])
        return list(set(direct + all_tools))

    def get_capability_providers(self, capability: str) -> list[str]:
        """Get tools that provide a specific capability."""
        inventory = self.scan()
        return inventory.capabilities.get(capability, [])

    def summary(self) -> dict:
        """Quick summary for dashboard display."""
        inventory = self.scan()
        by_cat = {}
        for t in inventory.found:
            by_cat.setdefault(t.category, []).append(t.name)
        return {
            "found": len(inventory.found),
            "missing": len(inventory.missing),
            "total": inventory.total_tools,
            "by_category": by_cat,
            "ai_agents": [
                t.name for t in inventory.found if t.category == "ai_agent"
            ],
            "scanned_at": inventory.scanned_at,
        }
