---
name: hermes-multi-agent-orchestration
description: "Set up and manage a multi-agent team using Hermes Profiles + Kanban + SOUL.md personas. Covers profile creation, soul injection, Kanban board init, task dispatch, and multi-profile coordination for parallel workstreams."
version: 1.3.0
author: Luke & 小卢
platforms: [macos, linux]
---

# Hermes Multi-Agent Orchestration

Orchestrate a team of AI agents using Hermes's built-in Profile system, Kanban board, and SOUL.md personality files. Each agent is a fully independent Hermes instance with its own config, memory, skills, and tool access — all coordinated by a central orchestrator (you).

## When to use

- User has a complex multi-domain project (e.g. product dev + content + operations + fundraising)
- User wants specialized agents handling different professions in parallel
- User wants a "CEO + project manager + team" dynamic rather than one agent doing everything
- User explicitly asks for an "AI team" or "fleet" or "multi-agent setup"

## Layered Architecture: Hermes Profile vs CrewAI Agent (Critical Design Decision)

Hermes Profiles and CrewAI Agents are NOT the same layer — they are complementary. Understanding this avoids conflict and overhead.

| Dimension | Hermes Profile | CrewAI Agent |
|-----------|---------------|-------------|
| Level | Macro — a full independent AI instance | Micro — a role within one Crew session |
| Persistence | ✅ Permanent (own DB, Memory, Skills, session history) | ❌ Ephemeral (created per Crew run, destroyed after) |
| Isolation | Complete isolation — profiles don't share context | Shared within a Crew — agents talk to each other |
| Configuration | Independent model / API key / toolset per profile | Unified model for the Crew; agent only has role/goal/backstory |
| Startup | `frontend-dev chat -q "task"` | Python code `Crew().kickoff()` |
| Complexity | Medium | Lightweight |

### Correct Layering: 3-Tier Multi-Agent Architecture

```
                    👑 Human CEO (the user)
                         │
              ┌──────────┴──────────┐
              │  Tier 1: Hermes     │ ← orchestrator (you / the default session)
              │  Orchestration       │   Kanban dispatch, delegate_task, cross-crew coordination
              │  (Kanban/Delegate)   │
              └──────────┬──────────┘
                         │
     ┌───────────────────┼────────────────────┐
     │                   │                    │
  frontend-dev       ai-vision           ops-engineer
  Profile            Profile              Profile
  (Tier 2)           (Tier 2)             (Tier 2)
  │                   │                    │
  └── Crew ──┐    └── Crew ──┐        └── Crew ──┐
  Senior Dev │    Vision Eng │        Deploy Eng  │
  Code Review│    DataLabeler│        Monitor Eng │
  QA Tester  │    Model Valid│        Alert Handler│
  Tier 3     │    Tier 3     │        Tier 3      │
```

| Tier | System | Responsibility | Persistence |
|------|--------|---------------|-------------|
| **Tier 1 — Orchestrator** | Hermes default session (you) | Kanban dispatch, delegate_task, cross-profile coordination, result synthesis | Permanent |
| **Tier 2 — Profiles** | Hermes Profile (e.g. `frontend-dev`) | Owns a professional domain. Independent model/config/tools/skills. Receives tasks from orchestrator. | Permanent (one per domain) |
| **Tier 3 — Crew** | CrewAI (nested inside a Profile) | Temporary collaboration team for a specific task. Autonomous agents talk to each other. | Ephemeral (task-scoped) |

### Key Design Rules for Luke's Setup

1. **Profile = professional domain, NOT project.** A Profile like `frontend-dev` serves ALL projects (badminton app + shenzhen map), not one project. Cross-project competence reuse.
2. **SOUL.md (Tier 2) vs CrewAI role (Tier 3) are two levels of identity.** SOUL.md says "I am a Frontend Developer who prefers React+TS". The CrewAI role says "In this specific task I am the Code Reviewer". They complement, not conflict.
3. **Phase in CrewAI only when needed.** For Luke's 5h/week side-project scale, Hermes-native tools (delegate_task, Kanban Swarm, Sprint Pipeline, 33 existing Profiles) cover most scenarios without CrewAI overhead. Add CrewAI when a single task needs multiple agents talking to each other simultaneously.
4. **Always start without CrewAI.** The question "does this task need multiple agents collaborating in real time?" is the gating factor. If no, use Hermes native. If yes, add CrewAI.
5. **🔴 Apex is the backbone, NEVER optional.** When building fleet features (GPU monitoring, task sync, node discovery, notifications), integrate them into Apex's native command structure and data flow. Do NOT create standalone scripts that bypass Apex and make it "optional to install." The fleet architecture exists in Apex — every cross-machine capability flows through `apex fleet <command>` → GitHub → the other machine. GPU monitoring is `fleet_status()` → `nodes/<id>.json` → `git push`. Task sync is Kanban → `fleet sync`. This is how the user corrected the GB10 GPU monitor design — the standalone `gb10_gpu_monitor.py` was wrong; the integration into `fleet_multi_mac.py` with `apex fleet gpu-status` was right.

## Architecture

```
                    👑 CEO / Product Owner (human)
                          │
              ┌───────────┴───────────┐
              │     Orchestrator      │
              │  (your/hermes session) │
              └───────────┬───────────┘
                          │
    ┌─────────┬─────────┬┴┬─────────┬──────────┐
    │         │         │ │         │          │
  💻开发线    🤖AI线    │ 📢商业线  🔒合规线   💰资本线
 Frontend    Vision    Content    Security   Fundraising
 Ops         Algorithm Marketing  Legal      Pitch/Deck
```

## Step 0 — Discover Available Profiles (Hermes & Apex)

Two systems manage profiles — always check both:

```bash
# Hermes profiles (chat-runtime layer)
hermes profile list

# Apex profiles (orchestration + team template layer)
cd ~/Desktop/2026AIAPP/Apex && source .venv/bin/activate
apex team template list
```

Sample Hermes output:
```
Profile          Model                        Gateway      Alias
───────────────    ───────────────────────────    ───────────    ──────────────
◆default         deepseek-v4-pro              running      —
 ai-algorithm    deepseek-v4-pro              stopped      ai-algorithm
 ai-vision       deepseek-v4-pro              stopped      ai-vision
 architect       deepseek-v4-pro              stopped      architect
 frontend-dev    deepseek-v4-pro              stopped      frontend-dev
 ops-engineer    deepseek-v4-pro              stopped      ops-engineer
```

Sample Apex template output:
```
Template  Name                   Roles
webapp    Web Application Team    product-manager, frontend-dev, backend-dev, devops
content   Content Creation Team   content-strategist, writer, editor, publisher
data      Data Pipeline Team      data-engineer, data-analyst, data-scientist, ml-engineer
startup   Startup MVP Team        ceo-pm, fullstack-dev, designer, growth-marketer
research  Research Team           lead-researcher, research-analyst, technical-writer, peer-reviewer
```

To see a profile's full identity definition (Hermes SOUL.md):

```bash
cat ~/.hermes/profiles/<name>/SOUL.md
```

To see what model it would use:

```bash
hermes profile show <name>
```

### Key observation: profiles have SOUL.md but NO config

The `hermes profile create` command creates a SOUL.md (personality) but does NOT create `config.yaml` or `.env`. Every profile needs both before it can do any work. **Use Apex team template instead** — it creates all config + SOUL.md + wrapper scripts in one command.

---

## 🚀 FAST PATH: Apex Team Template (One-Command Project Start)

