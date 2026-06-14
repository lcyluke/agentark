# New Project Fleet Blueprint (FinOps AI Pattern)

Template for creating a new multi-agent project fleet. Followed for `finopsai` (June 2026).

## Step 1: Design Fleet

Identify domains needed. Multi-tenant SaaS example:

| # | Role | Profile Name | Priority |
|---|------|-------------|----------|
| 1 | PM | `<proj>-pm` | P0 |
| 2 | Architect | `<proj>-architect` | P0 |
| 3 | Backend | `<proj>-backend` | P0 |
| 4 | Frontend | `<proj>-frontend` | P0 |
| 5 | DevOps | `<proj>-devops` | P1 |
| 6 | Security | `<proj>-security` | P1 |
| 7 | AI/ML | `<proj>-ai` | P1 |

Start with core 5 (P0+P1 DevOps), add the rest on demand.

## Step 2: Create Project Directory

```bash
mkdir -p ~/Desktop/2026AIAPP/<project>/{docs,specs,backend,frontend,infra,scripts}
```

## Step 3: Create PM Profile First

Write `SOUL.md` BEFORE creating the profile (or write after, but profile dir must exist):

```bash
# Write SOUL.md to ~/.hermes/profiles/<proj>-pm/SOUL.md
# Then create profile (already-exists error is harmless)
hermes profile create <proj>-pm
```

SOUL.md must include: Identity, Project Background, Personality, Core Responsibilities, Tech Stack, Team roster, Working directory, Communication principles, Kanban board.

## Step 4: Batch Create Remaining Profiles + Config

Use `delegate_task` for parallel SOUL.md creation, then batch config:

```python
profiles = ["<proj>-architect", "<proj>-backend", "<proj>-frontend", "<proj>-devops"]
for p in profiles:
    hermes profile create p  # creates dir + 89 skills + wrapper
    write_file(SOUL.md)       # role identity

# Batch config.yaml + .env for ALL profiles (including PM)
api_key = read from ~/.hermes/.env
for p in all_profiles:
    write config.yaml (deepseek-v4-pro, max_turns: 30)
    write .env (DEEPSEEK_API_KEY)
    # PM only: add kanban.board: <proj> to config.yaml
```

## Step 5: Register in Message Router

Add to `PROJECTS` dict in `apex/orchestration/message_router.py`:

```python
"<project>": Project(
    key="<project>",
    name="Project Name",
    emoji="💰",
    path="~/Desktop/2026AIAPP/<project>",
    keywords=[...],
    profiles=[...],
    categories=[...],
),
```

Also add to `PROJECT_AGENTS` in `apex/orchestration/task_decomposer.py`.

## Step 6: Set Up Cron Jobs

| Job | Schedule | Purpose |
|-----|----------|---------|
| PM日报 | `0 9 * * *` | Morning project report |
| 任务监控 | `every 30m` | Task completion monitor |

## Step 7: Verify

```bash
hermes profile list | grep <proj>
curl http://127.0.0.1:8080/api/router/quick?msg=<proj>测试
apex fleet inspect -p <project>
```

## Alternative: Lightweight Project (AIAgentOps Pattern)

For smaller open-source libraries/tools (not full SaaS), use a lighter fleet:

| # | Role | Profile Name |
|---|------|-------------|
| 1 | PM | `<proj>-pm` |
| 2 | Architect | `architect` (shared) |
| 3 | Ops | `ops-engineer` (shared) |
| 4 | Frontend | `frontend-dev` (shared) |

### Project Registration via Registry API

Instead of message_router, use `project_registry` functions for lightweight projects:

```python
from apex.interface import project_registry as pr

# 1. Propose with module dicts (NOT strings — strings break get_project_detail)
pr.propose_project(
    name="ProjectName",
    goal="One-line goal description",
    modules=[
        {"name": "Module A", "description": "What it does"},
        {"name": "Module B", "description": "What it does"},
    ]
)

# 2. Approve
pr.approve_project("ProjectName", "始祖Agent·小卢")

# 3. Create Kanban board
hermes kanban boards create <project-slug>
hermes kanban boards switch <project-slug>

# 4. Seed initial tasks
apex task create "Epic Name" --type epic --project ProjectName --hours 80
apex task create "Story Name" --type story --parent <EPIC_ID> --hours 16
```

### Dashboard Visibility

The Dashboard 项目作战室 auto-discovers projects from `projects_registry.json`. No message_router or task_decomposer registration needed for basic visibility. Tasks created via `apex task create` appear in CLI but may not show in Dashboard task count (Dashboard uses a separate kanban.db).
