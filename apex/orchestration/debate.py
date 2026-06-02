"""Multi-perspective analysis and refinement through structured debate."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core.runtime import Agent
from ..core.profile import Profile, ProfileManager


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class DebatePosition:
    """A single agent's stance throughout the debate lifecycle."""

    name: str
    stance: str
    expertise: str = ""
    opening_statement: str = ""
    critiques_received: list[str] = field(default_factory=list)
    rebuttal: str = ""
    final_position: str = ""

    @classmethod
    def from_profile(cls, profile: Profile, stance: str) -> "DebatePosition":
        """Build a DebatePosition from a Profile and assigned stance."""
        expertise = ", ".join(profile.soul.expertise) if profile.soul.expertise else profile.soul.role
        return cls(
            name=profile.name,
            stance=stance,
            expertise=expertise,
        )


@dataclass
class DebateResult:
    """Outcome of a full debate run."""

    success: bool = False
    positions: list[DebatePosition] = field(default_factory=list)
    moderator_notes: str = ""
    synthesis: str = ""
    error: str = ""


# ---------------------------------------------------------------------------
# Debate orchestrator
# ---------------------------------------------------------------------------


class Debate:
    """Orchestrate a structured multi-agent debate.

    Args:
        topic: The question or proposition under debate.
        agents: List of Agent instances (one per position).
        stances: List of stance labels (e.g. ``["pro", "con"]`` or
                 ``["optimist", "pessimist", "neutral"]``).
        moderator: Optional Agent that runs the synthesis phase.
                   If ``None`` the first agent is used as moderator
                   after submitting its own position.
        max_parallel: Maximum concurrent agent calls.
    """

    def __init__(
        self,
        topic: str,
        agents: list[Agent],
        stances: list[str],
        moderator: Optional[Agent] = None,
        max_parallel: int = 3,
    ) -> None:
        if len(agents) != len(stances):
            raise ValueError(
                f"Number of agents ({len(agents)}) must match "
                f"number of stances ({len(stances)})"
            )
        if len(agents) < 2:
            raise ValueError("Debate requires at least 2 agents")

        self.topic = topic
        self.agents = agents
        self.stances = stances
        self.moderator = moderator or agents[0]
        self.max_parallel = max_parallel

        # Populated during run()
        self.positions: list[DebatePosition] = [
            DebatePosition.from_profile(a.profile, s)
            for a, s in zip(agents, stances)
        ]

    # -- Public API ---------------------------------------------------------

    def run(self) -> DebateResult:
        """Execute the full debate pipeline."""
        result = DebateResult()

        try:
            self._phase_header(1, "Position Assignment")
            self._assign_positions()

            self._phase_header(2, "Opening Statements")
            self._opening_statements()

            self._phase_header(3, "Cross-Examination")
            self._cross_examination(rounds=2)

            self._phase_header(4, "Rebuttal")
            self._rebuttal()

            self._phase_header(5, "Synthesis")
            result.synthesis, result.moderator_notes = self._synthesis()

            result.success = True
        except Exception as exc:
            result.error = str(exc)

        result.positions = self.positions
        return result

    # -- Phase 1: Position Assignment ---------------------------------------

    def _assign_positions(self) -> None:
        """Assign each agent their stance — already done in __init__."""
        for pos in self.positions:
            print(f"  {pos.name:>20s}  →  {pos.stance}")
        print()

    # -- Phase 2: Opening Statements (parallel) -----------------------------

    def _opening_statements(self) -> None:
        """Each agent composes an opening statement in parallel."""

        def _open(position: DebatePosition, agent: Agent) -> DebatePosition:
            prompt = (
                f"You are arguing the **{position.stance}** position on the topic:\n"
                f"\"{self.topic}\"\n\n"
                f"Your expertise: {position.expertise}\n\n"
                f"Write a concise, evidence-based opening statement (2-3 paragraphs) "
                f"that clearly states your position and supports it with reasoning."
            )
            statement = agent.run(prompt)
            position.opening_statement = statement
            return position

        with ThreadPoolExecutor(max_workers=self.max_parallel) as pool:
            futures = {
                pool.submit(_open, p, a): p.name
                for p, a in zip(self.positions, self.agents)
            }
            for future in as_completed(futures):
                name = futures[future]
                future.result()  # propagate exceptions
                self._print_opening(name)

    # -- Phase 3: Cross-Examination ----------------------------------------

    def _cross_examination(self, rounds: int = 2) -> None:
        """Round-robin critique of each position."""
        n = len(self.positions)

        for r in range(1, rounds + 1):
            print(f"\n  --- Cross-Examination Round {r} ---")
            for i in range(n):
                critic = self.agents[i]
                critic_pos = self.positions[i]

                # Criticise the next position in the ring
                target_idx = (i + 1) % n
                target_agent = self.agents[target_idx]
                target_pos = self.positions[target_idx]

                critique = self._single_critique(
                    critic=critic,
                    critic_stance=critic_pos.stance,
                    target_agent=target_agent,
                    target_position=target_pos,
                )
                target_pos.critiques_received.append(
                    f"[Round {r} from {critic_pos.name} ({critic_pos.stance})]: {critique}"
                )

    def _single_critique(
        self,
        critic: Agent,
        critic_stance: str,
        target_agent: Agent,
        target_position: DebatePosition,
    ) -> str:
        """One agent critiques another's position."""
        prompt = (
            f"You are {critic.profile.name} arguing the **{critic_stance}** position.\n\n"
            f"Topic: \"{self.topic}\"\n\n"
            f"Your opponent {target_agent.profile.name} (stance: {target_position.stance}) "
            f"presented the following opening statement:\n\n"
            f"---\n{target_position.opening_statement}\n---\n\n"
            f"Provide a sharp, constructive critique of their argument. "
            f"Identify assumptions, logical gaps, missing evidence, or "
            f"counter-arguments. Be specific and direct."
        )
        critique = critic.run(prompt)
        print(f"  {critic.profile.name} → {target_agent.profile.name}")
        return critique.strip()

    # -- Phase 4: Rebuttal --------------------------------------------------

    def _rebuttal(self) -> None:
        """Each agent adjusts its position after receiving critiques."""
        for pos, agent in zip(self.positions, self.agents):
            critiques_text = "\n\n".join(pos.critiques_received)
            prompt = (
                f"You are {pos.name} arguing the **{pos.stance}** position.\n\n"
                f"Topic: \"{self.topic}\"\n\n"
                f"Your opening statement:\n---\n{pos.opening_statement}\n---\n\n"
                f"Critiques you received:\n---\n{critiques_text}\n---\n\n"
                f"Write a rebuttal that addresses the strongest critiques "
                f"and refines your position. Acknowledge valid points, "
                f"defend against weak objections, and produce an improved "
                f"final statement of your position."
            )
            pos.rebuttal = agent.run(prompt)
            pos.final_position = pos.rebuttal  # final refined stance
            print(f"  {pos.name:>20s}  rebuttal submitted")

    # -- Phase 5: Synthesis -------------------------------------------------

    def _synthesis(self) -> tuple[str, str]:
        """The moderator synthesises a converged answer from all positions."""
        positions_block = ""
        for pos in self.positions:
            positions_block += (
                f"\n### {pos.name} — {pos.stance}\n"
                f"Expertise: {pos.expertise}\n"
                f"Opening: {pos.opening_statement[:300]}...\n"
                f"Rebuttal / Final: {pos.final_position[:300]}...\n"
            )

        prompt = (
            f"You are the moderator of a structured debate on the topic:\n"
            f"\"{self.topic}\"\n\n"
            f"Below are the final positions from each participant:\n"
            f"{positions_block}\n\n"
            f"Your task:\n"
            f"1. Synthesise a balanced, converged answer that incorporates "
            f"the strongest evidence from all sides.\n"
            f"2. Note where consensus exists and where disagreements remain.\n"
            f"3. Provide a final recommended conclusion.\n\n"
            f"Format your response in two sections:\n"
            f"SYNTHESIS: <the converged answer>\n"
            f"MODERATOR_NOTES: <your observations on the debate dynamics>"
        )

        raw = self.moderator.run(prompt)

        synthesis, _, notes = raw.partition("MODERATOR_NOTES:")
        synthesis = synthesis.replace("SYNTHESIS:", "").strip()
        notes = notes.strip() or "No additional moderator notes."

        return synthesis, notes

    # -- Helpers ------------------------------------------------------------

    def _phase_header(self, phase: int, title: str) -> None:
        print(f"\n{'='*60}")
        print(f"  Phase {phase}: {title}")
        print(f"{'='*60}")

    def _print_opening(self, name: str) -> None:
        """Brief status line after an opening completes."""
        print(f"  {name:>20s}  opening statement ready")


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------


def create_debate(
    topic: str,
    stance_defs: list[tuple[str, str, Profile]],
    moderator_profile: Optional[Profile] = None,
    max_parallel: int = 3,
) -> Debate:
    """Quick factory to build a Debate from profile names and stances.

    Args:
        topic: Debate proposition.
        stance_defs: List of ``(profile_name, stance_label, profile)`` tuples.
        moderator_profile: Optional profile for the moderator agent.
        max_parallel: Max concurrent agent calls.

    Returns:
        A configured ``Debate`` instance ready to run.
    """
    agents = [Agent(profile=p) for _, _, p in stance_defs]
    stances = [s for _, s, _ in stance_defs]
    moderator = Agent(profile=moderator_profile) if moderator_profile else None
    return Debate(
        topic=topic,
        agents=agents,
        stances=stances,
        moderator=moderator,
        max_parallel=max_parallel,
    )
