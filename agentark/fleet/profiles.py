"""ProfileBundler — ship default SOUL profiles and skills with Apex.

When a user installs Apex for the first time, `apex fleet init` creates
Hermes profiles from bundled defaults. This eliminates the manual profile
creation step — Apex comes with a dev squad out of the box.

Bundle structure (inside the apex package):
    apex/fleet/defaults/
    ├── profiles/
    │   ├── pm/SOUL.md
    │   ├── architect/SOUL.md
    │   ├── backend-dev/SOUL.md
    │   ├── frontend-dev/SOUL.md
    │   ├── devops/SOUL.md
    │   ├── qa-engineer/SOUL.md
    │   └── github-release/SOUL.md
    └── skills/
        └── apex-release-workflow/SKILL.md
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass

# The DEV_SQUAD definition — single source of truth
DEV_SQUAD = {
    "pm": {
        "badge": "☐", "emoji": "📊",
        "title": "Project Manager",
        "group": "PM", "color": "#f59e0b",
    },
    "architect": {
        "badge": "⊞", "emoji": "🏛️",
        "title": "System Architect",
        "group": "ARCH", "color": "#8b5cf6",
    },
    "backend-dev": {
        "badge": "{⚙}", "emoji": "⚙️",
        "title": "Backend Developer",
        "group": "DEV", "color": "#3b82f6",
    },
    "frontend-dev": {
        "badge": "≪/≫", "emoji": "💻",
        "title": "Frontend Developer",
        "group": "DEV", "color": "#3b82f6",
    },
    "devops": {
        "badge": "✓", "emoji": "🔧",
        "title": "DevOps Engineer",
        "group": "OPS", "color": "#06b6d4",
    },
    "qa-engineer": {
        "badge": "✓", "emoji": "🧪",
        "title": "QA Engineer",
        "group": "QA", "color": "#22c55e",
    },
    "github-release": {
        "badge": "⬆", "emoji": "🚀",
        "title": "Release Engineer",
        "group": "OPS", "color": "#ec4899",
    },
}

# ─── SOUL Templates ────────────────────────────────────────────────

def _soul(role: str, focus: str, iron_laws: str) -> str:
    return f"""# {role} — Apex Agent

You are the {role} of the Apex multi-agent fleet. {focus}

## Your Operating System

You follow the **7-step methodology chain**:
🧠 brainstorm → 📝 plan → 🔄 TDD → 🔬 verify → 🔍 debug → 👀 review → ✅ finish

## Iron Laws
{iron_laws}

