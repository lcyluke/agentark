# Fleet Deploy & Schedule Workflow — Quick Reference

## 1. One-Shot Fleet Deployment

```bash
apex fleet deploy "为羽球宝增加视频上传和骨架分析" -p badminton-coach-ai
```

This does:
- Creates the team from webapp template (if not exist)
- AI decomposes the requirement into tasks
- Creates Epic + Tasks, assigns to matched agents
- Shows task breakdown table + fleet status table

**Flags:**
- `-p|--project <key>` — project scope
- `-t|--template <name>` — team template (webapp/content/data/startup/research)
- `--auto/--manual` — default auto (skip confirmations)
- `-m|--mode <mode>` — pipeline/chain/supervisor

## 2. After Deploy: View Schedule

```bash
apex schedule view -p badminton-coach-ai      # All project tasks in Gantt
apex schedule list -p badminton-coach-ai       # Flat list grouped by epic
```

## 3. Pipeline Modes

| Mode | Command | Auto Level |
|------|---------|------------|
| Pipeline | `apex pipeline normal "需求" --no-confirm` | Full auto |
| Chain | `apex chain run "goal" -p dev` | Full auto (sequential handoff) |
| Supervisor | `apex supervisor "goal" -w 3` | Semi-auto (PM approves gates) |
| Direct | `apex pipeline direct "task" -a <agent>` | Full auto (no decomposition) |

## 4. Quick Task Dispatch

```bash
apex dispatch-smart "需求描述" -p <project>    # AI decompose → auto-create
apex dispatch                                  # Dispatch queued tasks by capacity
apex task epic                                 # Epic tree overview
```

## Common Pitfalls

- **fleet deploy** calls `apex team template <name>` via subprocess — ensure the template name matches a key in `TEAM_TEMPLATES` (hermes_sync.py)
- **decompose_requirement** calls LLM — provider must be configured with API quota
- **schedule view** with no tasks returns "No tasks found" — create tasks first via dispatch-smart or pipeline normal
- The deploy command does NOT auto-start Hermes sessions — agents are in "未启动" state. Run `apex squad start` to open their terminal windows
