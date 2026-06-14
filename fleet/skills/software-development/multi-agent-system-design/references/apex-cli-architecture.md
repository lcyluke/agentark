# Apex CLI Architecture (v0.1.0 redesign — 2026-06-04)

## Design Principles

| Principle | Rule | Why |
|-----------|------|-----|
| **7±2 groups** | Top-level ≤ 9 command groups | Human working memory limit |
| **Verb-first** | `apex <action> <object>` | Intuitive, matches how users think |
| **Progressive discovery** | Common at top, specific nested | New users start shallow, experts go deep |
| **Consistency** | Same-domain operations under one group | Predictable tab-completion |
| **Short aliases** | High-frequency commands allow short form | Daily ergonomics |

## The CLI Tree

```
⚓ apex
│
├── init              🚀 Initialize workspace/project
├── run               ▶️  Execute a task (single or swarm)
├── chat              💬 Chat with an agent (interactive or piped)
├── dashboard         📊 Start Web Dashboard (port 8080)
├── demo              🎮 One-click demo (create fleet + open dashboard)
│
├── task              📋 Task management
│   ├── create            — Create hierarchical task (epic/story/task/subtask)
│   ├── list              — List tasks with project/assignee/type/status/phase filters
│   ├── show              — Show task with full tree
│   ├── status            — Transition task workflow status
│   ├── epic              — Show epic tree overview
│   ├── dispatch          — Auto-dispatch pending tasks by capacity
│   ├── dispatch-smart    — AI decompose requirement → create tasks → auto-assign
│   ├── capacity          — Show agent load (active/max/percentage)
│   └── schedule          — Gantt chart timeline view
│
├── team              👥 Agent team management
│   ├── create            — Create a new Agent
│   ├── list              — List all Agents
│   ├── show              — Show Agent details
│   ├── start             — Launch 5 dev agents in new Terminal windows
│   ├── status            — Dev squad readiness + methodology status
│   ├── attach            — Show detailed info for a specific squad member
│   ├── template          — Create full agent team from template (webapp/content/data/startup/research)
│   ├── sync              — Sync Apex profile → Hermes profile
│   ├── sync-all          — Sync all profiles to Hermes
│   └── hermes            — Launch Hermes with specific profile
│
├── fleet             🤖 Fleet monitoring
│   ├── status            — Fleet overview dashboard (--live for live-updating)
│   ├── show              — Detailed agent information
│   ├── refresh           — Force refresh all agent states
│   ├── history           — Recent fleet snapshot history
│   ├── inspect           — Fleet inspection (project progress + agent task status)
│   ├── monitors          — List all project monitoring agents
│   └── deploy            — One-click: create team → decompose requirement → dispatch → status
│
├── mode              🔧 Collaboration modes
│   ├── chain             — ⛓️ Sequential chain (agents handoff output)
│   ├── debate            — 🎯 Multi-agent debate (pro/con/neutral)
│   ├── supervise         — 🏛️ Hierarchical supervision (manager → workers → review)
│   └── pipeline          — 🔀 Task pipeline
│       ├── normal            — Requirement → AI decompose → dispatch → monitor
│       ├── direct             — Command → target agent → immediate execute
│       ├── status             — View pipeline status
│       └── confirm            — Approve pipeline gate to continue
│
├── project           📦 Project management
│   ├── create            — Smart project (auto-detect type/size, assign fleet)
│   ├── analyze           — Analyze project type/size, give recommendations
│   ├── list              — List all registered projects
│   └── sprint            — Start a new MVP sprint (solo/swarm)
│
├── system            ⚙️  System management
│   ├── skill             — 🧠 Skill Registry
│   │   ├── list              — List skills (--category, --agent flags)
│   │   ├── show              — Agent skill levels with evidence chain
│   │   ├── assess            — Update agent skill level (skill_name:L3)
│   │   ├── match             — Find best agent by skill matching
│   │   ├── evaluate          — Run evaluation pipeline
│   │   └── sync              — Generate SKILL.md for Hermes profile
│   ├── economy           — 💰 Token Economy
│   │   ├── status             — View economy status
│   │   └── classify           — Test task classification
│   ├── evolution         — 🧬 Skill Evolution
│   │   ├── status             — Evolution engine status
│   │   └── agent              — Agent evolution report
│   ├── knowledge         — 🧠 Knowledge Graph
│   │   ├── query              — Query with confidence/evidence/reasoning
│   │   └── stats              — Knowledge graph statistics
│   └── autonomous        — 🤖 Autonomous Engine
│       ├── status             — Full engine report
│       ├── start              — Start 7x24 mode
│       ├── stop               — Stop engine
│       ├── pause              — Pause dispatch (heartbeat continues)
│       ├── resume             — Resume dispatch
│       ├── schedule           — Schedule recurring task (cron/human-readable)
│       ├── unschedule         — Remove scheduled task
│       └── alerts             — Show unresolved alerts
│
├── help              ❓ Help system
│   ├── request           — 🆘 Request help from PM for agent
│   ├── approve           — ✅ PM approve + assign helper
│   └── list              — 📋 List help requests (--status filter)
│
├── origin            ⚓ Origin Agent (portfolio commander)
│   ├── init              — Deploy Origin Agent
│   ├── replicate         — Replicate skills to target agent(s)
│   ├── overview          — All portfolios status
│   └── portfolio         — 📊 Multi-project management
│       ├── list              — List portfolios
│       ├── create            — Create portfolio (--pm, --goal, --outcome)
│       └── status            — Portfolio milestones + tasks
│
└── integrate         🔗 Integrations
    ├── hermes            — 🤖 Hermes Integration
    │   └── profiles          — List all Hermes profiles
    ├── bridge            — 🌉 Apex-Hermes Bridge
    │   ├── init              — Create/update 6 bridge agents
    │   ├── sync              — Sync cycle (Kanban ← state.db)
    │   ├── status            — Bridge fleet health
    │   └── agents            — List 6 monitoring agents
    ├── router            — 🗺️ Smart Router
    │   └── route             — Route task to best-matching agent
    ├── monitor           — 👁️ Reactive Monitor
    │   └── check             — Run single monitor check (file/url/pattern)
    └── company           — 🏢 One-Click Company
        ├── create             — Create AI company by industry
        ├── start              — Start company executing a goal
        └── list               — List all companies
```

