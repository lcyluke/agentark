# Live Status & Project Operations — Real-time Hermes Sync

Built June 2026 to bridge Hermes runtime state into Apex Dashboard for real-time agent monitoring and project management.

## Module: `apex/interface/live_status.py`

Four APIs powering the Command Center's real-time features:

### `GET /api/live/runtime`
Real-time Hermes process and session tracking:
- Reads `state.db` for active sessions (not ended) with model, tokens, runtime_min
- Runs `ps aux` to find running `hermes` CLI processes (excludes gateway/lsp/webui)
- Returns: `{active_sessions, running_processes, processes: [{pid, cpu, mem, command}], sessions: [{source, model, tokens, cost, runtime_min}], by_source: [{source, count}]}`

### `GET /api/live/projects`
Auto-discovers projects from Kanban task titles:
- Parses `[ProjectName]` prefix from task titles
- Also reads `fleet_teams.json` for team-backed projects
- Returns: `[{name, task_count, has_team}]`

### `GET /api/live/project/<name>`
Comprehensive per-project dashboard:
- Task status breakdown (done/in_progress/ready/blocked/todo)
- Per-agent stats: load_pct, saturation (idle/busy/overloaded), task count by status
- Project health score (done/total %)
- Blockers list with priorities
- Ready-to-assign tasks
- Standup section: completions in last 24h with agent+task details

### `GET /api/live/standup/<task_id>`
Triggered when a task completes:
- Who completed, what project, remaining tasks
- Agent's current workload after completion
- Who is available to take new tasks

## Integration Pattern: Command Center Pulse

The Command Center's top bar pulse indicator and sidebar crew list read from `/api/live/runtime`:

```javascript
// Every 15 seconds
fetch('/api/live/runtime')
  .then(r => r.json())
  .then(data => {
    // Update pulse: "124 会话 · 9 进程"
    pulseTxt.textContent = `${data.active_sessions} 会话 · ${data.running_processes} 进程`;
    // Update sidebar crew: 6 most recent active sessions
    renderCrew(data.sessions.slice(0, 6));
  });
```

This replaces static data with live Hermes process tracking.

## Project View Pattern

When a user selects a project from the dropdown:

```javascript
// Dropdown populated from /api/live/projects
// On selection:
fetch(`/api/live/project/${selectedProject}`)
  .then(r => r.json())
  .then(data => {
    // Render health bar, agent workload cards, blockers, standup
    renderProject(data);
  });
```

Each agent workload card shows: agent name, saturation label (color-coded), load_pct bar, task breakdown (done ✓ / in_progress ⟳ / ready ○ / blocked ⊘).

## Data Sources

| API | Primary Data | Fallback |
|---|---|---|
| `/api/live/runtime` | Hermes state.db + ps aux | Static placeholder |
| `/api/live/projects` | Kanban task titles + fleet_teams.json | Empty array |
| `/api/live/project/<name>` | Kanban filtered by title LIKE `%[name]%` | Empty project |
| `/api/live/standup/<id>` | Kanban single task lookup + agent workload | Error message |
