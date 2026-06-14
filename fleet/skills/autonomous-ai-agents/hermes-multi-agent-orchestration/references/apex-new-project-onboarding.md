# Apex New Project Onboarding — End-to-End Workflow

Complete flow for adding a new project to the Apex ecosystem with PM agent, Kanban board, and Dashboard visibility.

## 6-Step Onboarding

### 1. Register Project in Apex

```python
from apex.interface import project_registry as pr

pr.propose_project(
    name="ProjectName",
    goal="One-line project description",
    modules=[
        {"name": "Module A", "description": "What it does"},
        {"name": "Module B", "description": "What it does"},
    ]
)
pr.approve_project("ProjectName", "始祖Agent·小卢")
```

**CRITICAL**: Modules MUST be dicts with `name` + `description`. Passing plain strings causes `AttributeError: 'str' object has no attribute 'get'` in `list_approved_projects()`.

### 2. Create Kanban Board

```bash
hermes kanban boards create <project-slug>
hermes kanban boards switch <project-slug>
```

### 3. Create PM Hermes Profile

```bash
hermes profile create pm-<project>
```

### 4. Configure PM Profile

Write to `~/.hermes/profiles/pm-<project>/`:
- **SOUL.md**: Role identity, project info, module architecture table
- **config.yaml**: Model config + `kanban.board: <project-slug>`
- **.env**: `DEEPSEEK_API_KEY=<key>` (copy from `~/.hermes/.env`)

### 5. Create Apex YAML Profile

Write `~/.apex/profiles/pm-<project>.yaml` with `project: <ProjectName>` field.

### 6. Seed Initial Tasks

```bash
cd ~/Desktop/2026AIAPP/Apex && source .venv/bin/activate
apex task create "Epic: First milestone" --type epic --project <ProjectName> --hours 80 --assignee pm-<project>
apex task create "Story: First task" --type story --parent <EPIC_ID> --hours 16 --assignee <agent> --project <ProjectName>
```

## Verification

- Dashboard: http://localhost:8080 → 项目作战室 → dropdown shows project
- CLI: `apex task list --project <ProjectName>` shows tasks
- Fleet: `apex fleet status` includes pm-<project>
- Kanban: tasks appear in board `<project-slug>`

## Common Pitfall

Dashboard shows "0 任务" even though tasks exist — this is because the Dashboard's `_count_project_tasks()` queries a different source than the Kanban board. Tasks created via `apex task create` go to the kanban board and are visible via `apex task list`, but the Dashboard counter may lag. Use the Apex CLI for authoritative task counts.