For Luke's workflow, the fastest way to launch a multi-agent team is through Apex. This is the **preferred workflow** — bypasses manual profile creation entirely.

### 1. Choose a template

```bash
cd ~/Desktop/2026AIAPP/Apex && source .venv/bin/activate
apex team template list
```

### 2. Create the team (one shot — 4 agents with SOUL + config + wrappers)

```bash
apex team template webapp
```

This single command:
- Creates 4 Apex profiles (product-manager, frontend-dev, backend-dev, devops)
- Writes SOUL.md for each (role identity, expertise, personality, skills)
- Generates config.yaml (inherits deepseek-v4-pro model config)
- Creates wrapper scripts at `~/.local/bin/<name>` (e.g. `frontend-dev` → runs `hermes -p frontend-dev chat`)
- Syncs everything to Hermes profile directory `~/.hermes/profiles/<name>/`

### 3. Open N terminals, run each agent

```bash
# Terminal 1 — PM
product-manager chat
# → Hermes starts, terminal title shows "📋 Product Manager"
# → System prompt = SOUL.md (PM identity)

# Terminal 2 — Frontend Developer
frontend-dev chat
# → "💻 Frontend Developer"

# Terminal 3 — Backend Developer
backend-dev chat
# → "⚙️ Backend Developer"

# Terminal 4 — DevOps
devops chat
# → "🔧 DevOps Engineer"
```

Each terminal shows the agent's role name (not "Hermes") because the SOUL.md defines the persona.

### 4. PM creates tasks with hierarchy

```bash
# In the PM terminal:
apex task create "Build User Dashboard v2" --type epic --project webapp --hours 80

apex task create "Frontend: Dashboard UI" --type story \
  --parent <EPIC_ID> --assignee frontend-dev --hours 24

apex task create "Backend: Dashboard API" --type story \
  --parent <EPIC_ID> --assignee backend-dev --hours 16

# Decompose further
apex task create "Header component" --type task \
  --parent <STORY_ID> --assignee frontend-dev --hours 6

# View full tree with progress
apex task epic "Build User Dashboard v2"
# → 🏗️ Build User Dashboard v2 [in_progress] ████░░░░░░ 40%
#    ├─ 📖 Frontend: Dashboard UI [in_progress] ██████░░░░ 60%
#    │  ├─ 📋 Header component ✅ completed
#    │  └─ 📋 Chart widgets 🔄 in_progress
#    └─ 📖 Backend: Dashboard API [pending] ░░░░░░░░░░ 0%
```

### 5. Cross-agent help request flow

When one agent needs another's help (PM must approve):

```bash
# Frontend needs backend API
apex help-request backend-dev "Need /api/charts endpoint" --task <TASK_ID>

# PM sees request, approves, assigns
apex help-approve <REQUEST_ID> --agent backend-dev

# Backend works on it, completes, task auto-updates
```

### 6. Capacity-aware dispatch

```bash
# See who's overloaded
apex capacity
# → Agent               Load    Active   Total
# → product-manager     ████░░  2/5     8
# → frontend-dev        ██████  3/5     12
# → backend-dev         ██░░░░  1/5     6
# → devops              ░░░░░░  0/5     3

# Auto-assign task to least-loaded
apex dispatch "Fix login bug" --hours 4
# → Dispatched to backend-dev (least loaded)
```

---

## LEGACY PATH: Manual Hermes Profile Creation (fallback when Apex is unavailable)

Only use these manual steps if Apex is not available; otherwise prefer `apex team template`.

### Manual Step 1 — Create a Profile (if needed)

```bash
hermes profile create <name>
```

This creates:
- `~/.hermes/profiles/<name>/` — profile home directory
- A CLI wrapper at `~/.local/bin/<name>` — run like `frontend-dev chat`
- 89 bundled skills synced automatically

### Manual Step 2 — Inject SOUL.md (personality)

Each profile gets a `SOUL.md` that defines its identity, personality, tech stack, core skills, and working principles.

**Minimal SOUL.md template:**

```markdown
# 👤 Role Name — Brief Description

## Identity
Who this agent is and what department they belong to.

## Personality
3-4 traits that define how they communicate and work.

## Tech Stack
Languages, frameworks, tools this agent uses.

## Core Skills
1. Concrete skill one
2. Concrete skill two
3. Concrete skill three

## Working Principles
1. First principle
2. Second principle
```

Write it to `~/.hermes/profiles/<name>/SOUL.md` with `write_file`.

### Manual Step 3 — Initialize Kanban Board

```bash
hermes kanban init
```

This creates `~/.hermes/kanban.db` — the shared task queue.

### Manual Step 4 — Dispatch Tasks via Kanban

```bash
hermes kanban create "Build X feature" --assignee frontend-dev --description "..."
hermes kanban create "Design Y algorithm" --assignee ai-vision --description "..."
```

### Manual Step 5 — Run Agents in Background

```bash
terminal(command="frontend-dev chat -q 'Build the checkin timeline page'", background=true, notify_on_complete=true)
terminal(command="ai-vision chat -q 'Design photo recognition pipeline'", background=true, notify_on_complete=true)
```

## Apex — The Multi-Agent Operating System (Active Production Alternative)

**Apex** (`~/Desktop/2026AIAPP/Apex/`) is now the production multi-agent OS. It has **replaced** Hermes-native multi-agent orchestration as the primary tool for complex multi-agent workloads.

### Status (as of June 2026)

- **Phase 0-6 all complete**: Runtime, Swarm, Crew, 5 Templates, Token Economy, Knowledge Graph, Evolution Engine, One-Click Company, MCP Hub, Self-Healing, Web Dashboard V5, Autonomous Engine 7x24, Message Router v2, Authorization Engine v3 (delegation + dual-approval + audit-guardian), **Sprint Pipeline (MVP闭环)**.
- **Fleet**: **33 Hermes Profiles** + **27 Apex YAML agents** (dual-registered), all on deepseek-v4-pro.
- **Fleet architecture**: 🧭监控层6 + 📋PM层5 + 💻开发6 + 🤖AI2 + 🔒安全5 + ✍️内容商业5 + 🔬质量2 + 🏗️项目模板5.
- **Sprint Pipeline**: 5-phase MVP closed-loop (PLAN→BUILD→VERIFY→SHIP→LEARN), 2 manual gates, solo/swarm modes. CLI: `apex sprint create/status/approve`. Dashboard card integrated.
- **18 orchestration modules** (authorization, autonomous, bridge_sync, chain, crew, debate, healing, kanban, message_router, monitor, ops, origin, router, sprint_pipeline, supervisor, swarm, task_manager, autonomous_daemon)
- **80+ REST API endpoints** (including 18 `/api/auth/*` + 5 `/api/sprint/*`)
- **GitHub**: https://github.com/lcyluke/apex.git (English codebase)
- **DeepSeek V4 Pro**: All profiles unified. Pricing: $1/M input, $4/M output.
- **Dashboard V5**: 7-tab Command Center with real-time data from all systems
- **Authorization Engine v3**: Delegation system (Origin → PM agents with scoped authority), dual-approval for cross-project/system ops, audit-guardian profile for immutable hash-chain verification. See `references/authorization-delegation-v3.md`.

For fleet cleanup workflow (37→27 agents, model unification, profile creation pattern), see `references/apex-hermes-fleet-cleanup.md`.
For Sprint Pipeline design and implementation, see `references/sprint-pipeline-design.md`.

### Apex Quick Reference

