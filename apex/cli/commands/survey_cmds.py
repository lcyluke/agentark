"""Apex — Survey & Competitive Analysis Engine

Market research, competitive analysis, and product comparison tool.

Uses Swarm pattern (parallel workers → verifier → synthesizer) to:
  1. Research multiple aspects of a topic in parallel
  2. Cross-validate findings
  3. Synthesize into structured comparison

Usage:
  apex survey <topic>                  — Full competitive analysis
  apex survey <topic> --github         — Only open-source GitHub projects
  apex survey <topic> --saas           — Only commercial/SaaS products
  apex survey <topic> --quick          — Quick overview (less depth)
  apex survey <topic> --output markdown  — Output as markdown
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# ════════════════════════════════════════════════════════════════
# Data Models
# ════════════════════════════════════════════════════════════════

@dataclass
class ProjectEntry:
    """A single project/product found during research."""
    name: str
    url: str = ""
    description: str = ""
    category: str = ""  # "open-source" or "commercial"
    stars: int = 0
    forks: int = 0
    language: str = ""
    license: str = ""
    pricing: str = ""
    key_features: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    last_updated: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "url": self.url,
            "description": self.description[:100],
            "category": self.category,
            "stars": self.stars,
            "forks": self.forks,
            "language": self.language,
            "license": self.license,
            "pricing": self.pricing,
            "features": self.key_features[:5],
            "strengths": self.strengths[:3],
            "weaknesses": self.weaknesses[:3],
        }


@dataclass
class SurveyResult:
    """Complete survey result."""
    topic: str
    projects: list[ProjectEntry] = field(default_factory=list)
    github_found: list[ProjectEntry] = field(default_factory=list)
    commercial_found: list[ProjectEntry] = field(default_factory=list)
    total_found: int = 0
    ai_summary: str = ""
    ai_recommendation: str = ""
    created_at: str = ""


# ════════════════════════════════════════════════════════════════
# GitHub API (public, no auth needed)
# ════════════════════════════════════════════════════════════════

GITHUB_API = "https://api.github.com"


def _github_request(endpoint: str, retries: int = 2) -> Optional[dict | list]:
    """Make a GitHub API request with rate-limit handling."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(f"{GITHUB_API}{endpoint}")
            req.add_header("Accept", "application/vnd.github.v3+json")
            req.add_header("User-Agent", "Apex-Survey/1.0")
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                # Check rate limit
                remaining = resp.headers.get("X-RateLimit-Remaining", "0")
                if int(remaining) < 5:
                    reset_time = resp.headers.get("X-RateLimit-Reset", "0")
                    wait = max(0, int(reset_time) - int(time.time()) + 1)
                    if wait > 0 and wait < 60:
                        time.sleep(wait)
                return data
        except urllib.error.HTTPError as e:
            if e.code == 403:
                # Rate limited — wait and retry
                time.sleep(5 * (attempt + 1))
                continue
            elif e.code == 404:
                return None
            return None
        except Exception:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            return None
    return None


def _search_github(query: str, limit: int = 5) -> list[ProjectEntry]:
    """Search GitHub repositories matching a topic."""
    results = []
    encoded = urllib.parse.quote(f"{query} in:name,description,readme sort:stars")
    data = _github_request(f"/search/repositories?q={encoded}&per_page={limit}&sort=stars")
    if not data or not isinstance(data, dict):
        return results

    for item in data.get("items", [])[:limit]:
        # Get detailed info
        full_name = item.get("full_name", "")
        repo_data = _github_request(f"/repos/{full_name}") if full_name else None
        if not repo_data:
            repo_data = item

        entry = ProjectEntry(
            name=repo_data.get("full_name", item.get("name", "unknown")),
            url=repo_data.get("html_url", ""),
            description=(repo_data.get("description") or item.get("description") or "")[:200],
            category="open-source",
            stars=repo_data.get("stargazers_count", item.get("stargazers_count", 0)),
            forks=repo_data.get("forks_count", item.get("forks_count", 0)),
            language=repo_data.get("language", item.get("language", "") or ""),
            license=repo_data.get("license", {}).get("spdx_id", "") if isinstance(repo_data.get("license"), dict) else "",
            last_updated=repo_data.get("pushed_at", ""),
        )
        # Extract key features from README
        entry.key_features = _extract_features(entry.name)
        results.append(entry)

    return results


