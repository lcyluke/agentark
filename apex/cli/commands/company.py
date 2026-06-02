"""Apex — One-Click Company CLI commands"""
from __future__ import annotations

import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from apex.core.profile import ProfileManager, Profile, SoulConfig, APEX_HOME
from apex.core.templates import get_template, TEMPLATES
from apex.orchestration.kanban import Kanban
from apex.orchestration.swarm import Swarm
from apex.orchestration.crew import Crew, DynamicTeamDesigner

console = Console()


@dataclass
class Company:
    """Complete definition of an AI company"""
    name: str
    description: str = ""
    industry: str = "tech"
    profiles: list[str] = field(default_factory=list)
    kanban_board: str = "default"
    sop: dict = field(default_factory=dict)
    created_at: float = 0.0


COMPANY_TEMPLATES = {
    "saas": {
        "description": "SaaS startup — Build a product from 0 to 1",
        "profiles": ["pm", "frontend", "backend", "devops", "content"],
        "sop": {
            "name": "SaaS Product Development Process",
            "steps": [
                "Requirements Analysis → PRD",
                "Architecture Design → Tech Spec",
                "Frontend & Backend Parallel Development → Code",
                "Integration Testing → Test Report",
                "Deploy → Production",
                "Content Publishing → Website/Docs",
                "Monitoring & Operations → Ops Report",
            ]
        }
    },
    "ai_product": {
        "description": "AI Product Company — Model + Application Integration",
        "profiles": ["pm", "frontend", "backend", "devops", "content"],
        "sop": {
            "name": "AI Product Development Process",
            "steps": [
                "Data Preparation & Labeling",
                "Model Training & Evaluation",
                "API Service Packaging",
                "Frontend Application Development",
                "Integration Testing",
                "Deploy",
                "User Feedback Collection",
            ]
        }
    },
    "content": {
        "description": "Content Creation Company — Multi-platform Content Matrix",
        "profiles": ["pm", "content", "frontend"],
        "sop": {
            "name": "Content Creation Process",
            "steps": [
                "Topic Planning → Topic Library",
                "Content Creation → First Draft",
                "Review & Revision → Final Draft",
                "Multi-platform Distribution → Publish",
                "Data Review → Optimization Report",
            ]
        }
    },
    "ecommerce": {
        "description": "E-commerce Company — From Products to Transactions",
        "profiles": ["pm", "frontend", "backend", "devops", "content"],
        "sop": {
            "name": "E-commerce Platform Development Process",
            "steps": [
                "Product Management System",
                "Shopping Cart & Orders",
                "Payment Integration",
                "User System",
                "Frontend Storefront",
                "Operations Dashboard",
                "Deployment & Monitoring",
            ]
        }
    },
    "freelance": {
        "description": "Solo Developer Studio — One person takes on projects",
        "profiles": ["pm", "frontend", "backend", "devops"],
        "sop": {
            "name": "Project Delivery Process",
            "steps": [
                "Requirements Discussion → Quote",
                "Technical Plan → Schedule",
                "Development → Delivery",
                "Testing & Acceptance → Launch",
                "Post-launch Maintenance",
            ]
        }
    },
}


