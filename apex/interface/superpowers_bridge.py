"""Apex — Superpowers Integration Bridge.

Connects the Superpowers development methodology to Apex Hermes profiles.
Creates the bootstrap injection mechanism and skill methodology chain.

Superpowers Methodology:
  brainstorm → write-plan → TDD → verify → debug → review → finish

Each development agent gets this methodology chain embedded in their SOUL.md,
plus access to the 4 new Superpowers-inspired skills.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

from apex.core.profile import ProfileManager, Profile, SoulConfig, APEX_HOME


# ════════════════════════════════════════════════════════════════
# Superpowers Skill Definitions (for Hermes SKILL.md files)
# ════════════════════════════════════════════════════════════════

SUPERPOWERS_SKILLS_DIR = Path(os.environ.get(
    "HERMES_HOME", Path.home() / ".hermes"
)) / "skills" / "dev-superpowers"

SUPERPOWERS_METHODOLOGY_CHAIN = [
    "brainstorming",
    "writing-plans",
    "test-driven-development",
    "verification-before-completion",
    "systematic-debugging",
    "requesting-code-review",
    "finishing-development",
]

SUPERPOWERS_DEV_AGENTS = [
    "frontend-dev",
    "backend-dev",
    "fullstack-dev",
    "architect",
    "devops",
]


# ════════════════════════════════════════════════════════════════
# Bootstrap Injection
# ════════════════════════════════════════════════════════════════


def inject_bootstrap_into_soul(soul_path: Path) -> bool:
    """Ensure a SOUL.md has the Superpowers bootstrap message.

    The bootstrap is a short block injected at the start of SOUL.md that
    tells the agent about skills and the methodology chain — similar to
    Superpowers' SessionStart hook that injects the using-superpowers content.

    Returns True if modified, False if already present.
    """
    if not soul_path.exists():
        return False

    content = soul_path.read_text()

    # Check if bootstrap already injected
    if "<!-- SUPERPRESETS-BOOTSTRAP" in content or "SUPERPOWERS-BOOTSTRAP" in content:
        return False

    bootstrap = """<!-- SUPERPOWERS-BOOTSTRAP -->
<EXTREMELY-IMPORTANT>
You have superpowers for development. Before ANY action — coding, debugging, fixing, or completing — check if a skill applies.

**If there is even a 1% chance a skill might apply, you MUST invoke it.**

This is not negotiable. This is not optional. You cannot rationalize your way out of this.

Development skills available (invoke using the Skill tool):
- brainstorming — Design before code. No implementation until design is approved.
- writing-plans — Decompose into bite-sized tasks with exact paths and code.
- test-driven-development — RED-GREEN-REFACTOR. Failing test first, then minimal code.
- verification-before-completion — NO completion claims without fresh verification evidence.
- systematic-debugging — NO fixes without root cause investigation first. 4-phase protocol.
- requesting-code-review — Always review before merging.
- finishing-development — Structured merge/PR/discard options.

**The development chain:** brainstorm → plan → TDD (implement) → verify → debug → review → finish

If you don't know which skill to use, start with brainstorming.
</EXTREMELY-IMPORTANT>

