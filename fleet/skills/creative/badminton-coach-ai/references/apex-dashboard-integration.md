# Apex Dashboard — Project Management Kanban

The Apex project at `~/Desktop/2026AIAPP/Apex/` provides a web dashboard with a built-in Kanban board for tracking tasks, epics, and sub-tasks across multi-agent projects.

## Quick Start

```bash
cd ~/Desktop/2026AIAPP/Apex
.venv/bin/python3 -c "
from apex.interface.web import run_dashboard
run_dashboard(host='127.0.0.1', port=8080, debug=False)
"
# Dashboard: http://127.0.0.1:8080
# API:       http://127.0.0.1:8080/api/tasks
# SSE:       http://127.0.0.1:8080/api/stream/logs
```

## Kanban Data Model

| Field | Type | Notes |
|:------|:-----|:------|
| `id` | string | Auto-generated `t_<uuid8>` |
| `title` | string | Task name |
| `description` | string | Details (optional) |
| `assignee` | string | Agent profile name (optional) |
| `status` | string | `todo` / `ready` / `in_progress` / `blocked` / `done` / `failed` |
| `priority` | int | 1=highest, 2=normal, 3=low |
| `parent_id` | string | Links subtask to epic (optional) |
| `depends_on` | string[] | JSON array of task IDs (optional) |
| `output` | string | Agent output text |
| `cost` | float | Token/dollar cost |
| `created_at` | ISO string | Auto-set |
| `completed_at` | ISO string | Auto-set when status→done/failed |

## REST API

### List all tasks
```bash
curl http://127.0.0.1:8080/api/tasks
```

### Create task
```bash
curl -X POST http://127.0.0.1:8080/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"任务名称","description":"描述","priority":1,"parent_id":"t_xxxx","assignee":"hermes"}'
```

### Update task status
```bash
curl -X PUT http://127.0.0.1:8080/api/tasks/t_5349c5f5 \
  -H "Content-Type: application/json" \
  -d '{"status":"done"}'
```

### Delete task
```bash
curl -X DELETE http://127.0.0.1:8080/api/tasks/t_xxxx
```

### Get status summary
```bash
curl http://127.0.0.1:8080/api/status
# Returns: {tasks: [...], task_summary: {todo:N, in_progress:N, done:N, ...}}
```

## Batch Import Pattern (Python)

```python
import json, urllib.request, time

BASE = "http://127.0.0.1:8080/api/tasks"

def create_task(title, **kwargs):
    data = json.dumps({"title": title, **kwargs}).encode()
    req = urllib.request.Request(BASE, data=data,
        headers={"Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(req).read())

# Create epics first, then subtasks with parent_id
epic = create_task("Epic Name", description="...", priority=1)
for title in ["Subtask 1", "Subtask 2"]:
    create_task(title, parent_id=epic["id"], priority=2)
    time.sleep(0.05)  # rate limit

# Mark all done
resp = urllib.request.urlopen(BASE)
tasks = json.loads(resp.read())
for t in tasks:
    if t.get("parent_id"):
        data = json.dumps({"status": "done"}).encode()
        req = urllib.request.Request(f"{BASE}/{t['id']}", data=data,
            headers={"Content-Type": "application/json"}, method="PUT")
        urllib.request.urlopen(req)
```

## Dashboard Pages

| URL | Description |
|:----|:------------|
| `/` | Main dashboard (latest template) |
| `/v4` | Dashboard v4 |
| `/v5` | Dashboard v5 |
| `/agents` | Agent profile management |
| `/logs` | Event log viewer |
| `/traces` | Execution trace viewer |

## Pitfalls

- **Kanban DB must exist.** The dashboard reads `~/.apex/kanban.db`. If it doesn't exist, `load_kanban()` returns None and tasks won't show. Create it via any task creation API call.
- **Port conflicts.** Default port is 8080. Check `lsof -ti:8080` before starting.
- **Existing tasks are NOT cleared.** The kanban.db persists across sessions. Old tasks from previous projects will still be there. Use the batch API to mark them done, or delete the DB to start fresh.
- **`parent_id` is for subtasks only.** Epics have no `parent_id`. Subtasks link to their epic via `parent_id`. Only mark subtasks as done; epics serve as headers.
- **SSE streaming requires client support.** The `/api/stream/logs` endpoint uses Server-Sent Events. Browsers handle this natively via `EventSource`.
