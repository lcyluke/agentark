# Apex — Autonomous Engine Reference

> 7x24 self-aware operation for multi-agent systems

## Architecture

```
                     👑 AutonomousEngine
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     Heartbeat        Scheduler       Dispatcher
     (30s loop)       (15s check)     (10s dispatch)
            │              │              │
            ▼              ▼              ▼
      Agent Health     Cron Task       Kanban Auto-
      Monitoring       Triggering      Dispatch
            │              │              │
            ▼              ▼              ▼
     Self-Awareness   Expo-Backoff    Escalation
     Report           Retry (3x)      Notification
```

## Core Loops

| Loop | Interval | Responsibility |
|------|----------|---------------|
| Heartbeat | 30s | Collect agent health/load/tasks from all profiles. Status: healthy/degraded/stalled/offline |
| Scheduler | 15s | Check cron tasks against next_run. Enqueue ready tasks sorted by priority |
| Dispatcher | 10s | Pop queue, execute with 3-strike retry + exponential backoff. Auto-dispatches Kanban ready tasks |

## CLI Commands

```bash
apex autonomous start        # Launch 7x24 engine
apex autonomous stop         # Graceful shutdown
apex autonomous pause        # Suspend dispatch only
apex autonomous resume       # Resume dispatch
apex autonomous status       # Full self-awareness report
apex autonomous schedule "name" "*/5 * * * *" "task" --agent frontend
apex autonomous unschedule <id>
apex autonomous list-scheduled
apex autonomous alerts       # Unresolved alerts
```

## Self-Awareness Report Components

- Engine status (running/paused/stopped) + uptime
- Heartbeats: agent_name, status, load (0-1), tasks_completed, last_active
- Scheduled tasks with next_run, last_result, success rate
- Pending queue depth
- Execution stats: total/succeeded/failed
- Knowledge graph nodes + evolution patterns count
- Active alerts + AI recommendations

## 3-Strike Retry

Attempt 1 → fail → wait 2s → Attempt 2 → fail → wait 4s → Attempt 3 → fail → wait 8s → escalate

## Source

apex/orchestration/autonomous.py (~770 lines)
apex/cli/commands/autonomous.py (~250 lines)  
/api/autonomous endpoint in apex/interface/web.py
