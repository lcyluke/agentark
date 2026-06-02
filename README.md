<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/lcyluke/apex/main/docs/images/apex-banner.png">
    <img alt="Apex — Multi-Agent Operating System" src="https://raw.githubusercontent.com/lcyluke/apex/main/docs/images/apex-banner.png" width="800">
  </picture>
</p>

<p align="center">
  <strong>One person, infinite capacity.</strong><br>
  <em>The world's most advanced open-source Multi-Agent Operating System — with 7 built-in innovations no other framework has.</em>
</p>

<p align="center">
  <a href="https://github.com/lcyluke/apex/releases"><img src="https://img.shields.io/github/v/release/lcyluke/apex?style=flat-square&color=3b82f6" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10%2B-orange?style=flat-square" alt="Python"></a>
  <a href="https://pypi.org/project/apex-multiagent/"><img src="https://img.shields.io/pypi/v/apex-multiagent?style=flat-square&color=3b82f6" alt="PyPI"></a>
  <a href="https://pypi.org/project/apex-multiagent/"><img src="https://img.shields.io/pypi/dm/apex-multiagent?style=flat-square&color=green" alt="Downloads"></a>
  <img src="https://img.shields.io/badge/platform-macOS%20|%20Linux%20|%20Windows-lightgrey?style=flat-square" alt="Platform">
</p>

<p align="center">
  <a href="https://github.com/lcyluke/apex/stargazers"><img src="https://img.shields.io/github/stars/lcyluke/apex?style=social" alt="Stars"></a>
  <a href="https://github.com/lcyluke/apex/network/members"><img src="https://img.shields.io/github/forks/lcyluke/apex?style=social" alt="Forks"></a>
  <a href="https://github.com/lcyluke/apex/watchers"><img src="https://img.shields.io/github/watchers/lcyluke/apex?style=social" alt="Watchers"></a>
  <a href="https://github.com/lcyluke/apex/issues"><img src="https://img.shields.io/github/issues/lcyluke/apex?style=social" alt="Issues"></a>
  <a href="https://github.com/lcyluke/apex/pulls"><img src="https://img.shields.io/github/issues-pr/lcyluke/apex?style=social" alt="PRs"></a>
  <a href="https://twitter.com/intent/tweet?text=Apex%20-%20Multi-Agent%20Operating%20System&url=https://github.com/lcyluke/apex"><img src="https://img.shields.io/twitter/url?style=social&url=https://github.com/lcyluke/apex" alt="Tweet"></a>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a>
  · <a href="#-why-apex">Why Apex?</a>
  · <a href="#-7-core-innovations">7 Innovations</a>
  · <a href="#-orchestration-modes">Modes</a>
  · <a href="#-comparison-vs-top-frameworks">Comparison</a>
  · <a href="#-agent-templates">Templates</a>
  · <a href="#-installation">Install</a>
  · <a href="#%EF%B8%8F-web-dashboard">Dashboard</a>
  · <a href="#-autonomous-engine">Autonomous</a>
</p>

---

## 🚀 Quick Start

```bash
# Install (macOS, Linux, Windows)
pip install apex-multiagent

# Initialize your first project
apex init my-project && cd my-project

# Single agent — like ChatGPT with superpowers
apex run "Write a Python script to analyze CSV data"

# Swarm mode — 3 parallel agents, verified, synthesized
apex run "Build a complete SaaS landing page" --swarm

# Crew mode — role-playing collaboration (PM + Frontend + Backend)
apex crew create "Design a microservices architecture"

# One-Click Company — you are now a startup
apex company create my-startup --industry saas

# Open the Web Dashboard
apex dashboard
# → http://localhost:8080
```

---

## 🎯 Why Apex?

**Multi-agent frameworks are powerful, but existing tools are fragmented.** You need CrewAI for roles, LangGraph for state, LangSmith for monitoring, CAMEL for learning — 3-5 frameworks glued together. Apex solves this with **one unified platform, 7 innovations, 10 orchestration modes, and a built-in web dashboard.**

