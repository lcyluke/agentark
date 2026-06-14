---
name: comparative-framework-analysis
description: "Evaluate and compare N open-source frameworks/tools/products across M standardized dimensions. Produces structured MD + Word reports with scoring tables, radar chart, and final recommendation."
version: 1.0.0
author: Hermes Agent
platforms: [linux, macos]
---

# Comparative Framework / Tool Analysis

## When to Use

- User asks "compare X vs Y vs Z" — any framework, tool, product, or service comparison
- User wants a recommendation with scoring, trade-offs, and implementation roadmap
- Decision-support research: "which one should I use for [use case]?"

Do NOT use for: simple feature lookups, "what is X", or single-tool deep dives.

## Standard Dimensions

These are the default 6 evaluation axes. Adjust per task — drop irrelevant ones, add domain-specific ones:

| # | Dimension | What It Measures |
|---|-----------|------------------|
| 1 | **Harness / Architecture** | Framework maturity, infrastructure quality, deployment readiness, codebase health |
| 2 | **Context & Prompt Engineering** | How agents manage prompts, context windows, system messages, memory |
| 3 | **Self-learning / Improvement** | RL, auto-tuning, data generation, evolution, scaling law research |
| 4 | **Team Management** | Multi-agent task assignment, role definition, dependency chains, swarm orchestration |
| 5 | **Monitoring / Observability** | Tracing, logging, metrics, dashboards, debugging tools |
| 6 | **Collaboration** | Agent-to-agent communication, handoff protocols, coordination patterns |
| 7 | **Build-vs-Assemble** | Whether the framework is ready-to-use, needs assembly with other tools, or should be built from scratch. Critical for the "compare → recommend → build" pipeline. |

## Research Process

### Step 1: Gather Data

For each candidate, collect from GitHub and docs:

```python
# Minimal data per framework:
{
    "name": "CrewAI",
    "stars": "52.6k",
    "language": "Python",
    "last_active": "8 hours ago",
    "positioning": "role-based agent teams",
    "readme_url": "https://raw.githubusercontent.com/org/repo/main/README.md"
}
```

Use browser_navigate for GitHub pages (check stars, forks, last commit).
Use `curl -sL` for raw README content.
Check recent commit activity — if >3 months stale, flag as 🟡 caution / 🔴 dead.

### Step 2: Score Each Framework

For each dimension, assign 1-5 stars with a one-sentence justification:

```markdown
**CrewAI** ⭐⭐⭐⭐⭐
- Role-based three-tier architecture (Agent → Task → Crew)
- Multiple process types: sequential, hierarchical
- Manager Agent auto-coordination
- Flows event-driven orchestration
- Industry-leading team management
```

Be opinionated. A ⭐ rating without a concrete reason is noise.

### Step 3: Build the Radar Matrix

```markdown
| 维度 | Hermes | CrewAI | LangGraph | CAMEL |
|------|--------|--------|-----------|-------|
| Harness | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
```

Sort columns: put the user's current tool first (e.g. Hermes), then competitors by relevance.

### Step 4: Make a Recommendation

Two-part output:
1. **Best-of-breed per dimension** — "For team management, use CrewAI"
2. **Final recommendation** — the optimal combination (e.g. "CrewAI + Hermes hybrid")

Include a "Why not X" section — for each rejected option, say why concisely.

### Step 5: Propose Implementation Roadmap

Break into phases (Phase 1 / Phase 2 / Phase 3). Each phase = time estimate + concrete actions.

### Step 6: Save Dual Format

1. **Markdown** — write to the user's project `洞察/` or `reports/` directory, OR to `~/Desktop/2026AIAPP/LuInsightFor<Name>/` for standalone analysis documents (per user preference — Luke's insight files go under `LuInsight`-prefixed dirs under `~/Desktop/2026AIAPP/`)
2. **Word** — generate via `word-report-generation` skill (see that skill for python-docx pitfalls)

### Step 7: Evolve the Recommendation into a Build Plan

Sometimes comparison leads to "none of these fit perfectly — build your own." When the analysis concludes with a hybrid-recommendation or a new-design recommendation:

