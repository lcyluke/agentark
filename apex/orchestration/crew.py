"""Apex — Crew Mode (Team Mode)
Role-based real-time collaboration + Dynamic team design engine + Zero-click team assembly.

Crew vs Swarm:
  Swarm = Parallel independent Workers + Verifier + Synthesizer (suitable for decomposable independent tasks)
  Crew  = Real-time chat collaboration between roles (suitable for tasks needing discussion and feedback)
"""
from __future__ import annotations

import json
import click
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text

from apex.core.profile import Profile, ProfileManager
from apex.core.runtime import Agent
from apex.core.templates import TEMPLATES, get_template, list_templates
from apex.providers import registry as provider_registry


console = Console()


@dataclass
class CrewMember:
    """A member of the Crew"""
    name: str
    profile: Profile
    role_description: str
    output: str = ""


@dataclass
class CrewResult:
    """Crew execution result"""
    goal: str
    members: list[CrewMember] = field(default_factory=list)
    discussion_log: list[dict] = field(default_factory=list)
    final_output: str = ""
    total_cost: float = 0.0


class DynamicTeamDesigner:
    """Dynamic team design engine — Zero-click team assembly core"""

    def __init__(self):
        pass

    def design_team(self, goal: str) -> dict:
        """Automatically design optimal team based on task"""
        goal_lower = goal.lower()

        # Keyword matching rules
        team_designs = {
            "web": {
                "goal": f"Build Web Application: {goal}",
                "members": [
                    ("pm", "Product Manager", "Requirements analysis and PRD"),
                    ("frontend", "Frontend Developer", "UI components and page implementation"),
                    ("backend", "Backend Architect", "API and database design"),
                ],
                "verifier": ("devops", "Architecture Review"),
            },
            "app": {
                "goal": f"Develop Application: {goal}",
                "members": [
                    ("pm", "Product Manager", "Define MVP scope"),
                    ("frontend", "Frontend Developer", "Interface development"),
                    ("backend", "Backend Architect", "API development"),
                ],
                "verifier": ("devops", "Deployment Plan Review"),
            },
            "deploy": {
                "goal": f"Deploy to Production: {goal}",
                "members": [
                    ("devops", "DevOps Engineer", "Deployment plan and CI/CD"),
                    ("backend", "Backend Architect", "Environment configuration confirmation"),
                ],
                "verifier": ("pm", "Verification"),
            },
            "content": {
                "goal": f"Content Creation: {goal}",
                "members": [
                    ("content", "Content Operations Specialist", "Copywriting"),
                    ("pm", "Product Manager", "Content strategy alignment"),
                ],
                "verifier": None,
            },
            "api": {
                "goal": f"API Development: {goal}",
                "members": [
                    ("backend", "Backend Architect", "API design and implementation"),
                    ("devops", "DevOps Engineer", "Deployment and monitoring"),
                ],
                "verifier": ("pm", "API Documentation Review"),
            },
            "data": {
                "goal": f"Data Analysis: {goal}",
                "members": [
                    ("backend", "Backend Architect", "Data pipeline design"),
                    ("pm", "Product Manager", "Data metric definition"),
                ],
                "verifier": None,
            },
        }

        # Intelligent matching
        for key, design in team_designs.items():
            if key in goal_lower:
                return design

        # Default: use AI to design team (if DeepSeek available)
        default = {
            "goal": f"Project: {goal}",
            "members": [
                ("pm", "Product Manager", "Requirements analysis and project management"),
                ("frontend", "Frontend Developer", "Frontend development"),
                ("backend", "Backend Architect", "Backend development"),
            ],
            "verifier": ("devops", "Quality Review"),
        }
        return default

    def design_team_from_scratch(self, goal: str) -> dict:
        """Use AI reasoning to design team (more precise, but slower)"""
        # Phase 2: call LLM for more precise team design
        return self.design_team(goal)


