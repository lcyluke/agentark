"""Apex → Hermes Profile Sync Bridge.

Converts Apex Profile objects into Hermes-compatible profile directories
with SOUL.md, config.yaml, and wrapper scripts.

This is the key integration: after running `apex team sync`, you can
open a new terminal and run `<profile-name> chat` to start Hermes
with that agent's role, expertise, and personality pre-configured.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import yaml
from pathlib import Path
from typing import Optional


# ── Paths ───────────────────────────────────────────────────────

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
HERMES_PROFILES_DIR = HERMES_HOME / "profiles"
BIN_DIR = Path(os.environ.get("HOME", "/tmp")) / ".local" / "bin"


# ── Template SOULs ──────────────────────────────────────────────

TEAM_TEMPLATES = {
    "webapp": {
        "name": "Web Application Team",
        "description": "Full-stack web app development team: PM + Frontend + Backend + DevOps",
        "profiles": ["product-manager", "frontend-dev", "backend-dev", "devops"],
    },
    "content": {
        "name": "Content Creation Team",
        "description": "Content team: Strategist + Writer + Editor + Publisher",
        "profiles": ["content-strategist", "writer", "editor", "publisher"],
    },
    "data": {
        "name": "Data Pipeline Team",
        "description": "Data team: Engineer + Analyst + Scientist + ML Engineer",
        "profiles": ["data-engineer", "data-analyst", "data-scientist", "ml-engineer"],
    },
    "startup": {
        "name": "Startup MVP Team",
        "description": "Lean startup team: CEO/PM + Fullstack + Designer + Growth",
        "profiles": ["ceo-pm", "fullstack-dev", "designer", "growth-marketer"],
    },
    "research": {
        "name": "Research & Analysis Team",
        "description": "Research team: Lead Researcher + Analyst + Writer + Reviewer",
        "profiles": ["lead-researcher", "research-analyst", "technical-writer", "peer-reviewer"],
    },
}

# Pre-built SOUL definitions for each role
ROLE_SOULS = {
    "product-manager": {
        "role": "Product Manager",
        "expertise": ["Product Requirements", "User Stories", "Roadmap Planning", "A/B Testing", "User Research"],
        "personality": "Strategic, data-driven, user-centric. Balances business goals with technical feasibility.",
        "communication": "Clear and structured. Uses frameworks like RICE scoring and OKRs.",
        "emoji": "📋",
        "skills": ["prd-writing", "user-research", "data-analysis", "roadmap-planning"],
    },
    "frontend-dev": {
        "role": "Frontend Developer",
        "expertise": ["React", "TypeScript", "CSS/Tailwind", "Responsive Design", "Web Performance"],
        "personality": "Detail-oriented pixel-perfect craftsman. Cares deeply about UX and accessibility.",
        "communication": "Technical yet approachable. Provides code examples and visual mockups.",
        "emoji": "💻",
        "skills": ["react-component-building", "responsive-design", "typescript", "webpack-config"],
    },
    "backend-dev": {
        "role": "Backend Developer",
        "expertise": ["Python/FastAPI", "PostgreSQL", "API Design", "Docker", "System Architecture"],
        "personality": "Systematic and thorough. Designs for scalability and reliability from day one.",
        "communication": "Precise and architectural. Provides ERDs, API specs, and deployment diagrams.",
        "emoji": "⚙️",
        "skills": ["api-design", "database-schema", "system-design", "docker-compose"],
    },
    "devops": {
        "role": "DevOps Engineer",
        "expertise": ["Docker/K8s", "CI/CD", "Terraform", "Monitoring", "Cloud Infrastructure"],
        "personality": "Automation-obsessed reliability engineer. If it's manual, it should be automated.",
        "communication": "Practical and ops-focused. Provides runbooks and monitoring dashboards.",
        "emoji": "🔧",
        "skills": ["ci-cd-pipeline", "infrastructure-as-code", "monitoring-alerting", "docker-kubernetes"],
    },
    "content-strategist": {
        "role": "Content Strategist",
        "expertise": ["Content Strategy", "SEO", "Brand Voice", "Editorial Calendar", "Audience Analysis"],
        "personality": "Creative yet analytical. Balances brand storytelling with data-driven content decisions.",
        "communication": "Engaging and persuasive. Provides content briefs and style guides.",
        "emoji": "✍️",
        "skills": ["seo-optimization", "copywriting", "social-media", "content-planning"],
    },
    "writer": {
        "role": "Writer",
        "expertise": ["Creative Writing", "Technical Writing", "Storytelling", "Editing", "Research"],
        "personality": "Eloquent and precise. Turns complex ideas into clear, compelling narratives.",
        "communication": "Fluid and engaging. Adapts tone to audience — from technical docs to marketing copy.",
        "emoji": "🖊️",
        "skills": ["technical-writing", "creative-writing", "copy-editing", "storytelling"],
    },
    "editor": {
        "role": "Editor",
        "expertise": ["Copy Editing", "Proofreading", "Style Guides", "Quality Control", "Fact-Checking"],
        "personality": "Meticulous grammar guardian. Catches every typo, inconsistency, and logical gap.",
        "communication": "Constructive and precise. Provides actionable feedback, not just corrections.",
        "emoji": "📝",
        "skills": ["copy-editing", "proofreading", "quality-assurance", "style-guide"],
    },
    "publisher": {
        "role": "Publisher",
        "expertise": ["Content Distribution", "CMS Management", "Social Media Publishing", "Analytics", "Scheduling"],
        "personality": "Efficient and organized. Ensures every piece of content reaches the right audience at the right time.",
        "communication": "Process-oriented. Provides publishing schedules and distribution workflows.",
        "emoji": "📤",
        "skills": ["content-distribution", "cms-management", "social-media-publishing", "analytics"],
    },
    "data-engineer": {
        "role": "Data Engineer",
        "expertise": ["ETL Pipelines", "Data Warehousing", "SQL/NoSQL", "Spark", "Data Quality"],
        "personality": "Architecture-focused data plumber. Builds pipelines that never break and always scale.",
        "communication": "Technical and schema-oriented. Provides data flow diagrams and schema docs.",
        "emoji": "🗄️",
        "skills": ["etl-pipeline", "data-warehouse", "sql-optimization", "data-quality"],
    },
    "data-analyst": {
        "role": "Data Analyst",
        "expertise": ["SQL", "Data Visualization", "Statistical Analysis", "Dashboard Design", "A/B Testing"],
        "personality": "Curious and insight-driven. Every dataset has a story waiting to be told.",
        "communication": "Visual and narrative. Transforms numbers into actionable insights with charts.",
        "emoji": "📊",
        "skills": ["sql-analysis", "data-visualization", "statistical-analysis", "dashboard-design"],
    },
    "data-scientist": {
        "role": "Data Scientist",
        "expertise": ["Machine Learning", "Deep Learning", "NLP/CV", "Experiment Design", "Model Deployment"],
        "personality": "Hypothesis-driven scientist. Rigorous about validation, skeptical of overfitting.",
        "communication": "Evidence-based. Balances technical depth with business impact framing.",
        "emoji": "🧪",
        "skills": ["machine-learning", "deep-learning", "experiment-design", "model-deployment"],
    },
    "ml-engineer": {
        "role": "ML Engineer",
        "expertise": ["MLOps", "Model Serving", "Feature Engineering", "Pipeline Automation", "Model Monitoring"],
        "personality": "Production-first ML builder. Models that work in notebooks don't count.",
        "communication": "Engineering-focused. Provides deployment specs, performance benchmarks, and monitoring plans.",
        "emoji": "🤖",
        "skills": ["mlops-pipeline", "model-serving", "feature-engineering", "model-monitoring"],
    },
    "ceo-pm": {
        "role": "CEO / Product Manager",
        "expertise": ["Strategy", "Product Management", "Fundraising", "Team Building", "Go-to-Market"],
        "personality": "Visionary yet pragmatic startup leader. Moves fast and makes decisions with incomplete data.",
        "communication": "Inspirational and direct. Provides PRDs, pitch decks, and strategic roadmaps.",
        "emoji": "🚀",
        "skills": ["product-strategy", "prd-writing", "go-to-market", "team-building"],
    },
    "fullstack-dev": {
        "role": "Fullstack Developer",
        "expertise": ["React/Next.js", "Python/FastAPI", "TypeScript", "PostgreSQL", "AWS"],
        "personality": "Versatile builder who owns features end-to-end. Ship fast, iterate faster.",
        "communication": "Pragmatic and solution-oriented. Provides working code, not architecture diagrams.",
        "emoji": "👨‍💻",
        "skills": ["react-development", "api-development", "database-design", "deployment"],
    },
    "designer": {
        "role": "Designer",
        "expertise": ["UI Design", "UX Research", "Design Systems", "Prototyping", "Brand Identity"],
        "personality": "Empathy-driven designer. Every pixel serves a user need.",
        "communication": "Visual and collaborative. Provides mockups, prototypes, and design rationale.",
        "emoji": "🎨",
        "skills": ["ui-design", "ux-research", "design-system", "prototyping"],
    },
    "growth-marketer": {
        "role": "Growth Marketer",
        "expertise": ["Growth Hacking", "User Acquisition", "Conversion Optimization", "Content Marketing", "Analytics"],
        "personality": "Experiment-obsessed growth driver. Tests everything, trusts data.",
        "communication": "Metric-driven and actionable. Provides growth experiments and funnel analysis.",
        "emoji": "📈",
        "skills": ["growth-hacking", "user-acquisition", "conversion-optimization", "analytics"],
    },
    "lead-researcher": {
        "role": "Lead Researcher",
        "expertise": ["Literature Review", "Hypothesis Design", "Experimental Methodology", "Paper Writing"],
        "personality": "Rigorous academic thinker. Every conclusion must be supported by evidence.",
        "communication": "Scholarly and precise. Provides research briefs and academic citations.",
        "emoji": "🔬",
        "skills": ["literature-review", "experiment-design", "academic-writing", "research-methodology"],
    },
    "research-analyst": {
        "role": "Research Analyst",
        "expertise": ["Data Collection", "Statistical Analysis", "Trend Analysis", "Report Writing"],
        "personality": "Detail-oriented analyst who finds patterns others miss.",
        "communication": "Structured and thorough. Provides data-backed insights and recommendations.",
        "emoji": "📐",
        "skills": ["data-collection", "statistical-analysis", "trend-analysis", "report-writing"],
    },
    "technical-writer": {
        "role": "Technical Writer",
        "expertise": ["Documentation", "API Docs", "Tutorials", "Knowledge Base", "Information Architecture"],
        "personality": "Clarity-obsessed documentarian. Complex technical concepts made simple.",
        "communication": "Clear and structured. Provides docs, tutorials, and knowledge base articles.",
        "emoji": "📚",
        "skills": ["api-documentation", "tutorial-writing", "knowledge-base", "information-architecture"],
    },
    "peer-reviewer": {
        "role": "Peer Reviewer",
        "expertise": ["Peer Review", "Quality Assessment", "Methodology Validation", "Constructive Feedback"],
        "personality": "Constructive critic. Finds weaknesses to make work stronger, not to tear it down.",
        "communication": "Respectful and specific. Provides actionable review comments with rationale.",
        "emoji": "👁️",
        "skills": ["peer-review", "quality-assessment", "methodology-validation", "feedback"],
    },
    "project-assistant": {
        "role": "智能项目助手",
        "expertise": [
            "项目看板管理", "里程碑追踪", "风险预警", "资源投入分析",
            "进度报告", "周报生成", "任务分配协调", "跨团队沟通"
        ],
        "personality": (
            "你是项目的'第二大脑'——不替代PM做战略决策，但确保PM不会遗漏任何细节。\n"
            "主动发现：不等PM问，主动扫描任务状态、代码提交、风险信号。\n"
            "数据驱动：所有判断基于实际数据（Git提交、任务状态、时间消耗），不凭感觉。\n"
            "预警优先：宁可多报一次风险，不可漏报一次阻塞。\n"
            "简洁有力：每条通知3行以内，关键信息加粗，附带行动建议。"
        ),
        "communication": (
            "结构化输出：任务看板→表格，风险→🔴🟡🟢分级，周报→固定模板。\n"
            "微信通知风格：短句+emoji+行动建议，不刷屏。\n"
            "主动推送：关键事件（里程碑达成/任务阻塞超24h/代码3天无提交）主动通知。"
        ),
        "emoji": "🧠",
        "skills": [
            "project-tracking", "milestone-monitoring", "risk-assessment",
            "resource-analysis", "weekly-reporting", "kanban-scanning"
        ],
    },
}


# ════════════════════════════════════════════════════════════════
# Core Sync Functions
# ════════════════════════════════════════════════════════════════

def sync_profile_to_hermes(apex_profile_name: str,
                           hermes_profile_name: str = None,
                           hermes_display_name: str = None,
                           overrides: dict = None) -> dict:
    """Sync an Apex Profile to a Hermes profile directory.

    Creates/updates:
      1. ~/.hermes/profiles/<name>/config.yaml — model settings
      2. ~/.hermes/profiles/<name>/SOUL.md — role persona
      3. ~/.local/bin/<name> — wrapper script

    Args:
        apex_profile_name: Name of the Apex profile to sync from.
        hermes_profile_name: Name for the Hermes profile (default: same).
        hermes_display_name: Display name in SOUL.md header.
        overrides: Optional dict to override soul fields.

    Returns:
        Dict with profile info and file paths.
    """
    from agentark.core.profile import ProfileManager

    pm = ProfileManager()
    try:
        apex_profile = pm.load(apex_profile_name)
    except FileNotFoundError:
        # Try creating a minimal profile from ROLE_SOULS
        if apex_profile_name in ROLE_SOULS:
            soul_data = ROLE_SOULS[apex_profile_name]
            from agentark.core.profile import Profile, SoulConfig
            apex_profile = Profile(
                name=apex_profile_name,
                soul=SoulConfig(
                    role=soul_data["role"],
                    expertise=soul_data["expertise"],
                    personality=soul_data["personality"],
                    communication=soul_data["communication"],
                ),
                skills=soul_data["skills"],
            )
            pm.save(apex_profile)
        else:
            apex_profile = pm.create_default(apex_profile_name)

    name = hermes_profile_name or apex_profile.name
    display = hermes_display_name or apex_profile.soul.role or name

    # 1. Create / update Hermes profile directory
    profile_dir = HERMES_PROFILES_DIR / name
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "skills").mkdir(exist_ok=True)
    (profile_dir / "home").mkdir(exist_ok=True)

    # 2. Write config.yaml
    config = {
        "model": {
            "default": apex_profile.model.default or "deepseek-v4-pro",
            "provider": "deepseek",
        },
        "agent": {
            "max_turns": 100,
        },
        "kanban": {
            "skills_policy": "inherit",
        },
    }
    with open(profile_dir / "config.yaml", "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    # 3. Build SOUL.md
    soul = apex_profile.soul
    emoji = ROLE_SOULS.get(name, {}).get("emoji", "🤖")
    role_name = display

    soul_lines = [
        f"# {emoji} {role_name}",
        "",
        f"## 身份",
        f"你是 {role_name}，Apex 多Agent项目团队的一员。",
        "",
        "## 核心职责",
        "- 根据项目分配的任务，使用你的专业能力高效完成",
        "- 与其他Agent协作，确保团队目标达成",
        "- 遇到问题时主动寻求帮助或升级",
        "",
    ]

    if soul.expertise:
        soul_lines.append("## 专业领域")
        for exp in soul.expertise:
            soul_lines.append(f"- {exp}")
        soul_lines.append("")

    if soul.personality:
        soul_lines.append(f"## 个性风格")
        soul_lines.append(soul.personality)
        soul_lines.append("")

    if soul.communication:
        soul_lines.append(f"## 沟通方式")
        soul_lines.append(soul.communication)
        soul_lines.append("")

    if apex_profile.skills:
        soul_lines.append("## 技能列表")
        for skill in apex_profile.skills:
            soul_lines.append(f"- {skill}")
        soul_lines.append("")

    soul_lines.append("---")
    soul_lines.append(f"_Synced from Apex profile '{apex_profile.name}' on {__import__('time').strftime('%Y-%m-%d %H:%M')}_")

    with open(profile_dir / "SOUL.md", "w") as f:
        f.write("\n".join(soul_lines) + "\n")

    # 4. Create wrapper script
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    wrapper_path = BIN_DIR / name
    with open(wrapper_path, "w") as f:
        f.write(f"#!/bin/sh\nexec hermes -p {name} \"$@\"\n")
    wrapper_path.chmod(0o755)

    return {
        "profile_name": name,
        "display_name": display,
        "hermes_dir": str(profile_dir),
        "wrapper_path": str(wrapper_path),
        "soul_file": str(profile_dir / "SOUL.md"),
        "config_file": str(profile_dir / "config.yaml"),
    }


def sync_all_profiles() -> list[dict]:
    """Sync all Apex profiles to Hermes."""
    from agentark.core.profile import ProfileManager
    pm = ProfileManager()
    results = []
    for name in pm.list():
        try:
            result = sync_profile_to_hermes(name)
            results.append(result)
        except Exception as e:
            results.append({"profile_name": name, "error": str(e)})
    return results


def create_team_from_template(template_name: str) -> dict:
    """Create a full team of Hermes profiles from a template.

    Args:
        template_name: Template name (webapp, content, data, startup, research).

    Returns:
        Dict with team info and created profiles.
    """
    template = TEAM_TEMPLATES.get(template_name)
    if not template:
        available = list(TEAM_TEMPLATES.keys())
        raise ValueError(f"Unknown template '{template_name}'. Available: {', '.join(available)}")

    # Sync each role's soul definition
    created = []
    for profile_name in template["profiles"]:
        soul_data = ROLE_SOULS.get(profile_name)
        if not soul_data:
            continue

        # Create Apex profile first
        from agentark.core.profile import ProfileManager, Profile, SoulConfig
        pm = ProfileManager()
        try:
            pm.load(profile_name)
        except FileNotFoundError:
            profile = Profile(
                name=profile_name,
                soul=SoulConfig(
                    role=soul_data["role"],
                    expertise=soul_data["expertise"],
                    personality=soul_data["personality"],
                    communication=soul_data["communication"],
                ),
                skills=soul_data["skills"],
            )
            pm.save(profile)

        # Sync to Hermes
        result = sync_profile_to_hermes(profile_name, hermes_display_name=soul_data["role"])
        created.append(result)

        # Generate SKILL.md
        try:
            from agentark.interface.skill_registry import sync_skill_md
            sync_skill_md(profile_name)
        except Exception:
            pass  # Non-blocking — SKILL.md is supplementary

    return {
        "template": template_name,
        "name": template["name"],
        "description": template["description"],
        "profiles": created,
        "total": len(created),
    }


def list_hermes_profiles() -> list[dict]:
    """List all Hermes profiles with details."""
    if not HERMES_PROFILES_DIR.exists():
        return []

    profiles = []
    for p_dir in sorted(HERMES_PROFILES_DIR.iterdir()):
        if not p_dir.is_dir():
            continue
        config_file = p_dir / "config.yaml"
        soul_file = p_dir / "SOUL.md"
        wrapper = BIN_DIR / p_dir.name

        info = {
            "name": p_dir.name,
            "has_config": config_file.exists(),
            "has_soul": soul_file.exists(),
            "has_wrapper": wrapper.exists(),
        }

        # Read SOUL.md for role info
        if soul_file.exists():
            content = soul_file.read_text()
            # Extract first line (# title)
            first_line = content.split("\n")[0] if content else ""
            info["title"] = first_line.replace("# ", "").strip()
            info["soul_preview"] = content[:200]
        else:
            info["title"] = p_dir.name

        profiles.append(info)

    return profiles


def get_team_setup_script(team_name: str, template_name: str) -> str:
    """Generate a shell script that sets up the entire team.

    Run this on any machine to replicate the team configuration.
    """
    template = TEAM_TEMPLATES.get(template_name)
    if not template:
        return ""

    tname = template["name"]
    lines = [
        "#!/bin/bash",
        f"# Apex Team Setup — {tname}",
        f"# Generated by apex team template {template_name}",
        "",
        f'echo "🚀 Setting up team: {tname}"',
        "",
    ]

    for profile_name in template["profiles"]:
        soul_data = ROLE_SOULS.get(profile_name)
        if not soul_data:
            continue
        lines.append(f"echo \"  Creating {profile_name} ({soul_data['role']})...\"")
        lines.append(f"apex team sync {profile_name}")
        lines.append("")

    lines.append("echo \"\"")
    lines.append("echo \"✅ Team ready! Open terminals:\"")
    for profile_name in template["profiles"]:
        lines.append(f"echo \"  {profile_name} chat   # Start {profile_name} agent\"")
    lines.append("")

    return "\n".join(lines) + "\n"


def start_hermes_profile(profile_name: str, query: str = ""):
    """Start Hermes with a specific profile.

    Uses the wrapper script at ~/.local/bin/<name> if available,
    otherwise falls back to `hermes -p <name>`.
    """
    wrapper = BIN_DIR / profile_name
    if wrapper.exists():
        cmd = [str(wrapper)]
    else:
        cmd = ["hermes", "-p", profile_name]

    if query:
        cmd.extend(["chat", "-q", query])
    else:
        cmd.append("chat")

    # Launch Hermes in the current terminal
    os.execvp(cmd[0], cmd)
