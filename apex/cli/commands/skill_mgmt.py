"""Apex — Skill Registry CLI commands.

Commands:
  apex skill list              — List all skills or filter by category
  apex skill show <agent>      — Show agent skill levels with evidence
  apex skill assess            — Assess/update agent skill level
  apex skill match <task>      — Find best agent for a task
  apex skill evidence          — Add evidence for agent skill
  apex skill diff <a> <b>      — Compare two agents' skill profiles
"""

from __future__ import annotations

import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import box
from rich.columns import Columns

from apex.interface.skill_registry import (
    get_registry, LEVEL_LABELS, LEVELS, SKILL_CATALOG, TASK_DIFFICULTY_LEVELS,
    sync_skill_md, sync_all_skill_md,
)
from apex.skill_evaluator import run_evaluation, generate_eval_summary

console = Console()


def list_cmd(category: str = "", agent: bool = False):
    """List all skills or show all agents and their skills."""
    registry = get_registry()

    if agent:
        # List agents grouped by their skills
        agents = registry.list_agents()
        if not agents:
            console.print("[yellow]No agents registered in skill registry.[/]")
            return

        table = Table(
            title="🤖 Agent Skill Levels",
            border_style="blue", box=box.ROUNDED,
        )
        table.add_column("Agent", style="cyan", no_wrap=True)
        table.add_column("Skills", style="white")

        for aname in agents:
            skills = registry.get_agent_skills(aname)
            skill_strs = []
            for s in skills:
                lvl = s["level"]
                conf = s["confidence"]
                bar = "█" * int(conf * 10) + "░" * (10 - int(conf * 10))
                skill_strs.append(f"{s['skill_name']}: {lvl} [{bar}]")
            table.add_row(aname, "\n".join(skill_strs) if skill_strs else "[dim]no skills[/]")

        console.print(table)
        return

    # List skill catalog
    skills = registry.list_skills(category=category)
    if not skills:
        console.print(f"[yellow]No skills found{f' in category {category}' if category else ''}.[/]")
        return

    table = Table(
        title=f"📚 Skill Catalog{f' — {category}' if category else ''}",
        border_style="green", box=box.ROUNDED,
    )
    table.add_column("Skill", style="cyan", no_wrap=True)
    table.add_column("Category", style="yellow")
    table.add_column("Description", style="white")
    table.add_column("Levels", style="dim")

    for s in skills:
        levels = s.get("levels", {})
        level_range = f"{min(levels.keys(), default='-')}–{max(levels.keys(), default='-')}" if levels else "-"
        table.add_row(
            s["name"],
            s["category"],
            s["description"][:60] + ("..." if len(s["description"]) > 60 else ""),
            level_range,
        )

    console.print(table)


def show_cmd(agent_name: str):
    """Show detailed skill levels for an agent with evidence."""
    registry = get_registry()
    agent = registry.get_agent_details(agent_name)

    if not agent:
        console.print(f"[red]Agent '{agent_name}' not found in skill registry.[/]")
        console.print(f"Registered agents: {', '.join(registry.list_agents())}")
        return

    skills = registry.get_agent_skills(agent_name)

    console.print(Panel(
        f"[bold cyan]🤖 {agent_name}[/]\n"
        f"Skills: [green]{agent['skill_count']}[/] registered",
        title="Agent Skill Profile",
        border_style="cyan",
    ))

    if not skills:
        console.print("[yellow]No skills registered.[/]")
        return

    # Group by category
    by_category: dict[str, list] = {}
    catalog_data = registry._data.get("skills", {})
    for s in skills:
        sname = s["skill_name"]
        cat_entry = catalog_data.get(sname, {})
        cat = cat_entry.get("category", "general") if isinstance(cat_entry, dict) else "general"
        by_category.setdefault(cat, []).append(s)

    for cat, cat_skills in sorted(by_category.items()):
        table = Table(
            title=f"📁 {cat.upper()}",
            border_style="blue", box=box.SIMPLE,
        )
        table.add_column("Skill", style="cyan")
        table.add_column("Level", style="yellow")
        table.add_column("Confidence", style="green")
        table.add_column("Description", style="dim")
        table.add_column("🪢 Evidence", style="white")

        for s in cat_skills:
            conf = s["confidence"]
            conf_bar = "█" * int(conf * 10) + "░" * (10 - int(conf * 10))
            desc = s.get("level_description", "")
            ev_count = s.get("evidence_count", 0)
            table.add_row(
                s["skill_name"],
                f"[bold]{s['level']}[/] {LEVEL_LABELS.get(s['level'], '')}",
                f"{conf_bar} {conf:.0%}",
                desc[:50] + ("..." if len(desc) > 50 else "") if desc else "[dim]-[/]",
                f"{'🧾' * min(ev_count, 3)}{f' +{ev_count-3}' if ev_count > 3 else ''}" if ev_count else "[dim]-[/]",
            )

        console.print(table)

    # Show evidence detail for a skill with most evidence
    max_ev = max(skills, key=lambda s: s.get("evidence_count", 0))
    if max_ev.get("evidence_count", 0) > 0:
        # Get full evidence from registry
        agent_data = registry._data.get("agents", {}).get(agent_name, {})
        sk_entry = agent_data.get("skills", {}).get(max_ev["skill_name"], {})
        ev_list = sk_entry.get("evidence", [])
        if ev_list:
            tree = Tree(f"🧾 [bold]Evidence Chain: {max_ev['skill_name']}[/]")
            for ev in ev_list[:5]:
                ev_type = ev.get("type", "?")
                ev_ref = ev.get("ref", "?")
                ev_desc = ev.get("description", "")
                ev_date = ev.get("date", "")
                tree.add(f"[dim]{ev_date}[/] [{ev_type}] {ev_ref}: {ev_desc}")
            if len(ev_list) > 5:
                tree.add(f"[dim]... and {len(ev_list)-5} more items[/]")
            console.print(tree)


