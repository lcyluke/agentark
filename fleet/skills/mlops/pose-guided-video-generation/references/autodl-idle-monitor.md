# AutoDL Idle Monitor — Automatic Shutdown

## Problem

AutoDL GPU instances cost money per hour even when idle. The user manually shuts down to save cost but forgets. Need automated idle detection → notification → confirmed shutdown.

## Solution: 3-tier idle monitoring with Hermes cron

### Architecture

```
cron (every 5m, no_agent=True)
  └→ autodl_idle_monitor.py
       ├→ check_inference_alive() → HTTP health check :8765
       ├→ check_inference_busy() → lsof ESTABLISHED connections on :8765
       └→ idle timer
            ├→ idle 60 min → warn notification to WeChat
            ├→ idle 180 min → critical notification
            └→ user replies "关闭AutoDL" → SSH shutdown
```

### Detection method

`lsof -i :8765 -s TCP:ESTABLISHED` — if any ESTABLISHED connections exist on the inference port, the service is actively processing a request. No connections = idle.

### State file

`/tmp/autodl_idle_state.json`:
```json
{
  "idle_since": 1717400000,
  "last_active": 1717390000,
  "last_notify_level": "warn",
  "last_notify_time": 1717400000,
  "confirmed_shutdown": false
}
```

### Cron setup

```bash
# Created via Hermes
hermes cron create \
  --name "AutoDL 空闲监控" \
  --schedule "every 5m" \
  --script autodl_idle_monitor.py \
  --no-agent
```

### Thresholds

| Level | Idle time | Action |
|:--|:--|:--|
| silent | < 60 min | nothing |
| warn | ≥ 60 min | WeChat message: "空闲 N 分钟，回复'关闭AutoDL'" |
| critical | ≥ 180 min | WeChat message: "已空闲 N 小时，建议立即关闭" |
| cooldown | — | same level won't re-notify for 1 hour |

### Shutdown methods

1. **SSH** (works now): `sshpass ssh root@host "shutdown -h now"`
2. **AutoDL API** (requires token): `POST https://api.autodl.com/api/instance/stop`

### Important: When AutoDL is intentionally offline

If the user manually shut down the server, `check_inference_alive()` returns false → the monitor resets its idle timer and goes silent. No false alarms.

## Script location

`~/.hermes/scripts/autodl_idle_monitor.py`

## Related

- `~/.hermes/scripts/autodl_health.py` — tunnel health monitoring (status change only, 2min interval)
- `~/.hermes/scripts/autodl_tunnel.sh` — SSH tunnel daemon with exponential backoff
- `references/autodl-rest-api.md` — full AutoDL REST API reference
