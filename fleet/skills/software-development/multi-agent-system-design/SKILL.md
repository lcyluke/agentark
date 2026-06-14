---
name: multi-agent-system-design
description: "Design and build a multi-agent operating system from scratch. Covers architecture design (5-layer onion), seven-core-innovation methodology, token economy, self-healing workflows, dynamic teaming, and phased build roadmap. Use when the user wants to build a new multi-agent framework/system rather than use an existing one."
version: 1.1.0
author: Luke & 小卢
platforms: [macos, linux]
---

# Multi-Agent System Design

## When to Use

- User finishes comparing frameworks (MetaGPT/CrewAI/LangGraph/CAMEL) and decides "none fits perfectly, let's build our own"
- User wants a multi-agent OS that is independent, open-source, and better than existing options
- User has experience with multi-agent concepts and wants to design the "ultimate" system absorbing all existing frameworks' best features

Do NOT use for: comparing existing frameworks (use `comparative-framework-analysis`), configuring Hermes Profiles (use `hermes-multi-agent-orchestration`), or running individual agents.

## Architecture: 5-Layer Onion

```
                    ┌─────────────────────────────┐
                    │  L5: Interface               │
                    │  CLI · Web UI · REST API ·   │
                    │  IDE Plugin · Mobile · Slack  │
                    ├─────────────────────────────┤
                    │  L4: Observability            │
                    │  Trace · Dashboard · Cost     │
                    │  Alerts · Agent Health · Audit│
                    ├─────────────────────────────┤
                    │  L3: Intelligence             │
                    │  Self-Learning · SOP Gen ·    │
                    │  Workflow Optimize · KG       │
                    ├─────────────────────────────┤
                    │  L2: Orchestration             │
                    │  Swarm · Crew · Pipeline ·     │
                    │  Graph · Kanban · Dynamic Team │
                    ├─────────────────────────────┤
                    │  L1: Agent Runtime             │
                    │  Profile · Memory · Skills     │
                    │  Tools · MCP · LLM Provider    │
                    └─────────────────────────────┘
Fundamental Layer: Token Economy + Security + Auth + Multi-tenant
```

### Layer 1 — Agent Runtime

Foundation. Every agent is a persistent entity with:

- **Universal Profile Format (UPF)**: YAML-defined identity (SOUL), model config (default/fallback/vision), token budget, tool registry, skill list, auto-improve flag
- **Hybrid Memory**: Short-term (SQLite/session), long-term (vector RAG), shared (knowledge graph — one agent learns = all learn)
- **Evolvable Skills**: Skills that auto-improve from execution feedback (confidence rating, success rate tracking)
- **MCP Hub**: All communication via MCP protocol — Agent-to-Agent, Agent-to-Tool, Agent-to-Human
- **Provider Abstraction**: Hot-swappable LLM providers (OpenAI, Anthropic, DeepSeek, Ollama, llama.cpp)

### Layer 2 — Orchestration

Nine built-in orchestration modes (built across Phases 0-2):

| Mode | File | Pattern | When |
|------|------|---------|------|
| **Single** | runtime.py | One agent, one task | Simple queries, quick tasks |
| **Swarm** | swarm.py | Parallel Workers → Verifier → Synthesizer | Independent sub-tasks, research |
| **Crew** | crew.py | Role-playing agents with round-table discussion | Collaborative design, code review |
| **Chain** | chain.py | Sequential stages with handoff verification | Content pipelines, ETL, dev workflows |
| **Debate** | debate.py | Pro/Con/Neutral positions → Cross-examine → Synthesize | Research, strategy, multi-perspective analysis |
| **Router** | router.py | Classify task → Route to specialized agent | Customer support, enterprise dispatch |
| **Supervisor** | supervisor.py | Manager decomposes → Workers execute → Review → Approve/Revise | Enterprise compliance, legal review |
| **Monitor** | monitor.py | Watch logs/APIs → Detect anomalies → Spawn fixer → Verify | DevOps, SRE, production monitoring |
| **Kanban** | kanban.py | Smart task board with dependencies + AI suggestions | Project management, backlog |

Plus: **Dynamic Teaming Engine** — AI analyzes task requirements and recommends optimal team composition. **Smart Kanban** — task board with AI suggestions (dependency detection, load balancing, duplicate detection).

### Layer 3 — Intelligence

- **Self-Learning Loop**: Execute → Record → Analyze → Refine → Update Skills → Share to Knowledge Graph
- **SOP Auto-Generation**: Extract repeatable workflows from history; confidence score based on N successful runs
- **Workflow Optimizer**: Based on AFlow (ICLR 2025 Oral), auto-detect bottlenecks and propose optimizations
- **Pattern Mining**: Discover best practices and anti-patterns from execution traces

### Layer 4 — Observability

- **Trace System**: Full execution tree per task (every step, decision, error, cost)
- **Real-time Dashboard**: Active agents, pending tasks, completion rate, token burn rate
- **Cost Tracker**: Per-agent, per-project, per-model cost breakdown
- **Alert System**: Deadline risk, budget threshold, agent health degradation

