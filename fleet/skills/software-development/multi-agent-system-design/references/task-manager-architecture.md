# Hierarchical Task Manager Architecture

## Overview

Apex's Task Manager (`apex/orchestration/task_manager.py`) provides enterprise-grade project management with PM approval workflow, agent capacity-aware auto-dispatch, and cross-agent help requests.

## Data Model

### 4-Tier Hierarchy

```
Epic (task_type="epic")          — Large initiative (Build Dashboard v5)
  └─ Story ("story")             — User story (Frontend Redesign)
       ├─ Task ("task")          — Single work unit (Header Nav)
       └─ Task ("task")          — Single work unit (API Layer)
            └─ Subtask ("subtask") — Sub-division (Auth middleware)
```

### Workflow: 10-State Machine

```
Draft → Requested → PM_Review → Approved → Assigned
  ↑         ↓                       ↓
  └── Rejected ←── PM rejects ─────┘

Assigned → In_Progress → Completed → PM_Verify → Verified → Closed
              ↓                          ↓
            Blocked ←──── Stuck ──────→ In_Progress (rework)
```

Transitions are enforced — `update_task_status()` validates that the new status is in the allowed set for the current status. Invalid transitions raise `ValueError` with a message listing allowed moves.

### State transition rules (Python dict):

```python
{
    WorkflowStatus.DRAFT:        [REQUESTED],
    WorkflowStatus.REQUESTED:    [PM_REVIEW, CLOSED],
    WorkflowStatus.PM_REVIEW:    [APPROVED, REJECTED],
    WorkflowStatus.REJECTED:     [DRAFT, CLOSED],
    WorkflowStatus.APPROVED:     [ASSIGNED],
    WorkflowStatus.ASSIGNED:     [IN_PROGRESS, BLOCKED],
    WorkflowStatus.IN_PROGRESS:  [COMPLETED, BLOCKED],
    WorkflowStatus.BLOCKED:      [IN_PROGRESS, CLOSED],
    WorkflowStatus.COMPLETED:    [PM_VERIFY, IN_PROGRESS],
    WorkflowStatus.PM_VERIFY:    [VERIFIED, IN_PROGRESS],
    WorkflowStatus.VERIFIED:     [CLOSED],
}
```

## Key Components

### `ProjectTask` dataclass
- `id`, `title`, `description`, `task_type` (epic/story/task/subtask)
- `workflow_status` (10-state enum)
- `parent_id` — links to parent for hierarchy
- `sub_task_ids` — list of child IDs for rollup
- `progress_pct` — auto-calculated from sub-tasks
- `estimated_hours`, `actual_hours`
- `pm_notes`, `rejection_reason`, `completion_notes`, `verification_notes`
- `project`, `tags`, `assignee`, `requested_by`, `reviewed_by`

### `HelpRequest` dataclass
- `requesting_agent` — who needs help
- `source_task_id` — the task that triggered this
- `assigned_agent` — helper assigned by PM
- `status` — pending → pm_review → approved → assigned → resolved

### `AgentCapacity` dataclass
- `agent_name`, `active_tasks`, `max_concurrent` (default 3)
- `available_slots = max - active`
- `load_pct` — percentage load
- `total_completed`, `total_failed`

## `TaskManager` Class

Singleton via `get_task_manager()`.

### CRUD
- `create_task()` — creates with hierarchy linking, auto-assigns best agent
- `get_task()` — by ID
- `get_task_tree(id, depth=3)` — recursive tree
- `get_epic_tree()` — all epics with full sub-tree
- `list_tasks()` — filterable by project/assignee/type/status/phase

### Progress Rollup
When a sub-task status changes, `_update_parent_progress()` recalculates parent progress as `completed_subtasks / total_subtasks * 100`. This propagates up the hierarchy.

### Auto-Dispatch
`auto_dispatch()` scans for tasks in "assigned" status, checks each agent's capacity, and marks them "in_progress" if the agent has available slots. Unassigned tasks get assigned to the least-loaded matching agent.

### Help Request Flow
1. Agent calls `request_help()` → creates HelpRequest in "pending"
2. PM reviews via `list_help_requests()`
3. PM calls `approve_help()` → changes to "approved", auto-creates sub-task for helper
4. Helper agent picks up the auto-created task

## Persistence

Stored in `~/.apex/ops.db` with two tables:
- `project_tasks` — 31 columns
- `help_requests` — 10 columns

Indexed on `assignee`, `workflow_status`, `project`.

## CLI Commands

```bash
apex task create <title> --type epic/story/task/subtask --parent <id> --assignee <agent>
apex task list --project X --assignee Y --type epic --status draft
apex task show <id>          # With recursive tree
apex task status <id> <new_status> --notes "reason"
apex task epic               # All epic trees
apex capacity                # Agent load dashboard
apex dispatch                # Auto-dispatch pending tasks
apex help-request <agent> <title> --description "..." --task <source_id>
apex help-approve <req_id> --agent <helper> --notes "..."
apex help-list               # All help requests
```

## API Endpoints

All under `api/taskmgr/` prefix:
```
POST /api/taskmgr/create             — Create task
GET  /api/taskmgr/list               — List with filters
GET  /api/taskmgr/<id>               — Task detail
GET  /api/taskmgr/<id>?tree=1        — Task + tree
PUT  /api/taskmgr/<id>/status        — Status transition
GET  /api/taskmgr/epics              — Epic trees
GET  /api/capacity                   — Agent capacity
POST /api/dispatch                   — Auto-dispatch
GET  /api/help/request               — List help requests
POST /api/help/request               — Create help request
POST /api/help/approve               — PM approves
```

## Agent Selection Algorithm

`_pick_best_agent(phase)`:
1. Scores each profile by `available_slots + preference_bonus`
2. Preference bonus = 10 if the agent name matches a known role for the phase
3. Role map: `frontend/backend/design/ops/content`
4. Returns the highest-scoring agent with at least 1 available slot
