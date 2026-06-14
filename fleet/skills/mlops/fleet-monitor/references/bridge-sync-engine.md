# Apex-Hermes Bridge Sync Engine

The bridge sync script (`scripts/bridge_sync.py` in the Apex repo) runs as a Hermes cron job (every 10min, `apex-bridge-sync`) to pull Hermes state data into the Apex Kanban DB for Dashboard display.

## Architecture

6 monitoring agents, each updating a task in `~/.apex/kanban.db`:

| Task ID | Agent | Data Source | What It Syncs |
|---------|-------|-------------|---------------|
| `watch-sessions` | session-scout | `~/.hermes/state.db` → `sessions` table | 24h session counts, token totals |
| `watch-tokens` | token-guardian | `~/.hermes/state.db` → `sessions` table | Daily/weekly token usage, model breakdown, budget alarms |
| `watch-gpu` | gpu-sentinel | `~/Desktop/2026AIAPP/monitor/logs/monitor.db` → `gpu_metrics` table | GPU utilization, memory, temperature, cost |
| `watch-profiles` | profile-syncer | `hermes profile list` subprocess | Profile names and running state |
| `watch-cron` | cron-medic | `hermes cron list` subprocess | Active/paused/error cron counts |
| `fleet-status` | fleet-commander | Aggregates 5 watch-* tasks | Fleet health summary (ok / offline / attention) |

## Execution Order (in main)

```
sync_profiles()  →  sync_cron()  →  sync_sessions()  →  sync_tokens()  →  sync_gpu()  →  sync_commander()
```
Lightweight subprocess calls first, then DB reads, then aggregation. Designed to avoid timeout under 30s.

## Pitfalls

### 1. HERMES_HOME Environment Variable Interference

**Symptom:** `state.db 不存在` even though `~/.hermes/state.db` exists.

**Cause:** Cron jobs run with `HERMES_HOME` set to the profile's subdirectory (e.g., `~/.hermes/profiles/cron-inspector`), not the root `~/.hermes/`. The script's original code used `os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))`, which picked up the env var and resolved `state.db` to `~/.hermes/profiles/cron-inspector/state.db` (which doesn't exist).

**Fix:** Always use `os.path.expanduser("~/.hermes")` for STATE_DB — never rely on the `HERMES_HOME` env var for the data DB path:
```python
HERMES_ROOT = Path(os.path.expanduser("~/.hermes"))
STATE_DB = HERMES_ROOT / "state.db"
```

### 2. upsert_task() Not Updating Title

**Symptom:** Kanban task titles show stale values (e.g., "🛡️ Cron | 5活跃/0暂停/0异常" when actual count is 0).

**Cause:** The `UPDATE` statements in `upsert_task()` only updated `output`, `status`, and `completed_at` — never `title`. The title was set on INSERT but never refreshed.

**Fix:** Add `title=?` to both UPDATE statements:
```python
# For done/failed status:
UPDATE tasks SET title=?, output=?, status=?, completed_at=? WHERE id=?
# For other statuses:
UPDATE tasks SET title=?, output=?, status=? WHERE id=?
```

### 3. Missing f-string Prefix

**Symptom:** Title shows literal `{today}今日/{total}总计` instead of `58今日/1350总计`.

**Cause:** Plain string used instead of f-string:
```python
# Wrong:
"🔍 会话侦测 | {today}今日/{total}总计"
# Correct:
f"🔍 会话侦测 | {today}今日/{total}总计"
```

### 4. GPU Data Missing (Not a Code Bug)

**Symptom:** `watch-gpu` shows "blocked" with "无GPU数据".

**Diagnosis:** `monitor.db` → `gpu_metrics` table has 0 rows. The GPU monitoring collector is not running or not writing to this table. Check:
```bash
sqlite3 ~/Desktop/2026AIAPP/monitor/logs/monitor.db "SELECT COUNT(*) FROM gpu_metrics;"
```

## Debugging

```bash
# Run manually
cd ~/Desktop/2026AIAPP/Apex && python3 scripts/bridge_sync.py

# Query kanban results
sqlite3 ~/.apex/kanban.db "SELECT id, status, title FROM tasks WHERE id LIKE 'watch-%' OR id='fleet-status';"

# Check HERMES_HOME in cron context
echo $HERMES_HOME  # If this is a profile subdir, the script was affected by Pitfall #1

# Verify data sources exist
ls -la ~/.hermes/state.db
ls -la ~/Desktop/2026AIAPP/monitor/logs/monitor.db
```

## Budget Thresholds (hardcoded in script)

- Daily: $5.00 — alarms at >80%
- Weekly: $25.00 — alarms at >100%
- Alarm triggers `in_progress` status on `watch-tokens`