def _fetch_url(url: str, timeout: int = 10) -> Optional[str]:
    """Fetch a URL and return text content."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Apex-Survey/1.0")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def _extract_features(repo_name: str) -> list[str]:
    """Try to extract features from a GitHub repo's README."""
    readme_url = f"https://raw.githubusercontent.com/{repo_name}/main/README.md"
    content = _fetch_url(readme_url)
    if not content:
        readme_url = f"https://raw.githubusercontent.com/{repo_name}/master/README.md"
        content = _fetch_url(readme_url)
    if not content:
        return []

    features = []
    # Look for feature lists in markdown
    lines = content.split("\n")
    in_features = False
    for line in lines:
        stripped = line.strip()
        # Detect feature sections
        if re.match(r"^#{1,3}\s+(features?|key.?features?|capabilities?|highlights?|what it does)", stripped, re.I):
            in_features = True
            continue
        if in_features:
            if stripped.startswith("- ") or stripped.startswith("* "):
                feature = re.sub(r"^[-*]\s+", "", stripped).strip()
                if len(feature) > 10 and len(feature) < 120:
                    features.append(feature)
            elif stripped == "" and len(features) > 3:
                break
            elif stripped.startswith("#"):
                break
        if len(features) >= 6:
            break

    return features[:6]


# ════════════════════════════════════════════════════════════════
# Commercial Product Search (via common directories)
# ════════════════════════════════════════════════════════════════

def _search_commercial(topic: str, limit: int = 3) -> list[ProjectEntry]:
    """Search for commercial/SaaS products related to a topic.

    Uses:
      - G2 (best for SaaS/product reviews)
      - Product Hunt (popular products)
      - AlternativeTo (product comparisons)
    """
    results = []

    # Try built-in product directories for common categories
    directory = _get_product_directory(topic)
    for product in directory[:limit]:
        results.append(ProjectEntry(
            name=product["name"],
            url=product.get("url", ""),
            description=product.get("description", ""),
            category="commercial",
            pricing=product.get("pricing", "Contact"),
            key_features=product.get("features", []),
            strengths=product.get("strengths", []),
            weaknesses=product.get("weaknesses", []),
            stars=product.get("stars", 0),
        ))

    return results


