<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/lcyluke/apex/main/docs/images/apex-banner.png">
    <img alt="Apex — Multi-Agent Operating System" src="https://raw.githubusercontent.com/lcyluke/apex/main/docs/images/apex-banner.png" width="800">
  </picture>
</p>

<p align="center">
  <strong>One person, infinite capacity.</strong><br>
  <em>Multi-Agent Operating System — 46 agents, 30 commands, one CLI.</em>
</p>

<p align="center">
  <a href="https://github.com/lcyluke/apex/releases"><img src="https://img.shields.io/github/v/release/lcyluke/apex?style=flat-square&color=3b82f6" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10%2B-orange?style=flat-square" alt="Python"></a>
  <img src="https://img.shields.io/badge/platform-macOS%20|%20Linux%20|%20Windows-lightgrey?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/agents-46-teal?style=flat-square" alt="Agents">
  <img src="https://img.shields.io/badge/commands-30-blue?style=flat-square" alt="Commands">
</p>

---

## ⚡ Quick Start

```bash
# Install
brew install lcyluke/homebrew-apex/apex

# Or via pip
pip install apex-multiagent

# Interactive project wizard (8 steps)
apex init my-project

# 5-minute demo — opens Command Center
apex demo

# Interactive walkthrough
apex tutorial
```

---

## 📋 Installation

### macOS (Homebrew)

```bash
brew tap lcyluke/apex
brew install apex
```

Verify:
```bash
apex --version
# Apex v0.5.0 — 46 Agents, 30 commands, infinite capacity.
apex doctor
# ✅ 一切正常
```

### pip

```bash
pip install apex-multiagent
# or from source:
pip install git+https://github.com/lcyluke/apex.git@v0.5.0
```

---

## 🎓 Getting Started

```bash
# 1. Interactive tutorial — 5 steps, 3 minutes
apex tutorial

# 2. System check
apex doctor

# 3. Create your first project
apex init my-saas
# → 8-step wizard: name → type → scale → tech stack → agents → integrations → roadmap → create

# 4. Quick init (skip wizard)
apex init --quick

# 5. Launch demo
apex demo
# → 3 demo tasks + Command Center at http://localhost:8080
```

---

## 📊 Command Reference

```
Usage: apex [options] [command]

Options:
  -m, --model <model>       Model override (e.g. deepseek-v4-pro)
  -p, --profile <name>      Agent profile to use
  -s, --swarm               Swarm mode for parallel execution
  -w, --workers <n>         Parallel workers (default: 3)
  -h, --help                Display help for command
  -V, --version             Output the version number

Commands:
  Hint: commands suffixed with * have subcommands.

  Setup & Start:
      setup                First-time setup
      quickstart           Quick start guide
      init                 Interactive project wizard (8 steps)
      demo                 Launch demo fleet + Command Center
      model-detect         Auto-detect available AI models

  Local Management:
      fleet *              Fleet Monitor
      monitor *            Agent status dashboard
      version              Show version + check for updates
      update               Self-update to latest release
      theme *              Switch CLI color themes
      alias *              Command aliases
      tutorial             5-step interactive walkthrough
      doctor               System diagnostics + auto-fix

  Task Management:
      task *               Task dispatch + scheduling
      run                  Execute a task
      chat *               Chat with an agent
      status               View current status

  Team & Agents:
      team *               Team management
      mode *               Collaboration modes

  PM & Project:
      pm *                 Project scheduling + assignment
      project *            Project management
      survey               Competitive survey
      dashboard            Start Web Dashboard

  System:
      system *             System management

  Integration:
      help *               Cross-agent help system
      integrate *          Hermes/OpenClaw integration
      origin *             Portfolio commander
```

### Built-in Shortcuts

```
apex s    → monitor status     Agent status panel
apex p    → pm dashboard       PM dashboard
apex fs   → fleet status       Fleet overview
apex v    → version            Show version
apex up   → update             Self-update
```

---

## 🏗️ Project Factory (`apex init`)

8-step interactive wizard with intelligent agent matching:

