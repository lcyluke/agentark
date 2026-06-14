# Intelligent Project Tiering Engine

How Apex auto-detects project type and size, then allocates agents and cron monitors by tier. This supports the project creation workflow from `hermes-multi-agent-orchestration`.

## Tiering Model

```
🟢 SMALL (seed)           🟡 MEDIUM (growth)           🔴 LARGE (mature)
<20 files, <3 weeks,      20-100 files, 1-3 months,    100+ files, 3+ months,
1 person                  2-3 people                   3+ people

PM also monitors          PM + 🧠 smart assistant       PM + 🧠 smart assistant
+ 1 core agent             + 3-4 core agents            + 5-6 core agents
+ Git pulse (optional)     + 5 monitoring crons         + 8 monitoring crons
```

### Smart Assistant (auto-provisioned for medium+ projects)

Independent `{project}-assistant` Profile:
- 📋 Task board scanning (30min)
- 🎯 Milestone tracking (daily 09:00)
- ⚠️ Risk alerting (daily 20:00)
- 📊 Project weekly (every Monday)
- 💰 Resource analysis (LARGE only, weekly)
- 🔗 Cross-project coordination (LARGE only, daily 14:00)

## CLI Commands

```bash
# Auto-detect type and size
apex project create my-app --name "My App"

# Manual override
apex project create dashboard --name "Dashboard" --type webapp --size large

# Specify project path for size detection
apex project create my-app --name "My App" --path ~/projects/my-app

# Dry run (preview only, no creation)
apex project create blog --name "Blog" --dry-run

# Analyze only
apex project analyze my-app --name "My App"

# List registered projects
apex project list
```

## 6 Project Types

| Type | Keywords | Auto-allocated Agents |
|:--|:--|:--|
| `webapp` | web, dashboard, api, saas | frontend/backend/fullstack/devops |
| `ai-ml` | ai, model, training, inference | ai-algorithm, ai-vision, ml-engineer, data-scientist |
| `mobile` | miniprogram, app, wechat | frontend-dev, backend-dev, devops |
| `data` | data, etl, analytics, visualization | data-engineer, data-analyst, data-scientist |
| `content` | content, article, blog, media | content-strategist, writer, editor, publisher |
| `infra` | infra, devops, docker, k8s, deploy | devops, ops-engineer, security-compliance |

Detection priority: name/description keywords > file extensions (`.wxml`→mobile, `.pth`→ai-ml, `Dockerfile`→infra) > default webapp.

## Size Detection

Based on project directory analysis (requires `--path`):

- `file_count >= 100` OR `commit_count >= 500` OR `age_weeks >= 12` → LARGE
- `file_count >= 20` OR `commit_count >= 50` OR `age_weeks >= 4` → MEDIUM
- Otherwise → SMALL

No path → default SMALL.

## Agent Allocation Matrix

Each project type has different agent configurations at 3 sizes. See `apex/core/project_template.py` → `TYPE_CORE_AGENTS`.

PM naming: first word of project key + `-pm` (e.g., `my-app` → `my-pm`).

## Monitoring Cron Tiers

| Size | Crons | Contents |
|:--|:--|:--|
| 🟢 SMALL | 0-1 | Git pulse only (if git path exists) |
| 🟡 MEDIUM | 5 | PM daily + board scan + milestones + risk + weekly |
| 🔴 LARGE | 8 | All medium + resource analysis + cross-project coordination |

## Creation Flow

1. Analyze project type and size
2. Display analysis results (Panel)
3. User confirmation
4. Create PM Profile → sync to Hermes
5. Create smart assistant (medium+ projects)
6. Create core agent Profiles
7. Register Cron monitoring tasks
8. Output completion report

## Key Files

| File | Description |
|:--|:--|
| `apex/core/project_template.py` | Tiering engine (~500 lines) |
| `apex/cli/main.py` | `project create/analyze/list` commands |
| `apex/interface/hermes_sync.py` | project-assistant ROLE_SOUL |

## Backward Compatibility

Existing 4 projects (badminton-coach-ai/Apex/FinOps/Shenzhen-map) registered in `LEGACY_TEMPLATES`, unaffected by the new engine. New projects use `apex project create`.
