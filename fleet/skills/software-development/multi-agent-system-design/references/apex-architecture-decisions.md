# Apex Architecture Decisions (Session: 2026-06-01)

## Build Rationale

Luke compared top-5 multi-agent frameworks (MetaGPT 68.5k, AutoGen 58.6k, CrewAI 52.6k, LangGraph 33.6k, CAMEL 17.1k) across 6 dimensions (Harness/Context/Self-learning/Team Mgmt/Monitoring/Collaboration). Conclusion: no single framework covers all needs. CrewAI has the best team/collaboration but no self-learning and poor cost control. CAMEL has the best self-learning but poor productization. LangGraph has the best infrastructure but a steep learning curve.

Decision: Build a new unified multi-agent OS absorbing all 5 frameworks' strengths.

## Name

**Apex** (originally Nexus, renamed per Luke's preference on 'Nexus' vs 'Apex' decision).

## Architecture Verification

The 5-layer onion (L1 Runtime → L2 Orchestration → L3 Intelligence → L4 Observability → L5 Interface) was implemented in full. Each layer was built and tested with live DeepSeek API calls during this one session.

## Project Location

`~/Desktop/2026AIAPP/Apex/` — this is the canonical path. NOT under `~/.openclaw/workspace/` or any other directory.

## Key File Map

| Path | Purpose |
|------|---------|
| `apex/core/profile.py` | UPF format, ProfileManager with YAML persistence |
| `apex/core/runtime.py` | Agent class with auto-evolution recording |
| `apex/core/memory.py` | SQLite short-term memory |
| `apex/core/skills.py` | Evolvable skill system (use_count, success_count, confidence) |
| `apex/core/knowledge.py` | KnowledgeGraph — entity/edge graph DB with Chinese entity extraction |
| `apex/core/evolution.py` | EvolutionEngine — execution recording, pattern mining, quality trends |
| `apex/core/templates.py` | 5 agent templates (frontend/backend/pm/content/devops) |
| `apex/providers/base.py` | ProviderRegistry — hot-swappable provider abstraction |
| `apex/providers/deepseek.py` | DeepSeek + Ollama providers |
| `apex/orchestration/swarm.py` | Swarm mode (parallel → verifier → synthesizer) |
| `apex/orchestration/crew.py` | Crew mode (4-phase: individual → roundtable → synthesis → verification) |
| `apex/orchestration/kanban.py` | Smart Kanban with status management |
| `apex/orchestration/healing.py` | Self-healing v2: 3-strike-rule, model downgrade, KG accumulation |
| `apex/economy/__init__.py` | Token Economy: 11 route rules, BudgetManager, TokenRouter |
| `apex/mcp/hub.py` | MCP Hub with 4 built-in tools (filesystem/shell/http/knowledge) |
| `apex/interface/web.py` | Flask dashboard with REST API |
| `apex/cli/main.py` | Click CLI — 12 command groups |
| `pyproject.toml` | hatchling build, MIT license |

## CLI Architecture (refactored 2026-06-04)

Designed with the **7±2 group principle** for intuitive command discovery. 

From `36 flat commands` → `17 top-level (9 groups, ~80 total subcommands)`.

**9 groups:**
| Group | Icon | Purpose | Subcommands |
|-------|------|---------|-------------|
| `task` | 📋 | Task management | create/list/show/status/epic/dispatch/dispatch-smart/capacity/schedule |
| `team` | 👥 | Agent team management | create/list/show/start/status/attach/template/sync/sync-all/hermes |
| `fleet` | 🤖 | Fleet monitoring | status/show/refresh/history/inspect/monitors/deploy |
| `mode` | 🔧 | Collaboration modes | chain/debate/supervise/pipeline(normal/direct/status/confirm) |
| `project` | 📦 | Project management | create/analyze/list/sprint |
| `system` | ⚙️ | System management | skill(6)/economy(2)/evolution(2)/knowledge(2)/autonomous(8) |
| `help` | ❓ | Help system | request/approve/list |
| `origin` | ⚓ | Origin Agent | init/replicate/overview/portfolio(3) |
| `integrate` | 🔗 | Integrations | hermes/bridge(4)/router/monitor/company(3) |

Plus 5 top-level commands: `init`, `run`, `chat`, `dashboard`, `demo`.

**Backward compatibility:** Old flat commands (`debate`, `supervisor`, `dispatch`) hidden but still work with deprecation notices. Removing after 1 release cycle.

See `references/apex-cli-architecture.md` for full tree and design rationale.

## Critical Learnings

### Provider Import
Providers must be explicitly imported in `__init__.py` or they won't register. The `base.py` creates a global `registry` but the registry is empty until `.deepseek` is imported. Fixed by adding `from . import deepseek` in `providers/__init__.py`.

### CLI Relative Imports
Click CLI commands in `apex/cli/commands/*.py` use relative imports like `from ...core.profile`. This fails because `cli/commands/` is nested 3 levels deep. All relative imports were replaced with absolute `from apex.core.profile` style. This is the correct pattern for Click-based CLI tools.

### Evolution Engine Recording
The evolution engine doesn't auto-record unless `runtime.py`'s `run()` method explicitly calls `_record_evolution()`. This was added as a try/except block so recording failures never break the primary execution flow.

### Knowledge Graph Entity Extraction
For Chinese queries to work, `_extract_entities()` needs to match `[\u4e00-\u9fff]{2,15}` (2+ consecutive Chinese characters). Without this, Chinese task descriptions produce empty entity lists and the KG returns no results.

### Self-Healing v2 Strategy Sequence
The strategy escalation (direct → model switch → simplify task) is critical. Direct retry handles transient failures. Model switch handles model-specific issues. Simplify task handles cases where the prompt is too complex.

### Canonical Activation
```bash
cd ~/Desktop/2026AIAPP/Apex && source .venv/bin/activate
apex run "task"
```

## File Counts as of Build Completion

- 34 Python source files (`.py`, excluding tests)
- 4,386 total lines of Python code
- 40 total files including README.md, pyproject.toml, HTML template
- Python 3.11.13 runtime
- Dependencies: click, httpx, pyyaml, pydantic, rich, jinja2, flask

## White Paper Reference

The full Apex design white paper (28KB, 500 lines) is stored at:
`~/Desktop/2026AIAPP/LuInsightForMutliAgent/Apex_多Agent操作系统设计白皮书.md`