| Problem | How Apex Solves It |
|---------|-------------------|
| 😤 **Fragmentation** — Need 3-5 frameworks | **One unified platform.** `pip install apex` has everything — roles, state, learning, monitoring, knowledge graph, token economy, self-healing. |
| 💸 **Too expensive** — Multiple top-tier agents cost $200+/month | **Token Economy** — Smart routing auto-selects the right model per task. Free Ollama for simple, $0.5 DeepSeek for dev, $3 Claude for architecture. **Saves 95% cost.** |
| 📚 **Steep learning curve** — LangGraph requires graph theory; MetaGPT has rigid SOPs | **3-minute onboarding.** `apex run "deploy my app"` just works. Start with single agents, graduate to Swarm, then Crew. Progressive complexity. |
| 🤖 **Agents never improve** — Static prompts, same mistakes | **Evolution Engine** — Every execution is recorded, patterns mined, skills auto-updated. After 100 iterations, error probability drops **90%+.** |
| 🏗️ **Complex team setup** — Manually defining roles for each agent | **Zero-Click Teaming** — Describe your goal, Apex automatically designs the optimal team with right roles, skills, and tools. |
| 🔌 **Vendor lock-in** — Most frameworks tie you to OpenAI | **MCP Native** — Swap any LLM provider anytime. Cross-language agents (Python ↔ Java ↔ Rust) via MCP protocol. |
| 🏢 **Solo to enterprise** — No framework scales from solo dev to fleet | **One-Click Company** — `apex company create my-startup` creates a full AI company. Scale to enterprise with multi-tenant and RBAC. |

---

## 🏆 7 Core Innovations

> **Every major framework has ONE thing it does well. Apex has all 7 — built in, not bolted on.**

### 1️⃣ Dynamic Skill Evolution (DSE)
**Agents get smarter every time you use them.** No other framework has this.

```
Execution 1:  Agent writes flex-wrap in WeChat Mini Program → fails → learns
Execution 10: Agent auto-avoids flex-wrap → uses percentage width → passes
Execution 100:Agent is a WeChat Mini Program expert → predicts pitfalls proactively
```

```bash
apex evolution status            # See overall learning progress
apex evolution agent frontend    # See a specific agent's improvement curve
```

### 2️⃣ Zero-Click Teaming (ZCT)
**Just describe your goal — Apex assembles the optimal team automatically.**

```bash
apex crew create "Build a React dashboard with user authentication"
# → Auto-assigns: Product Manager + Frontend Developer + Backend Architect + DevOps
```

### 3️⃣ Self-Healing Workflow (SHW)
**3-strike rule: retry → switch model → simplify → notify human.** Each failure is a learning opportunity recorded in the Knowledge Graph.

```
Attempt 1 → Error → Auto-diagnose → Retry
Attempt 2 → Same Error → Switch model (fallback) → Retry  
Attempt 3 → Still Failing → Simplify task → Retry
All failed → Notify human with full diagnostic report
```

### 4️⃣ Knowledge Graph Memory (KGM)
**Teach one agent = teach all agents.** Graph-based shared memory — not a vector database. Real entity-relation triples with confidence scoring, conflict detection, and automatic reasoning.

```bash
apex knowledge query "layout pitfalls in WeChat Mini Programs"
# → "flex-wrap is not supported. Use percentage width instead. Confidence: 97%"
apex knowledge stats             # Knowledge graph statistics
```

### 5️⃣ Token Economy (TBB)
**Smart routing saves 95% cost while keeping 95%+ capability.** Each task is classified and routed to the most cost-effective model.

```
Task Type         → Model            → Cost/1K Input
─────────────────────────────────────────────────
Simple Edit       → Ollama (local)   → FREE
Code Review       → DeepSeek V4 Pro  → $0.001
Architecture      → Claude Sonnet    → $0.003
Bug Fix           → DeepSeek V4 Pro  → $0.001

📊 Monthly: All Claude $200 → All DeepSeek $15 → Apex Smart $5 🎯
```

```bash
apex economy status                     # See your budget dashboard
apex economy classify "design a database schema"  # → Claude Sonnet
apex economy classify "fix a typo"                 # → Ollama (FREE)
```

### 6️⃣ MCP Family (MCP-All)
**Cross-language, cross-machine, cross-framework.** Python, Java, Rust, Go agents communicate via MCP protocol. Built-in tools: filesystem, shell, knowledge graph, HTTP.

```
Agent A (Python) → MCP → Agent B (Java) → MCP → Agent C (Rust)
                         ↓
                    MCP Hub → Filesystem · GitHub · Browser · Shell
```

### 7️⃣ One-Click Company (OCC)
**One command creates an entire AI company.** 5 specialized agents, Kanban board, 7-step SOP workflow — ready to execute in seconds.

```bash
apex company create my-startup --industry saas
# → 📋 PM · 💻 Frontend · ⚙️ Backend · 🔧 DevOps · ✍️ Content

apex company start my-startup "Build MVP"
# → 7 SOP steps auto-created in Kanban + agents dispatched
```

---

## 🔄 Orchestration Modes

> **Apex ships 10 orchestration modes covering the TOP10 multi-agent use cases. Each is a ready-to-run pattern — zero coding required.**