def assess_cmd(agent_name: str, skill_spec: str, confidence_str: str = ""):
    """Assess/update an agent's skill level.

    Args:
        agent_name: Agent name.
        skill_spec: Format "skill_name:L3" or just "skill_name" (default L1).
        confidence_str: Optional confidence override (0.0-1.0).
    """
    registry = get_registry()

    # Parse skill spec
    if ":" in skill_spec:
        parts = skill_spec.split(":")
        skill_name = parts[0]
        target_level = parts[1].upper()
    else:
        skill_name = skill_spec
        target_level = "L2"

    if target_level not in LEVELS:
        console.print(f"[red]Invalid level '{target_level}'. Use: L0, L1, L2, L3, L4, L5[/]")
        return

    # Validate skill exists in catalog
    catalog = registry._data.get("skills", {})
    if skill_name not in catalog:
        console.print(f"[yellow]Warning: Skill '{skill_name}' not in catalog. "
                      f"Adding automatically...[/]")
        # Auto-register skill
        catalog[skill_name] = {
            "name": skill_name.replace("-", " ").title(),
            "category": "general",
            "description": skill_name.replace("-", " "),
            "levels": {lvl: {"description": "", "examples": []} for lvl in LEVELS},
        }
        registry._data["skills"] = catalog

    # Parse confidence
    confidence = 0.7
    if confidence_str:
        try:
            confidence = max(0.0, min(1.0, float(confidence_str)))
        except ValueError:
            console.print(f"[red]Invalid confidence '{confidence_str}'. Use 0.0-1.0[/]")
            return

    result = registry.assess_skill(
        agent_name=agent_name,
        skill_name=skill_name,
        new_level=target_level,
        confidence=confidence,
    )

    console.print(Panel(
        f"[bold]✅ Skill Assessment Complete[/]\n"
        f"Agent: [cyan]{result['agent']}[/]\n"
        f"Skill: [yellow]{result['skill']}[/]\n"
        f"Level: [green]{result['old_level']} → {result['new_level']}[/]\n"
        f"Confidence: {result['confidence']:.0%}\n"
        f"Assessed by: [dim]{result['assessed_by']}[/]\n"
        f"Evidence items: {result['evidence_count']}",
        title="📊 Assessment Result",
        border_style="green",
    ))


