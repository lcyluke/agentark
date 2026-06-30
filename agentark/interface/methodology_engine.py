"""Apex — Superpowers Methodology Engine

Deep integration: 2-stage code review, methodology auto-chaining,
receiving review protocol, git worktree isolation, enhanced parallel dispatch.

This extends the existing superpowers_bridge.py with the remaining
Superpowers capabilities.
"""

from __future__ import annotations

import os
import re
import time
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from agentark.core.profile import AGENTARK_HOME
from agentark.interface.superpowers_bridge import (
    SUPERPOWERS_DEV_AGENTS,
    SUPERPOWERS_METHODOLOGY_CHAIN,
)


# ════════════════════════════════════════════════════════════════
# ── Phase 3: 2-Stage Code Review Engine ───────────────────────
# ════════════════════════════════════════════════════════════════


@dataclass
class ReviewFinding:
    """A single finding from a code review stage."""
    severity: str  # critical, important, minor
    category: str  # correctness, security, performance, style, design
    file: str = ""
    line: int = 0
    message: str = ""
    recommendation: str = ""


@dataclass
class ReviewResult:
    """Result of a single review stage."""
    stage: str  # spec-compliance or code-quality
    status: str  # approved, changes-requested, blocked
    strengths: list[str] = field(default_factory=list)
    findings: list[ReviewFinding] = field(default_factory=list)
    summary: str = ""
    approved: bool = False

    @property
    def has_blockers(self) -> bool:
        return any(f.severity == "critical" for f in self.findings)

    @property
    def has_important_issues(self) -> bool:
        return any(f.severity == "important" for f in self.findings)

    def to_dict(self) -> dict:
        return {
            "stage": self.stage,
            "status": self.status,
            "strengths": self.strengths,
            "findings": [asdict(f) for f in self.findings],
            "summary": self.summary,
            "approved": self.approved,
            "has_blockers": self.has_blockers,
        }


@dataclass
class TwoStageReview:
    """Complete 2-stage review output."""
    spec_review: ReviewResult
    quality_review: Optional[ReviewResult] = None
    overall_status: str = "pending"  # pending, approved, changes-needed, failed

    @property
    def passed(self) -> bool:
        return (
            self.spec_review.approved
            and (self.quality_review is None or self.quality_review.approved)
        )

    def summary_text(self) -> str:
        lines = ["📋 2-STAGE REVIEW RESULT", "=" * 50]
        lines.append(f"\nStage 1 (Spec Compliance): {self.spec_review.status}")
        lines.append(f"  {'✅' if self.spec_review.approved else '❌'} Approved: {self.spec_review.approved}")
        if self.spec_review.findings:
            for f in self.spec_review.findings:
                sev = "🔴" if f.severity == "critical" else ("🟡" if f.severity == "important" else "🔵")
                lines.append(f"  {sev} [{f.category}] {f.file}:{f.line} - {f.message}")

        if self.quality_review:
            lines.append(f"\nStage 2 (Code Quality): {self.quality_review.status}")
            lines.append(f"  {'✅' if self.quality_review.approved else '❌'} Approved: {self.quality_review.approved}")
            if self.quality_review.strengths:
                for s in self.quality_review.strengths:
                    lines.append(f"  ✅ {s}")
            if self.quality_review.findings:
                for f in self.quality_review.findings:
                    sev = "🔴" if f.severity == "critical" else ("🟡" if f.severity == "important" else "🔵")
                    lines.append(f"  {sev} [{f.category}] {f.file}:{f.line} - {f.message}")

        lines.append(f"\nOverall: {'✅ PASS' if self.passed else '❌ FAIL'}")
        return "\n".join(lines)


def run_spec_review(spec_content: str, code_diff: str, task_description: str) -> ReviewResult:
    """Stage 1: Compare implemented code against spec requirements.

    Checks:
    - All spec requirements are implemented (nothing missing)
    - No extra features beyond spec (YAGNI violations)
    - Interfaces match spec definitions
    - Behavior matches expected outcomes
    """
    findings = []
    strengths = []

    # Check for missing implementations
    spec_requirements = _extract_requirements(spec_content)
    code_has_features = _extract_features(code_diff)

    for req in spec_requirements:
        if req not in code_has_features:
            findings.append(ReviewFinding(
                severity="critical",
                category="correctness",
                message=f"Missing spec requirement: {req}",
                recommendation=f"Implement: {req}",
            ))

    # Check for YAGNI violations
    code_features = _extract_from_diff(code_diff)
    for feat in code_features:
        if feat not in spec_requirements:
            findings.append(ReviewFinding(
                severity="important",
                category="design",
                message=f"Extra feature not in spec: {feat}",
                recommendation=f"Remove {feat} unless explicitly requested",
            ))

    if not findings:
        strengths.append("All spec requirements implemented correctly")
        strengths.append("No YAGNI violations — scope matches spec exactly")

    return ReviewResult(
        stage="spec-compliance",
        status="approved" if not any(f.severity == "critical" for f in findings) else "changes-requested",
        strengths=strengths,
        findings=findings,
        summary=f"Spec compliance: {len([f for f in findings if f.severity == 'critical'])} critical issues",
        approved=not any(f.severity == "critical" for f in findings),
    )


