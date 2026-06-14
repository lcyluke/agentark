---
name: fleet-monitor
description: "Fleet Monitor — real-time agent status dashboard for Apex. Shows WORKING/IDLE/WAITING/STOPPED states, skill levels, tasks, and evidence per agent. Live-updating terminal UI."
version: 2.1.0
author: Origin Agent
---

# Fleet Monitor — Agent Status Dashboard

## Commands

| Command | Purpose |
|---------|---------|
| `apex fleet status` | Fleet overview (58 agents) |
| `apex fleet status --live` | Live-updating dashboard |
| `apex fleet show <agent>` | Agent detail: skills, tasks, stats |
| `apex fleet refresh` | Force-refresh all agent states |
| `apex fleet history` | Timeline of fleet snapshots |
| `apex fleet inspect` | ⚓ Full fleet inspection: project progress + agent workload |
| `apex fleet inspect -p <proj>` | Single-project inspection (auto-matches PM) |

## States

| Emoji | State | Condition |
|-------|-------|-----------|
| 🟢 | WORKING | Active tasks in progress |
| ⚪ | IDLE | No tasks, available |
| 🟡 | WAITING | Has tasks but stalled or long idle |
| 🔴 | STOPPED | No profile, no heartbeat, >24h inactive |

## State Detection Logic

`FleetMonitor._build_status()` checks in order:
1. **Profile existence** — Apex profile, Hermes profile dir, CLI wrapper
2. **Role extraction** — From Apex profile SOUL or SOUL.md first-line header
3. **Skills** — From SkillRegistry: counts, levels, evidence
4. **Work data** — From TaskManager: active tasks, completed/failed counts
5. **Heartbeats** — From AutonomousEngine (if available)
6. **State determination** — Active tasks→WORKING. Tasks stalled>2h→WAITING. No profile + no heartbeat + >24h→STOPPED. Else IDLE.

## Detecting Running Processes

```bash
pgrep -f "hermes -p <agent-name>"
```

## Squad Commands (Dev Agent Group)

| Command | Purpose |
|---------|---------|
| `apex squad status` | 11-Agent table with colored columns, aligned SQUARE borders |
| `apex squad start` | Launch all 11 in new Terminal windows (macOS) |
| `apex squad attach <name>` | Detailed skill/methodology status |

### Squad Status Display Requirements
- Use `Rich Table(box=box.SQUARE)` with aligned borders
- Emoji + full agent name (column width 22 chars)
- Color-coded agent names per role
- State: `● 在线` (green) / `○ 待启动` (dim)
- Short command names (`vuln-scan chat`, not full name)
- Methodology chain as single compact line above table
- Header row: bold cyan
- **Pitfall:** `show_lines=True` or `max_width` causes columns to disappear on narrow terminals. Use fixed `width` columns.

## Fleet Deploy — One-Shot Team Deployment

| Command | Purpose |
|---------|---------|
| `apex fleet deploy <requirement> -p <project> -t <template>` | Build team → decompose requirement → create tasks → agent status overview |
| Options | `--auto/--manual` (default auto), `--mode pipeline/chain/supervisor`, `--template webapp/content/data/startup/research` |

### Deploy Flow (4 steps)

```
Step 1/4: Team check → create from template if missing
Step 2/4: AI decomposition → Epic + Task list generation
Step 3/4: Task creation + smart dispatch → skill-matched agent assignment
Step 4/4: Fleet readiness check → agent status table output
```