```
Step 1: Project Identity     name, description, tagline
Step 2: Project Type         12 presets with smart keyword detection
Step 3: Scale                MVP / Startup / Growth / Enterprise
Step 4: Tech Stack           auto-recommend + customize per layer
Step 5: Agent Team           intelligent assignment, add/remove/confirm
Step 6: Integrations         WeChat / DingTalk / Feishu webhook config
Step 7: Roadmap              MVP definition, 24h plan, sprint tasks
Step 8: Confirm & Create     generates all project files
```

**12 Project Presets:**

| Type | Best For |
|------|----------|
| 📊 SaaS Dashboard | Admin panels, analytics dashboards |
| 🌐 Web Application | Full-stack web apps |
| 🛒 E-Commerce | Online stores, marketplaces |
| 🤖 AI Agent System | Multi-agent platforms |
| 🧠 ML Platform | Model training, deployment |
| 📊 Data Platform | Data pipelines, analytics |
| 💰 FinOps | Cloud cost optimization |
| ⌨️ CLI Tool | Developer tools, SDKs |
| 📱 Mobile App | iOS/Android apps |
| 🔒 Security Tool | Vulnerability scanners |
| 📝 Content Platform | CMS, blogs, wikis |
| 🎯 General | Any project |

---

## 📊 Command Center Dashboard

```bash
apex dashboard          # Start at http://localhost:8080
apex demo               # Demo with 3 pre-created tasks
```

**Features:**
- Real-time agent fleet monitoring
- Project war room with pipeline view
- User settings (profile, language, theme, notifications)
- Auto-sync with configurable interval (5s–60s)
- Click-to-cycle sync frequency
- Connection status indicator

---

## 👥 Agent Profiles

46 pre-built agent profiles covering every role:

| Category | Agents |
|----------|--------|
| Core Team | pm, architect, backend-dev, frontend-dev, devops, qa-engineer, fleet-commander |
| FinOps | finops-architect, finops-backend, finops-devops, finops-frontend, finops-pm |
| Security | vulnerability-scanner, penetration-tester, security-by-design, security-compliance |
| ML & Data | ml-engineer, data-engineer, data-analyst, data-scientist |
| PM & Ops | product-manager, project-manager, pm-agentops, ops-engineer |
| Specialists | 20+ more (badminton-pm, fundraising-pitch, gpu-sentinel, etc.) |

---

## 🔌 Integrations

| Platform | Status |
|----------|--------|
| Hermes Agent | Native — AGENTS.md injection, profile sync, session bridge |
| WeChat (企业微信) | Webhook config in project setup |
| DingTalk (钉钉) | Webhook config in project setup |
| Feishu (飞书) | Webhook config in project setup |

---

## 🧪 Demo

```bash
apex demo
```

What happens:
1. Environment check (python, dashboard, kanban, browser)
2. Creates 3 demo tasks (Frontend, Backend, PM)
3. Starts Command Center at http://localhost:8080
4. Opens browser with real-time dashboard
5. Press Ctrl+C to stop

---

## 🏗️ Architecture

```
apex/
├── cli/              CLI (Click + Rich, 30 commands, 7 groups)
│   ├── main.py       AliasedGroup, OpenClaw-style help
│   └── commands/     Command implementations
├── core/             Agent core (profile, runtime, memory, skills)
├── orchestration/    Multi-agent orchestration
├── interface/        Web dashboard + Hermes integration
│   ├── web.py        Flask REST API + SSE
│   ├── templates/    Command Center HTML
│   ├── project_factory.py   8-step project wizard
│   └── hermes_context.py    AGENTS.md generator
├── economy/          Token economy
├── fleet/            Fleet profiles (46 agents)
└── docs/             Documentation
```

---

## 🔧 Development

```bash
git clone https://github.com/lcyluke/apex.git
cd apex
pip install -e .

# Run tests
python -m pytest tests/ -q

# Dev mode
apex --help
```

---

## 📄 License

MIT — see [LICENSE](LICENSE).