### Layer 5 — Interface

- **CLI**: `apex init` / `apex run` / `apex status` / `apex team` (+ 9 groups, ~80 subcommands)
- **Web UI**: Dashboard + Kanban + Trace browser + Cost analysis
- **REST API**: Programmatic access for IDE plugins and CI/CD integration

> Full CLI architecture (9-group hierarchy, design principles, refactoring pattern): `references/apex-cli-architecture.md`

### Foundation: Token Economy

| Priority | Model | Cost/Task |
|----------|-------|-----------|
| P0 (critical) | Claude Sonnet/GPT-4 | ~$0.02 |
| P1 (standard) | DeepSeek | ~$0.0005 |
| P2 (cheap) | Local Ollama | $0 |
| P3 (template) | Cached/templated | $0 |

~95% cost savings vs all-Claude, while maintaining ~99% capability equivalence.

## TOP10 Multi-Agent Use Cases — Mode Selection Guide

## Seven Core Innovations

## Build Phases

## Dashboard & Command Center Evolution

Dashboard progression: V3 (synthetic data SPA) → V4 (single-page real data) → V5 (8-tab) → **Command Center (sidebar+14 views, single `command_center.html` at `http://localhost:8080/`)**

**Current architecture:**
- Single template file (`command_center.html`, ~3800 lines)
- Sidebar navigation with 3 sections (运营/智能/资源) + 董事会 crew list
- 14 views: 指挥中心/项目作战室/审批审计/Pipeline/AI舰队/自治引擎/知识图谱/数据流时序/模块市场/SKILL进化/成本中心/系统状态/GPU资源中心
- 总分+弹窗编辑 UX: every view shows summary cards, click opens right-side Drawer with edit form + Save/Cancel
- Tabler Icons (ti-*) for ALL UI chrome, zero emoji
- Dark/light theme with localStorage persistence
- Agent chat history integration (click agent → drawer → sessions → conversation view)

**Key architectural decisions:**
- Sidebar+view routing (not horizontal tabs) — scales better for 10+ views
- All data from real APIs (40+ endpoints), no synthetic fallback
- Drawer component reused across all views for editing
- One template file (cleaned up v3/v4/v5/daily/auth)

- `references/model-auto-discovery.md` — Model auto-detection from env/AWS SSO/tools
- `references/dashboard-consolidation.md` — 7→1 template cleanup pattern

## Pitfalls

