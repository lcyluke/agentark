# Multi-Agent Framework Comparison — June 2026

> Reference data from session 2026-06-01.
> Frameworks: MetaGPT / AutoGen / CrewAI / LangGraph / CAMEL
> This session produced: analysis report → hybrid recommendation → independent build decision → Apex v0.1.0

## Baseline Data

| Project | Stars | Language | Last Active | Positioning |
|---------|-------|----------|-------------|-------------|
| MetaGPT | 68.5k | Python | months ago | Software company SOP simulator |
| AutoGen | 58.6k | Python | Maintenance mode | Enterprise replaced by MAF |
| CrewAI | 52.6k | Python | hours ago | Role-based agent teams |
| LangGraph | 33.6k | Python | minutes ago | State graph orchestration |
| CAMEL | 17.1k | Python | days ago | Research multi-agent |

## Key Findings

### Who Wins What

| Dimension | Winner | Why |
|-----------|--------|-----|
| Harness | LangGraph | Pregel/Beam, durable execution, LangSmith |
| Prompt/Ctx | CAMEL | Code-as-Prompt, dynamic protocols |
| Self-learning | CAMEL | RL + verifiable rewards, scaling laws |
| Team Mgmt | CrewAI | Three-tier, Manager Agent, Flows |
| Monitoring | LangGraph+Smith | Trace, viz, metrics |
| Collaboration | CrewAI | Auto delegation, dependencies |

### Initial Recommendation

CrewAI + Hermes hybrid.

### Final Decision: Build Apex Instead

Apex at ~/Desktop/2026AIAPP/Apex/. Absorbs:
- CrewAI role-based teams
- LangGraph state machines
- CAMEL self-learning vision
- MetaGPT SOP automation
- Hermes Profile/Memory/Skills
- AutoGen MCP support
- Original: Token Economy, zero-click teaming, self-healing, knowledge graph memory

### URLs

- MetaGPT: https://github.com/FoundationAgents/MetaGPT
- Autogen: https://github.com/microsoft/autogen
- CrewAI: https://github.com/crewAIInc/crewAI
- LangGraph: https://github.com/langchain-ai/langgraph
- CAMEL: https://github.com/camel-ai/camel