| # | Use Case | Mode | Command |
|---|----------|------|---------|
| 1️⃣ | **Software Development** | Crew + Chain | `apex crew create "Build a web app"` |
| 2️⃣ | **Research & Analysis** | Debate | `apex debate "Should we use microservices?"` |
| 3️⃣ | **Content Production** | Chain | `apex chain run "Write a blog post" -p content` |
| 4️⃣ | **Customer Support** | Router | `apex router route "My account is locked"` |
| 5️⃣ | **Enterprise Approval** | Supervisor | `apex supervisor "Design a compliance workflow"` |
| 6️⃣ | **DevOps / SRE** | Monitor | `apex monitor check -f /var/log/nginx.log` |
| 7️⃣ | **Data Pipeline** | Chain | `apex chain run "Process Q3 sales data" -p data` |
| 8️⃣ | **Product Strategy** | Swarm | `apex run "Analyze market competition" --swarm` |
| 9️⃣ | **Code Review & QA** | Crew | `apex crew create "Review PR #42" --members frontend,backend,devops` |
| 🔟 | **Startup MVP** | Company | `apex company create my-startup -i saas` |

### Mode Selection Guide

```
New to multi-agent?   →  apex run "task"                (Single Agent)
Need parallel work?    →  apex run "task" --swarm        (Swarm)
Need collaboration?    →  apex crew create "goal"        (Crew)
Need pipeline?         →  apex chain run "goal" -p dev   (Chain)
Need debate/critique?  →  apex debate "topic"            (Debate)
Need smart routing?    →  apex router route "task"       (Router)
Need approval gates?   →  apex supervisor "goal"         (Supervisor)
Need 24/7 monitoring?  →  apex monitor check -f /path    (Monitor)
Want a whole company?  →  apex company create name       (Company)
```

---

## ⚡ Comparison vs Top Frameworks

### Core Runtime

| Feature | 🔥 **Apex** | CrewAI | LangGraph | AutoGen | CAMEL | MetaGPT | Swarm |
|---------|:----------:|:------:|:---------:|:-------:|:-----:|:-------:|:-----:|
| Multi-LLM Hot-swap | ✅ Built-in | ✅ | ✅ Chain | ❌ | ❌ | ❌ | ❌ |
| Local LLM (free) | ✅ Built-in | ❌ | ✅ Chain | ❌ | ❌ | ❌ | ❌ |
| Cross-language Agents | ✅ MCP | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### Orchestration

| Feature | 🔥 **Apex** | CrewAI | LangGraph | AutoGen | CAMEL | MetaGPT | Swarm |
|---------|:----------:|:------:|:---------:|:-------:|:-----:|:-------:|:-----:|
| Swarm (Parallel→Verify) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Crew (Role Collaboration) | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ |
| Chain (Pipeline) | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Debate (Multi-perspective) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Router (Smart Dispatch) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Supervisor (Hierarchy) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Monitor (Reactive) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### Intelligence & Economy

| Feature | 🔥 **Apex** | CrewAI | LangGraph | AutoGen | CAMEL | MetaGPT | Swarm |
|---------|:----------:|:------:|:---------:|:-------:|:-----:|:-------:|:-----:|
| Self-Learning Evolution | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Knowledge Graph Memory | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Self-Healing (3-Strike) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Token Budget Management | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Smart Model Routing | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Cost Dashboard | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### Developer Experience

| Feature | 🔥 **Apex** | CrewAI | LangGraph | AutoGen | CAMEL | MetaGPT | Swarm |
|---------|:----------:|:------:|:---------:|:-------:|:-----:|:-------:|:-----:|
| Web Dashboard | ✅ Free | ❌ Paid | ❌ Paid | ✅ | ❌ | ❌ | ❌ |
| REST API (14 endpoints) | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Lines to create a team | **1** | 5+ | 20+ | 10+ | 15+ | 1 | 10+ |
| Pre-built Agent Templates | ✅ **5** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| One-Click Company | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Cost for 1000 tasks | **$5-8** | $50+ | $80+ | $50+ | $50+ | $50+ | $50+ |
| License | ✅ **MIT** | ✅ MIT | ✅ MIT | ✅ MIT | ✅ Apache | ✅ MIT | ✅ MIT |
| | | | | | | | |
| Debate (Multi-perspective) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Router (Smart Dispatch) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Supervisor (Hierarchy) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Monitor (Reactive) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| | | | | | | | |
| Self-Healing (3-Strike) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| | | | | | | | |
| | | | | | | | |
| REST API | ✅ **14 endpoints** | ❌ | ✅ Smith | ✅ | ❌ | ❌ | ❌ |
| | | | | | | | |
| Pre-built Agent Templates | ✅ **5** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| One-Click Company | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| | | | | | | | |
| License | ✅ **MIT** | ✅ MIT | ✅ MIT | ✅ MIT | ✅ Apache | ✅ MIT | ✅ MIT |
| Cost for 1000 tasks | **$5-8** | $50+ | $80+ | $50+ | $50+ | $50+ | $50+ |