1. **Don't build everything at once.** Phase 0 should be a working piece of value, not an unfinished skeleton. Ship Swarm+CLI before starting Crew mode.
2. **Name matters.** Pick a name that's short (4-6 chars), memorable, available on PyPI, and evokes "peak/summit"—Nexus, Apex, Synapse, Vertex.
3. **Don't copy competitors' mistakes.** Each existing framework has known flaws: MetaGPT's rigid roles, AutoGen's maintenance mode, LangGraph's steep learning curve. Your design document should explicitly list "problems we solve" based on the comparative analysis.
4. **Token Economy isn't optional.** Without built-in cost control, multi-agent systems are too expensive for individuals. It's the single biggest adoption barrier.
5. **MCP is the future, not nice-to-have.** MCP-native design means your agents can talk to any other MCP-compatible agent, tool, or framework. Build it in from Phase 0.
6. **Persistence is a feature.** Ephemeral agents that lose context between sessions feel like toys. Every agent needs persistent memory, skills, and conversation history from day one.
7. **Self-healing before self-learning.** Before optimizing, make the system resilient. A system that crashes on first error will never get enough data to learn.
8. **PTY vs background for auth.** `gh auth login` requires a PTY for the one-time code flow — background the command, capture the code, tell the user to open the device URL. Or skip gh entirely and use a PAT via `git remote add origin`.
9. **Source Code Map must match the ACTUAL file tree exactly.** Run `find . -type f | sort` from the project root. Every directory, `__init__.py`, template, and submodule must appear. One-line descriptions only — no process histories or commit messages.
10. **Dashboard fails silently.** Test Flask routes with `app.url_map.iter_rules()` before claiming they work.
11. **Knowledge graph needs seed data to be useful.** Seed 5-10 entries via `kg.learn()` and `kg.relate()` before first query.
12. **Relative imports break at 3+ nesting levels.** Use absolute imports (`from apex.core.profile import ...`), not relative.
13. **Provider registration requires explicit import.** Modules must be imported at startup — put `from . import deepseek` in `providers/__init__.py`.
14. **Apex orchestrates, Hermes executes.** Apex agents are LLM-only — no terminal/SSH/file tools.
15. **Audit private methods, not just `run()`.** `inspect.getsource()` on `run()` misses Agent.run() calls inside `_execute_stage()`, `_decompose()`, etc. Check ALL methods.
16. **Check the full method tree when auditing orchestration completeness.** A false-positive audit that only checks top-level `.run()` methods can mislabel complete modes as scaffold. Use `inspect.getsource()` on every method in the class, not just the public entry point.
17. **Dashboard HTML pitfalls (V4+).** Flask caches templates — restart server after any edit, browser refresh is NOT enough. Canvas 2D context cannot parse CSS custom properties (`var(--accent)`) — always use hex colors (`#3b82f6`). DOM helper functions must handle number children (`el('span',{},5)` → convert to string, don't `.forEach()` on numbers). Subagent-generated HTML over-escapes JS quotes (`\\\"` instead of `"`) — validate with `node --check` on extracted JS. Flask route collision: GET `/api/x` (list) + GET `/api/x/<name>` (detail) → use `/api/x/list` instead.

## Cross-Language MCP Implementation

Apex's MCP stdio client (`apex/mcp/stdio_client.py`) connects to external MCP servers in any language via JSON-RPC 2.0 over stdin/stdout. Three verified implementations:

| Language | Server | Tools | Status |
|----------|--------|-------|--------|
| Node.js (v25) | `scripts/mcp-servers/mcp-node-server.js` | greet, weather, analyze_sentiment | 🟢 100% |
| Go (1.23) | `scripts/mcp-servers/mcp-go-server.go` | calculate, file_analysis, current_time | 🟢 100% |
| Rust (1.84) | `scripts/mcp-servers/mcp-rust-server.rs` | analyze_text, fibonacci, prime_factors | 🟢 94.9% |

Build pattern for adding a new language:
1. Write a subprocess that reads JSON-RPC 2.0 from stdin, writes to stdout
2. Emit `{"jsonrpc":"2.0","method":"server/ready",...}` on startup
3. Implement `tools/list` and `tools/call`
4. Test: `MCPStdioClient(command="binary", args=[])` → `client.connect()` → `client.list_tools()` → `client.call_tool()`
5. Register: `client.register_with_hub(hub, prefix="lang.")`

Key implementation details:
- Binary-safe reads (`os.read()`, not `stdout.readline()`) for Rust/Go
- Compact JSON (`separators=(',', ':')`) required by Rust string-based detection
- Test file: `tests/test_mcp_cross_language.py` (39 tests, 37/39)

## Task Manager System

Apex's task management system (`apex/orchestration/task_manager.py`) provides enterprise-grade project management:

- **4-tier hierarchy**: Epic → Story → Task → Subtask
- **10-state PM workflow**: Draft → Requested → PM_Review → Approved → ... → Closed
- **Progress rollup**: sub-task completion auto-calculates parent %
- **Agent capacity**: tracks active/max/available/load per profile
- **Auto-dispatch**: assigns tasks to least-loaded matching agent
- **Cross-agent help**: agent → PM → helper flow with automatic sub-task creation
- **CLI**: `apex task create/list/show/status/epic`, `apex capacity`, `apex dispatch`, `apex help-request/approve/list`
- **API**: 11 endpoints under `/api/taskmgr/` and `/api/help/`
- **DB**: persisted in `ops.db` (project_tasks table, 31 columns)

See `references/task-manager-architecture.md` for full details.

## Dashboard Backend v4

Apex's dashboard backend (`apex/interface/web.py` + new modules) serves ~50 endpoints:

- **Modules**: `web.py` (main Flask app), `middleware.py` (CORS/auth/logging), `event_stream.py` (pub/sub + SSE), `hermes_bridge.py` (Hermes integration), `openclaw_bridge.py` (6 tools, 4 workflows)
- **Streaming**: 2 SSE endpoints for real-time logs and events
- **Integrations**: Hermes sessions/tokens/GPU/pricing, OpenClaw tools/workflows
- **CORS**: All origins allowed, OPTIONS preflight handled globally

- `references/dashboard-backend-v4.md` — endpoint catalog and patterns
- `references/intelligent-project-template-engine.md` — smart tiered project init with agent allocation matrix

## README Source Code Map Pattern

When the user asks to sync the README's code map with the actual tree:
1. Run `find apex -type f | sort` to get the real file list
2. Format as a tree with one-line descriptions per file
3. Include ALL files: `__init__.py`, templates, static assets, nested commands
4. Descriptions are brief purpose summaries — not process logs or commit messages
5. Max depth: 3-4 levels. Group by package with clear section headers

## Related Skills

- `comparative-framework-analysis`
- `hermes-multi-agent-orchestration`
- `word-report-generation`

## Dashboard Development

When building or modifying Apex dashboard views (command_center.html):

- **UI Standards**: `references/dashboard-ui-standards.md` — NO emoji in UI chrome, Tabler Icons only, AgentCorp-OS design rules, sidebar+view architecture
- **Debugging**: `references/dashboard-debugging-pitfalls.md` — JS escaping, Canvas CSS variables in hex, Flask route collision fix, DOM helper number handling, template caching
- **Project Factory**: `references/intelligent-project-factory.md` — Module library (5 categories, 20+ templates), SKILL evolution (6 levels, XP system), Pipeline (7 stages), Project registry (始祖Agent approval gating)
