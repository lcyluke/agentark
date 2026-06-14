# Apex Dashboard V5 — 7-Tab Command Center

Built 2026-06-03. Access: `http://localhost:8080/v5` (or `apex demo` to auto-launch).

## Architecture

Single-file HTML (1,493 lines) with embedded CSS+JS. Flask backend at `apex/interface/web.py`.
Data flows through `apex/interface/hermes_bridge.py` which aggregates from:
- `~/.hermes/state.db` — session tokens, costs, source/model breakdown
- `~/Desktop/2026AIAPP/monitor/logs/monitor.db` — GPU metrics, cost_log
- `hermes profile list` / `hermes cron list` — CLI output parsing
- Apex economy, kanban, profiles, autonomous engine

## 7 Tabs

| Tab | Name | Key Data | API Endpoints |
|-----|------|----------|---------------|
| 1 | 🏠 Headquarters | 6 stat cards, cost clock, GPU big status, alerts, exec log | `/api/command-center` |
| 2 | 🖥 Fleet Deployment | OS/Hostname/Python/Hermes/Apex versions, installed tools table, configured providers, model pricing, disk usage | `/api/environment`, `/api/command-center` |
| 3 | 🤖 AI Fleet | Hermes profiles (10, gateway dots), Apex profiles (23, role/model/skills), cron jobs, autonomous engine+heartbeats, evolution patterns | `/api/profiles`, `/api/command-center`, `/api/autonomous` |
| 4 | 📋 Projects HQ | 3 projects (羽球宝AI/Apex/深圳羽球地图), per-project stats, token-by-source, agent assignment matrix, budget vs actual | `/api/command-center` |
| 5 | 🗂 Task Factory | Kanban 4-column board, task detail panel, Ops bugs+releases, quality trend canvas | `/api/tasks`, `/api/ops`, `/api/evolution` |
| 6 | 🧠 Knowledge Temple | Knowledge graph canvas, type distribution, tech stack relationships, agent SKILL inventory with search/filter | `/api/knowledge`, `/api/profiles` |
| 7 | 🔐 Audit Hall | Approval queue placeholder, operations log, SSH/GPU command history placeholder | internal log |

## File Locations

| File | Purpose |
|------|---------|
| `apex/interface/templates/dashboard_v5.html` | 7-tab SPA |
| `apex/interface/templates/dashboard_v4.html` | Legacy 1-page real-data version (kept as fallback) |
| `apex/interface/templates/dashboard.html` | Original V3 synthetic-data version |
| `apex/interface/web.py` | Flask routes (`/`, `/v4`, `/v5`) |
| `apex/interface/hermes_bridge.py` | Data aggregation from Hermes + monitor + Apex |
| `apex/cli/commands/demo.py` | `apex demo` command (creates tasks, opens Dashboard) |
| `scripts/record-demo.sh` | Asciinema recorder for README GIF |

## Building a New Tab

Pattern for adding a tab:
1. Add `<div class="panel" id="tabN">` in dashboard_v5.html
2. Write `renderTabN()` function that reads from `state.*`
3. Add to `renderAllTabs()` call chain
4. Add to nav tab click handler

## Pitfalls

1. **Flask caches templates.** After any HTML edit: kill the server process + restart. Browser hard-refresh is NOT sufficient.
2. **Canvas API: no CSS variables.** Use hex (`#3b82f6`) not `var(--accent)`. CSS variables in `style=` HTML attributes are fine.
3. **`el()` helper must handle numbers.** `el('span',{},5)` → should convert to `'5'`, not throw `.forEach is not a function`.
4. **Dashboard runs on port 8080.** If port is in use, `apex demo` still outputs the URL but the server won't start. Kill the old process first.
5. **Auto-refresh is 15 seconds.** Data updates in-place; tab state is preserved across refreshes.

## Adding Data Sources

To add a new real-data API:
1. Add the SQL/CLI-reading function in `hermes_bridge.py`
2. Add a Flask route in `web.py` that calls it
3. Add the endpoint to the fetch list in dashboard_v5.html's `loadAll()`
4. Update `state.*` and the relevant render function

## Demo Flow

`apex demo` does 4 steps:
1. **Environment check**: Python/dashboard/kanban/browser status
2. **Create demo tasks**: 3 Kanban tasks (Frontend/Backend/PM) for the demo project
3. **Launch Dashboard**: Start Flask in a daemon thread on port 8080
4. **Open browser**: `webbrowser.open()` to `http://localhost:8080/v5`

Flags: `--no-browser`, `--skip-tasks`, `--port`, `--host`
