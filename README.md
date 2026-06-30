     1|<p align="center">
     2|  <picture>
     3|    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/lcyluke/agentark/main/docs/images/agentark-banner.png">
     4|    <img alt="AgentArk — Multi-Agent Operating System" src="https://raw.githubusercontent.com/lcyluke/agentark/main/docs/images/agentark-banner.png" width="800">
     5|  </picture>
     6|</p>
     7|
     8|<p align="center">
     9|  <strong>One person, infinite capacity.</strong><br>
    10|  <em>Multi-Agent Operating System — 46 agents, 30 commands, one CLI.</em>
    11|</p>
    12|
    13|<p align="center">
    14|  <a href="https://github.com/lcyluke/agentark/releases"><img src="https://img.shields.io/github/v/release/lcyluke/agentark?style=flat-square&color=3b82f6" alt="Release"></a>
    15|  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
    16|  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10%2B-orange?style=flat-square" alt="Python"></a>
    17|  <img src="https://img.shields.io/badge/platform-macOS%20|%20Linux%20|%20Windows-lightgrey?style=flat-square" alt="Platform">
    18|  <img src="https://img.shields.io/badge/agents-46-teal?style=flat-square" alt="Agents">
    19|  <img src="https://img.shields.io/badge/commands-30-blue?style=flat-square" alt="Commands">
    20|</p>
    21|
    22|---
    23|
## ⚡ Quick Start

```bash
# 🍺 Homebrew (macOS)
brew install lcyluke/homebrew-apex/agentark

# 🐍 pip (any OS)
pip install git+https://github.com/lcyluke/agentark.git

# 📡 One-liner (curl)
curl -sSL https://raw.githubusercontent.com/lcyluke/agentark/main/scripts/install.sh | bash

# Interactive project wizard (8 steps)
agentark init my-project

# 5-minute demo — opens Command Center
agentark demo

# Interactive walkthrough
agentark tutorial
```

---

## 📋 Installation

### 🍺 macOS (Homebrew)

```bash
brew tap lcyluke/agentark
brew install agentark
```

Verify:
```bash
agentark --version
# AgentArk v0.5.0 — 46 Agents, 30 commands, infinite capacity.
agentark doctor
# ✅ 一切正常
```

### 🐍 pip (Any OS)

```bash
# Direct from GitHub (always latest)
pip install git+https://github.com/lcyluke/agentark.git

# Or from PyPI (coming soon)
pip install agentark-multiagent
```

### 📡 One-liner (curl)

```bash
curl -sSL https://raw.githubusercontent.com/lcyluke/agentark/main/scripts/install.sh | bash
```

This auto-detects Python 3.10+, creates a venv at `~/.agentark/`, installs, and symlinks to `~/.local/bin/agentark`.

### 🔧 From Source