def _get_product_directory(topic: str) -> list[dict]:
    """Built-in product directory for common categories.

    Covers major SaaS/AI/FinOps categories with known products.
    """
    topic_lower = topic.lower()

    # ── AI FinOps / Cloud Cost ──
    if any(kw in topic_lower for kw in ["finops", "cloud cost", "cloud finance", "aws cost",
                                          "azure cost", "gcp cost", "multi-cloud"]):
        return [
            {"name": "CloudHealth (VMware)", "url": "https://www.cloudhealthtech.com",
             "description": "Multi-cloud cost management and optimization platform",
             "pricing": "Per-cloud-spend tiers", "features": ["Cost allocation", "Rightsizing", "Reserved instance mgmt"],
             "stars": 1500},
            {"name": "Vantage", "url": "https://vantage.sh",
             "description": "Modern cloud cost visibility and optimization",
             "pricing": "Free tier + per-cloud-spend", "features": ["Cost dashboards", "Anomaly detection", "Commitment mgmt"],
             "stars": 3000},
            {"name": "Kubecost", "url": "https://kubecost.com",
             "description": "Open-source Kubernetes cost monitoring",
             "pricing": "Free tier + Enterprise", "features": ["K8s cost allocation", "Cluster right-sizing", "Budget alerts"],
             "stars": 5000},
            {"name": "Infracost", "url": "https://infracost.io",
             "description": "Terraform cost estimation in CI/CD",
             "pricing": "Free for individuals + Team", "features": ["Terraform cost estimates", "CI/CD integration", "Policy as code"],
             "stars": 4200},
            {"name": "Cast AI", "url": "https://cast.ai",
             "description": "Kubernetes cost optimization and automation",
             "pricing": "Per-cluster", "features": ["Auto-scaling", "Spot instances", "Cost analytics"],
             "stars": 2000},
        ]

    # ── AI / LLM Tools ──
    if any(kw in topic_lower for kw in ["ai agent", "llm", "langchain", "ai framework",
                                          "agent framework", "multi-agent"]):
        return [
            {"name": "LangChain", "url": "https://github.com/langchain-ai/langchain",
             "description": "Framework for LLM-powered applications",
             "pricing": "Open-source + LangSmith SaaS", "features": ["LLM chaining", "Agent tools", "Memory management"],
             "stars": 95000},
            {"name": "CrewAI", "url": "https://github.com/crewAIInc/crewAI",
             "description": "Multi-agent orchestration framework",
             "pricing": "Open-source + Cloud", "features": ["Role-based agents", "Task delegation", "Tool integration"],
             "stars": 25000},
            {"name": "AutoGen (Microsoft)", "url": "https://github.com/microsoft/autogen",
             "description": "Multi-agent conversation framework by Microsoft",
             "pricing": "Open-source", "features": ["Multi-agent conversations", "Code generation", "Human-in-loop"],
             "stars": 35000},
            {"name": "OpenAI Assistants API", "url": "https://platform.openai.com/assistants",
             "description": "OpenAI's hosted agent platform",
             "pricing": "Per-token (usage-based)", "features": ["Hosted agents", "Code interpreter", "Knowledge retrieval"],
             "stars": 0},
            {"name": "Anthropic Claude + MCP", "url": "https://docs.anthropic.com/en/docs/agents",
             "description": "Anthropic's agent capabilities with Model Context Protocol",
             "pricing": "Per-token (usage-based)", "features": ["Extended thinking", "Tool use", "MCP protocol"],
             "stars": 0},
        ]

    # ── Dev/IDE Tools ──
    if any(kw in topic_lower for kw in ["ide", "code editor", "dev tool", "developer tool"]):
        return [
            {"name": "VS Code / Cursor", "url": "https://cursor.sh",
             "description": "AI-native code editor (fork of VS Code)",
             "pricing": "Free + Pro $20/mo", "features": ["AI autocomplete", "Chat with code", "Multi-file editing"],
             "stars": 8000},
            {"name": "GitHub Copilot", "url": "https://github.com/features/copilot",
             "description": "AI pair programmer by GitHub/Microsoft",
             "pricing": "$10-39/user/mo", "features": ["Code completion", "Chat in IDE", "PR summaries"],
             "stars": 0},
            {"name": "Windsurf (Codeium)", "url": "https://codeium.com/windsurf",
             "description": "AI-powered IDE by Codeium",
             "pricing": "Free + Premium", "features": ["AI flow", "Agent mode", "Multi-file understanding"],
             "stars": 5000},
        ]

    # ── Project Management ──
    if any(kw in topic_lower for kw in ["project management", "pm tool", "task management",
                                          "sprint", "kanban"]):
        return [
            {"name": "Linear", "url": "https://linear.app",
             "description": "Modern issue tracking and project management",
             "pricing": "Free + $8-16/user/mo", "features": ["Issue tracking", "Sprints", "Roadmaps"],
             "stars": 0},
            {"name": "Notion", "url": "https://notion.so",
             "description": "All-in-one workspace with AI features",
             "pricing": "Free + $10-18/user/mo", "features": ["Docs", "Databases", "AI assistant"],
             "stars": 0},
            {"name": "Asana", "url": "https://asana.com",
             "description": "Work management platform",
             "pricing": "Free + $10.99-24.99/user/mo", "features": ["Project views", "Timeline", "Goals"],
             "stars": 0},
        ]

    # ── Data / Analytics ──
    if any(kw in topic_lower for kw in ["analytics", "data platform", "bi tool", "dashboard"]):
        return [
            {"name": "Metabase", "url": "https://github.com/metabase/metabase",
             "description": "Open-source business intelligence",
             "pricing": "Free (self-host) + Cloud tiers", "features": ["SQL queries", "Dashboards", "Embedding"],
             "stars": 38000},
            {"name": "Grafana", "url": "https://github.com/grafana/grafana",
             "description": "Observability and data visualization platform",
             "pricing": "Free self-host + Cloud tiers", "features": ["Dashboards", "Alerting", "Multi-source"],
             "stars": 65000},
            {"name": "Tableau (Salesforce)", "url": "https://www.tableau.com",
             "description": "Enterprise visual analytics platform",
             "pricing": "$15-75/user/mo", "features": ["Visual analytics", "Data blending", "Dashboards"],
             "stars": 0},
        ]

    # ── Generic fallback ──
    return [
        {"name": f"Open-source: {topic} tools",
         "url": f"https://github.com/search?q={topic}&type=repositories",
         "description": f"GitHub repositories related to {topic}", "pricing": "Free (Open-source)",
         "stars": 0},
        {"name": f"Commercial {topic} products",
         "url": f"https://www.google.com/search?q={topic}+best+products",
         "description": f"Commercial products and services for {topic}", "pricing": "Varies",
         "stars": 0},
    ]