def match_cmd(task_description: str, difficulty: str = "L2", required_skills: str = ""):
    """Find best agent(s) for a task based on skill matching.

    Args:
        task_description: Task description.
        difficulty: Minimum required difficulty level.
        required_skills: Optional comma-separated skill names.
    """
    registry = get_registry()

    if difficulty.upper() in LEVELS:
        difficulty = difficulty.upper()
    else:
        console.print(f"[yellow]Invalid difficulty '{difficulty}'. Using L2.[/]")
        difficulty = "L2"

    skills = []
    if required_skills:
        skills = [s.strip() for s in required_skills.split(",")]

    results = registry.match_task(task_description, skills, difficulty)

    if not results:
        console.print("[yellow]No matching agents found for this task.[/]")
        return

    diff_info = TASK_DIFFICULTY_LEVELS.get(difficulty, {})
    console.print(Panel(
        f"[bold]🎯 Task Match Results[/]\n"
        f"Task: [white]{task_description[:80]}[/]\n"
        f"Difficulty: [yellow]{difficulty}[/] ({diff_info.get('label', '')})\n"
        f"Required skills: {skills if skills else '[dim](auto-inferred)[/]'}\n"
        f"Agents evaluated: [cyan]{len(results)}[/]",
        title="🔍 Skill Match",
        border_style="blue",
    ))

    table = Table(border_style="green", box=box.ROUNDED)
    table.add_column("Rank", style="dim")
    table.add_column("Agent", style="cyan", no_wrap=True)
    table.add_column("Score", style="yellow")
    table.add_column("Matched", style="green")
    table.add_column("Missing", style="red")

    for i, r in enumerate(results[:10]):
        matched_str = "\n".join(r.matched_skills[:5])
        if len(r.matched_skills) > 5:
            matched_str += f"\n[dim]+{len(r.matched_skills)-5} more[/]"
        missing_str = "\n".join(r.missing_skills[:3])
        if len(r.missing_skills) > 3:
            missing_str += f"\n[dim]+{len(r.missing_skills)-3} more[/]"

        score_bar = "🟢" * int(r.match_score * 5) + "⚪" * (5 - int(r.match_score * 5))
        table.add_row(
            f"#{i+1}",
            r.agent_name,
            f"{r.match_score:.0%} {score_bar}",
            matched_str or "[dim]-[/]",
            missing_str or "[dim]-[/]",
        )

    console.print(table)

    # Show match capacity summary
    top = results[0]
    console.print(f"\n[bold]🏆 Best match:[/] [cyan]{top.agent_name}[/] ({top.details})")
    if top.match_score >= 0.8:
        console.print("[green]✓ Highly recommended — strong skill alignment[/]")
    elif top.match_score >= 0.5:
        console.print("[yellow]○ Adequate — some skills may need support[/]")
    else:
        console.print("[red]✗ Low match — consider training or alternative agent[/]")


def evidence_cmd(agent_name: str, skill_name: str, ev_type: str,
                 ev_ref: str, ev_desc: str):
    """Add evidence for an agent's skill demonstration."""
    registry = get_registry()

    result = registry.add_evidence(agent_name, skill_name, {
        "type": ev_type or "task",
        "ref": ev_ref,
        "description": ev_desc,
        "date": __import__("time").strftime("%Y-%m-%d"),
        "assessed_by": "user",
    })

    console.print(Panel(
        f"[bold green]✅ Evidence Added[/]\n"
        f"Agent: [cyan]{agent_name}[/]\n"
        f"Skill: [yellow]{skill_name}[/] (currently {result['level']})\n"
        f"Ref: [white]{ev_ref}[/] — {ev_desc}\n"
        f"Confidence: {result['confidence']:.0%} (+0.05 from new evidence)",
        title="🧾 Evidence Recorded",
        border_style="green",
    ))


def sync_cmd(agent_name: str):
    """Sync an agent's skills to their Hermes SKILL.md profile."""
    result = sync_skill_md(agent_name)
    if result["status"] == "synced":
        console.print(Panel(
            f"[bold green]✅ SKILL.md Synced[/]\n"
            f"Agent: [cyan]{result['agent']}[/]\n"
            f"Skills: {result['skills_count']} registered\n"
            f"Path: [dim]{result['path']}[/] ({result['size_bytes']} bytes)",
            title="📄 Skill Profile Generated",
            border_style="green",
        ))
    elif result["status"] == "skipped":
        console.print(f"[yellow]⚠️ Skipped: {result.get('reason', '')}[/]")
    else:
        console.print(f"[red]✗ Error: {result.get('reason', 'Unknown')}[/]")


def sync_all_cmd():
    """Sync ALL registered agents' skills to their Hermes profiles."""
    results = sync_all_skill_md()
    success = [r for r in results if r["status"] == "synced"]
    errors = [r for r in results if r["status"] == "error"]

    console.print(Panel(
        f"[bold]📄 Bulk SKILL.md Sync Complete[/]\n"
        f"Synced: [green]{len(success)}[/] profiles\n"
        f"Errors: {f'[red]{len(errors)}[/]' if errors else '[green]0[/]'}",
        title="📚 Skill Profile Generation",
        border_style="blue",
    ))

    if success:
        console.print("\n[bold]Synced:[/]")
        for r in success[:10]:
            console.print(f"  [green]✓[/] {r['agent']} — {r['skills_count']} skills ({r['size_bytes']} bytes)")
        if len(success) > 10:
            console.print(f"  [dim]... and {len(success)-10} more[/]")

    if errors:
        console.print("\n[bold red]Errors:[/]")
        for r in errors[:5]:
            console.print(f"  [red]✗[/] {r.get('agent', '?')}: {r.get('reason', '')}")


