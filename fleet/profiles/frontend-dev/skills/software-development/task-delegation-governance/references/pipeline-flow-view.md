# Pipeline Flow View — Implementation Details

## Overview
Added to `/cc` project war room view. When a project is selected, the dashboard shows:
1. Status distribution bar (in_progress/ready/blocked/gate/todo/done)
2. Kanban columns with task cards showing handoff info
3. Agent swimlane showing task flow per agent

## Backend: live_status.py changes

`get_project_dashboard()` now returns three new fields:

```python
"tasks": task_list,              # Full task array with handoff_from/handoff_to
"pipeline_stages": {...},        # Tasks grouped by status
"handoff_chain": [...]           # Handoff links between agents
```

Handoff detection: scans task titles for "(接班 xxx)" pattern.

## Frontend: command_center.html changes

### CSS additions (~50 lines)
- `.pipe-status-bar` — horizontal status distribution bar
- `.pipe-columns` / `.pipe-col` / `.pipe-card` — kanban layout
- `.pipe-lane` / `.pl-head` / `.pl-body` / `.pl-card` — swimlane layout
- Status color borders: `.st-done` (green), `.st-in_progress` (blue), `.st-ready` (teal), `.st-blocked` (red), `.st-gate` (amber), `.st-todo` (grey)

### JS additions (~80 lines)
In `renderProject()`, after the health bar card:
1. Extract `pj.tasks`, `pj.pipeline_stages`, `pj.handoff_chain`
2. Render status distribution bar
3. Render kanban columns filtered to non-empty statuses
4. Render per-agent swimlane with color-coded task pills and flow arrows

## Data flow
```
Browser selects project
  → GET /api/live/project/<name>
  → live_status.py::get_project_dashboard()
    → Scans kanban.db tasks with LIKE '%project%'
    → Detects handoff_from/to patterns
    → Groups by status
    → Returns JSON with tasks + pipeline_stages + handoff_chain
  → renderProject() renders HTML
```

## Verification
```bash
# Check pipeline API response
curl -s 'http://localhost:8080/api/live/project/%E7%BE%BD%E7%90%83%E5%AE%9DAI' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('tasks',[]))); print(list(d.get('pipeline_stages',{}).keys()))"
```

## Known limitations
- Project matching is fuzzy (LIKE '%name%') — can match partial names
- Handoff detection requires "(接班 xxx)" in task title
- Swimlane colors are hardcoded for known agent names
- Status bar doesn't animate transitions — static render only
