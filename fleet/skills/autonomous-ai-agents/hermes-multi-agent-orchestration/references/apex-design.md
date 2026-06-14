# Apex — Independent Multi-Agent Operating System

> Location: `~/Desktop/2026AIAPP/Apex/`
> Version: v0.1.0 (1499 lines, 23 files, Phase 0 completed)
> Status: Working prototype — single agent + Swarm mode verified

## When to Build Apex Instead of Using Hermes Profiles

| Signal | Hermes Profiles | Apex |
|--------|----------------|------|
| Number of agents | 1-9 | 1-unlimited |
| Agent memory sharing | ❌ Each profile isolated | ✅ Shared knowledge graph |
| Dynamic team formation | ❌ Manual Kanban assignment | ✅ AI-designed teams per task |
| Self-healing | ❌ No | ✅ Auto-diagnose + fix |
| Token optimization | ❌ Fixed model per profile | ✅ Smart routing per task value |
| MCP native | ❌ Partial | ✅ All communication via MCP |
| Exportability | ❌ Tied to Hermes config | ✅ Standalone pip package |
| Open source ambition | ❌ Internal tool | ✅ GitHub 60K stars target |

## Architecture (5 Layer Onion)

```
L5: Interface     — CLI / Web UI / REST API / IDE Plugin
L4: Observability — Trace / Dashboard / Cost / Alerts
L3: Intelligence  — Self-learning / SOP gen / Workflow optimization
L2: Orchestration — Swarm / Crew / Pipeline / Graph / Kanban
L1: Runtime       — Profile / Memory / Skills / MCP / Provider
Foundation: Token Economy + Security
```

## Seven Core Innovations

1. **Dynamic Skill Evolution** — Agents learn from every execution; same-error rate drops 90%+
2. **Zero-Click Teaming** — Say the task, Apex designs the optimal team
3. **Self-Healing Workflows** — Errors auto-diagnose and auto-fix (3 retries before human)
4. **Knowledge Graph Memory** — Teach one agent = teach all agents
5. **Token Budget Bank** — Smart routing per task value (save ~95% vs all-Claude)
6. **MCP All** — Cross-language, cross-machine, cross-framework agent communication
7. **One-Click Company** — `apex company create "AI SaaS"` → 2h later MVP is live

## Project Tree

```
apex/
├── core/           → profile.py / runtime.py / memory.py / skills.py
├── providers/      → base.py / deepseek.py (Ollama ready)
├── orchestration/  → swarm.py / kanban.py (Crew/Pipeline/Graph pending)
├── economy/        → (placeholder)
├── mcp/            → (placeholder)
├── cli/            → main.py / commands/
└── pyproject.toml  → click + httpx + pydantic + rich
```

## Development Roadmap

| Phase | Focus | Timeline |
|-------|-------|----------|
| 0 | Core Runtime + Swarm + CLI | ✅ Complete |
| 1 | Crew mode + Self-healing + Token Economy | Next |
| 2 | Web UI + Knowledge Graph + SOP gen | Next+ |
| 3 | Community launch + GitHub 60K stars | Target 3mo |

## How to Run

```bash
cd ~/Desktop/2026AIAPP/Apex
source .venv/bin/activate
apex init my-project
apex run "your task"                     # single agent
apex run "your task" --swarm --workers 3  # swarm mode
apex status                              # dashboard
```

The design white paper is at:
`~/Desktop/2026AIAPP/LuInsightForMutliAgent/Apex_多Agent操作系统设计白皮书.md`
