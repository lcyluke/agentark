# Project Operations Center — PM协作引擎

Built 2026-06-03. Enables multi-agent project teams with PM oversight.

## API Endpoints (live at Apex Dashboard port 8080)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/ops/agents/workloads` | GET | Agent load tracking: active tasks, saturation%, free slots, velocity (tasks/day) |
| `/api/ops/agents/match` | POST | Match task to best agent by skill + workload. Body: `{title, description, auto_assign: bool}` |
| `/api/ops/standup` | GET | PM standup report: blockers, in-progress, completed-24h, agent standings, auto-suggestions |
| `/api/ops/knowledge/search` | GET | Search known solutions across agents. Query param: `?q=problem description` |
| `/api/ops/knowledge/record` | POST | Record a solution for cross-agent learning |

## Core Concepts

### Agent Workload Model
- Each agent has a capacity (default 5 concurrent tasks)
- Load % = active_tasks / capacity × 100
- Saturation states: idle (<30%), busy (30-70%), overloaded (>70%)
- Velocity = completed_7d / 7 (tasks per day)
- Free slots = max(0, capacity - active_tasks)

### Auto Task Assignment
1. Extract keywords from task title + description
2. Score each agent by matching keywords against AGENT_SKILLS dictionary
3. Apply workload penalty/bonus (overloaded: -20, idle: +10)
4. Return top 5 candidates with scores, recommended is #1

### PM Standup Report
Generated from Kanban DB + workload tracker:
- Summary: total agents, active tasks, completed-24h, blocked count, idle/overloaded agents
- Blockers: tasks with status='blocked'
- In Progress: tasks with status='in_progress'
- Agent Standings: per-agent load%, done-today, velocity, free slots
- Auto Suggestions: ready tasks matched to best agent

### Knowledge Sharing
- Known solutions DB (problem → solution → solved_by → tags)
- Search by keyword matching across tags and problem text
- Record new solutions to prevent repeat problems across agents

## Implementation Files
- `apex/interface/project_ops.py` — backend module (15K, 5 functions)
- `apex/interface/fleet_manager.py` — profile/team CRUD
- `apex/interface/web.py` — 10 new API endpoints registered
