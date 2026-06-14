# Multi-Mac Fleet — Implemented Architecture

**Status**: ✅ Implemented (June 2026) | **Code**: `apex/interface/fleet_multi_mac.py` (600+ lines)

## Architecture

```
GitHub: lcyluke/hermes-fleet-config (private)
     ↙              ↘
Mac-A (Origin)    Mac-B (Worker)
  ~/.hermes/       ~/.hermes/
  ├── config.yaml  ├── config.yaml  ← git pull
  ├── skills/      ├── skills/      ← git pull
  ├── profiles/    ├── profiles/    ← git pull
  ├── nodes/       ├── nodes/       ← git push
  ├── state.db 🔒  ├── state.db 🔒  ← local only
  └── cron/ ✅     └── cron/ ❌     ← origin only
```

## Code Map

| File | Lines | Purpose |
|:--|:--|:--|
| `apex/interface/fleet_multi_mac.py` | 600+ | Backend engine |
| `apex/cli/commands/fleet_cmds.py` | +250 | CLI command handlers |
| `apex/cli/main.py` | +50 | Command registration |
| `scripts/fleet-join-worker.sh` | 160 | Zero-Apex join script |

## CLI Commands

```bash
apex fleet init-fleet -n "舰队名" -r <repo>  # Origin init
apex fleet join-fleet -r <repo>               # Worker join
apex fleet report                              # Heartbeat + GPU → GitHub
apex fleet nodes                               # All nodes + GPU
apex fleet gpu-status                          # GPU resource center
apex fleet sync --pull                         # Worker pulls config
apex fleet sync --push                         # Origin pushes config
```

## GPU Monitoring (Native Integration)

GPU status is a **fleet node attribute** — NOT a standalone script.

- `fleet_status()` calls `_probe_gpu()` — nvidia-smi local probe
- `_gpu_alerts()` — dual threshold: >90% overload, <30% idle (15min warn, 30min crit)
- Worker `fleet report` → pushes node status + GPU + alerts to GitHub
- Origin `fleet nodes` → sees all GPUs across fleet

## Key Design Rules

1. **Apex is the backbone, never optional.** GPU monitoring, notifications, task sync all flow through Apex commands, not standalone scripts.
2. **`~/.hermes/` always means `Path(os.path.expanduser("~/.hermes"))`** — never `HERMES_HOME` env var (profiles override it).
3. **state.db is local per Mac** — never synced via git.
4. **`.env` is local** — preserved during join, never pushed.
5. **Worker Macs disable cron** — only Origin runs scheduled jobs.

## Pitfalls

1. **HERMES_HOME override**: In Apex venv, `HERMES_HOME` is set to the active profile dir. Fleet code MUST use `Path(os.path.expanduser("~/.hermes"))` explicitly.
2. **`cfg.get("role")` returns None, not default**: JSON stores `"role": null`. Use `cfg.get("role") or "unconfigured"`.
3. **Worker join preserves .env**: The join script backs up, copies config, then restores .env.
4. **GitHub token for API**: Use `git credential fill` to extract token when `gh auth` unavailable.
