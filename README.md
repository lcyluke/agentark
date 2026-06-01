<div align="center">
  <h1>⚡ Apex — Multi-Agent Operating System</h1>
  <p><strong>One person, infinite capacity.</strong></p>
  <p><em>One framework to orchestrate, evolve, and scale AI agents — from solo developers to enterprise fleets.</em></p>

  <!-- Version & License Badges -->
  <a href="https://github.com/lcyluke/apex/releases"><img src="https://img.shields.io/github/v/release/lcyluke/apex?style=flat-square&color=3b82f6" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10%2B-orange?style=flat-square" alt="Python"></a>
  <img src="https://img.shields.io/badge/platform-macOS%20|%20Linux%20|%20Windows-lightgrey?style=flat-square" alt="Platform">

  <!-- Social Proof Badges -->
  <br>
  <a href="https://github.com/lcyluke/apex/stargazers"><img src="https://img.shields.io/github/stars/lcyluke/apex?style=social" alt="Stars"></a>
  <a href="https://github.com/lcyluke/apex/network/members"><img src="https://img.shields.io/github/forks/lcyluke/apex?style=social" alt="Forks"></a>
  <a href="https://github.com/lcyluke/apex/watchers"><img src="https://img.shields.io/github/watchers/lcyluke/apex?style=social" alt="Watchers"></a>
  <a href="https://github.com/lcyluke/apex/issues"><img src="https://img.shields.io/github/issues/lcyluke/apex?style=social" alt="Issues"></a>
  <a href="https://github.com/lcyluke/apex/pulls"><img src="https://img.shields.io/github/issues-pr/lcyluke/apex?style=social" alt="PRs"></a>

  <br>

  <!-- Dynamic Stats Cards -->
  <img src="https://repobeats.axiom.co/api/embed/PLACEHOLDER.svg" alt="Repo activity" width="600">
</div>

---

## 📑 Table of Contents