Output: Task breakdown table (#/title/assignee/hours/priority) + Fleet status table (badge/agent/state/skills/level/completed) + execution recommendations.

**Pitfall:** `fleet deploy` calls `apex team template <name>` via subprocess — the team template must exist in `TEAM_TEMPLATES` in `apex/interface/hermes_sync.py`.

**Pitfall:** The deploy command imports `decompose_requirement` and `dispatch_tasks` from `apex/orchestration/task_decomposer`. These call an LLM to decompose the requirement text — ensure the DeepSeek provider is configured and has API quota.

**Pitfall:** Team template by name (e.g. `webapp`) creates 4 agents with Hermes profiles and wrapper scripts. Templates are defined as dicts in `hermes_sync.py`, not in a config file.

## Schedule View — Gantt Chart Task Timeline

| Command | Purpose |
|---------|---------|
| `apex schedule view [task_id] -p <project>` | Gantt chart: task bars by priority, colored by status, "today" marker |
| `apex schedule list -p <project>` | Flat/epic-rolled-up task list with subtotal hours |

### Gantt Chart Rendering

- Rendered as a Rich Table with a "Timeline" column containing status-colored bars
- Bar fills per status: `█`=in_progress, `▓`=done, `░`=blocked, `━`=assigned, `─`=approved
- Tasks sorted by priority (urgent first), then estimated hours
- Daily marker header with `▼` today indicator
- Legend printed below the chart
- Epics shown as bold headers with their children indented, plus subtotal hours
- Timeline width auto-scaled to task range (min 10 days, padded to ±5 if range is small)

### Status Color Map

| Status | Color | Bar |
|--------|-------|-----|
| IN_PROGRESS | yellow | █ |
| COMPLETED/VERIFIED/CLOSED | green | ▓ |
| BLOCKED/REJECTED | red | ░ |
| APPROVED/ASSIGNED | cyan/blue | ━/━ |
| PM_REVIEW/PM_VERIFY | bright_yellow | ▒ |

### Gantt Data Model

Tasks come from `TaskManager.list_tasks()`. Bar position is calculated from:
- `started_at` / `completed_at` timestamps if available (actual dates)
- `estimated_hours / 8` = duration_days if no started_at
- `priority` offset (0=urgent → left, 3=low → right) if not started yet

### Dependencies

Tasks with `depends_on` show `→short-task-id` appended to their name in the Gantt.

## Key Files

| File | Purpose |
|------|---------|
| `apex/interface/agent_monitor.py` | FleetMonitor core (AgentStatus, state detection) |
| `apex/cli/commands/fleet_cmds.py` | Fleet dashboard CLI + deploy_cmd |
| `apex/cli/commands/squad_cmds.py` | Squad launch/status/attach commands |
| `apex/cli/commands/schedule_cmds.py` | Gantt chart view + flat/epic list |
| `apex/orchestration/task_decomposer.py` | AI requirement decomposition |
| `apex/orchestration/task_manager.py` | Task hierarchy + auto-dispatch |

## Cost Tracking

Dashboard: **http://localhost:8080/cost** — 实时成本控制中心，4 个 Tab:

| Tab | 内容 |
|:--|:--|
| 📋 定时任务成本 | 16个Cron按token/cost排行 |
| 🤖 Agent成本 | 按Profile+来源渠道分解 |
| 📦 项目成本 | 项目预算使用率+交互/Cron分拆 |
| 📈 趋势 | 7天柱状图+折线图 |

### API 端点

| 端点 | 说明 |
|:--|:--|
| `GET /api/cost/summary` | 总览（今日/本周/30天/累计） |
| `GET /api/cost/cron?days=30` | 每Cron任务token+成本明细 |
| `GET /api/cost/agents?days=30` | 每Agent Profile成本分解 |
| `GET /api/cost/sources` | 按weixin/cli/cron/webui渠道 |
| `GET /api/cost/projects` | 按项目聚合（羽球宝/Apex/FinOps/深圳） |
| `GET /api/cost/timeline?granularity=daily` | 趋势数据 |
| `GET /api/cost/full` | 完整快照（Dashboard数据源） |

### 成本数据源

从 Hermes `state.db` sessions 表读取 — session ID 格式 `cron_<job_id>_<date>_<time>`，
与 `hermes cron list` 输出交叉关联得到 cron 名称。

### 代码位置

| 文件 | 说明 |
|:--|:--|
| `apex/cost_tracker.py` | 成本追踪引擎 |
| `apex/interface/templates/cost_center.html` | Dashboard视图 |
| `apex/interface/web.py` | +7个API端点 + `/cost` 路由 |

## Cron

- `fleet-status-collector` (every 15min): Captures snapshot, reports state changes
- `apex-bridge-sync` (every 10min): Bridge Hermes→Apex data sync (reduced from 5min, saved $2.13/mo). See `references/bridge-sync-engine.md` for architecture, pitfalls, and debugging.
- Cron-inspector profile: lightweight profile for monitoring cron jobs, saves ~70% token cost per run

## Reference Files

| File | Contents |
|------|----------|
| `references/bridge-sync-engine.md` | Bridge sync architecture, 6 monitoring agents, 3 common pitfalls + fixes, debugging commands |
| `references/fleet-deploy-and-schedule-workflow.md` | fleet deploy + schedule view/list workflow, pipeline modes, common pitfalls |
| `references/dev-agent-methodology-summary.md` | Superpowers 7-skill chain, Iron Laws, 1% Rule, bootstrap injection |
| `references/new-agent-profile-workflow.md` | Step-by-step for creating a new Hermes agent profile |