## Quick Reference (Daily Use)

```bash
# 1st time use
apex init my-project
apex team template webapp
apex team start

# Daily
apex task dispatch "add login"     # decompose + assign
apex task schedule                  # Gantt chart
apex fleet status                   # fleet dashboard
apex chat frontend-dev              # talk to agent
apex mode pipeline normal "需求"    # full pipeline flow

# Collaboration modes
apex mode chain "develop auth" -p dev        # sequential
apex mode supervise "refactor payment" -w 3  # hierarchical
apex mode debate "microservices vs monolith" # debate

# System management
apex system skill list
apex system economy status
apex system autonomous start

# Global
apex origin overview
apex demo
```

## CLI Refactoring Pattern

### Why refactor from flat to hierarchical

**Before (36 flat commands):** `autonomous`, `bridge`, `capacity`, `chain`, `chat`, `company`, `crew`, `dashboard`, `debate`, `demo`, `dispatch`, `dispatch-smart`, `economy`, `evolution`, `fleet`, `help-request`, `help-approve`, `help-list`, `hermes`, `init`, `knowledge`, `monitor`, `ops`, `origin`, `pipeline`, `project`, `router`, `run`, `schedule`, `skill`, `sprint`, `squad`, `status`, `supervisor`, `task`, `team`, `template`

Pain points:
- Flat list forces user to read all 36 to find the one they want
- Overlapping concepts: `fleet`/`squad`, `dispatch`/`dispatch-smart`, `team`/`template`
- Missing discovery: no "what should I run first" guidance
- Inconsistent depth: some domains 1-deep, others flat at root

**After (17 top-level → ~80 total commands in 9 groups):**

Pain points resolved:
- 7±2 visible at top, 80+ commands discoverable via tab-completion
- Merged overlaps: squad→team, dispatch-smart→task dispatch, template→team template
- Top 5 most-used at root level (init/run/chat/dashboard/demo)
- Consistent nesting depth: 2-3 levels, never 4+

### Implementation approach

1. **Create wrapper modules** (`mode_cmds.py`, `system_cmds.py`, `help_cmds.py`) that delegate to existing command implementations
2. **Register new groups in main.py** — `@cli.group()` then `@group.command(name="sub")`
3. **Hide old commands** with `@cli.command(hidden=True)` so `--help` stays clean
4. **Add deprecation notices** on old commands that point users to new path
5. Old commands remain fully functional — zero breaking change

### Key implementation details

```python
# main.py pattern for hierarchical groups

# Group definition
@cli.group()
def task():
    """📋 Task Management — create, dispatch, schedule, track progress"""

# Subcommand delegates to existing implementation
@task.command(name="dispatch-smart")
@click.argument("requirement")
@click.option("--project", "-p", default="finopsai", help="Project key")
def task_dispatch_smart(requirement: str, project: str):
    """🧠 Smart dispatch: requirement → AI decompose → create tasks → auto-assign"""
    task_cmds.dispatch_smart_cmd(requirement, project)

# Old flat command hidden with deprecation
@cli.command(hidden=True)
def dispatch():
    """[DEPRECATED] Use: apex task dispatch"""
    console.print("[dim]⚠️  deprecated — use [cyan]apex task dispatch[/] instead[/]")
    task_cmds.dispatch_cmd()
```

### Best practices

1. **Group by user mental model, not implementation module.** `mode` groups chain/debate/supervise/pipeline even though they're in `orchestration/chain.py`, `orchestration/debate.py` etc.
2. **Icon + emoji per group for visual scanning.** Each group gets an emoji prefix (`📋`, `👥`, `🤖`) visible in `--help`.
3. **3-level max.** `apex system skill list` is the max depth. Never `apex a b c d`.
4. **Keep old aliases for 1 release cycle** before removing deprecated commands.
5. **Group subcommands by frequency.** Most-used first in `--help` output (Click shows in definition order).

## CLI vs Dashboard boundary

| Concern | CLI | Dashboard |
|---------|-----|-----------|
| One-off task execution | `apex run "task"` | — |
| Interactive chat | `apex chat <agent>` | — |
| Status checks | `apex fleet status` | Real-time dashboard |
| Deep configuration | `apex system economy status` | Charts + trends |
| Project setup | `apex project create` | — |
| Debugging | `apex mode chain "debug" -p dev` | Trace browser |
| Monitoring | `apex system autonomous status` | Always-on dashboard |