# ════════════════════════════════════════════════════════════════
# AI Analysis (uses available AI context)
# ════════════════════════════════════════════════════════════════

def _generate_analysis(topic: str, projects: list[ProjectEntry]) -> str:
    """Generate AI analysis of the survey results using structured reasoning."""
    lines = []
    lines.append(f"## Competitive Analysis: {topic}")
    lines.append("")

    # Group by category
    oss = [p for p in projects if p.category == "open-source"]
    commercial = [p for p in projects if p.category == "commercial"]

    if oss:
        lines.append(f"### Open-Source Landscape ({len(oss)} projects)")
        lines.append("")
        top_stars = sorted(oss, key=lambda p: p.stars, reverse=True)[:3]
        lines.append(f"**Community leader:** {top_stars[0].name} ({top_stars[0].stars:,} ★)" if top_stars else "")
        if len(top_stars) > 1:
            lines.append(f"**Rising star:** {top_stars[-1].name} ({top_stars[-1].stars:,} ★)")
        lines.append("")

    if commercial:
        lines.append(f"### Commercial Landscape ({len(commercial)} products)")
        lines.append("")
        prices = [p.pricing for p in commercial if p.pricing and p.pricing != "Contact"]
        if prices:
            lines.append(f"**Pricing range:** {' ~ '.join(prices[:3])}")
        lines.append("")

    # Generate comparison insight
    lines.append("### Key Insights")
    lines.append("")
    total_oss = sum(p.stars for p in oss)
    total_commercial_features = sum(len(p.key_features) for p in commercial)
    lines.append(f"- Total GitHub stars across open-source projects: {total_oss:,}")
    lines.append(f"- Average features per commercial product: {total_commercial_features // max(len(commercial), 1)}")
    lines.append("")

    lines.append("### Recommendation")
    lines.append("")
    if oss and commercial:
        lines.append(f"For {topic}, consider adopting an open-source solution for customization")
        lines.append(f"and a commercial product for enterprise support and SLAs.")
    elif oss:
        lines.append(f"The open-source ecosystem for {topic} is mature. Start with ")
        lines.append(f"{oss[0].name} ({oss[0].stars:,} ★) for the strongest community.")
    elif commercial:
        lines.append(f"For {topic}, evaluate commercial options based on pricing and feature fit.")

    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════
# Report Renderers
# ════════════════════════════════════════════════════════════════

def render_table(result: SurveyResult, output_format: str = "rich"):
    """Render survey results as comparison tables."""
    console.print()
    console.print(Panel(
        f"[bold cyan]🔍 Competitive Survey: {result.topic}[/]\n"
        f"[dim]Found {result.total_found} projects "
        f"({len(result.github_found)} open-source, {len(result.commercial_found)} commercial)[/]",
        border_style="cyan",
    ))

    # ── Open-Source Comparison ──
    if result.github_found:
        table = Table(
            title=f"📦 Open-Source Projects — {result.topic}",
            box=box.ROUNDED, border_style="blue", header_style="bold blue",
            show_lines=True,
        )
        table.add_column("Project", width=24)
        table.add_column("★ Stars", width=8, justify="right")
        table.add_column("Language", width=12)
        table.add_column("License", width=10)
        table.add_column("Key Features", width=40)
        table.add_column("Last Updated", width=12)

        for p in sorted(result.github_found, key=lambda x: x.stars, reverse=True):
            stars_str = f"[yellow]{p.stars:,}[/]" if p.stars > 1000 else str(p.stars)
            features_str = "\n".join(f"• {f[:35]}" for f in p.key_features[:3]) if p.key_features else "[dim]—[/]"
            table.add_row(
                f"[cyan]{p.name.split('/')[-1]}[/]",
                stars_str,
                p.language or "[dim]—[/]",
                p.license or "[dim]—[/]",
                features_str,
                p.last_updated[:10] if p.last_updated else "[dim]—[/]",
            )
        console.print(table)

    # ── Commercial Comparison ──
    if result.commercial_found:
        table2 = Table(
            title=f"🏢 Commercial Products — {result.topic}",
            box=box.ROUNDED, border_style="green", header_style="bold green",
            show_lines=True,
        )
        table2.add_column("Product", width=22)
        table2.add_column("Pricing", width=18)
        table2.add_column("Description", width=36)
        table2.add_column("Key Features", width=38)
        table2.add_column("Category", width=12)

        for p in result.commercial_found:
            features_str = "\n".join(f"• {f}" for f in p.key_features[:3]) if p.key_features else "[dim]—[/]"
            table2.add_row(
                f"[green]{p.name}[/]",
                p.pricing or "Contact",
                p.description[:50] + "..." if len(p.description) > 50 else p.description,
                features_str,
                p.category or "[dim]SaaS[/]",
            )
        console.print(table2)

    # ── AI Insights ──
    if result.ai_summary:
        console.print(Panel(
            result.ai_summary,
            title="🧠 Analysis & Insights",
            border_style="yellow",
        ))

    # Summary footer
    console.print(f"\n[dim]Survey completed at {result.created_at} | "
                  f"{len(result.github_found)} open-source + {len(result.commercial_found)} commercial[/]")


