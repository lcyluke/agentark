# Multi-Agent Framework Comparison (2026-06-01)

Quick reference: GitHub Top5 open-source multi-agent frameworks vs Hermes.

## Base Data

| Project | Stars | Language | Active | Positioning |
|---------|-------|----------|--------|-------------|
| MetaGPT | 68.5k | Python | 🔴 5mo stale | Software company SOP simulator |
| AutoGen | 58.6k | Python | 🟡 maintenance | Enterprise multi-agent → replaced by MAF |
| CrewAI | 52.6k | Python | 🟢 8h ago | Role-based agent team orchestration |
| LangGraph | 33.6k | Python | 🟢 8min ago | State-graph orchestration engine |
| CAMEL | 17.1k | Python | 🟢 3d ago | Research multi-agent framework |
| Hermes | ~3k | Python | 🟢 active | CLI-native agent with Profile/Memory/Skills |

## Six-Dimension Scoring (stars out of 5)

| Dimension | Hermes | CrewAI | LangGraph | CAMEL | MetaGPT | AutoGen |
|-----------|--------|--------|-----------|-------|---------|---------|
| Harness | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Context/Prompt | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Self-learning | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| Team Mgmt | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Monitoring | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| Collaboration | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

## Recommendations

- **Winner**: CrewAI + Hermes hybrid architecture (see layered design in SKILL.md)
- **When to skip CrewAI**: Luke's 5h/week side-project scale — Hermes delegate_task + Kanban Swarm covers most needs without CrewAI overhead
- **When to add CrewAI**: a single task genuinely needs multiple agents talking to each other simultaneously (e.g. developer + tester + architect debating a design)
- **Monitoring path**: LangSmith free tier when needed
- **Self-learning path**: borrow CAMEL's RL + data-gen ideas rather than full migration