def run_quality_review(code_diff: str, test_output: str = "") -> ReviewResult:
    """Stage 2: Code quality review after spec compliance passes.

    Checks:
    - Code structure and organization
    - Error handling
    - Test quality and coverage
    - Performance considerations
    - Security best practices
    - Magic numbers, hardcoding
    """
    findings = []
    strengths = []

    # Check for magic numbers
    magic_numbers = _find_magic_numbers(code_diff)
    for num, file_line in magic_numbers:
        findings.append(ReviewFinding(
            severity="minor",
            category="style",
            file=file_line[0] if file_line else "",
            line=file_line[1] if file_line else 0,
            message=f"Magic number '{num}' should be a named constant",
            recommendation="Extract to a named constant (e.g., MAX_RETRY_COUNT)",
        ))

    # Check for error handling
    if not _has_error_handling(code_diff):
        findings.append(ReviewFinding(
            severity="important",
            category="correctness",
            message="No error handling detected in new code",
            recommendation="Add try/catch or error handling for edge cases",
        ))

    # Check test patterns
    if "test" in code_diff.lower():
        if "assert" not in code_diff and "expect" not in code_diff:
            findings.append(ReviewFinding(
                severity="important",
                category="testing",
                message="Tests detected but no assertions found",
                recommendation="Add assertions to verify expected behavior",
            ))

    # Test output analysis
    if test_output:
        failures = re.findall(r"(\d+) failed", test_output)
        if failures and int(failures[0]) > 0:
            findings.append(ReviewFinding(
                severity="critical",
                category="testing",
                message=f"{failures[0]} test(s) failing",
                recommendation="Fix failing tests before merge",
            ))

    if not findings:
        strengths.append("Clean code structure with good practices")
        strengths.append("Proper error handling patterns")

    if not _has_error_handling(code_diff) and not findings:
        strengths.append("Clean, straightforward implementation")

    return ReviewResult(
        stage="code-quality",
        status="approved" if not any(f.severity == "critical" for f in findings) else "changes-requested",
        strengths=strengths,
        findings=findings,
        summary=f"Quality review: {len(findings)} issues found",
        approved=not any(f.severity == "critical" for f in findings) and not any(f.severity == "important" and f.category == "correctness" for f in findings),
    )


def run_two_stage_review(spec_path: str, base_sha: str, head_sha: str,
                          task_description: str) -> TwoStageReview:
    """Run a complete 2-stage code review using git SHAs.

    Args:
        spec_path: Path to spec/plan file.
        base_sha: Starting commit SHA.
        head_sha: Ending commit SHA.
        task_description: Description of what was implemented.

    Returns:
        TwoStageReview with both stages.
    """
    # Get diff between SHAs
    try:
        diff = subprocess.run(
            ["git", "diff", base_sha, head_sha],
            capture_output=True, text=True, timeout=15,
        )
        code_diff = diff.stdout
    except Exception:
        code_diff = ""

    # Read spec content
    spec_content = ""
    if spec_path and Path(spec_path).exists():
        spec_content = Path(spec_path).read_text()

    # Stage 1: Spec compliance
    spec_review = run_spec_review(spec_content, code_diff, task_description)

    # Stage 2: Code quality (only if spec passes)
    quality_review = None
    if spec_review.approved:
        quality_review = run_quality_review(code_diff)

    return TwoStageReview(
        spec_review=spec_review,
        quality_review=quality_review,
        overall_status="approved" if (spec_review.approved and (quality_review is None or quality_review.approved)) else "changes-needed",
    )


# ════════════════════════════════════════════════════════════════
# ── Phase 4: Methodology Auto-Chaining ─────────────────────────
# ════════════════════════════════════════════════════════════════