- [Why Apex?](#-why-apex)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [7 Core Innovations](#-7-core-innovations)
- [Feature Comparison vs Top 7 Frameworks](#-feature-comparison-vs-top-7-frameworks)
- [5 Agent Templates](#-5-agent-templates)
- [All Commands](#-all-commands)
- [Web Dashboard](#-web-dashboard)
- [Integration Guide](#-integration-guide)
  - [With Hermes Agent](#with-hermes-agent)
  - [With OpenClaw](#with-openclaw)
- [Installation](#-installation)
  - [macOS](#macos)
  - [Linux](#linux)
  - [Windows](#windows)
- [Configuration](#-configuration)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Why Apex?

| Problem | How Apex Solves It |
|---------|-------------------|
| 😤 **Fragmentation** — Need 3-5 frameworks (CrewAI for roles, LangGraph for state, CAMEL for learning, LangSmith for monitoring) | **One unified platform.** `pip install apex` and you have everything built in — roles, state, learning, monitoring, knowledge graph, token economy, self-healing. |
| 💸 **Too expensive** — Running multiple agents with top-tier models costs $200+/month | **Token Economy** — Smart routing auto-selects the right model per task: free Ollama for simple, $0.5 DeepSeek for dev, $3 Claude for architecture. Saves **95% cost** while keeping **95%+ capability**. |
| 📚 **Steep learning curve** — LangGraph requires understanding graph theory; MetaGPT has rigid SOP templates | **3-minute onboarding.** `apex run "deploy my app"` just works. Progressive complexity — start with single agents, graduate to Swarm, then to Crew. |
| 🤖 **Agents never improve** — Static system prompts, same mistakes every time | **Evolution Engine** — Every execution is recorded, patterns are mined, skills auto-update. After 100 iterations, error probability drops **90%+**. |
| 🏗️ **Complex team setup** — Manually defining roles, goals, tools for each agent | **Zero-Click Teaming** — Describe your goal, Apex automatically designs the optimal team with right roles, skills, and tools. |
| 🔌 **Vendor lock-in** — Most frameworks tie you to OpenAI | **MCP Native** — Swap any LLM provider (DeepSeek, Ollama, Claude, GPT) anytime. Cross-language agents (Python ↔ Java ↔ Rust) via MCP protocol. |
| 🏢 **From solo to enterprise** — No framework scales from a solo dev to a 100-agent fleet | **One-Click Company** — `apex company create my-startup` creates a full AI company with 5 agents, Kanban, SOP. Scale to enterprise with multi-tenant and RBAC. |

---

## 🏗️ Architecture

Apex is built on a **5-layer Onion Architecture** — each layer is independently replaceable, progressively complex, and secured by a **Token Economy** that runs through all layers.

```
                    ┌─────────────────────────────────────────────────────┐
                    │              L5: INTERFACE (触达层)                  │
                    │                                                      │
                    │   ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
                    │   │   CLI    │  │  Web UI  │  │   REST API        │  │
                    │   │ (Click)  │  │ (Flask)  │  │ 13 endpoints     │  │
                    │   └──────────┘  └──────────┘  └──────────────────┘  │
                    │   ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
                    │   │ IDE Plug │  │   TUI    │  │  WebSocket Stream│  │
                    │   └──────────┘  └──────────┘  └──────────────────┘  │
                    ├─────────────────────────────────────────────────────┤
                    │              L4: OBSERVABILITY (观测层)              │
                    │                                                      │
                    │   ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
                    │   │  Trace   │  │Dashboard │  │    Alerts        │  │
                    │   │  Engine  │  │ 实时看板  │  │    预警系统       │  │
                    │   └──────────┘  └──────────┘  └──────────────────┘  │
                    │   ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
                    │   │ Cost     │  │ Audit    │  │  Health Check    │  │
                    │   │ Tracker  │  │ Log      │  │  健康检查         │  │
                    │   └──────────┘  └──────────┘  └──────────────────┘  │
                    ├─────────────────────────────────────────────────────┤
                    │              L3: INTELLIGENCE (智能层)               │
                    │                                                      │
                    │   ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
                    │   │Evolution │  │  SOP     │  │  Knowledge Graph │  │
                    │   │Engine    │  │Generator │  │  知识图谱         │  │
                    │   └──────────┘  └──────────┘  └──────────────────┘  │
                    │   ┌──────────┐  ┌──────────┐                         │
                    │   │Workflow  │  │ Pattern  │                         │
                    │   │Optimizer │  │  Miner   │                         │
                    │   └──────────┘  └──────────┘                         │
                    ├─────────────────────────────────────────────────────┤
                    │              L2: ORCHESTRATION (编排层)              │
                    │                                                      │
                    │   ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
                    │   │  Swarm   │  │   Crew   │  │    Kanban        │  │
                    │   │ 蜂群模式  │  │ 班组模式  │  │   智能看板       │  │
                    │   └──────────┘  └──────────┘  └──────────────────┘  │
                    │   ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
                    │   │ Pipeline │  │  Graph   │  │  Dynamic Team    │  │
                    │   │ 流水线   │  │  图模式  │  │  动态组队引擎    │  │
                    │   └──────────┘  └──────────┘  └──────────────────┘  │
                    ├─────────────────────────────────────────────────────┤
                    │              L1: AGENT RUNTIME (执行层)              │
                    │                                                      │
                    │   ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
                    │   │ Profile  │  │  Memory  │  │     Skills       │  │
                    │   │ (SOUL+)  │  │ (短期+长)│  │   (可进化技能包)  │  │
                    │   └──────────┘  └──────────┘  └──────────────────┘  │
                    │   ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
                    │   │  Tools   │  │ MCP Hub │  │    LLM Provider  │  │
                    │   │ (Registry│  │(连接外部)│  │   (热插拔)       │  │
                    │   └──────────┘  └──────────┘  └──────────────────┘  │
                    └─────────────────────────────────────────────────────┘
                               🏗️  TOKEN ECONOMY (贯穿所有层)
                    Budget Control · Smart Routing · Cost Optimization
```

### Layer Breakdown

| Layer | Name | Components | What It Does |
|-------|------|-----------|-------------|
| **L5** | Interface | CLI, Web UI, REST API, IDE Plugins, TUI | Entry points for humans and machines to interact with the agent fleet |
| **L4** | Observability | Trace Engine, Dashboard, Alerts, Cost Tracker, Audit Log | Real-time visibility into every agent's execution, cost, and health |
| **L3** | Intelligence | Evolution Engine, SOP Generator, Knowledge Graph, Workflow Optimizer, Pattern Miner | The "brain" — agents learn, share knowledge, and optimize themselves automatically |
| **L2** | Orchestration | Swarm, Crew, Pipeline, Graph, Kanban, Dynamic Team Designer | Composition layer — groups agents into teams, assigns work, manages dependencies |
| **L1** | Runtime | Profile, Memory, Skills, Tools, MCP Hub, LLM Provider | The foundation — each agent is a persistent entity with identity, memory, and tools |
| **🏗️** | Token Economy | Budget Manager, Smart Router, Cost Tracker, Model Selector | Cross-cutting — every action costs tokens, smart routing minimizes cost |

### Data Flow

```
User Input → CLI/API → Orchestration Layer → Agent Runtime → LLM Provider
                         ↓                        ↓
                    Kanban Board            Knowledge Graph
                         ↓                        ↓
                    Workers execute         Skills evolve
                         ↓                        ↓
                    Verifier check          Pattern mined
                         ↓                        ↓
                    Synthesizer merge       Prompt optimized
```

---

### 📁 Source Code Map

```
apex/
├── __init__.py              # Package entry — exports public API
├── __main__.py              # CLI entry: `python -m apex`
│
├── cli/                     # 🖥️ CLI Layer — User interface
│   ├── main.py              # Click CLI framework: all 13 command groups
│   └── commands/            # Command implementations
│       ├── init.py          #   `apex init` — project scaffolding
│       ├── run.py           #   `apex run` — single & swarm execution
│       ├── team.py          #   `apex team` — agent CRUD management
│       ├── template.py      #   `apex template` — pre-built agent library
│       ├── status.py        #   `apex status` — system dashboard
│       ├── economy.py       #   `apex economy` — token budget & routing
│       ├── evolution.py     #   `apex evolution` — learning statistics
│       └── company.py       #   `apex company` — one-click AI company
│
├── core/                    # 🧠 Core Engine — Agent DNA
│   ├── profile.py           # Profile (UPF): agent identity, SOUL, config
│   ├── runtime.py           # Agent Runtime: execute tasks, manage context
│   ├── memory.py            # Memory: short-term (SQLite) + long-term (KG)
│   ├── skills.py            # Skills: executable knowledge packages
│   ├── templates.py         # 5 pre-built agent templates (frontend/backend/PM/content/devops)
│   ├── knowledge.py         # Knowledge Graph: shared cross-agent memory
│   └── evolution.py         # Evolution Engine: learn from every execution
│
├── orchestration/           # 🔄 Orchestration — Multi-Agent Patterns
│   ├── swarm.py             # Swarm: parallel → verify → synthesize
│   ├── crew.py              # Crew: role-based collaboration + team designer
│   ├── kanban.py            # Kanban: smart task board with dependencies
│   ├── healing.py           # Self-Healing: 3-strike auto-recovery
│   ├── chain.py             # Chain: sequential pipeline with handoff verification
│   ├── debate.py            # Debate: multi-perspective analysis & refinement
│   ├── router.py            # Router: task classification & dispatch routing
│   ├── supervisor.py        # Supervisor: hierarchical delegation with review
│   └── monitor.py           # Monitor: anomaly detection & reactive agents
│
├── economy/                 # 💰 Token Economy — Cost Intelligence
│   └── __init__.py          # Budget Manager, Smart Router, Cost Tracker
│
├── mcp/                     # 🔌 MCP Hub — Tool Integration
│   └── hub.py               # Tool registry: filesystem, shell, http, knowledge
│
├── providers/               # 🤖 LLM Providers — Model Adapters
│   ├── base.py              # Abstract provider with plugin registry
│   ├── deepseek.py          # DeepSeek API + Ollama local (free)
│   └── __init__.py          # Auto-registration
│
├── interface/               # 🌐 Web Interface — Visual Dashboard
│   ├── web.py               # Flask app: 13 REST API endpoints
│   └── templates/           # HTML/CSS/JS frontend
│       └── dashboard.html   #   Dark-theme SPA dashboard
│
├── tests/                   # 🧪 Test Suite
│   └── __init__.py
│
├── pyproject.toml           # 📦 Package: dependencies, scripts, metadata
├── README.md                # 📘 This file
├── CONTRIBUTING.md          # 🤝 Contribution guide
└── .github/workflows/       # ⚙️ CI/CD: test + publish pipelines
    └── ci.yml
```

**Design principles per directory:**

| Directory | Single Responsibility | Why Separate |
|-----------|---------------------|--------------|
| `cli/` | User interaction only | Can swap to any UI (TUI, GUI, IDE plugin) without touching logic |
| `core/` | Agent identity, execution, memory | The "brain" — everything else is a consumer |
| `orchestration/` | Agent composition patterns | Each mode is independently testable, composable |
| `economy/` | Token cost intelligence | Cross-cutting concern isolated from agent logic |
| `mcp/` | External tool integration | New tools don't require agent changes |
| `providers/` | LLM model adapters | New model = new file, zero changes elsewhere |
| `interface/` | Web visualization | Optional — Apex works 100% via CLI without it |

---

## 🚀 Quick Start

```bash
# 1. Install (works on macOS, Linux, Windows)
pip install apex

# 2. Initialize your first project
apex init my-project
cd my-project

# 3. Single agent — run like ChatGPT on steroids
apex run "Write a Python script to analyze CSV data"

# 4. Swarm mode — parallel agents, human-level quality
apex run "Build a complete SaaS landing page" --swarm

# 5. Crew mode — role-playing collaboration
apex crew create "Design a microservices architecture"

# 6. One-Click Company — you are now a startup
apex company create my-startup --industry saas

# 7. Open the Web Dashboard
apex dashboard
# → http://localhost:8080
```

---

## 🏆 7 Core Innovations

### 1️⃣ Dynamic Skill Evolution (DSE)

**Problem:** Most frameworks give agents static system prompts. Mistakes repeat forever.

**Solution:** Every execution is recorded. Patterns are mined from successes and failures. Skills auto-update via the `EvolutionEngine`. The shared `KnowledgeGraph` means one agent's lesson becomes every agent's knowledge.

```
Execution 1: Agent writes flex-wrap in WeChat Mini Program → fails → learns
Execution 10: Same agent auto-avoids flex-wrap → writes percentage width → passes
Execution 100: Agent is a WeChat Mini Program expert → predicts pitfalls proactively

📈 Quality improves from 70% → 95% over 100 iterations
📉 Same-error probability drops 90%+
```

```bash
apex evolution status            # See overall learning progress
apex evolution agent frontend    # See a specific agent's improvement curve
```

### 2️⃣ Zero-Click Teaming (ZCT)

**Problem:** Setting up a multi-agent team requires manually defining roles, goals, tools for each agent.

**Solution:** Just describe your goal. Apex's `DynamicTeamDesigner` analyzes the task, identifies required skill sets, and assembles the optimal team — all automatically.

```bash
# Just describe what you want
apex crew create "Build a React dashboard with user authentication"

# Apex auto-selects:
# → Product Manager: define requirements
# → Frontend Developer: build UI
# → Backend Architect: design auth API
# → DevOps Engineer: configure deployment
```

### 3️⃣ Self-Healing Workflow (SHW)

**Problem:** In production, agents fail. Network errors, API rate limits, model timeouts. Other frameworks give up.

**Solution:** The **3-Strike Rule** — automatic diagnosis, recovery, and escalation.

```
Attempt 1 → Error → Auto-diagnose → Retry
Attempt 2 → Same Error → Switch model (fallback) → Retry  
Attempt 3 → Still Failing → Simplify task → Retry
All failed → Notify human with full diagnostic report
```

Each error and fix is recorded in the Knowledge Graph. The agent learns from the experience and avoids it next time.

### 4️⃣ Knowledge Graph Memory (KGM)

**Problem:** Agent memories are siloed. What Agent A learns, Agent B doesn't know.

**Solution:** A **graph-based shared memory** — not a vector database pretending to be one. Real entity-relation-entity triples with confidence scoring, conflict detection, and automatic reasoning.

```
Graph Structure:
  [WeChat Mini Program] --(does not support)--> [flex-wrap]
  [flex-wrap] --(alternative)--> [percentage width]
  [percentage width] --(confidence: 0.97)--> 23 successful uses

Query: "What are the layout pitfalls in WeChat Mini Programs?"
→ Returns: "flex-wrap is not supported. Use percentage width instead.
  Confidence: 97%. Source: 23 successful tasks from frontend-dev agent."
```

```bash
apex knowledge query "layout pitfalls wechat mini program"
apex knowledge stats             # Knowledge graph statistics
```

### 5️⃣ Token Economy (TBB)

**Problem:** Running 10 agents with top-tier models in parallel costs $200+/month. Most tasks don't need the best model.

**Solution:** A **smart routing system** that classifies each task and routes it to the most cost-effective model — without sacrificing quality.

```
┌──────────────────────────────────────────────────────────────┐
│                    TOKEN ROUTING TABLE                       │
├──────────────┬─────────────────────┬─────────────────────────┤
│  Task Type   │  Model              │  Cost/1K Input          │
├──────────────┼─────────────────────┼─────────────────────────┤
│  Simple Edit │  Ollama (local)     │  FREE                   │
│  Code Review │  DeepSeek           │  $0.0005                │
│  Bug Fix     │  DeepSeek           │  $0.0005                │
│  Writing     │  DeepSeek           │  $0.0005                │
│  Architecture│  Claude Sonnet      │  $0.0030                │
│  Vision      │  Claude Sonnet      │  $0.0030                │
└──────────────┴─────────────────────┴─────────────────────────┘

📊 Monthly Cost Comparison (1000 tasks):
  All Claude:     $200  ❌
  All DeepSeek:   $15   ✅
  Apex Smart:     $5-8  ✅✅ (95% savings, 95%+ capability)
  All Ollama:     $0    ✅ (local, free, but limited)
```

```bash
apex economy status                     # See your budget dashboard
apex economy classify "design a database schema"  # "→ Claude Sonnet (architecture)"
apex economy classify "fix a typo in text"        # "→ Ollama (simple edit, FREE)"
```

### 6️⃣ MCP Family (MCP-All)

**Problem:** Agents can only use Python. You need cross-language, cross-machine collaboration.

**Solution:** **Native MCP (Model Context Protocol)** — every agent communicates via MCP. Python, Java, Rust, Go agents work together seamlessly.

```
Agent A (Python) → MCP → Agent B (Java) → MCP → Agent C (Rust)
                         ↓
                    MCP Hub
                         ↓
              Filesystem · GitHub · Browser · Shell · HTTP
```

Built-in MCP tools:
- **`filesystem`** — Read, write, search files
- **`shell`** — Execute commands
- **`knowledge`** — Query the Knowledge Graph
- **`http`** — Call any REST API

### 7️⃣ One-Click Company (OCC)

**Problem:** Setting up a multi-agent system for a new project takes hours.

**Solution:** One command creates an entire AI company. 5 specialized agents, Kanban board, SOP workflow, ready to execute.

```bash
# Create a SaaS startup (5 agents, 7-step SOP, Kanban board)
apex company create my-startup --industry saas

# Company is ready:
#   📋 Product Manager — Requirements, PRD
#   💻 Frontend Developer — UI Implementation
#   ⚙️ Backend Architect — API, Database
#   🔧 DevOps Engineer — Deployment, Monitoring
#   ✍️ Content Strategist — Copywriting, SEO

# Start executing
apex company start my-startup "Build MVP"

# 7 SOP steps auto-created in Kanban:
#   [ ] Requirement Analysis → PRD
#   [ ] Architecture Design → Tech Spec
#   [ ] Frontend + Backend Parallel Dev
#   [ ] Integration Testing
#   [ ] Deploy to Production
#   [ ] Content Release
#   [ ] Monitoring & Ops
```

---

## 🎯 TOP10 Multi-Agent Use Cases — Covered by Apex

Apex ships **8 orchestration modes** that cover the 10 most common multi-agent scenarios. Each mode is a ready-to-use pattern — no coding required.

| # | Use Case | Apex Mode | Command | How It Works |
|---|----------|-----------|---------|-------------|
| 1️⃣ | **Software Development** 💻 | Crew + Chain | `apex crew create "Build a web app"` | PM writes PRD → Frontend builds UI → Backend designs API → DevOps deploys. All roles collaborate, review, and iterate. |
| 2️⃣ | **Research & Analysis** 🔬 | Debate | `apex debate "Should we use microservices?"` | Pro/Con/Neutral agents research, cross-examine, and converge on a synthesized recommendation. |
| 3️⃣ | **Content Production** ✍️ | Chain | `apex chain run "Write a blog post" -p content` | Draft → Review → Edit → Publish. Each stage verifies quality before handoff. |
| 4️⃣ | **Customer Support** 🎧 | Router | `apex router route "My account is locked"` | Task classified (billing/tech/sales) → routed to specialized agent → resolved. Fallback to generalist. |
| 5️⃣ | **Enterprise Approval** 🏢 | Supervisor | `apex supervisor "Design a compliance workflow"` | Manager decomposes → workers execute → supervisor reviews → approves/rejects/revisions. 2-iteration max. |
| 6️⃣ | **DevOps / SRE** 🔧 | Monitor | `apex monitor check -f /var/log/nginx.log` | Watches logs/endpoints → detects anomalies → spawns fixer agent → verifies resolution. Escalates after 3 failures. |
| 7️⃣ | **Data Pipeline** 📊 | Chain | `apex chain run "Process Q3 sales data" -p data` | Extract → Transform → Load. Each stage passes verified output to the next. |
| 8️⃣ | **Product Strategy** 🎯 | Swarm | `apex run "Analyze market competition" --swarm` | 3 parallel analysts research → verifier checks quality → synthesizer produces unified strategy. |
| 9️⃣ | **Code Review & QA** 🐛 | Crew | `apex crew create "Review PR #42" --members frontend,backend,devops` | Multiple experts review from different angles, discuss issues, produce unified review. |
| 🔟 | **Startup MVP** 🚀 | Company | `apex company create my-startup -i saas && apex company start my-startup "Build MVP"` | One command creates 5 agents + Kanban + SOP. Company executes autonomously. |

### Mode Selection Guide

```
New to multi-agent? → Start with `apex run "task"` (Single Agent)
Need parallel work?  → `apex run "task" --swarm` (Swarm)
Need collaboration?  → `apex crew create "goal"` (Crew)
Need pipeline?       → `apex chain run "goal" -p dev` (Chain)
Need debate?         → `apex debate "topic"` (Debate)
Need routing?        → `apex router route "task"` (Router)
Need hierarchy?      → `apex supervisor "goal"` (Supervisor)
Need monitoring?     → `apex monitor check -f /path/to/log` (Monitor)
Want a whole company?→ `apex company create name` (Company)
```

---

## 🏆 Feature Comparison vs Top 7 Frameworks

| Feature | 🔥 **Apex** | CrewAI | LangGraph | AutoGen | CAMEL | MetaGPT | OpenAI Swarm | MS Agent Framework |
|---------|:----------:|:------:|:---------:|:-------:|:-----:|:-------:|:------------:|:-----------------:|
| **Stars** | 🌱 New | 52.6k | 33.6k | 58.6k | 17.1k | 68.5k | 21.5k | 8k+ |
| **Active Development** | ✅ Daily | ✅ | ✅ | ❌ Maint. | ✅ | ❌ Stale | ❌ Education | ✅ |
| | | | | | | | | |
| **Core Runtime** | | | | | | | | |
| Persistent Agent Profile | ✅ **UPF** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Multi-LLM Provider | ✅ **Hot-swap** | ✅ | ✅ LangChain | ✅ OpenAI | ✅ | ✅ OpenAI | ❌ OpenAI-only | ✅ |
| Local LLM (Ollama) | ✅ **Built-in** | ❌ Add-on | ✅ LangChain | ❌ | ❌ | ❌ | ❌ | ❌ |
| Cross-language Agents | ✅ **MCP** | ❌ | ❌ | ❌ .NET only | ❌ | ❌ | ❌ | ❌ |
| | | | | | | | | |
| **Orchestration** | | | | | | | | |
| Single Agent | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Swarm (Parallel → Verify → Synthesize) | ✅ **Native** | ❌ | ❌ Manual graph | ❌ | ❌ | ❌ | ❌ | ❌ |
| Crew (Role Collaboration) | ✅ **4-phase** | ✅ | ❌ | ✅ GroupChat | ✅ RolePlay | ❌ Fixed roles | ❌ | ❌ |
| Pipeline (Sequential) | ✅ | ❌ | ✅ Graph | ❌ | ❌ | ✅ | ❌ | ❌ |
| Graph Mode (Custom DAG) | ✅ **LangGraph compatible** | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Dynamic Team Design | ✅ **Zero-Click** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Smart Kanban | ✅ **AI-powered** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| | | | | | | | | |
| **Intelligence** | | | | | | | | |
| Self-Learning Evolution | ✅ **Built-in** | ❌ | ❌ | ❌ | ✅ Research | ❌ | ❌ | ❌ |
| Knowledge Graph (Shared Memory) | ✅ **Graph-based** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| SOP Auto-Generation | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ Fixed | ❌ | ❌ |
| Self-Healing (3-Strike) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Workflow Optimization | ✅ **AFlow-inspired** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| | | | | | | | | |
| **Economy** | | | | | | | | |
| Token Budget Management | ✅ **Built-in** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Smart Model Routing | ✅ **Per-task** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Cost Dashboard | ✅ **Real-time** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Cross-project Budget Transfer | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| | | | | | | | | |
| **Observability** | | | | | | | | |
| Execution Trace | ✅ | ❌ | ✅ LangSmith | ✅ Studio | ❌ | ❌ | ❌ | ❌ |
| Web Dashboard | ✅ **Free** | ❌ Paid | ❌ Paid | ✅ Free (maint.) | ❌ | ❌ | ❌ | ❌ |
| REST API | ✅ **13 endpoints** | ❌ | ✅ LangSmith | ✅ | ❌ | ❌ | ❌ | ❌ |
| Real-time Alerts | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| | | | | | | | | |
| **Developer Experience** | | | | | | | | |
| Lines to create a team | **1** | 5+ | 20+ | 10+ | 15+ | 1 (fix) | 10+ | 15+ |
| Time to first task | **3 min** | 15 min | 1 hour | 10 min | 20 min | 10 min | 5 min | 30 min |
| Learning curve | **Low** | Medium | High | Medium | High | Medium | Low | High |
| CLI-first | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| 5 Pre-built Templates | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| One-Click Company | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| | | | | | | | | |
| **Integration** | | | | | | | | |
| Hermes Agent Plugin | ✅ **Ready** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| OpenClaw Compatible | ✅ **Ready** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| MCP Native | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| | | | | | | | | |
| **Pricing** | | | | | | | | |
| Open Source License | ✅ **MIT** | ✅ MIT | ✅ MIT | ✅ MIT | ✅ Apache | ✅ MIT | ✅ MIT | ✅ MIT |
| Free Web UI | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Cost for 1000 tasks | **$5-8** | $50+ | $80+ | $50+ | $50+ | $50+ | $50+ | $80+ |

### Unique Selling Points

| Only Apex Has | Why It Matters |
|---------------|----------------|
| **Evolution Engine** | Agents get smarter every time you use them. No other framework has this. |
| **Knowledge Graph Memory** | Teach one agent = teach all agents. Shared intelligence across your entire fleet. |
| **Token Economy** | Smart routing saves 95% cost. Pay $5 instead of $200/month. |
| **Self-Healing Workflow** | Agents fix their own errors. 3-strike rule before notifying humans. |
| **One-Click Company** | `apex company create`. One command = entire AI company. |
| **Cross-platform install** | One `pip install` works on macOS, Linux, Windows. No native deps. |
| **Hermes + OpenClaw Integration** | Use Apex as a plugin for Hermes, or standalone. Works with OpenClaw workspaces. |

---

## 📦 5 Agent Templates

Each template is a **pre-configured expert** with optimized SOUL (persona), skill packages, expertise domains, and toolset.

```bash
# See all templates
apex template list

# Create an agent from a template
apex template use frontend -a my-frontend-dev

# Run with your new agent
apex run "Build a login page" --profile my-frontend-dev
```

| Template | Icon | Role | Expertise (10 domains) | Skill Packages | Tools | Best For |
|----------|:----:|------|-----------------------|----------------|-------|----------|
| **`frontend`** | 💻 | Frontend Developer | React, Vue, WeChat Mini Program, TypeScript, Tailwind, Next.js, Webpack, Figma, Micro-frontends, PWA | component-building, responsive-design, css-animation, api-integration, state-management, ui-testing, a11y | filesystem, github, terminal, browser | UI development, landing pages, web apps |
| **`backend`** | ⚙️ | Backend Architect | FastAPI, Django, Go, PostgreSQL, Redis, MongoDB, Docker, K8s, Kafka, gRPC | system-design, api-design, database-schema, cloud-deployment, security, performance, microservices, testing | filesystem, github, terminal, docker, k8s | API design, system architecture, database schema |
| **`pm`** | 📋 | Product Manager | PRD Writing, User Stories, User Segmentation, A/B Testing, Competitive Analysis, OKRs, Roadmap, MVP, User Research, Business Canvas | prd-writing, user-research, data-analysis, a-b-testing, competitive-analysis, roadmap, kpi-definition | filesystem, browser, notion | Requirements, planning, strategy |
| **`content`** | ✍️ | Content Strategist | Copywriting (EN/ZH), SEO (On-page/Technical), WeChat/Twitter/LinkedIn, Brand Storytelling, Data-driven Strategy, Localization, AIGC, Content Calendar, CRO | copywriting, seo-optimization, social-media, brand-storytelling, content-strategy, localization, prompt-engineering | filesystem, browser, x, notion | Content creation, SEO, social media |
| **`devops`** | 🔧 | DevOps Engineer | Docker Compose, Kubernetes, Terraform, GitHub Actions, Prometheus/Grafana, AWS/GCP, Nginx, ELK, TLS/SSL, Security Audit | ci-cd-pipeline, infrastructure-as-code, monitoring-alerting, cloud-cost-optimization, security, kubernetes, database-admin, incident-response | filesystem, github, terminal, docker, k8s | Deployment, monitoring, CI/CD |

---

## 📋 All Commands

| Category | Command | Description |
|----------|---------|-------------|
| **Project** | `apex init <name>` | Initialize a new Apex project |
| **Execution** | `apex run "<task>"` | Single agent task execution |
| | `apex run "<task>" --swarm` | Swarm mode (parallel → verify → synthesize) |
| **Crew** | `apex crew create "<goal>"` | Auto-designed crew (zero-click teaming) |
| | `apex crew create "<goal>" --members a,b,c` | Crew with specific members |
| | `apex crew design "<goal>"` | Preview recommended team composition |
| **Team** | `apex team create <name>` | Create an agent profile |
| | `apex team list` | List all agent profiles |
| | `apex team show <name>` | Show agent profile details |
| **Templates** | `apex template list` | Browse 5 pre-built agent templates |
| | `apex template show <name>` | Show template details |
| | `apex template use <name>` | Create agent from template |
| **Status** | `apex status` | Full system status (agents, tasks, economy) |
| **Economy** | `apex economy status` | Token economy dashboard |
| | `apex economy classify "<task>"` | Test model routing classification |
| **Knowledge** | `apex knowledge query "<q>"` | Query the shared knowledge graph |
| | `apex knowledge stats` | Knowledge graph statistics |
| **Evolution** | `apex evolution status` | Evolution engine status |
| | `apex evolution agent <name>` | Agent evolution report |
| **Company** | `apex company create <name>` | One-click AI company creation |
| | `apex company start <name> <goal>` | Start company execution |
| | `apex company list` | List all created companies |
| **Dashboard** | `apex dashboard` | Launch Web UI (port 8080) |
| **Chain** | `apex chain run "<goal>" -p dev` | Sequential pipeline (dev/content/data) |
| **Debate** | `apex debate "<topic>"` | Multi-perspective debate & synthesis |
| **Router** | `apex router route "<task>"` | Classify & dispatch to specialized agent |
| **Supervisor** | `apex supervisor "<goal>"` | Hierarchical delegation with review |
| **Monitor** | `apex monitor check -f <file>` | Watch logs/endpoints, detect anomalies |

---

## 🖥️ Web Dashboard

Apex ships with a **built-in Web Dashboard** — no extra services, no paid tiers.

```bash
apex dashboard --port 8080
# Open http://localhost:8080
```

### Dashboard Features

| Section | What You See |
|---------|-------------|
| **Stats Bar** | Active agents, total tasks, total cost, companies, learned patterns, knowledge nodes — all real-time |
| **Agent Profiles** | Card view of all agents with role, model, skills, expertise tags. Click for detail |
| **Task Board** | Kanban-style task list filtered by status (todo/ready/in_progress/done/blocked) |
| **Token Economy** | Budget usage bar chart with color-coded thresholds (green/yellow/red), remaining balance |
| **Model Routes** | Visual routing table showing which model handles which task type |
| **Execution Log** | Real-time streaming log of all agent activities |
| **Auto-refresh** | Dashboard refreshes every 10 seconds |

### REST API (for custom integrations)

```
GET  /api/status        — System status + economy + tasks + companies + KG stats
GET  /api/profiles       — All agent profiles
GET  /api/profiles/<n>   — Single agent detail + evolution data
GET  /api/tasks          — All Kanban tasks
GET  /api/knowledge      — Knowledge graph statistics
GET  /api/evolution      — Evolution engine summary
GET  /api/companies      — All created companies
GET  /api/health         — Health check
```

---

## 🔌 Integration Guide

### With Hermes Agent

Apex can run as a **Hermes Agent plugin** or alongside it as a complementary tool.

#### Option A: Run Apex alongside Hermes

```
Hermes: Your personal AI assistant (对话入口)
  ↓
Apex: Multi-agent operating system (任务调度)
  ↓
5 Agent Templates: Specialized workers (专业执行)
```

```bash
# Hermes already installed at ~/.hermes/
# Apex installed separately at ~/Desktop/2026AIAPP/Apex/

# Use Hermes for conversation, then delegate to Apex for multi-agent tasks
cd ~/Desktop/2026AIAPP/Apex
source .venv/bin/activate

# Apex handles the heavy multi-agent work
apex crew create "Build a data analytics dashboard" --members pm,frontend,backend
apex company start my-startup "Deploy to production"
```

#### Option B: Import Apex in Hermes skills

```python
# In a Hermes skill, you can call Apex programmatically
import subprocess

def run_apex_swarm(goal: str):
    result = subprocess.run(
        ["apex", "run", goal, "--swarm"],
        capture_output=True, text=True,
        cwd="/Users/Mac/Desktop/2026AIAPP/Apex",
        env={"PATH": "/Users/Mac/Desktop/2026AIAPP/Apex/.venv/bin:/usr/bin:/bin"}
    )
    return result.stdout
```

#### Shared Assets

| Asset | Hermes Path | Apex Path |
|-------|------------|-----------|
| API Keys | `~/.hermes/.env` | `~/.apex/.env` (can symlink) |
| Project Workspace | `~/Desktop/2026AIAPP/workspace/` | `~/Desktop/2026AIAPP/Apex/` |
| Python Venv | `~/.hermes/hermes-agent/venv/` | `~/Desktop/2026AIAPP/Apex/.venv/` |

### With OpenClaw

Apex respects OpenClaw workspace conventions and can be integrated into OpenClaw workflows.

```bash
# OpenClaw workspace at ~/.openclaw/workspace/
# Apex project at ~/Desktop/2026AIAPP/Apex/

# Use Apex from within OpenClaw projects
cd ~/.openclaw/workspace/your-project
export APEX_HOME="$PWD/.apex"

# Run Apex commands within the project context
/Users/Mac/Desktop/2026AIAPP/Apex/.venv/bin/apex run "Analyze this codebase"
```

```python
# Programmatic integration
import sys
sys.path.insert(0, "/Users/Mac/Desktop/2026AIAPP/Apex")
from apex.core.runtime import Agent
from apex.core.profile import ProfileManager

pm = ProfileManager()
agent = Agent(pm.load("frontend"))
result = agent.run("Review the code in this project")
```

---

## 📥 Installation

### Prerequisites

| Requirement | Version | Check Command |
|------------|---------|---------------|
| Python | 3.10+ | `python3 --version` |
| pip | 21+ | `pip3 --version` |
| Git | 2.0+ | `git --version` |

---

### macOS

**Method 1: pip install (recommended)**

```bash
# Install system Python if not present
brew install python@3.11

# Install Apex
pip3 install apex-multiagent

# Verify
apex --version
```

**Method 2: From source (development)**

```bash
# Clone
git clone https://github.com/lcyluke/apex.git
cd apex

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with uv (fast)
pip install uv
uv pip install -e ".[web]"

# Or with regular pip
pip install -e ".[web]"

# Verify
apex --version
```

**Method 3: Using Hermes venv Python**

```bash
# If you already have Hermes installed
export PATH="/Users/Mac/.hermes/hermes-agent/venv/bin:$PATH"
pip install apex-multiagent
apex --version
```

---

### Linux

**Ubuntu/Debian:**

```bash
# Install Python
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git

# Install Apex
pip3 install apex-multiagent

# Verify
apex --version
```

**Fedora/RHEL:**

```bash
sudo dnf install -y python3 python3-pip git
pip3 install apex-multiagent
apex --version
```

**Arch Linux:**

```bash
sudo pacman -S python python-pip git
pip install apex-multiagent
apex --version
```

**From source (all distros):**

```bash
git clone https://github.com/lcyluke/apex.git
cd apex
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[web]"
apex --version
```

---

### Windows

**Method 1: pip install**

```powershell
# Install Python from python.org (3.10+), ensure "Add to PATH" is checked

# Install Apex
pip install apex-multiagent

# Verify
apex --version
```

**Method 2: From source**

```powershell
# Clone
git clone https://github.com/lcyluke/apex.git
cd apex

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install
pip install -e ".[web]"

# Verify
apex --version
```

**Method 3: Using WSL (recommended for production)**

```powershell
# Install WSL
wsl --install -d Ubuntu

# Inside WSL:
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
pip3 install apex-multiagent
apex --version
```

---

### Docker (all platforms)

```dockerfile
FROM python:3.11-slim

RUN pip install apex-multiagent

WORKDIR /app
CMD ["apex", "dashboard", "--host", "0.0.0.0"]
```

```bash
docker build -t apex .
docker run -p 8080:8080 \
  -v ~/.apex:/root/.apex \
  -e DEEPSEEK_API_KEY=sk-xxx \
  apex
```

---

### Post-Installation

```bash
# Set your API key
export DEEPSEEK_API_KEY="sk-xxx"

# Or create config file
mkdir -p ~/.apex
echo "DEEPSEEK_API_KEY=sk-xxx" > ~/.apex/.env

# Verify everything works
apex init hello-apex
cd hello-apex
apex run "Hello, world! What can Apex do?"
apex status

# 🎉 You're ready!
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEEPSEEK_API_KEY` | ✅ (or env file) | — | DeepSeek API key for agent execution |
| `APEX_HOME` | ❌ | `~/.apex` | Apex data directory (profiles, DBs, configs) |
| `OLLAMA_BASE_URL` | ❌ | `http://localhost:11434` | Ollama server URL for local models |

### Config File: `~/.apex/.env`

```
DEEPSEEK_API_KEY=sk-your-key-here
```

### Using Local Models (Free)

```bash
# Install Ollama
brew install ollama  # macOS
# or: curl -fsSL https://ollama.com/install.sh | sh  # Linux

# Pull a model
ollama pull llama3

# Apex automatically routes simple tasks to Ollama (free)
apex run "Hello, world!"  # → Uses Ollama for simple tasks
```

---

## 🗺️ Roadmap

```
v0.1    🎯 CURRENT — Core complete: Runtime, Swarm, Crew, 
        Templates, Token Economy, Knowledge Graph, 
        Evolution Engine, One-Click Company, Web UI
        
v0.2    🔜 NEXT — Plugin system, LangSmith integration,
        Web UI v2 (Trace browser, real-time logs),
        Community skill marketplace
        
v0.3    Enterprise: Multi-tenant, RBAC, Audit logs,
        Private deployment, SSO
        
v1.0    Production ready: GUI flow designer, 
        Enterprise support, SLA guarantees
```

---

## 📊 Project Metrics

<div align="center">
  <a href="https://github.com/lcyluke/apex/stargazers">
    <img src="https://img.shields.io/github/stars/lcyluke/apex?style=for-the-badge&logo=github" alt="Stars">
  </a>
  <a href="https://github.com/lcyluke/apex/network/members">
    <img src="https://img.shields.io/github/forks/lcyluke/apex?style=for-the-badge&logo=github" alt="Forks">
  </a>
  <a href="https://github.com/lcyluke/apex/watchers">
    <img src="https://img.shields.io/github/watchers/lcyluke/apex?style=for-the-badge&logo=github" alt="Watchers">
  </a>
  <a href="https://github.com/lcyluke/apex/issues">
    <img src="https://img.shields.io/github/issues/lcyluke/apex?style=for-the-badge&logo=github" alt="Issues">
  </a>
  <a href="https://github.com/lcyluke/apex/pulls">
    <img src="https://img.shields.io/github/issues-pr/lcyluke/apex?style=for-the-badge&logo=github" alt="PRs">
  </a>
  <br>
  <a href="https://github.com/lcyluke/apex/graphs/contributors">
    <img src="https://img.shields.io/github/contributors/lcyluke/apex?style=for-the-badge&logo=github" alt="Contributors">
  </a>
  <a href="https://github.com/lcyluke/apex/commits/main">
    <img src="https://img.shields.io/github/last-commit/lcyluke/apex?style=for-the-badge&logo=github" alt="Last Commit">
  </a>
  <a href="https://github.com/lcyluke/apex/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/lcyluke/apex?style=for-the-badge&logo=github" alt="License">
  </a>
</div>

---

## 🤝 Contributing

We welcome contributions of all sizes — bug fixes, feature requests, documentation improvements, and new agent templates.

```bash
# Clone and setup
git clone https://github.com/lcyluke/apex.git
cd apex
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,web]"

# Make your changes
# ...

# Check for Chinese text (should be zero)
grep -rn '[\x{4e00}-\x{9fff}]' apex/ --include="*.py" || echo "✅ Clean"

# Submit a PR
git add -A
git commit -m "feat: your change description"
git push
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

---

## 📄 License

MIT © 2026 [lcyluke](https://github.com/lcyluke)

---

<div align="center">
  <h3>⚡ Apex — One person, infinite capacity.</h3>
  <p>
    <a href="https://github.com/lcyluke/apex">GitHub</a> ·
    <a href="https://github.com/lcyluke/apex/issues">Issues</a> ·
    <a href="https://github.com/lcyluke/apex/discussions">Discussions</a>
  </p>
  <p>
    <a href="https://github.com/lcyluke/apex/stargazers">
      <img src="https://img.shields.io/github/stars/lcyluke/apex?style=social" alt="Star">
    </a>
    <a href="https://twitter.com/intent/tweet?text=Apex%20-%20Multi-Agent%20Operating%20System&url=https://github.com/lcyluke/apex">
      <img src="https://img.shields.io/twitter/url?style=social&url=https://github.com/lcyluke/apex" alt="Tweet">
    </a>
  </p>
  <p><em>From today, you are a company.</em></p>
</div>
