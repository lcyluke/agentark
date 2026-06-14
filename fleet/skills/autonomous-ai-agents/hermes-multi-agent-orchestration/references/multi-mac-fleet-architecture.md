# Multi-Mac Hermes Fleet Architecture

**Status**: ✅ **IMPLEMENTED** as of June 2026. See `references/fleet-multi-mac-implementation.md` for code locations and setup.

## When to use
User has 3-5 Macs and wants Hermes to orchestrate across all of them with:
- One Mac as Origin (始祖) — runs cron, dashboard, authorization
- Other Macs as workers — execute tasks, each managing 1-3 projects
- Shared skills/profiles across fleet
- Independent local memory (state.db) per Mac

## Architecture

```
                    GitHub: hermes-fleet-config (private repo)
                         ↙   ↓   ↘
        ┌──────────────┬──────────────┬──────────────┐
        │   Mac-A      │   Mac-B      │   Mac-C      │
        │   始祖舰      │   执行舰      │   执行舰      │
        ├──────────────┼──────────────┼──────────────┤
        │ Cron 全部     │ 项目1-2       │ 项目3-4       │
        │ Dashboard     │ PM Agent     │ PM Agent     │
        │ 授权引擎      │              │              │
        ├──────────────┼──────────────┼──────────────┤
        │ skills (权威) │ skills (同步) │ skills (同步) │
        │ profiles(权威)│ profiles(同步)│ profiles(同步)│
        │ state.db(本地)│ state.db(本地)│ state.db(本地)│
        └──────────────┴──────────────┴──────────────┘
```

## Design Principles

1. **ONE Origin per fleet.** Origin holds cron, dashboard, authorization engine. Determined by who runs `apex fleet init-fleet`.
2. **Worker Macs pull config from Git.** `apex fleet join-fleet` clones the Origin's config repo into `~/.hermes/`.
3. **state.db is local per Mac.** Memory/context does NOT sync across Macs. Each Mac has its own conversation history.
4. **Origin transfer requires dual-approval.** New Origin runs `apex origin-request`. Current Origin runs `apex origin-approve <code>`.
5. **Projects assigned per Mac.** Each Mac typically manages 1-3 projects with a PM agent.

## Implemented Apex Fleet Commands

```bash
# On Origin Mac:
apex fleet init-fleet -n "FleetName" -r https://github.com/user/hermes-fleet-config

# On Worker Macs:
apex fleet join-fleet -r https://github.com/user/hermes-fleet-config

# Status & Discovery:
apex fleet nodes        # All nodes, roles, projects (auto-pulls from GitHub)
apex fleet sync         # Git pull config (default)
apex fleet sync --push  # Git push config (Origin only)
apex fleet report       # 📡 Report heartbeat → Worker becomes visible to Origin
apex origin-status      # Check Origin role

# Origin transfer:
apex origin-request -r "reason"
apex origin-approve <code>

# Project bootstrap:
apex project-init myapp --pm pm-agent --template webapp
```

## Node Discovery — GitHub Heartbeat Mechanism

Worker nodes report themselves via a GitHub-based heartbeat. No direct Mac-to-Mac connection needed — all communication goes through the private `hermes-fleet-config` repo.

```
Mac-B (Worker)                        Mac-A (Origin)
     │                                      │
     ├─ apex fleet report                   │
     │   ├─ git pull (get latest)          │
     │   ├─ write nodes/Mac-B.json          │
     │   ├─ git commit                      │
     │   └─ git push ─────────────────→ GitHub
     │                                      │
     │                              apex fleet nodes
     │                                ├─ git pull ← GitHub
     │                                ├─ read nodes/*.json
     │                                └─ display all nodes
```

Each node writes a JSON status file to `nodes/<machine_id>.json` containing:
- `machine_id`, `hostname`, `role`, `projects`, `profiles`, `skills`, `git_status`, `reported_at`

## Implementation

- Core module: `apex/interface/fleet_multi_mac.py` — FleetManager functions + node heartbeat
- CLI module: `apex/cli/commands/fleet_cmds.py` — fleet_init_cmd, fleet_join_cmd, fleet_sync_cmd, fleet_nodes_cmd, fleet_report_cmd
- CLI registration: `apex/cli/main.py` — `apex fleet init-fleet|join-fleet|sync|nodes|report`
- Config: `~/.hermes/fleet_config.json` — local fleet identity
- Node status: `~/.hermes/nodes/<machine_id>.json` — heartbeat files synced via git

## Pitfalls

- **`HERMES_HOME` env var override by profiles**: When running from Apex venv, `HERMES_HOME` is set to the active profile directory (e.g. `~/.hermes/profiles/cron-inspector`), NOT `~/.hermes/`. Fleet code MUST use `Path(os.path.expanduser("~/.hermes"))` explicitly — never `Path(os.environ.get("HERMES_HOME", ...))`. This broke fleet report/nodes until fixed.
- **`cfg.get('role')` returns None not default**: fleet_config.json stores `"role": null`. `dict.get('role', 'unconfigured')` returns None because the key EXISTS. Use `cfg.get('role') or 'unconfigured'`.
- **Network proxy blocks git push**: If SSH port 22 and HTTPS both fail, try fresh repo approach.
- **Origin must be unique**: Only one Mac runs cron. Worker Macs must NOT have cron jobs enabled.
- **state.db conflict**: Never git-commit state.db. In .gitignore by default.
- **Config drift**: After changing skills/profiles on Origin, run `apex fleet sync --push` on Origin then `apex fleet sync` on workers.
- **Large initial push**: First fleet-init commits ~40K files (skills + cron output). May take minutes. Subsequent syncs fast.