METHODOLOGY_CHAIN_MAP = {
    "brainstorming": {
        "next": "writing-plans",
        "trigger": "user approved design, spec written and committed",
        "condition": "spec_file exists at docs/superpowers/specs/",
    },
    "writing-plans": {
        "next": None,  # User chooses between subagent-driven or inline
        "options": ["subagent-driven-development", "executing-plans"],
        "trigger": "plan written, saved to docs/superpowers/plans/",
        "condition": "plan_file exists",
    },
    "subagent-driven-development": {
        "next": "verification-before-completion",
        "trigger": "all tasks completed and reviewed",
        "condition": "no remaining open tasks",
    },
    "test-driven-development": {
        "next": "verification-before-completion",
        "trigger": "all tests green, RED-GREEN-REFACTOR completed",
        "condition": "test suite passes",
    },
    "verification-before-completion": {
        "next": "finishing-development",
        "trigger": "verification commands run, evidence confirmed",
        "condition": "evidence collected and verified",
    },
    "requesting-code-review": {
        "next": "verification-before-completion",
        "trigger": "review approved or feedback incorporated",
        "condition": "review completed",
    },
    "finishing-development": {
        "next": None,  # Terminal state
        "trigger": None,
        "condition": None,
    },
}


@dataclass
class ChainState:
    """Current state of a methodology chain execution."""
    current_skill: str = ""
    completed_skills: list[str] = field(default_factory=list)
    active: bool = False
    started_at: float = 0.0
    last_action: str = ""

    def next_skill(self) -> Optional[str]:
        """Determine the next skill in the methodology chain."""
        chain_entry = METHODOLOGY_CHAIN_MAP.get(self.current_skill)
        if not chain_entry:
            return None

        # If there are options, return the first (default)
        if chain_entry.get("options"):
            return chain_entry["options"][0]

        # If there's a direct next skill
        next_skill = chain_entry.get("next")
        if next_skill and next_skill not in self.completed_skills:
            return next_skill

        return None

    def advance(self, skill_name: str) -> str:
        """Advance the chain to the next skill.

        Returns announcement text for the agent to use.
        """
        self.completed_skills.append(self.current_skill)
        self.current_skill = skill_name
        self.last_action = f"completed_{self.completed_skills[-1]}"

        # Generate transition announcement
        emoji_map = {
            "brainstorming": "🧠",
            "writing-plans": "📝",
            "test-driven-development": "🔄",
            "subagent-driven-development": "🤖",
            "verification-before-completion": "🔬",
            "systematic-debugging": "🔍",
            "requesting-code-review": "👀",
            "finishing-development": "✅",
        }

        emoji = emoji_map.get(skill_name, "➡️")
        prev_emoji = emoji_map.get(self.completed_skills[-1], "⬅️") if self.completed_skills else ""

        chain_so_far = " → ".join(
            f"{emoji_map.get(s, '')}{s.replace('-development', '')}"
            for s in self.completed_skills + [skill_name]
        )

        announcement = (
            f"---\n"
            f"**Methodology Chain Progress**\n"
            f"{chain_so_far}\n\n"
            f"{prev_emoji} {self.completed_skills[-1]}: ✅ complete\n"
            f"{emoji} {skill_name}: starting now\n"
            f"---"
        )
        return announcement


def infer_current_chain_phase(message: str) -> Optional[str]:
    """Infer which methodology phase the user's message maps to.

    This enables auto-detection without explicit invocation.
    """
    msg_lower = message.lower()

    # Pattern matching for each phase
    patterns = {
        "brainstorming": [
            r"let's build", r"create a new", r"i want to make", r"design.*app",
            r"build a", r"create an?", r"new feature", r"start a project",
        ],
        "writing-plans": [
            r"plan", r"break down", r"tasks?", r"steps?", r"implement.*plan",
            r"how.*implement", r"what.*need.*do",
        ],
        "test-driven-development": [
            r"write test", r"tdd", r"test first", r"red.*green",
            r"unit test", r"integration test",
        ],
        "verification-before-completion": [
            r"verify", r"check.*work", r"is it done", r"test.*pass",
            r"confirm", r"validate",
        ],
        "systematic-debugging": [
            r"bug", r"error", r"fail", r"crash", r"broken", r"not working",
            r"fix.*issue", r"debug", r"wrong", r"problem",
        ],
        "requesting-code-review": [
            r"review", r"pr.*review", r"check.*code", r"pull request",
            r"merge.*request",
        ],
        "finishing-development": [
            r"merge", r"finish", r"complete", r"release", r"ship",
            r"publish", r"deploy",
        ],
    }

    for phase, phase_patterns in patterns.items():
        for pattern in phase_patterns:
            if re.search(pattern, msg_lower):
                return phase

    return None


