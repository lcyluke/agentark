# Mac-B Worker Join Guide

## Quick Path (Zero Dependencies)

```bash
curl -fsSL https://raw.githubusercontent.com/lcyluke/hermes-fleet-config/main/join-fleet.sh | bash
```

This single command: installs Hermes → configures API → clones fleet config → registers Worker.

## What Syncs vs What Stays Local

| Syncs (from GitHub) | Stays Local |
|:--|:--|
| `config.yaml` | `.env` (API keys) |
| `SOUL.md` | `state.db` (conversation memory) |
| `skills/` (136 skills) | `logs/` |
| `profiles/` (46 agents) | `sessions/` |

## After Join: Install Apex for Fleet Commands

```bash
cd ~/Desktop/2026AIAPP && git clone https://github.com/lcyluke/apex.git
cd Apex && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Report heartbeat + GPU
apex fleet report

# Verify Origin can see you
apex fleet nodes
```

## Worker Lifecycle

| Action | Command |
|:--|:--|
| Join fleet | `curl ... | bash` or `apex fleet join-fleet` |
| Report heartbeat | `apex fleet report` |
| Pull latest config | `apex fleet sync --pull` |
| Check fleet status | `apex fleet nodes` |
| Check GPU status | `apex fleet gpu-status` |

## Worker Constraints

- ❌ No cron jobs (only Origin runs scheduled tasks)
- ❌ No Dashboard (only Origin hosts :8080)
- ❌ No config push (`sync --push` is Origin-only)
- ✅ Pull config from Origin
- ✅ Report heartbeat + GPU to Origin
- ✅ Execute tasks with shared profiles
