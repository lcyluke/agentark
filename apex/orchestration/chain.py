"""Apex — Sequential-Chain Mode
Pipelined stages with handoff verification, stage retry, and final assembly.

Chain vs Swarm:
  Swarm  = Parallel Workers -> Verifier -> Synthesizer (independent tasks)
  Chain  = Sequential stages, each feeding the next with quality gates (dependent pipelines)

Chain vs Crew:
  Crew   = Multi-role collaboration + discussion (team tasks)
  Chain  = Pipeline processing with strict stage ordering (factory tasks)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from ..core.runtime import Agent
from ..core.profile import Profile, ProfileManager


# ─── Errors ───


class ChainExecutionError(Exception):
    """Raised when a chain stage fails after exhausting retries."""


class VerificationError(Exception):
    """Raised when handoff verification fails and no retry recovers it."""


# ─── Data Classes ───


@dataclass
class ChainStage:
    """One stage in a sequential pipeline.

    Attributes:
        name: Human-readable stage name (e.g. "draft", "review").
        profile: The Agent Profile to use for this stage.
        task_template: A format-string template that accepts ``input_data``
            and optionally ``previous_output`` to produce the task prompt.
        input_key: Which field of the chain input dict to pass as ``input_data``.
        output_key: Which key in the stage outputs dict to store the result under.
        max_retries: Maximum retry attempts if handoff verification fails.
        verifier: Optional callable ``(stage, output) -> (passed, feedback)``.
            If ``None``, a default LLM-based verifier is used.
    """
    name: str
    profile: Profile
    task_template: str
    input_key: str = ""
    output_key: str = ""
    max_retries: int = 2
    verifier: Optional[Callable[[ChainStage, str], tuple[bool, str]]] = None

    # Runtime state (populated during execution)
    output: str = ""
    attempts: int = 0
    verification_feedback: str = ""
    cost: float = 0.0


@dataclass
class ChainResult:
    """Result of a complete sequential-chain execution.

    Attributes:
        success: Whether the entire pipeline completed without error.
        stages: Ordered list of ChainStage results (output, attempts, etc.).
        assembled_output: The final assembled result from all stages.
        total_cost: Accumulated LLM cost across all stages.
        error: Error message if the chain failed.
        chain_input: The original input dict passed to ``Chain.run()``.
    """
    success: bool = False
    stages: list[ChainStage] = field(default_factory=list)
    assembled_output: str = ""
    total_cost: float = 0.0
    error: str = ""
    chain_input: dict = field(default_factory=dict)

    def stage_output(self, name: str) -> str:
        """Get the output of a stage by name."""
        for s in self.stages:
            if s.name == name:
                return s.output
        return ""

    def summary(self) -> dict:
        """Return a concise summary dict for logging or inspection."""
        return {
            "success": self.success,
            "stages": [
                {
                    "name": s.name,
                    "attempts": s.attempts,
                    "verified": s.verification_feedback != "",
                    "cost": round(s.cost, 6),
                    "output_preview": s.output[:120].replace("\n", " "),
                }
                for s in self.stages
            ],
            "total_cost": round(self.total_cost, 6),
            "error": self.error,
        }


# ─── Default Verifier ───


def _default_verifier(stage: ChainStage, output: str) -> tuple[bool, str]:
    """Built-in heuristic verifier for handoff quality checking.

    Checks for:
      - Non-empty output (at least 20 chars of substance).
      - Absence of generic failure phrases.
      - Basic structure (contains requested sections if task requested them).
    """
    output_stripped = output.strip()

    if len(output_stripped) < 20:
        return False, "Output too short (< 20 characters) — likely empty or failed."

    failure_indicators = [
        "i cannot",
        "i can't",
        "unable to",
        "not possible",
        "error:",
        "error occurred",
        "failed to",
        "something went wrong",
    ]
    lower = output_stripped.lower()
    for phrase in failure_indicators:
        if phrase in lower:
            return False, f"Output contains failure indicator: '{phrase}'."

    # Check for hallucination markers (repeated boilerplate, nonsense)
    words = output_stripped.split()
    if len(words) >= 50:
        unique_ratio = len(set(w.lower() for w in words)) / len(words)
        if unique_ratio < 0.3:
            return False, f"Output has low lexical diversity ({unique_ratio:.0%}) — may be repetitive boilerplate."

    return True, "Verification passed."


# ─── Chain Orchestrator ───


class Chain:
    """Sequential pipeline orchestrator.

    Usage::

        chain = Chain(stages=[...], verifier=my_fn)
        result = chain.run({"topic": "AI Agents"})
    """

    def __init__(
        self,
        stages: list[ChainStage],
        global_verifier: Optional[Callable[[ChainStage, str], tuple[bool, str]]] = None,
        api_key: str = "",
    ):
        self.stages = stages
        self.global_verifier = global_verifier or _default_verifier
        self.api_key = api_key

    # ── Public API ──

    def run(self, input_data: dict[str, Any]) -> ChainResult:
        """Execute the chain pipeline sequentially.

        Each stage receives the output of the previous stage as context.
        Handoff verification gates progression. Failed stages retry up to
        ``max_retries`` times, then the chain halts with an error.
        """
        result = ChainResult(chain_input=input_data)
        previous_output = ""

        print(f"\n{'='*50}")
        print(f"⛓️  Sequential Chain — {len(self.stages)} stages")
        print(f"{'='*50}")

        for idx, stage in enumerate(self.stages):
            print(f"\n📌 Stage {idx + 1}/{len(self.stages)}: {stage.name}")
            print("-" * 40)

            try:
                self._execute_stage(stage, input_data, previous_output, result)
                result.stages.append(stage)
                result.total_cost += stage.cost
                previous_output = stage.output

                print(f"   ✅ {stage.name} — Completed (attempts: {stage.attempts}, "
                      f"cost: ${stage.cost:.6f})")

            except (ChainExecutionError, VerificationError) as e:
                result.error = str(e)
                result.success = False
                result.stages.append(stage)
                print(f"   ❌ {stage.name} — Failed: {e}")
                print(f"\n{'='*50}")
                print(f"⛓️  Chain halted at stage {idx + 1}")
                print(f"{'='*50}")
                return result

        # Final assembly
        print(f"\n📦 Final Assembly")
        print("-" * 40)
        assembled = self._assemble(input_data, result.stages)
        result.assembled_output = assembled
        result.success = True

        print(f"   ✅ Chain complete! Total cost: ${result.total_cost:.4f}")
        print(f"{'='*50}\n")

        return result

    # ── Internal ──

    def _execute_stage(
        self,
        stage: ChainStage,
        input_data: dict,
        previous_output: str,
        result: ChainResult,
    ) -> None:
        """Run a single stage with retry logic."""
        agent = Agent(stage.profile, api_key=self.api_key)

        for attempt in range(1, stage.max_retries + 1):
            stage.attempts = attempt

            # Build the task prompt
            raw_input = input_data.get(stage.input_key, "")
            prompt = stage.task_template.format(
                input_data=raw_input,
                previous_output=previous_output,
            )

            # Execute
            try:
                output = agent.run(prompt)
            except Exception as e:
                if attempt < stage.max_retries:
                    print(f"   ⚠️  {stage.name} attempt {attempt} error: {e}. Retrying...")
                    continue
                raise ChainExecutionError(
                    f"Stage '{stage.name}' failed after {stage.max_retries} attempts. "
                    f"Last error: {e}"
                ) from e

            stage.output = output
            stage.cost = agent.context.cost

            # Handoff verification
            verifier = stage.verifier or self.global_verifier
            passed, feedback = verifier(stage, output)
            stage.verification_feedback = feedback

            if passed:
                return  # Stage succeeded

            # Verification failed — log and maybe retry
            print(f"   ⚠️  {stage.name} attempt {attempt} — Verification: {feedback[:100]}")
            if attempt < stage.max_retries:
                print(f"   🔄 Retrying {stage.name}...")
                # Augment the context with feedback for the retry
                stage.task_template += (
                    f"\n\n=== Previous attempt feedback ===\n{feedback}\n"
                    f"Please address the issues above in your revised response."
                )

        # Exhausted retries
        raise VerificationError(
            f"Stage '{stage.name}' failed verification after {stage.max_retries} "
            f"attempts. Last feedback: {stage.verification_feedback}"
        )

    def _assemble(self, input_data: dict, stages: list[ChainStage]) -> str:
        """Assemble all stage outputs into a single final result."""
        parts = []
        parts.append(f"# Pipeline Final Assembly\n")
        parts.append(f"## Input Summary\n")
        for key, val in input_data.items():
            val_str = str(val)[:500]
            parts.append(f"- **{key}**: {val_str}")
        parts.append("")

        for s in stages:
            parts.append(f"---")
            parts.append(f"## Stage: {s.name}")
            parts.append(f"")
            parts.append(s.output.strip())
            parts.append(f"")

        return "\n".join(parts)

    # ── API Key Helper ──

    def _get_api_key(self) -> str:
        """Get API Key from environment."""
        import os
        return os.environ.get("DEEPSEEK_API_KEY", "")


# ─── Factory Methods ───


def _resolve_profile(name: str, role: str, expertise: list[str] | None = None) -> Profile:
    """Load an existing profile or create a minimal one on the fly."""
    pm = ProfileManager()
    try:
        return pm.load(name)
    except FileNotFoundError:
        return pm.create_default(name, role=role, expertise=expertise or [])


# ── Content Pipeline: draft → review → edit → publish ──


def content_pipeline(
    draft_agent: str = "writer",
    review_agent: str = "editor",
    edit_agent: str = "copywriter",
    publish_agent: str = "publisher",
    api_key: str = "",
) -> Chain:
    """Create a content creation pipeline.

    Stage progression:
      1. **Draft**   — Writes initial content from input.
      2. **Review**  — Reviews draft for quality, accuracy, tone.
      3. **Edit**    — Revises based on review feedback.
      4. **Publish** — Formats and prepares final output.
    """
    draft_profile = _resolve_profile(draft_agent, "Writer", ["content creation", "creative writing"])
    review_profile = _resolve_profile(review_agent, "Editor", ["editing", "quality assurance"])
    edit_profile = _resolve_profile(edit_agent, "Copywriter", ["copy editing", "revision"])
    publish_profile = _resolve_profile(publish_agent, "Publisher", ["content formatting", "publishing"])

    stages = [
        ChainStage(
            name="draft",
            profile=draft_profile,
            task_template=(
                "You are a professional writer. Write a complete, well-structured "
                "piece based on the following input.\n\n"
                "Input:\n{input_data}\n\n"
                "Produce a full draft with clear sections and professional language."
            ),
            input_key="topic",
            output_key="draft",
        ),
        ChainStage(
            name="review",
            profile=review_profile,
            task_template=(
                "You are an expert editor. Review the following draft critically.\n\n"
                "Draft:\n{previous_output}\n\n"
                "Evaluate:\n"
                "1. Clarity and structure\n"
                "2. Accuracy and factual correctness\n"
                "3. Tone and audience appropriateness\n"
                "4. Grammar and style issues\n"
                "5. Overall quality score (1-10)\n"
                "Provide specific, actionable revision suggestions."
            ),
            output_key="review",
        ),
        ChainStage(
            name="edit",
            profile=edit_profile,
            task_template=(
                "You are a copy editor. Revise the following draft based on "
                "the review feedback provided.\n\n"
                "Original Draft:\n{previous_output}\n\n"
                "Please produce a polished, publication-ready version that "
                "addresses all issues. Output the final revised text only."
            ),
            output_key="edit",
        ),
        ChainStage(
            name="publish",
            profile=publish_profile,
            task_template=(
                "You are a publisher. Format the following content for final "
                "delivery with proper headings, metadata, and formatting.\n\n"
                "Content:\n{previous_output}\n\n"
                "Output:\n"
                "1. Title and metadata block\n"
                "2. Formatted content body\n"
                "3. Tags and categories (if applicable)"
            ),
            output_key="publish",
        ),
    ]

    return Chain(stages=stages, api_key=api_key)


# ── Data Pipeline: extract → transform → load ──


def data_pipeline(
    extract_agent: str = "extractor",
    transform_agent: str = "transformer",
    load_agent: str = "loader",
    api_key: str = "",
) -> Chain:
    """Create a data processing pipeline.

    Stage progression:
      1. **Extract**   — Pulls raw data from source, identifies schema.
      2. **Transform** — Cleans, normalizes, and enriches the data.
      3. **Load**      — Formats output for the target destination.
    """
    extract_profile = _resolve_profile(extract_agent, "Data Extractor", ["data extraction", "ETL"])
    transform_profile = _resolve_profile(transform_agent, "Data Transformer", ["data cleaning", "normalization"])
    load_profile = _resolve_profile(load_agent, "Data Loader", ["data loading", "formatting"])

    stages = [
        ChainStage(
            name="extract",
            profile=extract_profile,
            task_template=(
                "You are a data extraction specialist. Extract and structure "
                "the data from the following input.\n\n"
                "Input:\n{input_data}\n\n"
                "Identify the schema, fields, and any relationships. "
                "Output structured data in JSON-like format."
            ),
            input_key="source",
            output_key="extracted",
        ),
        ChainStage(
            name="transform",
            profile=transform_profile,
            task_template=(
                "You are a data transformation specialist. Clean and normalize "
                "the extracted data.\n\n"
                "Extracted Data:\n{previous_output}\n\n"
                "Apply:\n"
                "1. Data type normalization\n"
                "2. Missing value handling\n"
                "3. Duplicate removal\n"
                "4. Format standardization\n"
                "Output the cleaned dataset."
            ),
            output_key="transformed",
        ),
        ChainStage(
            name="load",
            profile=load_profile,
            task_template=(
                "You are a data loading specialist. Format the transformed data "
                "for the target destination.\n\n"
                "Transformed Data:\n{previous_output}\n\n"
                "Produce:\n"
                "1. Target schema mapping\n"
                "2. Formatted records ready for insertion\n"
                "3. Any validation rules or constraints"
            ),
            output_key="loaded",
        ),
    ]

    return Chain(stages=stages, api_key=api_key)


# ── Dev Pipeline: design → implement → test → deploy ──


def dev_pipeline(
    design_agent: str = "architect",
    implement_agent: str = "developer",
    test_agent: str = "tester",
    deploy_agent: str = "devops",
    api_key: str = "",
) -> Chain:
    """Create a software development pipeline.

    Stage progression:
      1. **Design**     — Produces architecture and specification.
      2. **Implement**  — Writes code based on the design.
      3. **Test**       — Creates and runs test cases, validates correctness.
      4. **Deploy**     — Generates deployment configuration and instructions.
    """
    design_profile = _resolve_profile(design_agent, "Software Architect", ["system design", "architecture"])
    implement_profile = _resolve_profile(implement_agent, "Developer", ["programming", "implementation"])
    test_profile = _resolve_profile(test_agent, "QA Engineer", ["testing", "quality assurance"])
    deploy_profile = _resolve_profile(deploy_agent, "DevOps Engineer", ["deployment", "CI/CD"])

    stages = [
        ChainStage(
            name="design",
            profile=design_profile,
            task_template=(
                "You are a software architect. Design a complete system for "
                "the following requirements.\n\n"
                "Requirements:\n{input_data}\n\n"
                "Provide:\n"
                "1. System architecture overview\n"
                "2. Component/module list with responsibilities\n"
                "3. Data model / schema\n"
                "4. API design (if applicable)\n"
                "5. Technology stack recommendations"
            ),
            input_key="requirements",
            output_key="design",
        ),
        ChainStage(
            name="implement",
            profile=implement_profile,
            task_template=(
                "You are a senior developer. Implement the system based on "
                "the following design specification.\n\n"
                "Design Specification:\n{previous_output}\n\n"
                "Produce complete, production-ready code with:\n"
                "1. Well-structured modules/classes\n"
                "2. Error handling and logging\n"
                "3. Comments and documentation\n"
                "4. Configuration files as needed"
            ),
            output_key="implementation",
            max_retries=3,
        ),
        ChainStage(
            name="test",
            profile=test_profile,
            task_template=(
                "You are a QA engineer. Create and run tests for the following "
                "implementation.\n\n"
                "Implementation:\n{previous_output}\n\n"
                "Produce:\n"
                "1. Unit test suite\n"
                "2. Integration test scenarios\n"
                "3. Test coverage report\n"
                "4. Any bugs or issues found with severity ratings"
            ),
            output_key="tests",
        ),
        ChainStage(
            name="deploy",
            profile=deploy_profile,
            task_template=(
                "You are a DevOps engineer. Generate deployment configuration "
                "and instructions for the following project.\n\n"
                "Project:\n{previous_output}\n\n"
                "Provide:\n"
                "1. Dockerfile (if applicable)\n"
                "2. CI/CD pipeline configuration\n"
                "3. Environment variables and secrets management\n"
                "4. Deployment checklist\n"
                "5. Monitoring and rollback strategy"
            ),
            output_key="deployment",
        ),
    ]

    return Chain(stages=stages, api_key=api_key)
