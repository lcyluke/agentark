# Project Registry + Agent Capability Profiles (June 2026)

## Architecture

Two new modules extend the Command Center with formal project management:

### 1. Project Registry (`apex/interface/project_registry.py`)

Manages project lifecycle through approval gating:

```
propose_project() → status="proposed"
    ↓
approve_project() → status="approved" (by 始祖Agent·小卢)
    ↓
add_project_module() → add module with sub-functions
    ↓
add_sub_function() → assign agent + track task progress
```

**Key endpoints:**
- `GET /api/projects/approved` — only approved projects appear in Command Center dropdown
- `GET /api/projects/<name>` — full detail: goal, modules, sub-functions, agent assignments
- `POST /api/projects/propose` — create project proposal
- `POST /api/projects/approve` — 始祖Agent approval (sets approved_by field)
- `POST /api/projects/module` — add module
- `POST /api/projects/subfunction` — add sub-function with agent assignment

**Data stored in `~/.apex/projects_registry.json`:**
```json
{
  "projects": {
    "羽球宝AI": {
      "name": "羽球宝AI",
      "goal": "...",
      "status": "approved",
      "approved_by": "始祖Agent·小卢",
      "modules": [{
        "name": "用户端小程序",
        "description": "...",
        "sub_functions": [{
          "name": "评估页面",
          "description": "...",
          "assigned_agent": "羽球宝AI_frontend"
        }]
      }]
    }
  },
  "agent_profiles": {}
}
```

### 2. Agent Capability Profiles

`get_agent_profile(agent_id)` returns comprehensive agent dossier:

```json
{
  "agent_id": "羽球宝AI_frontend",
  "role": "前端开发工程师",
  "level": 5,
  "skills": ["wechat-miniprogram", "react", "ui-ux", "responsive"],
  "completed_projects": ["羽球宝AI"],
  "active_projects": ["羽球宝AI"],
  "task_queue": [{title, status, priority}],
  "task_queue_count": 2,
  "model_comparison": {
    "deepseek-v4-pro": {
      "scores": {"coding": 9, "reasoning": 9, "speed": 8, "cost_efficiency": 7},
      "best_for": ["架构设计", "复杂推理", "代码审查"]
    },
    "claude-sonnet-4": {
      "scores": {"coding": 10, "reasoning": 10, "speed": 7, "cost_efficiency": 3},
      "best_for": ["系统设计", "安全审计", "关键决策"]
    }
  }
}
```

### 3. Live Status Bridge (`apex/interface/live_status.py`)

Real-time Hermes session tracking:

- `GET /api/live/runtime` — active sessions, running processes, per-source breakdown
- `GET /api/live/projects` — auto-discovered projects from Kanban task titles
- `GET /api/live/project/<name>` — per-project dashboard: health%, agent workloads, blockers, standup
- `GET /api/live/standup/<task_id>` — task completion standup with suggestions

**Runtime data sources:**
- `~/.hermes/state.db` sessions table (active = ended_at IS NULL)
- `ps aux` for running Hermes CLI processes
- `~/.apex/kanban.db` for task aggregation by project

## Command Center Integration

The `/cc` view uses these APIs in the 项目作战室 view:

1. Project dropdown: `GET /api/projects/approved` → only 始祖Agent-approved projects
2. Project detail: `GET /api/projects/<name>` → goal banner + module grid + sub-function list with agent progress
3. Agent drawer: `GET /api/agents/<agent_id>` → skills, projects, task queue, model comparison bars
4. Top bar pulse: `GET /api/live/runtime` → "N 会话 · M 进程" live counter

## Agent Skill Registry

Hardcoded in `project_registry.py` as `AGENT_SKILLS_DB` — maps agent_id to role, skills list, and level (1-5). Used for:
- Agent capability profiling
- Auto task assignment (skill-matching)
- Model comparison recommendations

## Model Comparison Reference

When displaying model comparison in the Agent drawer, use 4 dimensions:
| Dimension | Color | Meaning |
|-----------|-------|---------|
| Coding | --teal | Code quality and generation ability |
| Reasoning | --violet | Complex logic and architecture |
| Speed | --blue | Response time and throughput |
| Cost Efficiency | --amber | Tokens-per-dollar value |