class CompanyBuilder:
    """AI Company Builder"""

    def __init__(self):
        self.pm = ProfileManager()
        self.kanban = Kanban(APEX_HOME / "kanban.db")

    def create(self, name: str, industry: str = "saas") -> Company:
        """Create an AI company"""

        template = COMPANY_TEMPLATES.get(industry, COMPANY_TEMPLATES["saas"])

        company = Company(
            name=name,
            description=template["description"],
            industry=industry,
            profiles=[],
            created_at=time.time(),
        )

        # Step 1: Create Profiles
        pm = ProfileManager()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"🏗️ Assembling: {name}...", total=len(template["profiles"]) + 3)

            for tmpl_name in template["profiles"]:
                t = get_template(tmpl_name)
                if t:
                    profile_name = f"{name}_{tmpl_name}"
                    profile = t.to_profile(profile_name)
                    pm.save(profile)
                    company.profiles.append(profile_name)
                    progress.update(task, description=f"  ✅ Created {t.display} ({profile_name})", advance=1)
                else:
                    progress.update(task, description=f"  ⚠️ Skipped {tmpl_name} (template not found)", advance=1)

            # Step 2: Initialize Kanban tasks
            progress.update(task, description="  📋 Initializing Kanban...", advance=1)
            for i, step in enumerate(template["sop"]["steps"]):
                assignee = company.profiles[i % len(company.profiles)] if company.profiles else ""
                self.kanban.create_task(
                    title=f"[{name}] {step}",
                    assignee=assignee,
                    priority=1 if i == 0 else 2,
                    description=f"SOP Step {i+1}: {step}",
                    status="todo",
                )

            # Step 3: Save Company config
            progress.update(task, description="  💾 Saving company config...", advance=1)
            config_path = APEX_HOME / "companies" / f"{name}.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                json.dump({
                    "name": company.name,
                    "description": company.description,
                    "industry": company.industry,
                    "profiles": company.profiles,
                    "sop": template["sop"],
                    "created_at": company.created_at,
                }, f, indent=2, ensure_ascii=False)

            progress.update(task, description=f"  ✅ {name} assembled!", advance=1)

        # Display result
        self._show_company_summary(company, template)

        return company

    def _show_company_summary(self, company: Company, template: dict):
        """Display company summary"""
        table = Table(title=f"🏢 {company.name} — AI Company", box=None, border_style="cyan")
        table.add_column("Department", style="cyan")
        table.add_column("Role", style="green")
        table.add_column("Duty", style="white")
        table.add_column("Ready", style="green")

        tmpl_role_map = {
            "pm": ("📋 Product", "Product Manager", "Requirements Analysis, PRD"),
            "frontend": ("💻 Frontend", "Frontend Dev", "UI Implementation"),
            "backend": ("⚙️ Backend", "Backend Dev", "API/Database"),
            "content": ("✍️ Content", "Content Ops", "Copywriting/SEO"),
            "devops": ("🔧 DevOps", "DevOps", "Deployment/Monitoring"),
        }

        for p_name in company.profiles:
            base = p_name.replace(f"{company.name}_", "")
            dept, role, duty = tmpl_role_map.get(base, ("🤖", base, ""))
            table.add_row(dept, role, duty, "✅")

        console.print(table)

        info = Panel.fit(
            f"[bold]Industry:[/] {company.industry} | "
            f"[bold]SOP:[/] {template['sop']['name']} "
            f"({len(template['sop']['steps'])} steps)\n"
            f"[bold]Command:[/] apex company start \"{company.name}\" \"first task\"\n"
            f"[bold]Team:[/] {', '.join(company.profiles)}",
            title=f"🎯 {company.name} is live!",
        )
        console.print(info)

    def start(self, name: str, goal: str):
        """Start the company to execute the first task"""
        config_path = APEX_HOME / "companies" / f"{name}.json"
        if not config_path.exists():
            console.print(f"[red]✗ Company '{name}' does not exist. Create one with 'apex company create' first[/]")
            return

        with open(config_path) as f:
            config = json.load(f)

        console.print(f"\n[bold]🚀 Starting {name}...")
        console.print(f"   Goal: {goal}")
        console.print(f"   SOP: {config['sop']['name']} ({len(config['sop']['steps'])} steps)")
        console.print()

        # Use the first Profile as PM to lead task decomposition
        profiles = config.get("profiles", [])
        if not profiles:
            console.print("[red]✗ Company has no profiles[/]")
            return

        pm_profile = self.pm.load(profiles[0])
        from apex.core.runtime import Agent
        pm_agent = Agent(pm_profile)

        # Automatically decompose tasks
        decomposition_prompt = f"""You are the product manager of {name}.
Company SOP: {config['sop']['name']}
Company Team: {', '.join(profiles)}

Please decompose the following goal into Kanban tasks, assign each task to a team member:

Goal: {goal}

Output JSON format:
{{
  "goal": "Goal summary",
  "tasks": [
    {{"title": "Task 1", "assignee": "pm_profile_name", "description": "..."}},
    {{"title": "Task 2", "assignee": "frontend_profile_name", "description": "..."}}
  ]
}}"""

        try:
            plan_text = pm_agent.run(decomposition_prompt)
            import re
            json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
            else:
                console.print("[red]✗ Failed to parse task decomposition[/]")
                return

            # Create Kanban tasks
            for t in plan.get("tasks", []):
                self.kanban.create_task(
                    title=f"[{name}] {t['title']}",
                    assignee=t.get("assignee", profiles[0]),
                    description=t.get("description", ""),
                    status="ready",
                )

            console.print(f"\n[bold green]✅ {name} started! {len(plan.get('tasks',[]))} tasks created[/]")
            console.print(f"   View: [bold]apex status[/]")
            console.print(f"   Monitor: [bold]apex dashboard[/]")

        except Exception as e:
            console.print(f"[red]✗ Failed to start: {e}[/]")


def list_companies():
    """List all created companies"""
    companies_dir = APEX_HOME / "companies"
    if not companies_dir.exists():
        console.print("[yellow]No companies created yet[/]")
        return

    companies = list(companies_dir.glob("*.json"))
    if not companies:
        console.print("[yellow]No companies created yet[/]")
        return

    table = Table(title="🏢 AI Companies List", box=None)
    table.add_column("Name", style="cyan")
    table.add_column("Industry", style="green")
    table.add_column("Team Size", style="yellow")
    table.add_column("Created At")

    for c_path in companies:
        with open(c_path) as f:
            data = json.load(f)
        created = time.strftime("%Y-%m-%d %H:%M", time.localtime(data.get("created_at", 0)))
        table.add_row(data["name"], data["industry"], str(len(data.get("profiles", []))), created)

    console.print(table)