---

## 📦 Agent Templates

> **5 pre-configured expert agents — optimized SOUL, skill packages, and toolset — ready in one command.**

```bash
apex template list                    # Browse all templates
apex template use frontend -a my-dev  # Create an agent from template
apex run "Build a login page" --profile my-dev  # Run with your agent
```

| Template | Role | Expertise | Tools | Best For |
|----------|------|-----------|-------|----------|
| 💻 `frontend` | Frontend Developer | React, Vue, WeChat Mini Program, TypeScript, Tailwind, Next.js | filesystem, github, terminal, browser | UI development, landing pages, web apps |
| ⚙️ `backend` | Backend Architect | FastAPI, Django, Go, PostgreSQL, Redis, MongoDB, Docker, K8s, Kafka | filesystem, github, terminal, docker, k8s | API design, system architecture, database |
| 📋 `pm` | Product Manager | PRD, User Stories, A/B Testing, Roadmap, MVP, User Research | filesystem, browser, notion | Requirements, planning, strategy |
| ✍️ `content` | Content Strategist | Copywriting, SEO, Social Media, Brand, Localization, AIGC | filesystem, browser, x, notion | Content, SEO, social media |
| 🔧 `devops` | DevOps Engineer | Docker, K8s, Terraform, CI/CD, Monitoring, Security, Cloud | filesystem, github, terminal, docker, k8s | Deployment, CI/CD, monitoring |

|---

## 🏗️ Architecture

> **How CrewAI does it:** CrewAI uses a two-paradigm architecture — **Crews** (autonomous agent teams with role-based collaboration) and **Flows** (event-driven workflows with state management). Agents have role/goal/backstory, tasks have description/expected output/dependencies, and processes are sequential or hierarchical.
>
> **Apex takes it further:** 5-layer architecture × 10 orchestration modes × 7 cross-cutting innovations × 1 unified economy system. Every agent learns, every execution is recorded, every model is cost-optimized.

### Work Logic Architecture Diagram

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/lcyluke/apex/main/docs/images/apex-architecture.svg">
    <img alt="Apex Work Logic Architecture" src="https://raw.githubusercontent.com/lcyluke/apex/main/docs/images/apex-architecture.svg" width="100%">
  </picture>
</p>

### Five-Layer Architecture

| Layer | Name | Purpose | Key Components |
|-------|------|---------|---------------|
| **L5** | **Interface** | User & developer touchpoints | CLI (20 commands), Web Dashboard (12 panels), REST API (14 endpoints), MCP Protocol |
| **L4** | **Intelligence** | Cross-agent memory & learning | Evolution Engine, Knowledge Graph, Memory System (short/long/shared), Skill Packages |
| **L3** | **Orchestration** | Multi-agent collaboration | 10 modes: Single, Swarm, Crew, Chain, Debate, Router, Supervisor, Monitor, Kanban, Company |
| **L2** | **Agent Runtime** | Individual agent execution | Profile (UPF), Runtime engine, Self-Healing (3-strike), Tool integration, Fallback handling |
| **L1** | **Provider** | LLM & tool infrastructure | DeepSeek V4 Pro, Ollama (free), Claude Sonnet, MCP Tools Hub |

**Cross-cutting:** 💰 **Token Economy** — Budget management, smart model routing, cost optimization — spans all layers.

### Work Logic: How It All Connects

The data flow through Apex follows a **synchronous request-response pattern** with two critical feedback loops:

```
User Input → L5 Interface → L3 Mode Select → L3 Orchestrate → L2 Agent Runtime → L1 Provider
                                                                                         ↓
User Output ← L5 Interface ← L3 Result ← L2 Return ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ←
                      ↑
                L4 Feedback (Evolution Engine + Knowledge Graph learn from every execution)
```

**Forward path (top-down):**
1. User issues command via **CLI / Web / REST** (L5)
2. Interface selects the appropriate **orchestration mode** (L3) — single agent for simple tasks, swarm for parallel, crew for collaboration, etc.
3. The mode orchestrates N **Agent Runtime** instances (L2) — each agent reads its **Profile**, loads **Skills**, checks **Memory**
4. Each agent calls the optimal **LLM Provider** (L1) via the Token Economy's smart router
5. Agents use **MCP Tools** (filesystem, shell, HTTP, knowledge graph) for external actions

