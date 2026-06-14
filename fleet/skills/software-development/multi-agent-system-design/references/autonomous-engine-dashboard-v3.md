# Autonomous Engine + Dashboard V3 Implementation

Built in one session (2026-06-02) as part of Apex Phase 4.

## Files

- `apex/orchestration/autonomous.py` (769 lines) — The self-aware 7x24 engine
- `apex/cli/commands/autonomous.py` — 9 CLI commands
- `apex/interface/templates/dashboard.html` (1,314 lines) — 9-panel SPA replacement
- `apex/interface/web.py` — Added `/api/autonomous` endpoint (14th API)

## Autonomous Engine Architecture

Three background threads run continuously:

| Thread | Interval | Responsibility |
|--------|----------|---------------|
| Heartbeat | 30s | Collect agent status (healthy/degraded/stalled/offline), load 0-1, task counts |
| Scheduler | 15s | Check cron expressions against DB, enqueue due tasks in priority order |
| Dispatcher | 10s | Pop from queue, execute with retry, auto-dispatch ready Kanban tasks |

### 3-Strike Retry with Exponential Backoff

```
Attempt 1 → Wait 2s
Attempt 2 → Wait 4s
Attempt 3 → Wait 8s (max)
All fail → Record to KG + notify
```

### Self-Awareness Report

`generate_report()` returns `AutonomousReport` with:
- Engine status (running/paused/stopped)
- Uptime
- All 18+ agent heartbeats
- Scheduled tasks + queue depth
- Execution stats (total/succeeded/failed)
- Knowledge graph size + evolution patterns
- Active alerts + AI recommendations

### CLI Commands

```bash
apex autonomous start        # Start 7x24 engine
apex autonomous stop         # Stop
apex autonomous pause        # Pause dispatch (heartbeat continues)
apex autonomous resume       # Resume
apex autonomous status       # Full self-awareness report
apex autonomous schedule "name" "*/5 * * * *" "task" --agent frontend
apex autonomous list-scheduled
apex autonomous unschedule <id>
apex autonomous alerts       # View unresolved alerts
```

## Dashboard V3 — 9 Panels

1. **Stats Row** (6 animated cards): Active Agents, Total Tasks, Cost, Knowledge Nodes, Patterns, Alerts
2. **Agent Fleet** (interactive grid): Status dots, load bars, click for detail modal
3. **Task Board** (Kanban): 4 columns — Ready/In Progress/Done/Failed
4. **Knowledge Graph** (Canvas): 25 nodes, edges, confidence sizing, type coloring
5. **Token Economy** (SVG gauge): Budget arc, 7-day cost trend, model routing table
6. **Autonomous Engine** (status indicator): Heartbeat list, scheduled tasks with countdown, alert feed
7. **Execution Log** (terminal-style): Color-coded, auto-scroll, pause on hover
8. **Quality Trends** (Canvas chart): Accuracy + F1 over 20 epochs
9. **Navigation Bar**: 6 tabs, real-time clock, connection indicator

## Key Design Decisions

- **Singleton pattern** for AutonomousEngine — `get_engine()` creates once, reuses
- **Thread safety** via `threading.Lock` on task queue
- **Daemon threads** — auto-kill on main process exit
- **Knowledge Graph integration** — every failure is recorded as a learning opportunity
- **Evolution Engine integration** — every execution feeds the self-learning system
- **Colored status dots**: 🟢 healthy, 🟡 degraded, 🔴 stalled, ⚫ offline
- **Load visualization**: `██████░░░░ 60%` bars
- **Auto-refresh** every 10 seconds via `setInterval(loadAll, 10000)`
- **Falls back to synthetic data** when APIs unavailable