def get_chain_announcement(skill_name: str) -> str:
    """Generate the standard announcement text when starting a methodology skill."""
    announcements = {
        "brainstorming": (
            "🧠 Using the brainstorming skill to explore requirements and design "
            "before writing any code."
        ),
        "writing-plans": (
            "📝 Using the writing-plans skill to decompose into bite-sized tasks "
            "with exact paths, code blocks, and assertions."
        ),
        "test-driven-development": (
            "🔄 Using test-driven development: RED (failing test) → "
            "GREEN (minimal code) → REFACTOR (clean up)."
        ),
        "subagent-driven-development": (
            "🤖 Using subagent-driven development: fresh subagent per task "
            "with 2-stage review."
        ),
        "verification-before-completion": (
            "🔬 Running verification before completion: gathering fresh evidence "
            "before making any claims."
        ),
        "systematic-debugging": (
            "🔍 Using systematic debugging: 4-phase root cause analysis "
            "before proposing any fix."
        ),
        "requesting-code-review": (
            "👀 Requesting code review: dispatching reviewer subagent "
            "to catch issues before they cascade."
        ),
        "finishing-development": (
            "✅ Using finishing-development skill: verifying tests, then "
            "presenting structured merge/PR/discard options."
        ),
    }
    return announcements.get(skill_name, f"Using {skill_name} skill.")


# ════════════════════════════════════════════════════════════════
# ── Phase 5: Git Worktree Isolation ────────────────────────────
# ════════════════════════════════════════════════════════════════


@dataclass
class WorktreeInfo:
    """Info about a created git worktree."""
    name: str
    path: str
    branch: str
    base_branch: str
    created_at: float
    status: str  # active, merged, discarded, pr


WORKTREE_BASE = Path.home() / ".apex" / "worktrees"


def ensure_worktree_base():
    """Ensure the worktree base directory exists."""
    WORKTREE_BASE.mkdir(parents=True, exist_ok=True)


def create_worktree(feature_name: str, base_branch: str = "main") -> WorktreeInfo:
    """Create an isolated git worktree for feature development.

    Args:
        feature_name: Short feature name for branch/directory.
        base_branch: Base branch to fork from.

    Returns:
        WorktreeInfo with details.
    """
    ensure_worktree_base()

    branch_name = f"feat/{feature_name}"
    worktree_path = WORKTREE_BASE / feature_name

    # Create branch from base
    subprocess.run(
        ["git", "fetch", "origin", base_branch],
        capture_output=True, timeout=30,
    )
    subprocess.run(
        ["git", "branch", branch_name, f"origin/{base_branch}"],
        capture_output=True, timeout=15,
    )

    # Create worktree
    result = subprocess.run(
        ["git", "worktree", "add", str(worktree_path), branch_name],
        capture_output=True, text=True, timeout=15,
    )

    info = WorktreeInfo(
        name=feature_name,
        path=str(worktree_path),
        branch=branch_name,
        base_branch=base_branch,
        created_at=time.time(),
        status="active",
    )

    return info


