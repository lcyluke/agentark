# Friendly Notification Pattern for Hermes Cron

## Problem

Raw `terminal()` background process failures dump into Hermes notifications with:
- Full SSH command lines including `sshpass -p 'PASSWORD'`
- Unfiltered `stderr` like `Connection closed by remote host (exit 255)`
- Repetitive noise when a service flaps (every restart attempt = a new notification)

This leaks secrets and creates hostile UX.

## Pattern: `no_agent=true` cron + health-check script

Move monitoring OUT of Hermes' process tracking. A `no_agent=true` cron job runs a Python script whose stdout becomes the notification. The script controls exactly what the user sees and when.

### Core traits of the health-check script

```python
# 1. State file — remember last status + timestamp
STATE_FILE = "/tmp/service_state"
COOLDOWN_SEC = 300  # change to adjust frequency

def load_state(): ...  # returns {"status": "up"|"down"|"unknown", "since": int}
def save_state(status): ...

# 2. should_notify — only notify on state CHANGE, with cooldown
def should_notify(status, prev_state):
    if prev_state["status"] == status:
        if (time.time() - prev_state.get("since", 0)) < COOLDOWN_SEC:
            return False  # still cooling down
    return True

# 3. main — check health, print friendly message ONLY when needed
def main():
    prev = load_state()
    ok = check_health()

    if not should_notify("up" if ok else "down", prev):
        save_state(...); return  # SILENT — no stdout → no notification

    save_state(...)
    if ok:
        if prev["status"] == "down":
            print("🟢 服务已恢复")  # recovery notification
        else:
            print("🟢 服务在线")    # initial notification only
    else:
        print("🔴 服务离线 — 正在自动重连")
```

### Cron registration

```bash
hermes cron create "every 2m" \
  --name "服务名健康监控" \
  --script myservice_health.py \
  --no-agent \
  --deliver origin
```

Use `every 2m` for frequent checks, `every 5m` for less critical services. Always use `--deliver origin` to route back to the user's current channel.

### Why `no_agent=true`

- Zero token cost — no LLM call per check
- Script controls the EXACT message text
- No risk of the LLM hallucinating status or re-interpreting error messages
- Empty stdout = silent tick = no notification noise

### Cooldown tuning

| Cooldown | Use case |
|:--|:--|
| 60s | Critical service, user wants to know fast |
| 300s | Normal service, avoid notification fatigue |
| 900s | Non-critical, only notify if long outage |