"""

    # Inject right after the identity section (after first ## 身份 or similar)
    lines = content.split("\n")
    inject_after = 0
    for i, line in enumerate(lines):
        if line.startswith("## 身份") or line.startswith("## Identity") or line.startswith("## 核心职责"):
            inject_after = i
            break

    if inject_after > 0:
        lines.insert(inject_after + 1, bootstrap)
    else:
        # If no section header found, inject after the first heading
        for i, line in enumerate(lines):
            if line.startswith("# "):
                lines.insert(i + 1, bootstrap)
                break
        else:
            lines.insert(0, bootstrap)

    soul_path.write_text("\n".join(lines))
    return True


def inject_bootstrap_all_agents() -> list[dict]:
    """Inject Superpowers bootstrap into all development agent SOUL.md files.

    Returns list of (agent_name, modified) results.
    """
    hermes_profiles = Path(os.environ.get(
        "HERMES_HOME", Path.home() / ".hermes"
    )) / "profiles"

    results = []
    for agent_name in SUPERPOWERS_DEV_AGENTS:
        soul_path = hermes_profiles / agent_name / "SOUL.md"
        if soul_path.exists():
            modified = inject_bootstrap_into_soul(soul_path)
            results.append({
                "agent": agent_name,
                "modified": modified,
                "path": str(soul_path),
            })

    return results


# ════════════════════════════════════════════════════════════════
# Agent Methodology Updater
# ════════════════════════════════════════════════════════════════


def sync_superpowers_skills_to_hermes(registry: "SkillRegistry" = None) -> list[dict]:
    """Register the Superpowers skills in the Skill Registry and generate SKILL.md files.

    This makes the methodology chain visible in apex skill list/show and
    cross-references with agent skill levels.

    Returns list of sync results.
    """
    if registry is None:
        from apex.interface.skill_registry import get_registry
        registry = get_registry()

    results = []

    # Register each skill in the chain
    superpowers_catalog = {
        "brainstorming": ("product", "Design exploration and requirements gathering. Hard gate: no code before design approval."),
        "verification-before-completion": ("devops", "Evidence before claims. Iron law: no completion claim without fresh verification."),
        "finishing-development": ("devops", "Structured branch completion: merge, PR, keep, or discard with cleanup."),
        "systematic-debugging": ("general", "4-phase root cause analysis: investigate → pattern → hypothesis → fix."),
    }

    # Register skills in registry
    for sname, (category, description) in superpowers_catalog.items():
        if sname not in registry._data.get("skills", {}):
            from apex.interface.skill_registry import SkillDef, SkillLevelDef, LEVELS
            levels = {}
            for lvl in LEVELS:
                levels[lvl] = {"description": "", "examples": []}
            levels["L0"] = {"description": f"不了解 {sname} 方法论", "examples": []}
            levels["L1"] = {"description": f"了解 {sname} 概念但无法独立执行", "examples": []}
            levels["L2"] = {"description": f"能独立执行 {sname} 工作流", "examples": []}
            levels["L3"] = {"description": f"精通 {sname}，能指导和优化", "examples": []}
            levels["L4"] = {"description": f"能设计 {sname} 策略和流程", "examples": []}
            levels["L5"] = {"description": "能创建方法论框架", "examples": []}

            registry._data.setdefault("skills", {})[sname] = {
                "name": sname.replace("-", " ").title(),
                "category": category,
                "description": description,
                "levels": levels,
            }

    # Assign methodology skills to dev agents at baseline
    now = time.strftime("%Y-%m-%d")
    for agent_name in SUPERPOWERS_DEV_AGENTS:
        for sname in SUPERPOWERS_METHODOLOGY_CHAIN:
            sinfo = registry._data.get("agents", {}).get(agent_name, {}).get("skills", {})
            if sname not in sinfo:
                registry._data.setdefault("agents", {}).setdefault(
                    agent_name, {"agent_name": agent_name, "skills": {}}
                )["skills"][sname] = {
                    "level": "L2",
                    "confidence": 0.6,
                    "assessed_by": "origin",
                    "assessed_at": now,
                    "evidence": [{
                        "type": "initialization",
                        "ref": "superpowers-integration",
                        "description": f"Superpowers methodology chain: {sname}",
                        "date": now,
                    }],
                }
                results.append({
                    "agent": agent_name,
                    "skill": sname,
                    "level": "L2",
                    "status": "registered",
                })

    registry.save()

    # Generate SKILL.md files
    try:
        from apex.interface.skill_registry import sync_all_skill_md
        sync_results = sync_all_skill_md(registry=registry)
        results.extend(sync_results)
    except Exception:
        pass

    return results


# ════════════════════════════════════════════════════════════════
# Verify Integration
# ════════════════════════════════════════════════════════════════


def verify_integration() -> dict:
    """Verify the Superpowers integration is complete.

    Checks:
    - 4 Superpowers skills exist in ~/.hermes/skills/dev-superpowers/
    - All 5 dev agents have SOUL.md with bootstrap and methodology
    - Skills are registered in Skill Registry
    - SKILL.md files exist for dev agents

    Returns dict with verification results.
    """
    results = {
        "skills": {},
        "agents": {},
        "registry": {},
        "overall": "checking",
    }

    # 1. Check skills — can be in dev-superpowers or the main skills dir
    existing_skills = set()
    skills_base = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")) / "skills"
    for sname in SUPERPOWERS_METHODOLOGY_CHAIN:
        # Check dev-superpowers first, then main skill directories
        for subdir in ["dev-superpowers", "software-development", "productivity"]:
            sp = skills_base / subdir / sname / "SKILL.md"
            if sp.exists():
                results["skills"][sname] = {"exists": True, "size": sp.stat().st_size, "location": str(sp)}
                existing_skills.add(sname)
                break
        else:
            results["skills"][sname] = {"exists": False, "size": 0, "location": "not found"}

    # 2. Check agent SOUL.md files
    hermes_profiles = Path(os.environ.get(
        "HERMES_HOME", Path.home() / ".hermes"
    )) / "profiles"

    for agent_name in SUPERPOWERS_DEV_AGENTS:
        soul_path = hermes_profiles / agent_name / "SOUL.md"
        skill_md = hermes_profiles / agent_name / "SKILL.md"
        if soul_path.exists():
            content = soul_path.read_text()
            has_bootstrap = "SUPERPOWERS-BOOTSTRAP" in content
            has_methodology = "Development Methodology" in content or "开发方法论" in content
            has_iron_laws = "Iron Laws" in content or "铁律" in content
            has_red_flags = "Red Flags" in content or "危险信号" in content or "Anti-Rationalization" in content

            results["agents"][agent_name] = {
                "exists": True,
                "size": soul_path.stat().st_size,
                "has_bootstrap": has_bootstrap,
                "has_methodology": has_methodology,
                "has_iron_laws": has_iron_laws,
                "has_red_flags": has_red_flags,
                "has_skill_md": skill_md.exists(),
            }

    # 3. Check registry
    try:
        from apex.interface.skill_registry import get_registry
        registry = get_registry()

        for sname in SUPERPOWERS_METHODOLOGY_CHAIN:
            in_catalog = sname in registry._data.get("skills", {})
            results["registry"][sname] = {"in_catalog": in_catalog}

        for agent_name in SUPERPOWERS_DEV_AGENTS:
            agent_data = registry._data.get("agents", {}).get(agent_name, {})
            if agent_data:
                has_methodology_skills = all(
                    s in agent_data.get("skills", {})
                    for s in SUPERPOWERS_METHODOLOGY_CHAIN
                )
                results["registry"][f"{agent_name}_skills"] = {
                    "has_all_methodology": has_methodology_skills,
                    "count": len(agent_data.get("skills", {})),
                }
    except Exception as e:
        results["registry_error"] = str(e)

    # Overall verdict
    all_skills_ok = len(existing_skills) == len(SUPERPOWERS_METHODOLOGY_CHAIN)
    all_agents_ok = all(
        r.get("has_bootstrap") and r.get("has_methodology")
        for r in results["agents"].values()
    )

    results["overall"] = "✅ PASS" if (all_skills_ok and all_agents_ok) else "⚠️ PARTIAL"
    return results