```bash
git clone https://github.com/lcyluke/agentark.git && cd agentark
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```
    53|
    54|Verify:
    55|```bash
    56|agentark --version
    57|# AgentArk v0.5.0 — 46 Agents, 30 commands, infinite capacity.
    58|agentark doctor
    59|# ✅ 一切正常
    60|```
    61|
    62|### pip
    63|
    64|```bash
    65|pip install agentark-multiagent
    66|# or from source:
    67|pip install git+https://github.com/lcyluke/agentark.git@v0.5.0
    68|```
    69|
    70|---
    71|
    72|## 🎓 Getting Started
    73|
    74|```bash
    75|# 1. Interactive tutorial — 5 steps, 3 minutes
    76|agentark tutorial
    77|
    78|# 2. System check
    79|agentark doctor
    80|
    81|# 3. Create your first project
    82|agentark init my-saas
    83|# → 8-step wizard: name → type → scale → tech stack → agents → integrations → roadmap → create
    84|
    85|# 4. Quick init (skip wizard)
    86|agentark init --quick
    87|
    88|# 5. Launch demo
    89|agentark demo
    90|# → 3 demo tasks + Command Center at http://localhost:8080
    91|```
    92|
    93|---
    94|
    95|## 📊 Command Reference
    96|
    97|```
    98|Usage: agentark [options] [command]
    99|
   100|Options:
   101|  -m, --model <model>       Model override (e.g. deepseek-v4-pro)
   102|  -p, --profile <name>      Agent profile to use
   103|  -s, --swarm               Swarm mode for parallel execution
   104|  -w, --workers <n>         Parallel workers (default: 3)
   105|  -h, --help                Display help for command
   106|  -V, --version             Output the version number
   107|
   108|Commands:
   109|  Hint: commands suffixed with * have subcommands.
   110|
   111|  Setup & Start:
   112|      setup                First-time setup
   113|      quickstart           Quick start guide
   114|      init                 Interactive project wizard (8 steps)
   115|      demo                 Launch demo fleet + Command Center
   116|      model-detect         Auto-detect available AI models
   117|
   118|  Local Management:
   119|      fleet *              Fleet Monitor
   120|      monitor *            Agent status dashboard
   121|      version              Show version + check for updates
   122|      update               Self-update to latest release
   123|      theme *              Switch CLI color themes
   124|      alias *              Command aliases
   125|      tutorial             5-step interactive walkthrough
   126|      doctor               System diagnostics + auto-fix
   127|
   128|  Task Management:
   129|      task *               Task dispatch + scheduling
   130|      run                  Execute a task
   131|      chat *               Chat with an agent
   132|      status               View current status
   133|
   134|  Team & Agents:
   135|      team *               Team management
   136|      mode *               Collaboration modes
   137|
   138|  PM & Project:
   139|      pm *                 Project scheduling + assignment
   140|      project *            Project management
   141|      survey               Competitive survey
   142|      dashboard            Start Web Dashboard
   143|
   144|  System:
   145|      system *             System management
   146|
   147|  Integration:
   148|      help *               Cross-agent help system
   149|      integrate *          Hermes/OpenClaw integration
   150|      origin *             Portfolio commander
   151|```
   152|
   153|### Built-in Shortcuts
   154|
   155|```
   156|agentark s    → monitor status     Agent status panel
   157|agentark p    → pm dashboard       PM dashboard
   158|agentark fs   → fleet status       Fleet overview
   159|agentark v    → version            Show version
   160|agentark up   → update             Self-update
   161|```
   162|
   163|---
   164|
   165|## 🏗️ Project Factory (`agentark init`)
   166|
   167|8-step interactive wizard with intelligent agent matching:
   168|
   169|```
   170|Step 1: Project Identity     name, description, tagline
   171|Step 2: Project Type         12 presets with smart keyword detection
   172|Step 3: Scale                MVP / Startup / Growth / Enterprise
   173|Step 4: Tech Stack           auto-recommend + customize per layer
   174|Step 5: Agent Team           intelligent assignment, add/remove/confirm
   175|Step 6: Integrations         WeChat / DingTalk / Feishu webhook config
   176|Step 7: Roadmap              MVP definition, 24h plan, sprint tasks
   177|Step 8: Confirm & Create     generates all project files
   178|```
   179|
   180|**12 Project Presets:**
   181|
   182|| Type | Best For |
   183||------|----------|
   184|| 📊 SaaS Dashboard | Admin panels, analytics dashboards |
   185|| 🌐 Web Application | Full-stack web apps |
   186|| 🛒 E-Commerce | Online stores, marketplaces |
   187|| 🤖 AI Agent System | Multi-agent platforms |
   188|| 🧠 ML Platform | Model training, deployment |
   189|| 📊 Data Platform | Data pipelines, analytics |
   190|| 💰 FinOps | Cloud cost optimization |
   191|| ⌨️ CLI Tool | Developer tools, SDKs |
   192|| 📱 Mobile App | iOS/Android apps |
   193|| 🔒 Security Tool | Vulnerability scanners |
   194|| 📝 Content Platform | CMS, blogs, wikis |
   195|| 🎯 General | Any project |
   196|
   197|---
   198|
   199|## 📊 Command Center Dashboard
   200|
   201|```bash
   202|agentark dashboard          # Start at http://localhost:8080
   203|agentark demo               # Demo with 3 pre-created tasks
   204|```
   205|
   206|**Features:**
   207|- Real-time agent fleet monitoring
   208|- Project war room with pipeline view
   209|- User settings (profile, language, theme, notifications)
   210|- Auto-sync with configurable interval (5s–60s)
   211|- Click-to-cycle sync frequency
   212|- Connection status indicator
   213|
   214|---
   215|
   216|## 👥 Agent Profiles
   217|
   218|46 pre-built agent profiles covering every role:
   219|
   220|| Category | Agents |
   221||----------|--------|
   222|| Core Team | pm, architect, backend-dev, frontend-dev, devops, qa-engineer, fleet-commander |
   223|| FinOps | finops-architect, finops-backend, finops-devops, finops-frontend, finops-pm |
   224|| Security | vulnerability-scanner, penetration-tester, security-by-design, security-compliance |
   225|| ML & Data | ml-engineer, data-engineer, data-analyst, data-scientist |
   226|| PM & Ops | product-manager, project-manager, pm-agentops, ops-engineer |
   227|| Specialists | 20+ more (badminton-pm, fundraising-pitch, gpu-sentinel, etc.) |
   228|
   229|---
   230|
   231|## 🔌 Integrations
   232|
   233|| Platform | Status |
   234||----------|--------|
   235|| Hermes Agent | Native — AGENTS.md injection, profile sync, session bridge |
   236|| WeChat (企业微信) | Webhook config in project setup |
   237|| DingTalk (钉钉) | Webhook config in project setup |
   238|| Feishu (飞书) | Webhook config in project setup |
   239|
   240|---
   241|
   242|## 🧪 Demo
   243|
   244|```bash
   245|agentark demo
   246|```
   247|
   248|What happens:
   249|1. Environment check (python, dashboard, kanban, browser)
   250|2. Creates 3 demo tasks (Frontend, Backend, PM)
   251|3. Starts Command Center at http://localhost:8080
   252|4. Opens browser with real-time dashboard
   253|5. Press Ctrl+C to stop
   254|
   255|---
   256|
   257|## 🏗️ Architecture
   258|
   259|```
   260|apex/
   261|├── cli/              CLI (Click + Rich, 30 commands, 7 groups)
   262|│   ├── main.py       AliasedGroup, OpenClaw-style help
   263|│   └── commands/     Command implementations
   264|├── core/             Agent core (profile, runtime, memory, skills)
   265|├── orchestration/    Multi-agent orchestration
   266|├── interface/        Web dashboard + Hermes integration
   267|│   ├── web.py        Flask REST API + SSE
   268|│   ├── templates/    Command Center HTML
   269|│   ├── project_factory.py   8-step project wizard
   270|│   └── hermes_context.py    AGENTS.md generator
   271|├── economy/          Token economy
   272|├── fleet/            Fleet profiles (46 agents)
   273|└── docs/             Documentation
   274|```
   275|
   276|---
   277|
   278|## 🔧 Development
   279|
   280|```bash
   281|git clone https://github.com/lcyluke/agentark.git
   282|cd apex
   283|pip install -e .
   284|
   285|# Run tests
   286|python -m pytest tests/ -q
   287|
   288|# Dev mode
   289|agentark --help
   290|```
   291|
   292|---
   293|
   294|## 📄 License
   295|
   296|MIT — see [LICENSE](LICENSE).
   297|