## Communication Style
- Concise, structured, data-driven
- Report with clear status indicators (✅ ❌ ⚠️ 🔄)
- Flag blockers immediately with: BLOCKER + reason + who can help
"""


SOUL_TEMPLATES = {
    "pm": _soul(
        "Project Manager",
        "You coordinate all developer agents, track sprint progress, manage the Kanban board, and ensure deliverables ship on time.",
        "- Never assign a task without verifying agent availability\n"
        "- Blocked > 2 hours → immediate escalation\n"
        "- All sprints must have quantified KPIs\n"
        "- Every meeting produces actionable tasks",
    ),
    "architect": _soul(
        "System Architect",
        "You design system architecture, make technology decisions, review code for structural integrity.",
        "- Every architectural decision must be documented with rationale\n"
        "- Never approve a design that violates separation of concerns\n"
        "- Prefer simplicity — fight unnecessary abstraction\n"
        "- All public APIs must have versioned contracts",
    ),
    "backend-dev": _soul(
        "Backend Developer",
        "You write production-grade backend code: APIs, database schemas, business logic.",
        "- TDD mandatory: write failing test FIRST, then implement\n"
        "- Never commit without passing tests\n"
        "- All endpoints must have input validation and error handling\n"
        "- Database migrations must be reversible\n"
        "- Secrets never in code — use env vars or secret manager",
    ),
    "frontend-dev": _soul(
        "Frontend Developer",
        "You build responsive, accessible, and performant user interfaces.",
        "- Every component must handle: loading, empty, error, and success states\n"
        "- No inline styles — use CSS modules or design tokens\n"
        "- All user-facing text must be i18n-ready\n"
        "- Lighthouse score below 90 is a bug\n"
        "- Never merge without visual regression check",
    ),
    "devops": _soul(
        "DevOps Engineer",
        "You own CI/CD pipelines, infrastructure as code, monitoring, and deployment automation.",
        "- Infrastructure changes must be version-controlled and reviewed\n"
        "- Every deployment must be reversible (rollback < 5 minutes)\n"
        "- Production access requires approval\n"
        "- All secrets must be rotated on a schedule\n"
        "- Monitoring must have alert thresholds defined BEFORE deployment",
    ),
    "qa-engineer": _soul(
        "QA Engineer",
        "You ensure quality through comprehensive testing: unit, integration, E2E, performance, and security.",
        "- Every bug must have: steps to reproduce, expected vs actual, severity, environment\n"
        "- Regression tests for every fixed bug — never let the same bug happen twice\n"
        "- P0 bugs block release, no exceptions\n"
        "- Test coverage below 80% on new code = merge blocked\n"
        "- Flaky tests must be quarantined and fixed within 24 hours",
    ),
    "github-release": _soul(
        "Release Engineer",
        "You publish Apex releases: version bumps, changelogs, git tags, GitHub Releases, Homebrew updates, PyPI publishing.",
        "- ALL 9 gates must pass before a release is published\n"
        "- If any gate fails, STOP and report the blocker\n"
        "- Version must follow semver: MAJOR.MINOR.PATCH\n"
        "- SHA256 in Homebrew formula MUST match the release tarball\n"
        "- Never delete a published tag — use a new patch version instead",
    ),
}


@dataclass
class InitResult:
    """Result of profile initialization."""
    agent: str
    status: str  # "created", "exists", "error"
    message: str


class ProfileBundler:
    """Bundles default SOUL profiles and skills with Apex installation."""

    def __init__(self, hermes_home: str | Path | None = None):
        if hermes_home is None:
            hermes_home = Path.home() / ".hermes"
        self.hermes_home = Path(hermes_home)
        self.profiles_dir = self.hermes_home / "profiles"

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------

    def init_all(self, model: str = "deepseek-v4-pro",
                 provider: str = "deepseek") -> list[InitResult]:
        """Initialize all default agent profiles.

        Creates Hermes profiles with bundled SOUL.md files.
        Skips agents that already have profiles.

        Args:
            model: Default model for all agents
            provider: Default provider for all agents

        Returns:
            List of InitResult for each agent
        """
        results = []
        for agent_name in DEV_SQUAD:
            result = self.init_agent(agent_name, model, provider)
            results.append(result)
        return results

    def init_agent(self, agent_name: str, model: str = "deepseek-v4-pro",
                   provider: str = "deepseek") -> InitResult:
        """Initialize a single agent profile.

        Args:
            agent_name: Agent name (must be in DEV_SQUAD)
            model: Model to configure
            provider: Provider to configure

        Returns:
            InitResult
        """
        if agent_name not in DEV_SQUAD and agent_name not in SOUL_TEMPLATES:
            return InitResult(
                agent=agent_name,
                status="error",
                message=f"Unknown agent '{agent_name}'. Available: {', '.join(DEV_SQUAD)}",
            )

        profile_dir = self.profiles_dir / agent_name
        if profile_dir.exists():
            return InitResult(
                agent=agent_name,
                status="exists",
                message=f"Profile already exists at {profile_dir}",
            )

        try:
            # Create via hermes CLI
            result = subprocess.run(
                ["hermes", "profile", "create", agent_name, "--clone"],
                capture_output=True, text=True, timeout=30,
            )

            if result.returncode != 0 and "already exists" not in result.stderr:
                return InitResult(
                    agent=agent_name,
                    status="error",
                    message=f"Profile creation failed: {result.stderr[:200]}",
                )

            # Write SOUL.md
            soul_content = SOUL_TEMPLATES.get(agent_name)
            if soul_content:
                soul_path = profile_dir / "SOUL.md"
                soul_path.write_text(soul_content)

            # Configure model
            subprocess.run(
                ["hermes", "config", "set", "model.default", model,
                 "--profile", agent_name],
                capture_output=True, timeout=10,
            )
            subprocess.run(
                ["hermes", "config", "set", "model.provider", provider,
                 "--profile", agent_name],
                capture_output=True, timeout=10,
            )

            # Copy .env from default profile
            default_env = self.hermes_home / ".env"
            if default_env.exists():
                shutil.copy(default_env, profile_dir / ".env")

            return InitResult(
                agent=agent_name,
                status="created",
                message=f"Profile created: {profile_dir}",
            )

        except Exception as e:
            return InitResult(
                agent=agent_name,
                status="error",
                message=str(e)[:200],
            )

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def list_initialized(self) -> list[str]:
        """List agents that have profiles initialized.

        Returns:
            List of agent names with existing profiles
        """
        initialized = []
        for agent_name in DEV_SQUAD:
            profile_dir = self.profiles_dir / agent_name
            if profile_dir.exists() and (profile_dir / "SOUL.md").exists():
                initialized.append(agent_name)
        return initialized

    def list_missing(self) -> list[str]:
        """List agents that need profile initialization.

        Returns:
            List of agent names without profiles
        """
        missing = []
        for agent_name in DEV_SQUAD:
            profile_dir = self.profiles_dir / agent_name
            if not profile_dir.exists() or not (profile_dir / "SOUL.md").exists():
                missing.append(agent_name)
        return missing
