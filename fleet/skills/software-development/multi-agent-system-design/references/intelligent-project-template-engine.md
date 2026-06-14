# Intelligent Project Template Engine

> Added 2026-06-05 — Session: Smart tiered project initialization with agent allocation

## Overview

Replaces the old hardcoded `project_template.py` (4 fixed templates, 3 monitors each) with a **smart tiered engine** that classifies projects by type and size, then allocates the right agents automatically.

## Three-Tier Model

| Tier | Size | PM Model | Core Agents | Cron Monitors | Total Agents |
|:--|:--|:--|:--|:--|:--|
| 🟢 Small | <20 files, <3w, 1p | PM doubles as inspector | 1-2 | 0-1 (Git pulse only) | 2-3 |
| 🟡 Medium | 20-100 files, 1-3m, 2-3p | PM + 🧠 Smart Assistant | 3-4 | 5 (PM daily + assistant suite) | 5-6 |
| 🔴 Large | 100+ files, 3+m, 3+p | PM + 🧠 Smart Assistant + specialty | 5-6 | 8 (full suite + resources + cross-project) | 7-9 |

## Six Project Types

Each type has its own agent allocation matrix across the three tiers:

- `webapp` — web apps (fullstack/frontend/backend/devops)
- `ai-ml` — AI/ML (data-scientist/ai-algorithm/ai-vision/ml-engineer)
- `mobile` — mobile/miniprograms (frontend-dev/backend-dev/content-marketing)
- `data` — data pipelines (data-engineer/data-analyst/data-scientist)
- `content` — content creation (writer/editor/publisher/designer)
- `infra` — infrastructure (devops/ops-engineer/security-compliance)

## Type Detection Logic

1. **Keyword matching** — scans project name + description against keyword lists per type
2. **File extension analysis** — `.pth/.pt` → AI-ML, `.wxml/.wxss` → Mobile, `.jsx/.tsx` → Webapp
3. **Config file detection** — Dockerfile → Infra
4. Default: `webapp`

## Size Detection Logic

1. **File count** — `find ... -type f | wc -l`
2. **Git commit count** — `git log --oneline --all | wc -l`
3. **Repo age** — first commit timestamp → weeks
4. Thresholds:
   - ≥100 files OR ≥500 commits OR ≥12 weeks → Large
   - ≥20 files OR ≥50 commits OR ≥4 weeks → Medium
   - Otherwise → Small

## Smart Project Assistant (🧠)

Auto-created for Medium and Large projects. Separate Hermes Profile (`<key>-assistant`) that handles:

| Scan | Schedule | Responsibility |
|:--|:--|:--|
| 📋 Kanban scan | every 30m | Completion/blockage instant notification |
| 🎯 Milestone tracking | 0 9 * * * | Deviation >20% alert |
| ⚠️ Risk scan | 0 20 * * * | Git inactivity + task blockage + anomalies |
| 📊 Weekly report | 0 9 * * 1 | Comprehensive 15-line report |
| 💰 Resource analysis | 0 9 * * 1 | Large projects only — API/GPU/human resource tracking |
| 🔗 Cross-project coordination | 0 14 * * * | Large projects only — dependency/blocking check |

## CLI Commands

```bash
# Auto-detect everything, create project group
apex project create my-app --name "My App"

# Specify type and size
apex project create dashboard --name "Dashboard" --type webapp --size large

# Preview without creating
apex project create blog --name "Blog" --dry-run

# Analyze a project
apex project analyze my-app --name "My App"

# List registered projects
apex project list
```

## Key Files

- `apex/core/project_template.py` — Smart template engine (~540 lines)
  - `build_smart_template()` — main entry point
  - `detect_project_type()` — keyword + file analysis
  - `detect_project_size()` — git + file count analysis
  - `TYPE_CORE_AGENTS` — agent allocation matrix
  - `build_assistant_monitors()` — smart assistant cron jobs
  - `build_small_monitors()` / `build_large_monitors()` — tiered monitoring
- `apex/interface/hermes_sync.py` — `project-assistant` ROLE_SOUL added
- `apex/cli/main.py` — `project` command group (create/analyze/list)

## Design Principle

**PM decides strategy; Assistant ensures nothing is missed.** The assistant does NOT make strategic decisions — it scans, tracks, alerts, and reports. The PM remains the single decision-maker. This separation prevents "too many cooks" while ensuring comprehensive coverage.
