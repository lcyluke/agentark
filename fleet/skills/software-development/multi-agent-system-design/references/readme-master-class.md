# README Master Class — CrewAI-Style Layout for Apex

Based on analysis of crewAIInc/crewAI README (52.6k stars) and redesign of Apex README (session 2026-06-02).

## CrewAI README Structure (Reference)

1. **Logo Banner** — centered `<picture>` with dark/light mode support, 600px width
2. **Trendshift + Homepage Links** — navigation row: Homepage · Docs · Start Cloud Trial · Blog · Forum
3. **Badge Row 1** — GitHub stars, forks, issues, PRs, License
4. **Badge Row 2** — PyPI version, PyPI downloads, Twitter follow
5. **Tagline** — "Fast and Flexible Multi-Agent Automation Framework" with bold emphasis
6. **Product Suite Section** — CrewAI AMP Suite description
7. **Table of Contents** — 15+ navigation anchors
8. **Build with AI** — Claude Code/Cursor plugin instructions
9. **Why CrewAI** — 5 bullet points with description
10. **Getting Started** — Video tutorial + text guide
11. **Installation** — pip install + troubleshooting
12. **YAML Configuration** — Project structure tree + agents.yaml/tasks.yaml examples
13. **Running Your Crew** — Code examples + .env setup
14. **Connecting to a Model** — Provider setup
15. **How CrewAI Compares** — Comparison with LangGraph
16. **FAQ** — Common questions
17. **Contribution** — Contribution guide
18. **License** — MIT

## Apex Redesign Decisions (2026-06-02)

Kept the same visual structure but replaced content with Apex's superior feature set:

| Section | CrewAI | Apex (Improved) |
|---------|--------|-----------------|
| Header | Logo + Badges | Logo + 9 badges (added PyPI/downloads/tweet) |
| Navigation | Homepage · Docs · Cloud | 9 anchor links to sections |
| Tagline | 2 sentences | Tagline + subtitle + em combined |
| Why | 5 bullets | 7-row problem/solution table |
| Getting Started | Video + text | Quick start: pip → init → run → swarm → crew → company → dashboard |
| Key Features | Described in paragraphs | 7 Core Innovations with visual examples, commands, data |
| Comparison | 1 framework (LangGraph) | 7 frameworks across 30+ dimensions |
| Templates | None | 5 agent templates with detailed table |
| Modes | Crews + Flows only | 10 orchestration modes with TOP10 use cases |
| Dashboard | None (paid) | 9 features + 14 REST API endpoints |
| Autonomous | None | 7x24 engine architecture + 9 CLI commands |
| Installation | pip install only | macOS/Linux/Windows/Docker + post-install |
| Config | .env setup | 3 env vars + local models |
| Commands | None | 30+ commands in categorized table |
| Architecture | Not shown | ASCII diagram + source code map |
| Metrics | Not shown | 10 GitHub badges |
| Chinese README | Not available | Full Chinese translation synced |

## Key Formatting Patterns

### Navigation Links
```markdown
<p align="center">
  <a href="#-quick-start">Quick Start</a>
  · <a href="#-why-apex">Why Apex?</a>
  · <a href="#-7-core-innovations">7 Innovations</a>
</p>
```

### Badge Groups (PyPI version, downloads)
```markdown
<a href="https://pypi.org/project/apex-multiagent/"><img src="https://img.shields.io/pypi/v/apex-multiagent?style=flat-square" alt="PyPI"></a>
<a href="https://pypi.org/project/apex-multiagent/"><img src="https://img.shields.io/pypi/dm/apex-multiagent?style=flat-square" alt="Downloads"></a>
```

### Social Proof (style=social for stars/forks)
```markdown
<a href="https://github.com/lcyluke/apex/stargazers"><img src="https://img.shields.io/github/stars/lcyluke/apex?style=social" alt="Stars"></a>
```

### Problem-Solution Table
```markdown
| 😤 **Problem** — Description | **Solution** — Description with **bold emphasis** |
```

### Command Blocks (no prompt prefix, no output noise)
```bash
apex init my-project
apex run "task"
apex dashboard
```

## File Location

Banner image stored at `docs/images/apex-banner.png` (800×436, ~455KB compressed). Referenced via:
```markdown
https://raw.githubusercontent.com/lcyluke/apex/main/docs/images/apex-banner.png
```

CrewAI stores images at `docs/images/` — using same convention.

## Verifying README Display

1. Push to GitHub
2. Open `https://github.com/lcyluke/apex` in browser
3. Check: logo renders, badges resolve, emoji display correctly
4. Dark mode: toggle GitHub theme, verify logo `<picture>` tag switches sources