```bash
cd ~/Desktop/2026AIAPP/Apex
source .venv/bin/activate

apex init <name>                # Initialize a project
apex run "<task>"               # Single agent
apex run "<task>" --swarm       # Swarm mode (parallel → verify → synthesize)
apex crew create "<goal>"       # Crew mode (role collaboration)
apex demo                        # 5-min wow: 3 agents + Dashboard → browser
apex dashboard                   # 7-tab Command Center (port 8080)
apex template list              # 5 pre-built agent templates
apex template use <name>        # Create agent from template
apex economy status             # Token economy dashboard
apex knowledge query "<q>"      # Query shared knowledge graph
apex evolution status           # Evolution engine
apex company create <name>      # One-Click Company
apex chain run "<goal>" -p dev  # Sequential pipeline
apex debate "<topic>"           # Multi-perspective debate
apex router route "<task>"      # Task classification routing
apex supervisor "<goal>"        # Hierarchical delegation
apex monitor check -f <file>    # Anomaly detection
apex autonomous start           # 7x24 self-aware operation
apex autonomous status          # Self-awareness report
apex status                     # Full system status
apex sprint create "<goal>"      # Start MVP sprint (--mode solo|swarm)
apex sprint status               # Sprint progress + gates
apex sprint approve              # Approve current manual gate
apex dispatch-smart \"<req>\" -p <proj>  # 🧠 需求→拆解→分派 (智能调度管线)
apex pipeline normal \"<req>\" -p <proj> # 📋 正常流程: 需求→AI拆解→分派
apex pipeline direct \"<task>\" -a <agt>  # ⚡ 专项直达: 指令→Agent→执行
apex pipeline status <pipe_id>           # 📊 管线状态查询
apex fleet inspect                       # ⚓ 全项目巡检 (进度+Agent负载)
apex fleet inspect -p finopsai           # 单项目巡检 (自动匹配PM)
apex fleet init-fleet -n "舰队名"         # ⚓ 初始化多Mac舰队 Origin (v2单仓库)
apex fleet join-fleet                    # 🔗 加入舰队 Worker (v2单仓库)
apex fleet nodes                         # 🖥 舰队节点状态 (含GPU列)
apex fleet gpu-status                    # 🖥 舰队GPU资源中心
apex fleet report                        # 📡 上报心跳+GPU (cron 5min)
apex fleet sync --pull                   # 🔄 拉取 fleet/ 配置
apex fleet sync --push                   # 🔄 推送 fleet/ 配置
apex origin-status                       # 👑 始祖身份查看
apex origin-request                      # 📋 请求成为始祖
apex origin-approve <code>               # ✅ 批准始祖转让
apex project-init <name> --pm <agent>    # 📁 初始化项目+Agent团队
apex project-init <name> --pm <agent>    # 📁 初始化项目+Agent团队
```

## Linked References

- `references/dashboard-v4-command-center.md` — V4 architecture, API specs, DB schemas, pricing, pitfalls
- `references/apex-templates.md` — 5 agent template details
- `references/apex-autonomous-engine.md` — 7x24 self-aware operation
- `references/apex-design.md` — Original design white paper
- `references/multi-agent-framework-comparison.md` — Top 7 frameworks vs Apex
- `references/sprint-pipeline-pattern.md` — MVP closed-loop pipeline: 5-phase state machine, 2 manual gates
- `references/gpu-auto-shutdown-pattern.md` — Agent-driven GPU auto-shutdown with Apex+Hermes hybrid
- `references/authorization-delegation-v3.md` — v3 delegation system, dual-approval flow, audit-guardian, scope boundaries, all 18 REST endpoints
- `references/autonomous-daemon-deployment.md` — AutonomousEngine daemon, dual scheduling architecture, task registration
- `references/numpy-pickle-compat.md` — NumPy cross-version pickle fix: retrain from features when old models fail to load
- `references/multi-mac-fleet-architecture.md` — Multi-Mac fleet v2: single-repo (Apex only), fleet/ directory, GPU monitoring, node heartbeat via GitHub
- `references/worker-join-guide.md` — Step-by-step Mac-B Worker join guide (4 steps, what syncs vs what stays local)
- `references/git-push-troubleshooting.md` — Git push failures: large repos, network blocks, fresh-repo fix
- `references/new-project-fleet-blueprint.md` — Fleet setup template (finopsai pattern)
- `references/smart-dispatch-pipeline.md` — Smart dispatch: requirements→tasks→auto-assign→monitor
- `references/apex-new-project-onboarding.md` — End-to-end workflow: register project → kanban board → PM profile → Apex YAML → seed tasks → Dashboard verification
- `references/github-readme-video-gif.md` — GitHub README video/GIF embedding pattern

## Sprint Pipeline — MVP Closed-Loop Development
35. Project name shorthand = PM Agent. When the user says a project name like finopsai or badminton with no additional context, they mean the PM agent for that project — NOT rebuild the entire project from scratch. Check if a PM profile already exists first, then create/update the PM agent.

Apex has a built-in Sprint Pipeline for end-to-end MVP development. 5 phases, 2 manual gates:

```
📝 PLAN ──👤 设计审批 ──→ ⚙️ BUILD ──🤖──→ 🧪 VERIFY ──👤 发版审批 ──→ 🚀 SHIP ──🤖──→ 🔄 LEARN
```

**Two manual gates only:**
- **设计审批** (PLAN → BUILD): 老卢 reviews PRD + API design + task breakdown
- **发版审批** (VERIFY → SHIP): 老卢 approves deployment after tests pass

All other gates auto-advance based on exit criteria (contract tests, coverage, deploy health).

**Dual build modes:** `solo` (fullstack-dev alone) | `swarm` (frontend+backend with API contract).

**CLI:** `apex sprint create/status/complete/approve/list`
**API:** `GET/POST /api/sprint/*` (5 endpoints for Dashboard)
**Core:** `apex/orchestration/sprint_pipeline.py`
**Spec:** `~/Desktop/2026AIAPP/Apex/docs/specs/sprint-pipeline.md`
**Reference:** `references/sprint-pipeline-pattern.md`

**Design rules learned:**
1. Keep phases few — 5 is the sweet spot. Merge define+design, merge feedback+iterate.
2. Minimize manual gates — exactly 2. 老卢's time is the bottleneck.
3. Solo vs swarm is a build-mode choice, not a phase.
4. Dashboard visibility is mandatory — sprint progress must be always visible.

When upgrading the default LLM model across Apex (e.g. deepseek-chat → deepseek-v4-pro):

1. **Update source code**: 6 files need the model string changed
   - `apex/core/profile.py` — default model in dataclass
   - `apex/core/templates.py` — default_model in each template
   - `apex/core/runtime.py` — matching logic comment
   - `apex/economy/__init__.py` — ModelRoute entries (model name + pricing + quality score)
   - `apex/providers/deepseek.py` — fallback model + pricing docstring + cost calculation
   - `apex/cli/commands/init.py` — project scaffold model + display

2. **Update pricing**: economy/__init__.py and provider cost formula must match new model's per-token pricing.

3. **Update profile YAMLs**: All `~/.apex/profiles/*.yaml` files need the `model.default` field updated. Use `sed -i '' 's/old-model/new-model/g' *.yaml` in the profiles directory.

4. **Update quality scores**: In economy/__init__.py, adjust quality_score (last int in ModelRoute tuple) if the new model performs better/worse.

5. **Verify**: `apex run "What model are you?"` should return the new model name.