1. Add a "Why Not Build from Scratch" section that lists what would need to be built (and what already exists)
2. Propose a phased build roadmap (Phase 0 → Phase 1 → Phase 2 → Phase 3)
3. Reference the `multi-agent-system-design` skill if the user wants to proceed with building
4. The architecture of the new system should absorb the best features identified during the comparison (e.g. take CrewAI's team management, LangGraph's state machine, CAMEL's self-learning)
5. **Include Hermes/your-current-tool in the comparison** — users want to know "should I switch from what I already use?" not just "which external tool is best"
6. **The analysis is complete when you can confidently say either "use X" or "build Y"** — a recommendation that says "it depends" without an opinion is incomplete

## Step 8: Save to Correct Location

Per the user's preference (Luke/老卢):
- **Standalone analysis documents** go to `~/Desktop/2026AIAPP/LuInsight<Name>/` (e.g. `LuInsightForMutliAgent/`)
- **Project-specific reports** go to the project directory's `洞察/` or `reports/` subfolder
- Always save both `.md` and `.docx` formats
- The `.docx` file inherits content from the `.md` — they must match

## Step 9: Offer to Save as Skill

If the analysis involved:
- A new evaluation dimension not covered by the standard 6
- A new tool/framework comparison category that might repeat
- A tricky multi-step workflow that future sessions should reuse

...offer to either patch this skill or create a reference file before leaving the session.

## Reference Template

```markdown
# [Topic] — [N] Frameworks Compared

> Generated: YYYY-MM-DD
> Scope: [what was evaluated]
> Dimensions: [list]

## 1. Baseline Data

| Name | Stars | Lang | Active | Positioning |

## 2. N-Dimension Deep Dive

### 2.1 Dimension One

**Framework A** ⭐⭐⭐⭐⭐
- Point
- Point

**Framework B** ⭐⭐⭐
- Point

## 3. Radar Matrix

## 4. Final Recommendation

### 🏆 [Winner] + [Current Stack] Hybrid

### Architecture

### Why Not Others

## 5. Implementation Roadmap

### Phase 1 — ... (X days/weeks)
### Phase 2 — ... (X days/weeks)
### Phase 3 — ... (ongoing)

## Appendix
```

## Automated Research: `apex survey` Command

Apex now has a built-in CLI command that automates the research process:

```
apex survey <topic>                    — Full competitive analysis
apex survey <topic> --quick            — Quick overview (less depth)
apex survey <topic> --github-only      — Only open-source GitHub projects
apex survey <topic> --saas-only        — Only commercial/SaaS products
apex survey <topic> --output markdown  — Markdown format output
```

### How It Works

The `apex survey` command uses parallel workers (ThreadPoolExecutor) to research open-source and commercial options simultaneously, then synthesizes into structured comparison:

```
Worker 1 (GitHub)     Worker 2 (Commercial)   Synthesizer
  ┌──────────┐         ┌──────────────┐        ┌───────────┐
  │ Search   │         │ Directory    │        │ Rich      │
  │ repos    │ ────────│ lookup       │ ───────│ Tables +  │
  │ README   │         │ Pricing      │        │ AI        │
  │ features │         │ Features     │        │ Insights  │
  └──────────┘         └──────────────┘        └───────────┘
```

### When to Use Each Method

| Method | Best For | When |
|--------|----------|------|
| Manual analysis (this skill) | Deep technical comparison | Need architecture review, code inspection, nuanced trade-offs |
| `apex survey` CLI command | Quick market landscape | First pass, competitive intelligence, product directory lookup |

The `apex survey` command is good for **first-pass research** — when you need a structured overview fast. Use this skill for **deep-dive technical comparisons** where you need to inspect code, verify claims, and build nuanced recommendations.

## Pitfalls

1. **README vs reality** — GitHub READMEs overstate capabilities. Check recent commits, open issues, and "last commit" date for the real story.
2. **Stars ≠ quality** — High stars can mean good marketing. Cross-check with issue response time and PR merge cadence.
3. **Maintenance mode** — Some projects look active but are officially deprecated (e.g. AutoGen → MAF). Always check the README banner.
4. **Score inflation** — Resist giving everything ⭐⭐⭐⭐. If a framework lacks a feature entirely, give ⭐ or ⭐⭐ honestly.
5. **GitHub API without login** — browser_navigate works for public repos but raw.githubusercontent.com returns content directly via `curl -sL` — faster and no bot detection.

## Output

Save to `洞察/<topic>.md` and `洞察/<topic>.docx` inside the user's project directory.
