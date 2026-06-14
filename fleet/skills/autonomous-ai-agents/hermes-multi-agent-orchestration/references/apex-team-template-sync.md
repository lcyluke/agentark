# Apex Team Template & Profile Sync Reference

> Built: June 2026 — `apex/interface/hermes_sync.py` and `apex/orchestration/task_manager.py`

## Architecture

```
User wants a multi-agent team
    │
    ▼
apex team template <name>           # Step 1: Create team from template
    │                                  Creates 4 Apex profiles with:
    │                                  - SOUL.md (role identity)
    │                                  - config.yaml (model config)
    │                                  - wrapper script (~/.local/bin/<name>)
    │
    ▼
apex team sync <profile>             # Step 2 (optional): Sync existing Apex profile to Hermes
    │                                  Writes SOUL.md + config.yaml + wrapper
    │
    ▼
<name> chat                          # Step 3: Launch Hermes with profile persona
    │                                  Terminal shows role name, not "Hermes"
    │
    ▼
apex task create / dispatch          # Step 4: PM assigns hierarchical tasks
apex capacity                        #         View agent load balancing
apex help-request / help-approve     #         Cross-agent help with PM approval
```

## Key Source Files

### `apex/interface/hermes_sync.py`
Profile sync bridge — the core of `apex team` commands:
- `ROLE_SOULS` dict — 20 role personality definitions
- `TEAM_TEMPLATES` — 5 team templates (webapp, content, data, startup, research)
- `sync_profile_to_hermes()` — writes SOUL.md + config.yaml + wrapper script
- `create_team_from_template()` — loops sync_profile_to_hermes for all template roles
- `list_hermes_profiles()` — parses `hermes profile list` output
- `get_team_setup_script()` — generates a bash script for manual runner setup

### `apex/orchestration/task_manager.py`
Hierarchical task management with PM workflow:
- 4-tier hierarchy: Epic → Story → Task → Subtask
- 10-stage PM workflow: Draft → Requested → PM_Review → Approved/Rejected → Assigned → In_Progress → Blocked → Completed → PM_Verify → Verified → Closed
- Progress rollup: parent % = weighted average of children by `estimated_hours`
- Agent capacity tracking: each agent has `max_active_tasks` and `active_task_count`
- Auto-dispatch: assigns to least-loaded agent
- Cross-agent help requests: PM approval gate for inter-agent dependency

### `apex/cli/commands/task_mgmt.py`
CLI command handlers:
- `apex task create` — create epic/story/task with hierarchy
- `apex task list` — filter by status/agent/project
- `apex task show <id>` — full detail with parent/children tree
- `apex task status <id> <new>` — transition + progress_pct + notes
- `apex task epic <title>` — full tree view with progress bars
- `apex capacity` — agent load table
- `apex dispatch <title>` — auto-assign to least-loaded
- `apex help-request` / `apex help-approve` / `apex help-list` — cross-agent help

## CLI Reference

### Team Management
```bash
apex team template list                      # Show 5 templates with roles
apex team template <name>                    # Create team (4 agents, one shot)
apex team sync <profile>                     # Sync existing Apex profile to Hermes
apex team sync-all                           # Sync ALL Apex profiles to Hermes
```

### Task Management (4-tier hierarchy)
```bash
apex task create "<title>" --type epic|story|task|subtask
  [--parent <id>] [--assignee <agent>] [--project <proj>] [--hours <num>]
apex task list [--status <status>] [--assignee <agent>] [--project <proj>]
apex task show <id> [--tree]                 # Detail + optional tree view
apex task status <id> <new_status>
  [--progress <0-100>] [--notes "<text>"]
apex task epic "<title>"                     # Full tree with progress bars
```

### Capacity & Dispatch
```bash
apex capacity                                # All agents with load bars
apex dispatch "<title>" --hours <num>        # Auto-assign to least-loaded
```

### Cross-Agent Help
```bash
apex help-request <target-agent> "<description>"
  [--task <task_id>] [--priority <1-5>]
apex help-approve <request_id> --agent <helper>
  [--notes "<text>"]
apex help-list [--status pending|approved|rejected|completed]
```

## Status Machine

```
Draft → Requested → PM_Review → Approved → Assigned → In_Progress → Completed → PM_Verify → Verified → Closed
                   ↓                       ↓             ↓
                 Rejected → Draft         Blocked → In_Progress    Returned → In_Progress
```

## API Endpoints (behind Apex Dashboard)

All under `/api/taskmgr/*` prefix:
- `POST /api/taskmgr/create` — create task
- `GET /api/taskmgr/list` — list with filters
- `GET /api/taskmgr/<id>?tree=1` — show with tree
- `PUT /api/taskmgr/<id>/status` — transition status
- `GET /api/taskmgr/epics` — all epics with progress
- `POST /api/dispatch` — auto-dispatch
- `GET /api/capacity` — agent capacity
- `GET /api/help/request` — list help requests
- `POST /api/help/request` — create help request
- `POST /api/help/approve/<id>` — approve/reject

## Verification

```bash
cd ~/Desktop/2026AIAPP/Apex && source .venv/bin/activate

# Create team
apex team template webapp

# Check profiles exist
hermes profile list | grep -E "product-manager|frontend-dev|backend-dev|devops"

# Create tasks
apex task create "Sprint 1" --type epic --project webapp --hours 40
apex task create "Login page" --type story --parent <EPIC_ID> --assignee frontend-dev --hours 8

# Check capacity
apex capacity

# Launch a profile (new terminal)
frontend-dev chat -q "What is my role?"
```