## P0 Roles (start here)

| Role | Profile Name | Why First |
|------|-------------|-----------|
| Frontend Developer | `frontend-dev` | UI/UX work, app pages |
| Vision/AI Engineer | `ai-vision` | Image recognition, video analysis |
| Architect | `architect` | System design, DB schema, scalability |

## P1 Roles

| Role | Profile Name | Why |
|------|-------------|-----|
| Apex PM | `apex-pm` | Apex platform health, auth engine, Kanban dispatch, milestone tracking |
| Algorithm Engineer | `ai-algorithm` | Recommendation engine, user profiling |
| Content/Marketing | `content-marketing` | Blog, social media, brand voice |
| Security/Compliance | `security-compliance` | Privacy policy, data protection, audits |
| Ops Engineer | `ops-engineer` | Deployment, nginx, monitoring, CI/CD |
| Audit Guardian | `audit-guardian` | Origin's read-only clone — hash-chain verification, grant scanning, audit reports |
| Fleet Commander | `fleet-commander` | 6-agent monitoring fleet (with gpu-sentinel, token-guardian, session-scout, cron-medic, profile-syncer) |

## P2 Roles

| Role | Profile Name | Why |
|------|-------------|-----|
| Fundraising/Pitch | `fundraising-pitch` | BP, financial models, investor decks |
| Decision Analyst | `decision-analyst` | Market research, data-driven decisions |

## Model Cost Strategy

| Task Type | Recommended Model | Est. Monthly Cost |
|-----------|------------------|-------------------|
| 🟢 Simple coding, chat | DeepSeek (used in session) | ~5-15 RMB |
| 🟡 Complex reasoning, architecture | Claude Sonnet | ~50-100 RMB |
| 🔴 Vision, video analysis | Claude/GPT-4V | ~100-300 RMB |
| ⚪ Local tasks, cron scripts | Local LLM (free) | 0 RMB |

## Batch Profile Configuration

Newly-created profiles have no `config.yaml` or `.env` — you must create them. Do it programmatically for many profiles at once:

```python
import os
from hermes_tools import write_file

profiles = ["ai-algorithm", "ai-vision", "architect", "frontend-dev", ...]
base_dir = "/Users/Mac/.hermes/profiles"

# Read API key from main profile's .env
r = terminal("grep DEEPSEEK_API_KEY /Users/Mac/.hermes/.env | head -1")
api_key = r["output"].strip().split("=", 1)[1].strip()

config = """model:
  default: deepseek-v4-pro
  provider: deepseek
  base_url: https://api.deepseek.com/anthropic
providers:
  deepseek:
    base_url: https://api.deepseek.com/anthropic
agent:
  max_turns: 30
"""

for p in profiles:
    write_file(path=f"{base_dir}/{p}/config.yaml", content=config)
    write_file(path=f"{base_dir}/{p}/.env", content=f"DEEPSEEK_API_KEY={api_key}\n")
```

**Profile skills**: profiles inherit 89+ bundled skills automatically. The `skills/` subdirectory exists and is populated on `hermes profile create`.

**badminton-pm special case**: the PM profile should include `kanban.board: yuji` (or whatever board name) in its config.yaml so its dispatcher targets the right board.

## Kanban Swarm Mode (Parallel Workers → Verifier → Synthesizer)

The `hermes kanban swarm` command creates a complete parallel-processing task graph in one call. **If `apex swarm` is not available (CLI may lack this command), use `delegate_task` with parallel tasks as the equivalent pattern:**

```python
delegate_task(tasks=[
    {"goal": "Analyze from architecture dimension", "context": "...", "toolsets": ["web","terminal"]},
    {"goal": "Analyze from UI/UX dimension", "context": "...", "toolsets": ["web","terminal"]},
    {"goal": "Analyze from feature dimension", "context": "...", "toolsets": ["web","terminal"]},
])
```

This is functionally identical to Swarm — 3 agents analyze in parallel, results merge at conclusion. The `delegate_task` batch mode is the reliable fallback when `apex swarm` CLI is unavailable.

```bash
hermes kanban swarm \
  --worker "frontend-dev:Task title 1:skill1,skill2" \
  --worker "ai-vision:Task title 2" \
  --worker "ops-engineer:Task title 3" \
  --verifier architect \
  --synthesizer badminton-pm \
  --priority 1 \
  --json \
  "Swarm goal description"
```

**How it works:**
1. Creates N parallel worker tasks (one per `--worker`), all immediately `ready`
2. Creates a verifier task with all workers as parents → starts after all workers complete
3. Creates a synthesizer task with the verifier as parent → starts after verification
4. The default Gateway's embedded dispatcher picks up `ready` tasks every 60 seconds

**Priority is an integer** (1, 2, 3...), NOT a string like "P0". `--priority P0` will error.

**JSON output** returns the task IDs:
```json
{
  "root_id": "t_abcdef01",
  "worker_ids": ["t_11111111", "t_22222222", "t_33333333"],
  "verifier_id": "t_44444444",
  "synthesizer_id": "t_55555555"
}
```

You can inspect the full graph with `hermes kanban list`.

## Cleanup Before First Real Use

When re-purposing an existing Kanban board that has old/completed tasks:

```bash
# Archive everything — the board has no "purge" command
hermes kanban list --archived  # see all tasks including archived
hermes kanban archive <task_id>  # archive one by one, or loop:
for tid in t_xxx t_yyy t_zzz; do hermes kanban archive $tid; done
```

Archived tasks stay in the DB for audit but don't show in default list views.

## Hybrid Architecture: Apex Orchestration + Hermes Execution

Apex and Hermes are complementary, not redundant. Understanding their boundary prevents design mistakes:

| Layer | System | What it does | What it CAN'T do |
|-------|--------|-------------|-----------------|
| **Orchestration** | Apex | Profile management, Kanban tasks, Autonomous Engine (7×24 scheduling), Dashboard V3 visualization | SSH, file I/O, WeChat, terminal commands, OS operations |
| **Execution** | Hermes | Terminal tools, SSH, file read/write, WeChat send_message, subprocess management, browser access | Cross-profile task routing, multi-project Kanban, 9-panel dashboard |

### Correct Pattern

```
Apex Autonomous Engine (scheduler)
    │  triggers every N minutes
    ▼
Hermes Cron Job (executor)
    │  SSH → nvidia-smi → decision → WeChat → shutdown
    ▼
Apex Dashboard (observer)
    └─ reads results, shows GPU status panel
```

