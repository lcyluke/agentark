# 7-Framework Mega-Comparison Pattern

This reference documents the comparison approach used in the GitHub Top 5 multi-agent framework analysis (June 2026) and the Apex vs Top 7 comparison table in the README.

## Framework Set

When doing a multi-agent framework comparison, include ALL of these:

1. **CrewAI** — 52.6k stars, role-based teams
2. **LangGraph** — 33.6k stars, state machine orchestration
3. **AutoGen / MS Agent Framework** — 58.6k stars, Microsoft's framework (note: AutoGen is in maintenance mode)
4. **CAMEL** — 17.1k stars, research-focused, self-learning
5. **MetaGPT** — 68.5k stars, SOP automation (note: stale, last commit >3 months ago)
6. **OpenAI Swarm** — 21.5k stars, educational exploration (not production)
7. **Your product** — always put your own framework first column with a 🔥 or ⚡ emoji

## Comparison Groups (7 groups, 30+ rows)

### Core Runtime
- Persistent Agent Profile
- Multi-LLM Provider
- Local LLM (Ollama)
- Cross-language Agents

### Orchestration
- Single Agent
- Swarm (Parallel → Verify → Synthesize)
- Crew (Role Collaboration)
- Pipeline (Sequential)
- Graph Mode (Custom DAG)
- Dynamic Team Design
- Smart Kanban

### Intelligence
- Self-Learning Evolution
- Knowledge Graph (Shared Memory)
- SOP Auto-Generation
- Self-Healing
- Workflow Optimization

### Economy
- Token Budget Management
- Smart Model Routing
- Cost Dashboard
- Cross-project Budget Transfer

### Observability
- Execution Trace
- Web Dashboard (Free vs Paid)
- REST API
- Real-time Alerts

### Developer Experience
- Lines to create a team
- Time to first task
- Learning curve
- CLI-first
- Pre-built templates
- One-click setup

### Integration & Pricing
- Hermes Agent Plugin
- OpenClaw Compatible
- MCP Native
- Open Source License
- Free Web UI
- Cost for 1000 tasks

## Phases of Analysis

### Phase 1: Landscape Assessment
- Collect baseline data (stars, language, last commit, positioning)
- Flag stale/maintenance-mode projects
- Check README banners for deprecation warnings

### Phase 2: Deep Dive into Each Framework
- Read official README and docs
- Note architecture patterns, not just feature lists
- Identify each framework's ONE unique strength (not everything is equally good)

### Phase 3: Build the Comparison Matrix
- Group by capability domain
- Be honest about your own product's gaps
- Add a "Only We Have" or "Unique Selling Points" summary

### Phase 4: Recommendation
- Never say "it depends" without an opinion
- Cost comparison is the highest-impact row
- Include integration guide for the user's current stack

## Output Formats

1. Markdown — for project docs and GitHub README
2. Word (.docx) — for formal presentation
3. Both go to `~/Desktop/2026AIAPP/LuInsight<Name>/` for standalone studies