def evaluate_cmd():
    """Run skill evaluation pipeline across all agents and tasks."""
    console.print("[bold blue]🔬 Running skill evaluation...[/]")
    try:
        report = run_evaluation()
        summary = generate_eval_summary(report)
        console.print(summary)

        # Save report to file
        from pathlib import Path
        report_path = Path.home() / ".apex" / "eval-reports"
        report_path.mkdir(parents=True, exist_ok=True)
        ts = __import__("time").strftime("%Y%m%d-%H%M%S")
        report_file = report_path / f"eval-{ts}.md"
        report_file.write_text(summary)
        console.print(f"\n[dim]Report saved: {report_file}[/]")

        return report
    except Exception as e:
        console.print(f"[red]✗ Evaluation failed: {e}[/]")
        import traceback
        console.print(traceback.format_exc())
        return None


def diff_cmd(agent_a: str, agent_b: str):
    """Compare two agents' skill profiles."""
    registry = get_registry()
    a_skills = {s["skill_name"]: s for s in registry.get_agent_skills(agent_a)}
    b_skills = {s["skill_name"]: s for s in registry.get_agent_skills(agent_b)}

    all_skills = set(list(a_skills.keys()) + list(b_skills.keys()))

    table = Table(
        title=f"⚔️ Skill Diff: {agent_a} vs {agent_b}",
        border_style="yellow", box=box.ROUNDED,
    )
    table.add_column("Skill", style="cyan")
    table.add_column(f"{agent_a} Level", style="green")
    table.add_column(f"{agent_b} Level", style="blue")
    table.add_column("Gap", style="magenta")

    for sname in sorted(all_skills):
        a_lvl = a_skills.get(sname, {}).get("level", "-")
        b_lvl = b_skills.get(sname, {}).get("level", "-")
        if a_lvl == "-" and b_lvl == "-":
            continue

        # Calculate gap
        a_idx = LEVELS.index(a_lvl) if a_lvl in LEVELS else -1
        b_idx = LEVELS.index(b_lvl) if b_lvl in LEVELS else -1
        if a_idx >= 0 and b_idx >= 0:
            gap = a_idx - b_idx
            gap_str = f"{'+' if gap > 0 else ''}{gap}"
            gap_style = "green" if gap > 0 else ("red" if gap < 0 else "dim")
            gap_fmt = f"[{gap_style}]{gap_str}[/]"
        elif a_lvl == "-":
            gap_fmt = f"[red]→ {b_lvl}[/]"
        elif b_lvl == "-":
            gap_fmt = f"[green]{a_lvl} ←[/]"
        else:
            gap_fmt = "[dim]-[/]"

        table.add_row(sname, f"[green]{a_lvl}[/]", f"[blue]{b_lvl}[/]", gap_fmt)

    console.print(table)

    # Summary
    shared = len(set(a_skills.keys()) & set(b_skills.keys()))
    a_only = len(set(a_skills.keys()) - set(b_skills.keys()))
    b_only = len(set(b_skills.keys()) - set(a_skills.keys()))

    a_avg = sum(LEVELS.index(s["level"]) for s in a_skills.values() if s["level"] in LEVELS) / max(len(a_skills), 1)
    b_avg = sum(LEVELS.index(s["level"]) for s in b_skills.values() if s["level"] in LEVELS) / max(len(b_skills), 1)

    console.print(Panel(
        f"[bold]Summary[/]\n"
        f"Shared skills: {shared} | {agent_a} only: {a_only} | {agent_b} only: {b_only}\n"
        f"Average level: {agent_a}={a_avg:.1f} / {agent_b}={b_avg:.1f} "
        f"{'[green]' + agent_a + ' leads[/]' if a_avg > b_avg else '[blue]' + agent_b + ' leads[/]' if b_avg > a_avg else '[dim]tied[/]'}",
        border_style="blue",
    ))


# Not used as a standalone — registered via main.py
if __name__ == "__main__":
    console.print("[red]Use `apex skill <command>` instead of running this file directly.[/]")