**Anti-pattern**: Trying to make Apex execute SSH commands directly (it can't — Apex agents are LLM-only, no OS tools). **Anti-pattern**: Trying to make raw Hermes Profiles coordinate complex multi-project workflows without Kanban.

### When Apex Alone Is Enough → When You Need Hermes

| Task | Use | Why |
|------|-----|-----|
| Decompose a feature into tasks, assign to team | Apex Kanban | Pure coordination, no OS access needed |
| Design architecture, write PRD | Apex Profile → LLM | Pure reasoning |
| SSH to AutoDL, run nvidia-smi, shutdown GPU | Hermes Cron | Needs OS-level execution |
| Send WeChat notification | Hermes send_message | Platform integration |
| Visualize all projects + GPU + cost | Apex Dashboard V3 | Already built |
| Clone repo, run tests, commit code | Hermes terminal | Needs file system + git |

### GPU Auto-Shutdown Reference Pattern

The ops-engineer Hermes Profile, driven by a Cron job, acts as the GPU night-watch:

```
Cron (every 10min) → ops-engineer profile
    │
    ├─ SSH AutoDL → nvidia-smi
    │     ├─ GPU > 5%: training active → log, exit
    │     └─ GPU < 5%:
    │           ├─ Check process list (nvidia-smi shows python? training still?)
    │           ├─ 15min idle: WeChat "GPU idle 15min — still need it?"
    │           ├─ 25min idle: WeChat "5min until auto-shutdown"
    │           └─ 30min idle: autodl shutdown → WeChat "Shut down, saved ¥X"
```

## Dual Scheduling Architecture: Hermes Cron + Apex AutonomousEngine

Apex operates **two scheduling layers** — they are complementary, not redundant:

| Layer | Engine | What it does | Runs as |
|-------|--------|-------------|---------|
| **Hermes Cron** | Gateway-internal scheduler | External timed delivery: PM日报, 备份, WeChat notifications | Inside Gateway process |
| **Apex AutonomousEngine** | 3-thread daemon (`autonomous_daemon.py`) | Internal self-awareness: heartbeat collection, scheduled task dispatch, Kanban auto-dispatch | Standalone `nohup` process |

**They serve different purposes:**
- Cron delivers results to the user (日报, 告警, 备份)
- AutonomousEngine manages the agent fleet internally (心跳, 调度, Kanban分发)

**Cron = responsibility of `ops-engineer` for health, `default` is just the host process.**

See `references/autonomous-daemon-deployment.md` for full daemon setup, startup command, task registration, and process isolation details.

### Authorization Engine v3 — Delegation + Dual Approval + Audit Guardian

All privileged operations flow through the authorization engine integrated in Apex. v3 adds delegation, scope boundaries, and dual-approval — superseding the v2 single-approver model.

**Architecture:**
```
⚓ Origin (default) — AuthorizationEngine owner
    │
    ├── delegation → apex-pm [project:apex:*]
    ├── delegation → badminton-pm [project:badminton:*]
    ├── delegation → content-marketing [project:shenzhen:*]
    └── delegation → audit-guardian [audit:read:*] (read-only clone)
```

**Approval flow by scope class:**
| Scope class | Approver | Example |
|-------------|----------|---------|
| `project:{proj}:*` (in-scope) | PM single-approve | apex-pm approves `project:apex:model:assign` |
| `project:{proj}:*` (out-of-scope) | Origin pre → target PM final | apex-pm requests `project:badminton:*` |
| `cross-project:*` | Origin pre → Origin final | `cross-project:budget:reallocate` |
| `system:*` | Origin only | `system:delegation:modify` |

**Dual-approval flow:**
```
1. Agent requests → request_code generated
2. engine.origin_pre_approve(request_code) → status="origin_approved"
3. engine.approve(request_code, approved_by=<final_approver>) → status="approved"
4. engine.consume(grant_id) → one-shot execution
```

**Key files:**
- `apex/orchestration/authorization.py` — core engine (~1200 lines, v3)
- `apex/interface/web.py` — 18 REST endpoints under `/api/auth/*`
- `apex/orchestration/message_router.py` — `auth` category routes to `apex-pm`
- `~/.hermes/scripts/authorization_engine.py` — thin CLI wrapper
- `~/.hermes/profiles/audit-guardian/SOUL.md` — audit clone personality

**See `references/authorization-delegation-v3.md` for full scope list, delegation registry, REST endpoint reference, and pitfalls.**

### Agent Responsibility Matrix

Clear ownership of four cross-cutting functions:

| Function | Owner Agent | Profile | Mechanism |
|----------|------------|---------|-----------|
| 🩺 Health monitoring | ops-engineer | `ops-engineer` | AutonomousEngine task + Hermes cron scripts |
| 📨 Message management | default (Origin) | `default` | message_router.py (auto-classify) + notification_dispatcher (cron) |
| 📋 Agent division | badminton-pm / apex-pm | `badminton-pm` / `apex-pm` | Kanban boards (yuji / apex) |
| 📊 PM project tracking | Per-project PM | 3 PM agents | PM日报 cron + AutonomousEngine scheduled tasks |

**Cron is NOT an agent responsibility** — it runs in the Gateway process. Cron health monitoring IS an agent responsibility (ops-engineer). The default profile is the cron host, not the cron maintainer.

### AutonomousEngine 7×24 Daemon

The AutonomousEngine runs as a standalone daemon process (`nohup python3 -u autonomous_daemon.py &`), NOT inside the Gateway. It manages 7 recurring tasks assigned to different profiles:

```
🔧 ops-engineer     🛡️ 健康巡检(every 30m) + 🔔 通知系统(every 60m)
🦅 apex-pm          📡 脉搏(2h) + 🦅 晨报(9:00) + 🔐 授权扫描(every 60m)
🎯 badminton-pm          🏸 羽球宝日报(9:30)
🔍 audit-guardian   🔍 审计分身巡检(every 60m)
```

Startup: `nohup python3 -u ~/Desktop/2026AIAPP/Apex/apex/orchestration/autonomous_daemon.py > /tmp/apex-autonomous.log 2>&1 &`
Always use `-u` flag (unbuffered) — without it, daemon output is invisible.
- `references/sprint-pipeline-pattern.md` — MVP closed-loop pipeline: 5-phase state machine, 2 manual gates
- `references/gpu-auto-shutdown-pattern.md` — Agent-driven GPU auto-shutdown with Apex+Hermes hybrid
- `references/authorization-delegation-v3.md` — v3 delegation system, dual-approval flow, audit-guardian, scope boundaries, all 18 REST endpoints
- `references/autonomous-daemon-deployment.md` — AutonomousEngine daemon, dual scheduling architecture, task registration
- `references/multi-mac-fleet-architecture.md` — Multi-Mac fleet v2: single-repo (Apex only), fleet/ directory, GPU monitoring, node heartbeat via GitHub
- `references/fleet-multi-mac-implementation.md` — **IMPLEMENTED**: working code, CLI commands, setup guide, pitfalls
## Pitfalls

1. **Each new profile has no API keys or config.**
2. **Kanban dispatcher runs inside the Gateway.** The standalone `hermes kanban daemon` is deprecated — tasks are dispatched by the default profile's Gateway. Start it with `hermes gateway start`. The default profile must be running as the scheduler; if the default Gateway is stopped, tasks sit in 'ready' forever.
3. **Parallel profile sessions burn tokens faster.** DeepSeek is cheap (~0.5 RMB/million tokens), Claude is not. Budget accordingly.
4. **`delegate_task` max_concurrent_children defaults to 3.** For larger parallel bursts, increase `delegation.max_concurrent_children` in config.yaml, or spawn background `hermes chat -q` processes via terminal.
5. **Profile context isolation:** each profile has its own session DB and memory. Cross-agent context must be shared via the filesystem (shared project directory) or Kanban task descriptions.
6. **`project.config.json` miniprogramRoot gotcha with CLI.** If using `--project ./miniprogram` (pointing directly at the miniprogram dir), do NOT include `miniprogramRoot` in project.config.json — it causes "请检查 project.config.json 是否存在及是否有效 (code 19)". For GUI use, keep `miniprogramRoot` in a root-level config and open the parent directory.
7. **Model upgrade requires 6 source files + all profile YAMLs.** Use `sed -i '' 's/old-model/new-model/g' *.yaml` in `~/.apex/profiles/` for the YAML batch. Don't forget economy pricing and provider cost formula adjustments.
8. **Private repo images return 404 on raw.githubusercontent.com.** raw.githubusercontent.com only serves **public** repos. A committed image that 404s usually means the repo is private. Fix: `gh repo edit user/repo --visibility public` or use the API. This is NOT a commit issue — it's an infrastructure constraint.
9. **Clone competitor README structure before redesigning.** When the user asks "make my README look like [competitor]'s", fetch the competitor's raw README first via `curl -sL https://raw.githubusercontent.com/...`. CrewAI's structure is: hero banner → badges → nav links → tagline → quick start → why → features → comparison → architecture → commands → dashboard → install → contribute. Map the project's content into that skeleton.
10. **Large comparison tables must be split.** Tables with 7+ columns and 30+ rows wrap badly in GitHub markdown. Split into focused sub-tables by topic (Core Runtime / Orchestration / Intelligence & Economy / Developer Experience). Each sub-table independently fits narrow viewports.
11. **Subagent-generated HTML JS strings need quote-escaping audit.** When delegate_task produces dashboard HTML with inline JS string concatenation (e.g. innerHTML='...'), the subagent may over-escape quotes: `\\\"` instead of `"`. This creates JS syntax errors that manifest as blank tabs. Fix: `node -e "html.replace(/\\\\\\\"/g, '\"')"` to remove one level of escaping, then validate with `node --check`. Always run `node --check` on extracted JS after subagent HTML changes.
12. **Flask route naming conflict: list vs detail.** A GET route `/api/items` (list) and GET `/api/items/<name>` (detail) collide — Flask treats "items" as a `<name>` value. Fix: use distinct paths like `/api/items/list` and `/api/items/<name>`, or merge into one function that checks `name` for a known sentinel value.
13. **Kanban `create` takes a positional `title`, not `--title`.** `hermes kanban create --title 'Task'` fails with "unrecognized arguments: --title". Correct: `hermes kanban create 'Task' --assignee <name> --priority 1`. Use `hermes kanban create --help` to confirm parameter names.
14. **Kanban `--board` is a global flag before the subcommand, not a subcommand argument.** `hermes kanban list --board apex` fails. Correct: `hermes kanban --board apex list`. For board-scoped operations: `hermes kanban --board <slug> <subcommand>`. Switch the active board with `hermes kanban boards switch <slug>` to avoid repeating `--board`.
15. **Cron: WeChat rate limiting when multiple jobs fire at the same minute.** Stagger cron schedules by ≥5 minutes. Do NOT put 4+ agent jobs at the same time — the gateway delivers them in rapid succession and WeChat rate-limits `sendmessage`. Symptom: `delivery error: Weixin send failed: iLink sendmessage rate limited: ret=-2`. Fix: spread delivery across a window (e.g. 21:00 → 21:05, not 4 jobs all at 21:00).
16. **Cron: security scanner false positives on PM agent jobs.** If a cron job attaches a skill with security keywords (e.g. `authorization-contract` with "阿宝" passphrase), the threat scanner may flag the prompt as `destructive_root_rm` and block execution. Fix: use `hermes cron edit <job_id> --clear-skills` to remove the offending skill attachment.
17. **Cron: unconfigured delivery targets cause per-run errors.** If a job delivers to `origin` but the platform adapter isn't wired (e.g. DingTalk not configured), every run logs a delivery failure. Fix: pause the job with `hermes cron pause <job_id>` until the platform is set up. Check with `hermes gateway setup`.
18. **default.SOUL.md lives at `~/.hermes/SOUL.md`, NOT `~/.hermes/profiles/default/SOUL.md`.** The default (origin) profile has no subdirectory. Its SOUL.md goes in the Hermes home root. Named profiles use `~/.hermes/profiles/<name>/SOUL.md`. Writing to the wrong path silently fails — the default session continues with no personality definition.
19. **AutonomousEngine daemon output buffering.** When daemonized with `nohup`, Python stdout is fully buffered (not line-buffered). Always use `python3 -u` flag. Without it, no log output appears until the 8KB buffer fills. Symptom: daemon process is alive but log file stays empty.
20. **sqlite3 `lastrowid` is on Cursor, not Connection.** `conn.execute()` returns a Cursor. Writing `c.lastrowid` where `c` is a `sqlite3.Connection` raises `AttributeError`. Fix: `cur = c.execute(...); new_id = cur.lastrowid`.
21. **Token verification: reuse auth_api.verify_token(), don't query `tokens` table.** auth_api uses HMAC-signed stateless tokens (format `uid.exp.sig`). There is no `tokens` SQL table. Querying it causes `sqlite3.OperationalError: no such table: tokens`. Fix: `from .auth_api import verify_token; uid = verify_token(token)`.
22. **Dashboard restart: use `run_dashboard()` not `python3 -m apex.interface.web`.** The web.py module has no `__main__` block. Routes added to `create_app()` need a restart to take effect. Correct: `python3 -c "from apex.interface.web import run_dashboard; run_dashboard()"`.
23. **SOUL.md created BEFORE `hermes profile create` blocks profile creation.** If the directory already exists, `hermes profile create` fails with "already exists". Create profile FIRST, then write SOUL.md.
24. **Cron watch_pattern: old buffered errors fire after hot-reload fix.** When uvicorn --reload picks up a code fix, errors logged BEFORE reload are buffered. A watch_pattern match may fire for an already-fixed bug. Verify with a fresh API call before reacting.
25. **PM rename: use `sed -i '' 's/old-pm/new-pm/g'` across ALL files, then update cron prompts.**
26. **`delegate_task` subagents write to the WRONG project path.** Subagents spawned via `delegate_task` receive the project context string but frequently default to `/Users/Mac/Desktop/2026AIAPP/Apex/` instead of the actual target project directory (e.g. `/Users/Mac/Desktop/2026AIAPP/apex-orchestrator/`). After every `delegate_task` call, ALWAYS verify file locations with `find` and copy misplaced files to the correct project. Pattern: `cp /Users/Mac/Desktop/2026AIAPP/Apex/apex/<module>.py <correct-project>/apex/<module>.py`.
27. **`apex task status` requires sequential transitions.** Tasks cannot skip states. `assigned → completed` fails with "Cannot transition". Correct: `assigned → in_progress → completed`. Valid WorkflowStatus values: draft, requested, pm_review, approved, rejected, assigned, in_progress, blocked, completed, pm_verify, verified, closed.
28. **Epic task IDs get truncated in `apex task list` output.** The table display truncates IDs at ~13 chars. Use `python3 -c "from apex.orchestration.task_manager import TaskManager; ..."` for full IDs or query the kanban DB directly. When creating child tasks with `--parent`, extract the epic ID from the `apex task create` output (which shows full IDs), not from `apex task list`.
29. **New-project bootstrap workflow** — see `references/new-project-bootstrap-pattern.md` for the full 6-step pattern: project registry → PM profile → Kanban board → Dashboard view → task creation → fleet status verification.
26. **Demo command `webbrowser.open()` triggers macOS osascript error -10814.** On macOS, `webbrowser.open()` calls `osascript` which may fail in terminal-only environments. Fix: use `subprocess.run(["open", url], capture_output=True, timeout=5)` instead.
27. **Demo port conflict: add `--overwrite` flag.** When `apex demo` runs and port 8080 is already occupied (previous dashboard process), the new server fails to bind. Fix: add `--overwrite` flag that runs `lsof -ti :8080 | xargs kill -9` before starting.
28. **Dashboard URL: always `http://localhost:8080` (root).** Never use `/v5`, `/v4`, `/cc`, or `/dashboard` as the primary URL. The single entry point is root `/` serving `command_center.html`.\n29. **delegate_task subagents often write to WRONG project paths.** Subagents have no memory of the session's working directory. They may write files to `/Users/Mac/Desktop/2026AIAPP/Apex/` (the default Apex project) instead of the intended target project. ALWAYS explicitly pass the full absolute `cwd` or target directory in the task context. After subagent completion, verify files landed in the correct project with `find <project> -name \"*.py\" -newer <reference-file>`. Move misplaced files with `cp` if needed.\n30. **Subagent protocol.py rewrites break existing code.** When a subagent adds new types (CommandStatus, TaskStatus) to protocol.py in one project, it may also rewrite another project's protocol.py with incompatible changes. Always diff the protocol.py after subagent work: `diff <project-a>/apex/protocol.py <project-b>/apex/protocol.py`.
31. **Task status transitions are step-by-step, not direct.** `apex task status <id> completed` from `assigned` fails with "Cannot transition from assigned to completed. Allowed: ['in_progress', 'blocked']". You must walk the state machine: `assigned → in_progress → completed`. Same for all other status transitions — check allowed transitions first by reading the error message or consulting the WorkflowStatus enum.
32. **propose_project modules must be dicts, not strings.** `pr.propose_project(modules=["模块名"])` creates string entries that crash `list_approved_projects()` and `get_project_detail()` with `AttributeError: 'str' object has no attribute 'get'`. Always use `modules=[{"name": "模块名", "description": "说明"}]`.
33. **Batch profile config: API key from main .env, not hardcoded.** When creating config.yaml for new profiles, read `DEEPSEEK_API_KEY` from `~/.hermes/.env` via `grep`/`subprocess`. Never hardcode keys. The config template is: `model.default: deepseek-v4-pro`, `model.provider: deepseek`, `model.base_url: https://api.deepseek.com/anthropic`, `agent.max_turns: 30`. PM profiles also need `kanban.board: <board-slug>`.
34. **Subagent timeout → manual build fallback.** Subagents doing `npm install`, network downloads, or heavy API calls often hit the 600s timeout. When this happens, do NOT retry with another subagent — build the module manually with `write_file` calls. Manual builds are faster (no subagent overhead), more reliable (no path errors), and produce cleaner code (single author, consistent style). Use subagents for pure code generation; avoid them for tasks with network dependencies.
36. **Git push failure → fresh repo from tar.gz.** When `git push` times out (HTTP 408) or fails with SSL_ERROR_SYSCALL, the git pack is too large or the network blocks GitHub. Extract current state: `tar -czf /tmp/proj.tar.gz --exclude='.git' --exclude='venv' ... .` then init a fresh repo from the tar.gz. A 74MB repo becomes ~6MB and pushes instantly. See `references/git-push-troubleshooting.md`.
37. **README: dual separate files preferred over single-file toggles.** User prefers `README.md` + `README_CN.md` with mutual links over single-file `<details>` folding panels. GitHub `<video>` tags don't work; use GIF for demos. Architecture diagrams: hand-coded SVG with dark theme.
38. **Multi-Mac fleet v2: single-repo Apex.** Use `apex fleet init-fleet/join-fleet/nodes/sync/gpu-status`. All fleet config lives in `lcyluke/apex/fleet/`. The old `hermes-fleet-config` repo is archived (June 2026). Worker one-liner: `curl ...apex/main/scripts/fleet-join-worker.sh | bash`. See `references/multi-mac-fleet-architecture.md` and `references/worker-join-guide.md`.
39. **numpy pickle incompatibility fix: retrain from features.** When `pickle.load` fails with `ValueError: MT19937 is not a known BitGenerator`, the model was trained with an older numpy. Do NOT try to monkey-patch numpy internals. Instead: load X_features.npy + y.npy, retrain with same sklearn params, save with current numpy. CV score should match original (±1%). See `references/numpy-pickle-compat.md`.
40. **`HERMES_HOME` env var overridden by profiles in Apex venv**: When running from Apex venv, `HERMES_HOME` is set to the active profile directory (e.g. `~/.hermes/profiles/cron-inspector`), NOT `~/.hermes/`. Code that reads/writes files in the root Hermes home (fleet config, shared state) MUST use `Path(os.path.expanduser("~/.hermes"))` explicitly — never `Path(os.environ.get("HERMES_HOME", ...))`. This broke `apex fleet report/nodes` until fixed.
36. **CLI `--lang` flag must support BOTH `--lang zh` and `--lang=zh`.** Users type `--lang EN` (space) expecting it to work, but naive arg parsing only checks `startswith("--lang=")`. Fix: iterate `sys.argv`, check both `a == "--lang"` (take next arg) and `a.startswith("--lang=")` (split on `=`). Always `.lower()` the value for case-insensitive matching. Default to English, not system locale.
- `references/authorization-delegation-v3.md` — v3 delegation system, dual-approval flow, audit-guardian, scope boundaries, all 18 REST endpoints
- `references/apex-new-project-onboarding.md` — End-to-end workflow: register project → kanban board → PM profile → Apex YAML → seed tasks → Dashboard verification

## Multi-Mac Fleet Architecture (v2 — Single Repo)

As of June 2026, the fleet uses a **single-repo** design. ALL fleet configuration, node heartbeats, skills, and profiles live in `lcyluke/apex/fleet/`. No separate config repo.

- **Origin** runs `apex fleet init-fleet` — creates `fleet/` directory, syncs Hermes config in, commits.
- **Worker** runs `apex fleet join-fleet` — pulls `fleet/` from Apex repo, syncs to `~/.hermes/`.
- **GPU monitoring** is built into `fleet_status()` — every `fleet report` includes GPU util/temp/mem.
- **Node discovery** via `fleet/nodes/<machine_id>.json` — Workers push heartbeats, Origin reads them all.
- Worker one-liner: `curl -fsSL https://raw.githubusercontent.com/lcyluke/apex/main/scripts/fleet-join-worker.sh | bash`

Full details: `references/multi-mac-fleet-architecture.md`

## Active Project Portfolio (June 2026)

| Project | Key | PM Profile | Agents | Cron |
|---------|-----|-----------|--------|------|
| 🏸 羽球宝AI搭子 | `badminton-coach-ai` | `badminton-pm` | 6 | 日报 09:30 + 暮报 21:05 |
| 🦅 Apex Dashboard | `apex` | `apex-pm` | 4 | 日报 10:00 |
| 💰 FinOps AI | `finopsai` | `finops-pm` | 5 | 监控 30m + 日报 09:00 |
| 🗺️ 深圳羽球地图 | `shenzhen-badminton` | — | 2 | 周报 周一 10:00 |
| 🤖 AIAgentOps | `apex-orchestrator` | `pm-agentops` | 3 | M1-M5 完成(21模块) |
| 🖱 AutoClicker | `auto_confirm` | — | — | v1.0.3 跨平台IDE点击器 |
| ⚓ Fleet | `apex/fleet/` | Origin (Mac-A) | 2-5 Nodes | `apex fleet` 舰队指挥 |

### Demo Recording Pipeline (NEW)
- Record: `asciinema rec demo.cast -c "bash scripts/demo.sh"`
- Convert to GIF: `agg --cols 70 --rows 28 --font-size 14 --speed 1.2 demo.cast demo.gif`
- Install: `brew install agg`. Target <500KB. See `references/demo-recording-pipeline.md`.
- GitHub does NOT support `<video>` tags; GIF is the only reliable inline format.

### CLI Flag Hygiene (NEW)
- `--lang` must support both `--lang zh` and `--lang=zh`. Iterate `sys.argv`. Always `.lower()`.
- `--version`/`--update` MUST be handled BEFORE imports (after docstring, before non-stdlib deps). Use only `sys`+`os`.
- Default language to English, not system locale.

Each PM has a kanban board: `badminton-pm → board:yuji`, `apex-pm → board:apex`, `finops-pm → board:finops`.

## Verification

```bash
hermes profile list
hermes kanban list
# Test a specific profile:
frontend-dev chat -q 'What is my role and project directory?'
# Test Apex:
cd ~/Desktop/2026AIAPP/Apex && source .venv/bin/activate && apex status
```

### PM Agent Self-Test (Autonomous Health Check)

Run a PM profile autonomously in background to produce a structured health report:

```bash
hermes chat -q "作为 <project> PM，快速检查项目整体健康度，输出结构化报告" \
  --profile <pm-profile> --quiet
```

For background validation (non-blocking):
```python
terminal(
    command="hermes chat -q '作为 Apex PM，快速检查授权引擎状态 + 项目整体健康度，输出结构化报告' --profile apex-pm --quiet",
    background=True,
    notify_on_complete=True
)
```

The PM agent will autonomously enumerate modules, check file states, read stats from the auth engine, verify git status, and produce a structured report with risk levels and action items. This is the go-to pattern for validating a newly-configured profile end-to-end.

## GitHub TOP3 Optimization Pattern

When preparing an open-source multi-agent project for GitHub stardom:

### Repository Infrastructure (13 files)
- **Issue templates**: bug_report.md, feature_request.md, config.yml
- **PR template**: checklist for type of change, testing, docs
- **Security**: SECURITY.md, CODE_OF_CONDUCT.md, CODEOWNERS
- **Automation**: dependabot.yml, pre-commit-config.yaml, editorconfig
- **Funding**: FUNDING.yml (GitHub Sponsors)
- **Release**: .github/workflows/release.yml — auto-build + PyPI publish on tag

### Testing Infrastructure
- **conftest.py**: Fixtures for tmp_apex_home, ProfileManager, Kanban, KnowledgeGraph
- **Test files by module**: test_profile.py, test_economy.py, test_knowledge.py, test_mcp.py, test_orchestration_kanban.py, test_orchestration_swarm.py, test_orchestration_healing.py
- **42 tests minimum** covering: Profile CRUD, Kanban CRUD + dependencies, Economy classification + routing + budget, Knowledge Graph entities + queries + learning, MCP hub init + tools
- **CI/CD**: Matrix build (Python 3.10/3.11/3.12), ruff lint, pytest with coverage, coverage badge

### PyPI Publishing
```bash
# Manual:
python -m build
twine upload dist/*

# Automatic: tag push v* triggers release.yml workflow
git tag v0.2.0
git push --tags
```

### Launch Sequence (3 months to Top 3)
```
Day 1:  Hacker News → 500 stars
Days 2-7: Reddit r/MachineLearning + r/Python → +4k stars
Week 2: Product Hunt → +5k stars
Month 1: 20k stars → Month 2: 40k → Month 3: 60k+
```

## Command Center — 14-View Enterprise Dashboard (V6, Current)

Apex has a **production-quality Command Center** at `http://localhost:8080` (single entry point). 3794-line single-file HTML with sidebar+view routing architecture. All old dashboard versions (v3/v4/v5/daily/auth) have been **deleted** — only `command_center.html` remains.

### Architecture

- **Sidebar** (230px): 3 nav sections (运营/智能/资源) + real-time crew list showing active Hermes sessions
- **14 views**: 指挥中心 | 项目作战室 | 审批审计 | Pipeline | AI舰队 | 自治引擎 | 知识图谱 | 数据流时序 | 模块市场 | SKILL进化 | 成本中心 | 系统状态 | GPU资源中心
- **"总分+弹窗编辑" UX**: every view shows summary cards → click any item → right-side Drawer opens with full detail + edit form + Save/Cancel buttons
- **40+ REST API endpoints** across 8 backend modules (fleet_manager, hermes_bridge, live_status, project_factory, project_ops, project_registry, audit_flow, web.py)
- **Agent chat history**: click agent in AI舰队 → drawer shows recent sessions from Hermes state.db → click session → full conversation view
- **SKILL Evolution engine**: 6-level XP system (学徒→大师), leaderboard, per-project XP awards
- **Module Marketplace**: 5 categories (小程序/SAAS/Android/AI Chat/Backend), 20+ reusable code templates with file paths
- **Pipeline**: 7-stage dev→deploy→evaluate with per-project report aggregation
- **Professional dark theme**: Tabler Icons CDN, Sora/Manrope/IBM Plex Mono fonts, light theme toggle with localStorage

### Key Patterns

1. **Subagent HTML JS escaping**: When delegate_task produces dashboard HTML, JS strings may be over-escaped (`\\\\\\\"`). Fix: `node -e "html.replace(/\\\\\"/g, '\"')"`, then `node --check`
2. **Flask caching**: Restart server after every HTML edit — browser hard-refresh is NOT enough
3. **Canvas API**: Use HEX colors only (`#3b82f6`), NOT CSS variables (`var(--accent)`)
4. **el() helper**: Must handle numbers — `typeof children==='number' ? textContent : ...`
5. **Route collision**: Never `/api/items` (list) + `/api/items/<name>` (detail) — use `/api/items/list`

### Reference

See `references/command-center-v6-architecture.md` for full architecture, design tokens, API map, startup commands, and pitfall checklist.

## Linked References

- `references/dashboard-v4-command-center.md` — V4 architecture, API specs, DB schemas, pricing, pitfalls
- `references/apex-templates.md` — 5 agent template details
- `references/apex-autonomous-engine.md` — 7x24 self-aware operation
- `references/apex-design.md` — Original design white paper
- `references/multi-agent-framework-comparison.md` — Top 7 frameworks vs Apex
- `references/sprint-pipeline-pattern.md` — MVP closed-loop pipeline: 5-phase state machine, 2 manual gates
- `references/gpu-auto-shutdown-pattern.md` — Agent-driven GPU auto-shutdown with Apex+Hermes hybrid
- `references/authorization-delegation-v3.md` — v3 delegation system, dual-approval flow, audit-guardian, scope boundaries, all 18 REST endpoints
- `references/autonomous-daemon-deployment.md` — AutonomousEngine daemon, dual scheduling architecture, task registration
- `references/multi-mac-fleet-architecture.md` — Multi-Mac fleet v2: single-repo (Apex only), fleet/ directory, GPU monitoring, node heartbeat via GitHub
- `references/fleet-multi-mac-implementation.md` — **IMPLEMENTED**: working code, CLI commands, setup guide, pitfalls
- `references/git-push-troubleshooting.md` — Git push failures: large repos, network blocks, fresh-repo fix
- `references/new-project-fleet-blueprint.md` — Fleet setup template (finopsai pattern)
- `references/smart-dispatch-pipeline.md` — Smart dispatch: requirements→tasks→auto-assign→monitor
- `references/apex-new-project-onboarding.md` — End-to-end workflow: register project → kanban board → PM profile → Apex YAML → seed tasks → Dashboard verification
- `references/github-readme-video-gif.md` — GitHub README video/GIF embedding pattern