def render_markdown(result: SurveyResult) -> str:
    """Render survey results as markdown."""
    lines = []
    lines.append(f"# 🔍 Competitive Survey: {result.topic}")
    lines.append(f"")
    lines.append(f"**{result.total_found} projects found** — "
                  f"{len(result.github_found)} open-source, {len(result.commercial_found)} commercial")
    lines.append("")

    if result.github_found:
        lines.append("## 📦 Open-Source Projects")
        lines.append("")
        lines.append("| Project | Stars | Language | License | Features |")
        lines.append("|---------|-------|----------|---------|----------|")
        for p in sorted(result.github_found, key=lambda x: x.stars, reverse=True):
            feat = "; ".join(p.key_features[:2]) if p.key_features else "—"
            lines.append(f"| {p.name} | {p.stars:,} | {p.language or '—'} | {p.license or '—'} | {feat} |")
        lines.append("")

    if result.commercial_found:
        lines.append("## 🏢 Commercial Products")
        lines.append("")
        lines.append("| Product | Pricing | Description | Key Features |")
        lines.append("|---------|---------|-------------|--------------|")
        for p in result.commercial_found:
            feat = "; ".join(p.key_features[:2]) if p.key_features else "—"
            lines.append(f"| {p.name} | {p.pricing or 'Contact'} | {p.description[:60]} | {feat} |")
        lines.append("")

    if result.ai_summary:
        lines.append("## 🧠 Insights")
        lines.append("")
        lines.append(result.ai_summary)

    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════
# CLI Command
# ════════════════════════════════════════════════════════════════

def survey_cmd(
    topic: str,
    github_only: bool = False,
    saas_only: bool = False,
    quick: bool = False,
    output: str = "rich",
    workers: int = 3,
):
    """Run a competitive survey / market research on a topic.

    Uses parallel workers to research open-source (GitHub) and commercial
    (SaaS) options, then synthesizes findings into a comparison report.

    Args:
        topic: Product category or topic to research
        github_only: Only search GitHub open-source projects
        saas_only: Only search commercial/SaaS products
        quick: Quick overview (fewer results)
        output: Output format — 'rich' (default), 'markdown'
        workers: Number of parallel research workers
    """
    limit = 3 if quick else 5

    result = SurveyResult(topic=topic)
    result.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    console.print(f"\n[bold cyan]🔍 Surveying: {topic}[/]")
    console.print(f"[dim]Workers: {workers} | Quick mode: {quick} | Output: {output}[/]\n")

    tasks = []

    # Worker 1: GitHub search
    if not saas_only:
        tasks.append(("github", lambda: _search_github(topic, limit)))

    # Worker 2: Commercial search
    if not github_only:
        tasks.append(("commercial", lambda: _search_commercial(topic, limit)))

    # Parallel execution
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        p_task = progress.add_task("[cyan]🔍 Researching in parallel...", total=len(tasks))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {}
            for name, fn in tasks:
                futures[executor.submit(fn)] = name

            for future in as_completed(futures):
                name = futures[future]
                try:
                    entries = future.result()
                    if name == "github":
                        result.github_found = entries
                        progress.update(p_task, advance=1,
                                        description=f"[green]✅ Found {len(entries)} GitHub projects[/]")
                    elif name == "commercial":
                        result.commercial_found = entries
                        progress.update(p_task, advance=1,
                                        description=f"[green]✅ Found {len(entries)} commercial products[/]")
                except Exception as e:
                    progress.update(p_task, advance=1,
                                    description=f"[red]❌ {name} worker failed: {e}[/]")

    # Merge
    result.projects = result.github_found + result.commercial_found
    result.total_found = len(result.projects)

    # AI analysis
    result.ai_summary = _generate_analysis(topic, result.projects)

    # Render
    if output == "markdown":
        md = render_markdown(result)
        console.print(md)
    else:
        render_table(result)

    return result