class Crew:
    """Crew mode executor — Multi-role real-time collaboration"""

    def __init__(self, members: list[CrewMember], verifier: Optional[CrewMember] = None):
        self.members = members
        self.verifier = verifier
        self.discussion_log = []
        self.total_cost = 0.0

    @classmethod
    def from_template_names(cls, names: list[str], goal: str) -> "Crew":
        """Create Crew from a list of template names"""
        pm = ProfileManager()
        members = []
        for name in names:
            template = get_template(name)
            if template:
                profile = template.to_profile(f"crew_{name}")
                members.append(CrewMember(
                    name=name,
                    profile=profile,
                    role_description=template.display,
                ))
            else:
                # Try to load Profile directly
                try:
                    profile = pm.load(name)
                    members.append(CrewMember(
                        name=name,
                        profile=profile,
                        role_description=profile.soul.role or name,
                    ))
                except FileNotFoundError:
                    console.print(f"[red]✗ Agent '{name}' not found[/]")
        return cls(members=members)

    @classmethod
    def auto_design(cls, goal: str) -> "Crew":
        """Zero-click team assembly — automatically design team"""
        designer = DynamicTeamDesigner()
        design = designer.design_team(goal)
        pm = ProfileManager()
        members = []

        for template_name, role, task in design["members"]:
            template = get_template(template_name)
            if template:
                profile = template.to_profile(f"crew_{template_name}")
                pm.save(profile)
                member = CrewMember(name=template_name, profile=profile, role_description=role)
            else:
                try:
                    profile = pm.load(template_name)
                    member = CrewMember(name=template_name, profile=profile, role_description=role)
                except FileNotFoundError:
                    console.print(f"[yellow]⚠ Skipped: {template_name}[/]")
                    continue
            members.append(member)

        verifier = None
        if design.get("verifier"):
            v_name, v_role = design["verifier"]
            v_template = get_template(v_name)
            if v_template:
                v_profile = v_template.to_profile(f"crew_{v_name}")
                verifier = CrewMember(name=v_name, profile=v_profile, role_description=v_role)

        return cls(members=members, verifier=verifier)

    def run(self, goal: str) -> CrewResult:
        """Execute Crew collaboration"""
        result = CrewResult(goal=goal, members=self.members)

        console.print(f"\n[bold]🎭 Crew assembled![/]")
        console.print(f"   Goal: [bold]{goal[:80]}{'...' if len(goal) > 80 else ''}[/]")
        console.print(f"   Members: {', '.join(f'{m.name}({m.role_description})' for m in self.members)}")
        if self.verifier:
            console.print(f"   Verifier: {self.verifier.name}({self.verifier.role_description})")
        console.print()

        # Phase 1: Each member works independently
        console.print("[bold]📋 Phase 1: Members work independently[/]")
        console.print("-" * 40)

        with ThreadPoolExecutor(max_workers=len(self.members)) as executor:
            future_map = {}
            for member in self.members:
                agent = Agent(member.profile)
                task_prompt = f"""You are {member.role_description} ({member.name}).
Project Goal: {goal}

Please complete the following work from your professional perspective:
1. Analyze the parts of the task requirements relevant to your expertise
2. Provide professional solutions and recommendations
3. List items requiring cooperation from other roles

Please output a complete, professional, and directly usable solution."""
                future = executor.submit(agent.run, task_prompt)
                future_map[future] = member

            for future in as_completed(future_map):
                member = future_map[future]
                try:
                    member.output = future.result()
                    console.print(f"   ✅ {member.name} — Completed")
                except Exception as e:
                    member.output = f"Error: {e}"
                    console.print(f"   ❌ {member.name} — Failed: {e}")

        # Phase 2: Round-table discussion (each member sees others' output, provides feedback)
        if len(self.members) >= 2:
            console.print(f"\n[bold]💬 Phase 2: Round-table Discussion[/]")
            console.print("-" * 40)

            for i, member in enumerate(self.members):
                others_output = "\n\n".join(
                    f"=== {m.name}({m.role_description})'s Solution ===\n{m.output[:1500]}"
                    for j, m in enumerate(self.members)
                    if j != i
                )

                agent = Agent(member.profile)
                review_prompt = f"""You are {member.role_description} ({member.name}).
Project Goal: {goal}

Below are your team members' solutions. Please review and provide:
1. Parts you agree with
2. Issues or risks you identify
3. Suggested modifications
4. Items requiring your cooperation to implement

Other team members' solutions:
{others_output}

Please output your feedback (professional, direct, actionable)."""
                try:
                    feedback = agent.run(review_prompt)
                    self.discussion_log.append({
                        "from": member.name,
                        "type": "feedback",
                        "content": feedback,
                    })
                    result.discussion_log = self.discussion_log
                    console.print(f"   💬 {member.name} — Feedback completed")
                except Exception as e:
                    console.print(f"   ⚠️ {member.name} — Feedback failed: {e}")

        # Phase 3: Final synthesis (PM or first member produces final output)
        console.print(f"\n[bold]📦 Phase 3: Final Synthesis[/]")
        console.print("-" * 40)

        lead = max(self.members, key=lambda m: len(m.output))
        agent = Agent(lead.profile)

        all_outputs = "\n\n".join(
            f"=== {m.name}({m.role_description}) ===\n{m.output}"
            for m in self.members
        )

        feedback_section = ""
        if self.discussion_log:
            feedback_section = "\n\n=== Discussion Feedback ===\n" + "\n\n".join(
                f"From {log['from']}: {log['content'][:1000]}"
                for log in self.discussion_log
            )

        synthesis_prompt = f"""You are the project integration lead.
Project Goal: {goal}

Please integrate the solutions from all roles into a complete deliverable:

{all_outputs}
{feedback_section}

From the perspective of a {lead.role_description}, output a structured integration plan:
1. Overall architecture/solution overview
2. Detailed design of each module
3. Relationships between modules
4. Implementation suggestions and priorities
5. Risk points and mitigation"""
        try:
            result.final_output = agent.run(synthesis_prompt)
            console.print(f"   ✅ Synthesis completed")
        except Exception as e:
            result.final_output = f"Synthesis failed: {e}"
            console.print(f"   ❌ Synthesis failed: {e}")

        # Phase 4: Verification (optional)
        if self.verifier:
            console.print(f"\n[bold]🔍 Phase 4: Verification ({self.verifier.name})[/]")
            console.print("-" * 40)

            v_agent = Agent(self.verifier.profile)
            verify_prompt = f"""Please review the quality and completeness of the following project deliverable.
Project Goal: {goal}

Deliverable:
{result.final_output[:4000]}

Please provide:
1. Overall quality score (1-10)
2. Issues found (critical/moderate/minor)
3. Items that must be changed
4. Overall conclusion: Approved / Conditionally Approved / Rejected"""
            try:
                verify_output = v_agent.run(verify_prompt)
                self.discussion_log.append({
                    "from": self.verifier.name,
                    "type": "verification",
                    "content": verify_output,
                })
                console.print(f"   ✅ Verification completed")
            except Exception as e:
                console.print(f"   ⚠️ Verification failed: {e}")

        console.print(f"\n[bold green]✅ Crew collaboration complete![/]")
        return result