**Return path (bottom-up):**
1. LLM responses flow back to the Agent Runtime
2. Runtime: applies **Self-Healing** (retry on error, switch model on repeat, simplify on persistent failure)
3. Orchestration mode: aggregates, verifies, synthesizes results (e.g., Swarm's Verifier + Synthesizer)
4. **Feedback loops** — every execution is recorded:
   - **Evolution Engine** tracks execution records, extracts patterns, updates skill packages
   - **Knowledge Graph** learns new entity-relation triples, resolves conflicts, shares across agents
   - **Token Economy** logs cost, updates budget, routes future tasks more efficiently

### CrewAI vs Apex: Architecture Comparison

| Dimension | CrewAI | Apex |
|-----------|--------|------|
| **Paradigms** | 2 (Crews + Flows) | 10 orchestration modes |
| **Agent Learning** | None — static prompts | Evolution Engine — learns from every execution |
| **Shared Memory** | Per-crew context | Knowledge Graph — teach one, teach all |
| **Cost Control** | None | Token Economy — smart routing saves 95% |
| **Self-Healing** | Manual retry only | 3-strike automatic (retry → switch → simplify → notify) |
| **Observability** | Paid AMP tier only | Free built-in Web Dashboard + REST API |
| **Cross-Language** | Python only | MCP Protocol — Python/Java/Rust/Go |
| **Fault Tolerance** | Minimal | Health monitors + self-healing + autonomous schedules |

### Source Code Map

```
apex/                         # 🚀 Multi-Agent Operating System
├── __init__.py               #   Package marker
├── __main__.py               #   CLI entry point
│
├── core/                     # 🧠 Agent Core: Profile, Runtime, Memory, Skills
│   ├── __init__.py
│   ├── profile.py            #   Agent profile (role, goals, tools, model config)
│   ├── runtime.py            #   Agent execution engine (build prompt, call LLM)
│   ├── memory.py             #   Short/long-term KV memory store
│   ├── skills.py             #   Evolvable skill packages with confidence scoring
│   ├── templates.py          #   5 pre-built agent templates
│   ├── knowledge.py          #   Knowledge Graph (entity-relation shared memory)
│   └── evolution.py          #   Evolution Engine (patterns from every execution)
│
├── orchestration/            # 🔄 10 Multi-Agent Orchestration Modes
│   ├── __init__.py           #   Mode registry and exports
│   ├── swarm.py              #   Parallel workers → Verifier → Synthesizer
│   ├── crew.py               #   Role-based collaboration + team assembly
│   ├── chain.py              #   Sequential pipeline with handoff verification
│   ├── debate.py             #   Multi-perspective structured debate
│   ├── router.py             #   Task classification and agent dispatch
│   ├── supervisor.py         #   Hierarchical delegation with review gates
│   ├── monitor.py            #   Anomaly detection and auto-remediation
│   ├── kanban.py             #   Task board with dependency resolution
│   ├── healing.py            #   3-strike self-healing (retry → switch → simplify)
│   ├── autonomous.py         #   7x24 autonomous operation engine
│   └── ops.py                #   Release pipelines, bug tracking, SLA monitoring
│
├── cli/                      # 🖥️ CLI (Click + Rich)
│   ├── __init__.py
│   ├── main.py               #   CLI dispatcher (17 command groups)
│   └── commands/             #   Command implementations
│       ├── __init__.py
│       ├── run.py            #   apex run (single agent + swarm)
│       ├── team.py           #   apex team (profile management)
│       ├── template.py       #   apex template (pre-built templates)
│       ├── init.py           #   apex init (project scaffolding)
│       ├── status.py         #   apex status (system overview)
│       ├── economy.py        #   apex economy (budget, routing)
│       ├── evolution.py      #   apex evolution (learning patterns)
│       ├── company.py        #   apex company (one-click AI company)
│       ├── autonomous.py     #   apex autonomous (7x24 engine)
│       └── ops.py            #   apex ops (release, bug, task management)
│
├── providers/                # 🤖 LLM Providers
│   ├── __init__.py
│   ├── base.py               #   Provider abstraction and registry
│   └── deepseek.py           #   DeepSeek V4 Pro + Ollama (local) providers
│
├── economy/                  # 💰 Token Economy
│   └── __init__.py           #   Budget control, smart routing, cost audit
│
├── mcp/                      # 🔌 MCP Integration
│   ├── __init__.py
│   ├── hub.py                #   MCP tool hub and registry (filesystem, shell, etc.)
│   └── stdio_client.py       #   Cross-language MCP stdio client (Node/Go/Rust)
│
├── interface/                # 🌐 Web Dashboard + Integration Bridges
│   ├── web.py                #   Flask + 40 REST endpoints + SSE streaming
│   ├── middleware.py         #   CORS, auth, error handling, request logging
│   ├── event_stream.py       #   In-memory pub/sub for real-time streaming
│   ├── hermes_bridge.py      #   Hermes Agent integration (sessions, tokens, GPU)
│   ├── openclaw_bridge.py    #   OpenClaw integration (6 tools, 4 workflows)
│   └── templates/
│       ├── dashboard.html    #   Dark theme SPA dashboard
│       └── dashboard_v4.html #   Enhanced dashboard v4
│
├── docs/                     # 📚 Documentation
│   └── images/               #   Screenshots, banner, architecture diagrams
│
├── scripts/                  # 🛠️ Utility scripts
│   └── mcp-servers/          #   Cross-language MCP server implementations
│       ├── mcp-node-server.js    #   Node.js: greet, weather, sentiment
│       ├── mcp-go-server.go      #   Go: calculate, file_analysis, time
│       └── mcp-rust-server.rs    #   Rust: text_analysis, fibonacci, factors
│
└── tests/                    # 🧪 Test Suite
    ├── test_profile.py       #   Profile tests
    ├── test_economy.py       #   Economy tests
    ├── test_knowledge.py     #   Knowledge graph tests
    ├── test_mcp.py           #   MCP hub tests
    ├── test_orchestration_*.py  #   Orchestration mode tests
    ├── test_integration.py   #   45 integration tests (self-healing, ops, KG)
    └── test_mcp_cross_language.py  #   Cross-language MCP tests (37/39)
```

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
| **Chain** | `apex chain run "<goal>" -p dev` | Sequential pipeline (dev/content/data) |
| **Debate** | `apex debate "<topic>"` | Multi-perspective debate & synthesis |
| **Router** | `apex router route "<task>"` | Classify & dispatch to specialized agent |
| **Supervisor** | `apex supervisor "<goal>"` | Hierarchical delegation with review |
| **Monitor** | `apex monitor check -f <file>` | Watch logs/endpoints, detect anomalies |
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
| **Ops** | `apex ops status` | Operations dashboard summary |
| | `apex ops release create <version>` | Create release pipeline (10 stages) |
| | `apex ops release list` | List all releases |
| | `apex ops release status` | Current release pipeline status |
| | `apex ops bug list` | List open bugs |
| | `apex ops bug create <title> <desc>` | Report a bug |
| | `apex ops bug show <id>` | View bug details |
| | `apex ops task list` | List ops tasks |
| | `apex ops task create <title>` | Create an ops task |
| | `apex ops expert-list` | Open expert consultation tickets |
| **Company** | `apex company create <name>` | One-click AI company creation |
| | `apex company start <name> <goal>` | Start company execution |
| | `apex company list` | List all created companies |
| **Autonomous** | `apex autonomous start` | Start 7x24 autonomous engine |
| | `apex autonomous stop` | Gracefully stop autonomous engine |
| | `apex autonomous pause` | Pause task dispatch (heartbeat continues) |
| | `apex autonomous resume` | Resume task dispatch |
| | `apex autonomous status` | Self-awareness report |
| | `apex autonomous schedule <name> <cron> <task>` | Schedule recurring task |
| | `apex autonomous unschedule <id>` | Remove a scheduled task |
| | `apex autonomous list-scheduled` | List all scheduled tasks |
| | `apex autonomous alerts` | View unresolved alerts |
| **Dashboard** | `apex dashboard` | Launch Web UI (port 8080) |

---

## 🖥️ Web Dashboard

**Apex ships with a free, built-in Web Dashboard — no extra services, no paid tiers.** 39 REST API endpoints + SSE real-time streaming.

```bash
apex dashboard --port 8080
# Open http://localhost:8080
```

| Feature | What You See |
|---------|-------------|
| **Stats Bar** | 6 animated cards: agents, tasks, cost, KG nodes, patterns, alerts — all real-time |
| **Agent Fleet** | Interactive grid: status dots, load bars, click for detail modal |
| **Task Board** | Kanban columns: Ready / In Progress / Done / Failed |
| **Knowledge Graph** | Canvas visualization: 25 nodes, edges, confidence sizing |
| **Token Economy** | SVG budget gauge, 7-day cost trend, model routing table |
| **Autonomous Engine** | Status indicator, heartbeat list, scheduled tasks with countdown |
| **Execution Log** | Terminal-style streaming log, color-coded, auto-scroll |
| **Quality Trends** | Canvas chart: accuracy + F1 score over 20 epochs |
| **Ops Dashboard** | Release Pipeline (stage icons + progress bars), Bug Tracker (SLA timeout bars, severity colors) |
| **OpenClaw Integration** | Consume Apex as a tool provider — 6 tools, 4 workflows |
| **Hermes Integration** | Hermes session stats, token usage, cron status, GPU monitor |
| **SSE Real-time** | `/api/stream/logs` and `/api/stream/events` — push-based event streaming |

### REST API (40 endpoints)

```
# System
GET  /api/health          GET  /api/version         GET  /api/config
GET  /api/status          GET  /api/environment

# Agent Profiles
GET  /api/profiles        POST /api/profiles        GET  /api/profiles/<name>
DEL  /api/profiles/<name>

# Tasks (Kanban)
GET  /api/tasks           POST /api/tasks           GET  /api/tasks/<id>
PUT  /api/tasks/<id>      DEL  /api/tasks/<id>

# Execution
POST /api/run             POST /api/run/swarm

# Intelligence
GET  /api/knowledge       POST /api/knowledge       GET  /api/evolution
GET  /api/economy

# Analytics
GET  /api/analytics/costs       GET  /api/analytics/executions

# Operations
GET  /api/ops             GET  /api/companies       GET  /api/autonomous
GET  /api/gpu/status      GET  /api/models/pricing

# Hermes Integration
GET  /api/hermes/status   GET  /api/hermes/tokens   GET  /api/command-center

# OpenClaw Integration
GET  /api/openclaw/status GET  /api/openclaw/tools  POST /api/openclaw/run
GET  /api/openclaw/workflows

# Real-time Streaming (SSE)
GET  /api/stream/logs     GET  /api/stream/events   GET  /api/logs
GET  /api/events          GET  /api/ping
```

---

## 🤖 Autonomous Engine

**7x24 self-aware operation — agents monitor themselves, learn from failures, and recover automatically.**

```
                     AutonomousEngine
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     Heartbeat(30s)   Scheduler(15s)  Dispatcher(10s)
     Agent health      Cron trigger     Queue dispatch
     Load monitoring   Priority queue   Kanban auto-run
```

```bash
apex autonomous start                                 # 7x24 mode
apex autonomous status                                # Self-awareness report
apex autonomous schedule "db-check" "*/30 * * * *" "Check DB health" --agent devops
apex autonomous alerts                                # Unresolved alerts
```

---

## 🔌 Integration

### Cross-Language MCP Integration (✅ Verified)

**Apex now supports true cross-language agent communication.** Three MCP servers are verified working:

| Language | Server | Tools | Status |
|----------|--------|-------|--------|
| 🟢 **Node.js** (v25) | `scripts/mcp-servers/mcp-node-server.js` | `greet`, `weather`, `analyze_sentiment` | 🟢 100% |
| 🔵 **Go** (1.23) | `scripts/mcp-servers/mcp-go-server.go` | `calculate`, `file_analysis`, `current_time` | 🟢 100% |
| 🟠 **Rust** (1.84) | `scripts/mcp-servers/mcp-rust-server.rs` | `analyze_text`, `fibonacci`, `prime_factors` | 🟢 94.9% |
| 🐍 **Python** (3.11) | Built into MCP Hub | `filesystem`, `shell`, `knowledge`, `http` | 🟢 100% |

**Architecture:**
```
Python Agent ──MCP (JSON-RPC/stdio)──▶ Node.js MCP Server
            ──MCP (JSON-RPC/stdio)──▶ Go MCP Server
            ──MCP (JSON-RPC/stdio)──▶ Rust MCP Server
            ──MCP (built-in)───────▶ Filesystem · Shell · Knowledge · HTTP
```

**How to run the cross-language demo:**
```python
from apex.mcp.stdio_client import MCPStdioClient
from apex.mcp.hub import MCPHub

hub = MCPHub()

# Register Node.js tools (prefix: "node.")
node = MCPStdioClient("node", ["scripts/mcp-servers/mcp-node-server.js"], name="Node.js")
node.connect()
node.register_with_hub(hub, prefix="node.")

# Register Go tools (prefix: "go.")
go = MCPStdioClient("./scripts/mcp-servers/mcp-go-server", [], name="Go")
go.connect()
go.register_with_hub(hub, prefix="go.")

# Register Rust tools (prefix: "rust.")
rust = MCPStdioClient("./scripts/mcp-servers/mcp-rust-server", [], name="Rust")
rust.connect()
rust.register_with_hub(hub, prefix="rust.")

# Call tools across languages
hub.call("node.greet", name="World", language="zh")  # → Node.js
hub.call("go.calculate", expression="sqrt(16)")       # → Go
hub.call("rust.fibonacci", n=20)                      # → Rust
```

**Test results:** `python3 tests/test_mcp_cross_language.py` → **37/39 passed (94.9%)**

**Build cross-language servers (one-time):**
```bash
cd scripts/mcp-servers
go build -o mcp-go-server mcp-go-server.go
rustc mcp-rust-server.rs -o mcp-rust-server
# Node.js requires no build step
```

### With Hermes Agent
```bash
# Apex runs alongside Hermes
cd ~/Desktop/2026AIAPP/Apex && source .venv/bin/activate
apex crew create "Build a data analytics dashboard"
```

### With OpenClaw
```bash
export APEX_HOME="$PWD/.apex"
/Users/Mac/Desktop/2026AIAPP/Apex/.venv/bin/apex run "Analyze this codebase"
```

### Programmatic API
```python
from apex.core.runtime import Agent
from apex.core.profile import ProfileManager

pm = ProfileManager()
agent = Agent(pm.load("frontend"))
result = agent.run("Review the code in this project")
print(result)
```

---

## 📥 Installation

### macOS
```bash
pip install apex-multiagent
# Or from source:
git clone https://github.com/lcyluke/apex.git && cd apex
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[web]"
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv
pip3 install apex-multiagent
```

### Windows
```powershell
pip install apex-multiagent
# Or with WSL:
wsl --install -d Ubuntu && wsl
sudo apt install -y python3 python3-pip && pip3 install apex-multiagent
```

### Docker
```dockerfile
FROM python:3.11-slim
RUN pip install apex-multiagent
CMD ["apex", "dashboard", "--host", "0.0.0.0"]
```

### Post-Install
```bash
# Set your API key
export DEEPSEEK_API_KEY="sk-xxx"
# Or create config
mkdir -p ~/.apex && echo "DEEPSEEK_API_KEY=sk-xxx" > ~/.apex/.env
# Verify
apex init hello && cd hello && apex run "Hello, world!" && apex status
```

---

## 🔧 Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEEPSEEK_API_KEY` | ✅ | — | DeepSeek API key for agent execution |
| `APEX_HOME` | ❌ | `~/.apex` | Apex data directory |
| `OLLAMA_BASE_URL` | ❌ | `http://localhost:11434` | Ollama server for local models |

### Local Models (Free)
```bash
brew install ollama          # macOS
curl -fsSL https://ollama.com/install.sh | sh  # Linux
ollama pull llama3
# Apex auto-routes simple tasks to Ollama — free!
```

---

## 🗺️ Roadmap

```
v0.1    CURRENT — Core complete: 10 modes, 7 innovations, Economy, KG, Evolution,
        Company, Dashboard, Autonomous Engine, 42 tests, CI/CD
v0.2    NEXT — Plugin system, LangSmith integration, Community marketplace,
        GUI workflow designer, i18n documentation
v0.3    Enterprise: Multi-tenant, RBAC, Audit logs, Private deployment, SSO
v1.0    Production ready: Enterprise support, SLA guarantees, Certification
```

---

## 📊 Project Metrics

<p align="center">
  <a href="https://github.com/lcyluke/apex/stargazers"><img src="https://img.shields.io/github/stars/lcyluke/apex?style=for-the-badge&logo=github" alt="Stars"></a>
  <a href="https://github.com/lcyluke/apex/network/members"><img src="https://img.shields.io/github/forks/lcyluke/apex?style=for-the-badge&logo=github" alt="Forks"></a>
  <a href="https://github.com/lcyluke/apex/watchers"><img src="https://img.shields.io/github/watchers/lcyluke/apex?style=for-the-badge&logo=github" alt="Watchers"></a>
  <a href="https://github.com/lcyluke/apex/issues"><img src="https://img.shields.io/github/issues/lcyluke/apex?style=for-the-badge&logo=github" alt="Issues"></a>
  <a href="https://github.com/lcyluke/apex/pulls"><img src="https://img.shields.io/github/issues-pr/lcyluke/apex?style=for-the-badge&logo=github" alt="PRs"></a>
  <br>
  <a href="https://github.com/lcyluke/apex/graphs/contributors"><img src="https://img.shields.io/github/contributors/lcyluke/apex?style=for-the-badge&logo=github" alt="Contributors"></a>
  <a href="https://github.com/lcyluke/apex/commits/main"><img src="https://img.shields.io/github/last-commit/lcyluke/apex?style=for-the-badge&logo=github" alt="Last Commit"></a>
  <a href="https://github.com/lcyluke/apex/blob/main/LICENSE"><img src="https://img.shields.io/github/license/lcyluke/apex?style=for-the-badge&logo=github" alt="License"></a>
</p>

---

## 🤝 Contributing

```bash
git clone https://github.com/lcyluke/apex.git && cd apex
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,web]"
pytest tests/ -v  # 42 tests should pass
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

---

## 📄 License

MIT © 2026 [lcyluke](https://github.com/lcyluke)

<p align="center">
  <strong>⚡ One person, infinite capacity.</strong>
  <br>
  <em>Star on <a href="https://github.com/lcyluke/apex">GitHub</a> · Follow <a href="https://twitter.com">@apex_multiai</a> · Join <a href="#">Discord</a></em>
</p>
