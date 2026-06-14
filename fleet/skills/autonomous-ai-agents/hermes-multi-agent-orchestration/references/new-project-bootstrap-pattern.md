# New Project Bootstrap Pattern (AIAgentOps → 21 modules in 1 session)

Complete 6-step workflow to onboard a new project into Apex multi-agent fleet.

## Step 1: Register Project in Apex Registry

```python
from apex.interface import project_registry as pr

# Propose with dict-format modules (NOT strings — strings crash the registry)
result = pr.propose_project(
    name="ProjectName",
    goal="One-line project goal",
    modules=[
        {"name": "Module A", "description": "What it does"},
        {"name": "Module B", "description": "What it does"},
    ]
)
# Approve
pr.approve_project("ProjectName", "始祖Agent·小卢")
```

**Critical: modules must be dicts with `name`+`description` keys.** Passing string modules causes `AttributeError: 'str' object has no attribute 'get'` in `list_approved_projects()` and `get_project_detail()`.

## Step 2: Create PM Hermes Profile

```bash
hermes profile create pm-projectname
```

Write SOUL.md, config.yaml (kanban.board: projectname), and .env (DEEPSEEK_API_KEY from main .env).

## Step 3: Create Apex YAML Profile

```yaml
name: pm-projectname
project: ProjectName
model:
  default: deepseek-v4-pro
skills: [prd-writing, roadmap-planning, task-decomposition]
```

## Step 4: Create Kanban Board

```bash
hermes kanban boards create projectname
hermes kanban boards switch projectname
```

## Step 5: Seed Tasks via Apex CLI

```bash
# Epic
apex task create "M1: First Milestone" --type epic --project ProjectName --hours 80 --assignee pm-projectname

# Stories (parent = epic ID)
apex task create "Story title" --type story --parent <EPIC_ID> --hours 16 --assignee <agent> --project ProjectName
```

Task status transitions: `assigned → in_progress → completed`. Cannot skip states.

## Step 6: Verify Dashboard

Check `http://localhost:8080` → 项目作战室 → dropdown includes new project with module count.

Run: `apex fleet status` to see the PM agent in the fleet.

## Development Flow

1. User gives directive ("开干", "继续", "下一步")
2. Decompose into `delegate_task` parallel subagents (max 3 concurrent)
3. **After every delegate_task: verify file locations** — subagents default to writing in `/Users/Mac/Desktop/2026AIAPP/Apex/` instead of the target project. Fix with `find` + `cp`.
4. Subagent timeout (>600s) → fall back to manual `write_file` — faster, no path errors
5. Commit, push, update Apex task statuses
6. Show summary table, wait for next directive