# ─── CLI Commands ───
@click.group()
def crew():
    """Manage Crew teams"""
    pass


@crew.command(name="create")
@click.argument("goal")
@click.option("--members", "-m", help="Members (comma-separated template names)")
def crew_create(goal: str, members: str):
    """Create and execute a Crew"""
    if members:
        names = [n.strip() for n in members.split(",")]
        c = Crew.from_template_names(names, goal)
    else:
        console.print("[bold]🎯 Zero-click team assembly in progress...[/]")
        c = Crew.auto_design(goal)

    result = c.run(goal)

    if result.final_output:
        console.print(Panel(
            result.final_output[:3000],
            title=f"📦 Crew Deliverable: {goal[:50]}...",
            border_style="green",
        ))


@crew.command(name="design")
@click.argument("goal")
def crew_design(goal: str):
    """Preview the automatically designed team"""
    designer = DynamicTeamDesigner()
    design = designer.design_team(goal)

    table = Table(title=f"🎯 Recommended Team: {goal[:50]}", box=None)
    table.add_column("Role", style="cyan")
    table.add_column("Template", style="green")
    table.add_column("Responsibility", style="white")

    for t_name, role, task in design["members"]:
        table.add_row(role, t_name, task)

    console.print(table)
    if design.get("verifier"):
        console.print(f"\nVerifier: [bold]{design['verifier'][0]}[/]({design['verifier'][1]})")
    console.print(f"\n[dim]Usage: [bold]apex crew create \"{goal}\" --members {'/'.join(m[0] for m in design['members'])}[/][/dim]")