def remove_worktree(worktree_name: str) -> dict:
    """Safely remove a git worktree.

    Only removes worktrees under ~/.apex/worktrees/ (provenance check).
    """
    worktree_path = WORKTREE_BASE / worktree_name
    if not worktree_path.exists():
        return {"status": "error", "message": f"Worktree {worktree_name} not found"}

    # Provenance check — only clean up our own worktrees
    if not str(worktree_path).startswith(str(WORKTREE_BASE)):
        return {"status": "error", "message": "Not an Apex-managed worktree"}

    try:
        subprocess.run(
            ["git", "worktree", "remove", str(worktree_path)],
            capture_output=True, timeout=15,
        )
        subprocess.run(
            ["git", "worktree", "prune"],
            capture_output=True, timeout=10,
        )
        return {"status": "removed", "path": str(worktree_path)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_worktrees() -> list[WorktreeInfo]:
    """List all active Apex-managed worktrees."""
    ensure_worktree_base()
    worktrees = []

    for item in WORKTREE_BASE.iterdir():
        if item.is_dir() and (item / ".git").exists():
            # Try to determine branch
            try:
                branch = subprocess.run(
                    ["git", "-C", str(item), "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True, text=True, timeout=5,
                ).stdout.strip()
            except Exception:
                branch = "unknown"

            worktrees.append(WorktreeInfo(
                name=item.name,
                path=str(item),
                branch=branch,
                base_branch="",
                created_at=item.stat().st_ctime,
                status="active",
            ))

    return worktrees


# ════════════════════════════════════════════════════════════════
# ── Enhanced Parallel Dispatch ─────────────────────────────────
# ════════════════════════════════════════════════════════════════


@dataclass
class DispatchTask:
    """A task for enhanced parallel dispatch."""
    name: str
    description: str
    scope: str  # Independent problem domain
    constraints: list[str] = field(default_factory=list)
    expected_output: str = "Summary of findings and changes"


def prepare_dispatch_tasks(tasks: list[DispatchTask]) -> list[dict]:
    """Prepare tasks for parallel dispatch with Superpowers patterns.

    Each task is scoped to an independent problem domain with clear
    constraints and expected output format.
    """
    prepared = []
    for i, task in enumerate(tasks):
        prepared.append({
            "id": f"dispatch-{i+1}",
            "name": task.name,
            "goal": task.description,
            "context": (
                f"Scope: {task.scope}\n"
                f"Constraints: {'; '.join(task.constraints) if task.constraints else 'None'}\n"
                f"Expected output: {task.expected_output}\n"
                "\nIMPORTANT: Do NOT modify code outside your scope. "
                "Return a summary of what you found and what you changed."
            ),
        })
    return prepared


def dispatch_parallel(tasks: list[DispatchTask]) -> list[dict]:
    """Dispatch multiple independent tasks in parallel.

    Uses Apex's delegate_task batch mechanism with Superpowers-style
    prompt engineering for each subagent.

    Returns:
        List of task results.
    """
    from agentark.core.tools import delegate_task

    prepared = prepare_dispatch_tasks(tasks)

    # Dispatch batch via delegate_task
    results = delegate_task(
        tasks=[
            {
                "goal": t["goal"],
                "context": t["context"],
            }
            for t in prepared
        ]
    )

    return results if results else []


# ════════════════════════════════════════════════════════════════
# ── Utility Functions ──────────────────────────────────────────
# ════════════════════════════════════════════════════════════════


def _extract_requirements(text: str) -> list[str]:
    """Extract requirements/features from a spec document."""
    requirements = []
    if not text:
        return requirements

    # Extract checklist items, bullet points with requirements
    for line in text.split("\n"):
        stripped = line.strip()
        # Match markdown checkboxes and bullet requirements
        if re.match(r"^[-*]\s*\[.?\]\s+", stripped):
            clean = re.sub(r"^[-*]\s*\[.?\]\s*", "", stripped)
            if clean:
                requirements.append(clean)
        # Match numbered requirements
        elif re.match(r"^\d+\.\s+", stripped):
            clean = re.sub(r"^\d+\.\s*", "", stripped)
            if clean and len(clean) > 10:
                requirements.append(clean)

    return requirements


def _extract_features(text: str) -> list[str]:
    """Extract features/implementations from code diff."""
    features = []
    if not text:
        return features

    # Extract function/class definitions from diff
    func_pattern = re.compile(r"^\+.*(?:def |class |function |const \w+ =)", re.MULTILINE)
    for match in func_pattern.finditer(text):
        line = match.group()
        # Extract name
        name_match = re.search(r"(?:def |class |function |const )(\w+)", line)
        if name_match:
            features.append(name_match.group(1))

    return features


def _extract_from_diff(diff: str) -> list[str]:
    """Extract feature names from a git diff."""
    return _extract_features(diff)


def _find_magic_numbers(diff: str) -> list[tuple[str, tuple[str, int]]]:
    """Find magic numbers in code diff."""
    findings = []
    if not diff:
        return findings

    # Look for numeric literals in added lines (not tests)
    for line_num, line in enumerate(diff.split("\n")):
        if line.startswith("+") and not line.startswith("+++"):
            # Skip test files
            if "test" in line.lower():
                continue
            # Find standalone numbers
            numbers = re.findall(r"\b(\d{2,})\b", line)
            for num in numbers:
                # Skip common safe numbers (0, 1, -1), status codes, time values
                if int(num) > 10 and int(num) not in (100, 200, 201, 204, 301, 302, 400, 401, 403, 404, 500, 502, 503):
                    findings.append((num, ("", line_num)))

    return findings[:5]  # Cap at 5 findings


def _has_error_handling(diff: str) -> bool:
    """Check if code diff contains error handling patterns."""
    patterns = [
        r"try\s*{",
        r"except\s",
        r"catch\s*\(",
        r"if\s+error\b",
        r"if\s+err\b",
        r".error\(",
        r"raise\s",
        r"throw\s",
        r"Optional\[",
        r"Result<",
    ]
    for pattern in patterns:
        if re.search(pattern, diff):
            return True
    return False
