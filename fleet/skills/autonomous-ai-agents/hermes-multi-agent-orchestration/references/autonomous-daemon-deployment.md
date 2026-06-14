# AutonomousEngine Daemon Deployment

## Dual Scheduling Architecture

Apex operates **two scheduling layers** — they are complementary, not redundant:

| Layer | Engine | What it does | Runs as |
|-------|--------|-------------|---------|
| **Hermes Cron** | Gateway-internal scheduler | External timed delivery: PM日报, 备份, WeChat notifications | Inside Gateway process |
| **Apex AutonomousEngine** | 3-thread daemon (autonomous_daemon.py) | Internal self-awareness: heartbeat collection, scheduled task dispatch, Kanban auto-dispatch | Standalone `nohup` process |

They serve different purposes:
- Cron delivers results to the user (日报, 告警, 备份)
- AutonomousEngine manages the agent fleet internally (心跳, 调度, Kanban分发)

## Daemon Startup

```bash
# Start as background daemon (survives terminal close)
nohup python3 -u ~/Desktop/2026AIAPP/Apex/apex/orchestration/autonomous_daemon.py \
  > /tmp/apex-autonomous.log 2>&1 &

# Verify it's alive
ps aux | grep autonomous_daemon | grep -v grep
cat /tmp/apex-autonomous.log
```

## Critical: Python Output Buffering

The daemon uses `print()` for heartbeat output. Without `-u` (unbuffered) flag, stdout is **fully buffered** when piped to a file — no output appears until the buffer fills (usually 8KB). Always use `python3 -u`.

The daemon also sets `sys.stdout.reconfigure(line_buffering=True)` as a fallback, but `-u` is the reliable method.

## Daemon Architecture

```
autonomous_daemon.py
    │
    ├─ ✅ Signal handling: SIGTERM/SIGINT → graceful shutdown
    ├─ ✅ Start AutonomousEngine (3 threads):
    │     💓 Heartbeat thread (30s) — collect status from all profiles
    │     📅 Scheduler thread (15s) — check scheduled_tasks, enqueue due ones
    │     📤 Dispatcher thread (10s) — pop queue, execute tasks, dispatch Kanban
    ├─ ✅ Load scheduled tasks from SQLite DB (autonomous.db)
    ├─ ✅ Print startup summary
    └─ ✅ Heartbeat logging every 5 minutes to stdout
```

## Process Isolation Gotcha

The daemon runs in its **own Python process**. When you query `get_engine()` from another process (CLI, tests), you get a **different instance** — `is_running` will be `False` in that process even though the daemon is alive. Scheduled task data persists in `autonomous.db` (SQLite), so `list_scheduled()` works across processes.

## Registered Tasks (6 standard)

```
🛡️ 健康巡检        every 30m    agent=ops-engineer
📡 项目脉搏 (2h)    every 120m   agent=apex-pm
🦅 Apex PM 晨报    0 9 * * *    agent=apex-pm
🏸 羽球宝PM日报     30 9 * * *   agent=badminton-pm
🔔 通知系统巡检      every 60m    agent=ops-engineer
🔐 授权引擎扫描      every 60m    agent=apex-pm
```

## Registering Tasks

```python
from apex.orchestration.autonomous import get_engine
e = get_engine()

e.schedule(
    name="任务名称",
    cron_expr="every 30m",   # or "0 9 * * *" or "every 2h"
    task_description="LLM-level task description",
    assigned_agent="ops-engineer",  # Hermes Profile name
    priority=2,
)
```

Tasks persist in SQLite — registered once, survive restarts.

## Killing the Daemon

```bash
pkill -f autonomous_daemon
# or find PID and:
kill <pid>
```

The daemon catches SIGTERM and gracefully exits (stops engine threads, prints uptime).
