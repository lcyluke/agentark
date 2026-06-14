# 七大核心创新实现方案 (Seven Core Innovations Implementation)

This reference documents how each of the 7 innovations was actually implemented in the Apex codebase. Use this as a template for building similar systems or for extending Apex.

## 1. 动态技能进化 (Dynamic Skill Evolution)

**Status**: Fully implemented

**Key files**: `apex/core/evolution.py`, `apex/core/runtime.py`

**How it works**:
- Every `Agent.run()` call auto-records to `EvolutionEngine` via `_record_evolution()` in runtime.py
- Record stores: agent_name, task, prompt, output, success, duration_ms, quality_score
- On record, `_analyze_patterns()` checks for error/success patterns and updates the `patterns` table
- SQLite DB at `~/.apex/evolution.db`
- Tables: `executions` (detailed log), `patterns` (extracted insights), `quality_history` (trends)

**Schema**:
```sql
CREATE TABLE executions (id INTEGER PRIMARY KEY, agent_name TEXT, task TEXT, task_type TEXT, 
  prompt TEXT, output TEXT, success INTEGER, duration_ms INTEGER, error TEXT, 
  quality_score REAL, tokens_used INTEGER, model TEXT, timestamp REAL);
CREATE TABLE patterns (pattern TEXT UNIQUE, trigger TEXT, action TEXT, confidence REAL, 
  source_count INTEGER, improvement REAL, created_at REAL, last_applied REAL);
CREATE TABLE quality_history (agent_name TEXT, execution_num INTEGER, quality_score REAL, timestamp REAL);
```

**To extend**: Call `evo.record(ExecutionRecord(...))` from any code path that completes a task.

## 2. 零点击组队 (Zero-Click Teaming)

**Status**: Fully implemented

**Key files**: `apex/orchestration/crew.py` (DynamicTeamDesigner class)

**How it works**:
- `apex crew create "goal"` loads DynamicTeamDesigner
- `design_team()` uses keyword matching on goal text against known task types (web/app/deploy/content/api/data)
- Maps task types to team compositions (which templates + roles)
- Falls back to default PM/frontend/backend team if no match
- Phase 2 should replace keyword matching with LLM-based reasoning

**Patterns**:
```yaml
"web" -> pm, frontend, backend + devops verifier
"deploy" -> devops, backend + pm verifier
"content" -> content, pm
"api" -> backend, devops + pm verifier
```

**CLI**: `apex crew design "goal"` to preview, `apex crew create "goal"` to execute

## 3. 自愈工作流 (Self-Healing Workflow)

**Status**: Fully implemented (v2)

**Key files**: `apex/orchestration/healing.py`

**How it works**:
- SelfHealingExecutor wraps an Agent and kanban
- Strategy escalation:
  1. Attempt 1: Direct retry (same params)
  2. Attempt 2: Switch to fallback model (profile.model.fallback)
  3. Attempt 3: Simplify task via healer agent
- On each failure, calls KnowledgeGraph.learn_from_experience() to persist the failure pattern
- On each failure, records to EvolutionEngine
- After 3 failures: marks Kanban task as FAILED, returns descriptive error

**Key code pattern**:
```python
executor = SelfHealingExecutor(agent, kanban)
result = executor.run(task, max_attempts=3)
```

## 4. 知识图谱记忆 (Knowledge Graph Memory)

**Status**: Fully implemented

**Key files**: `apex/core/knowledge.py`

**How it works**:
- SQLite-backed graph DB with nodes (entity) and edges (relationship) tables
- FTS5 full-text search on knowledge_fts virtual table
- Chinese-aware entity extraction: matches [\u4e00-\u9fff]{2,15} sequences
- learn(entity, type, description) creates node
- relate(source, relation, target, context) creates edge
- query(question) auto-reasoning: entity extraction -> transitive traversal -> answer assembly
- learn_from_experience(agent, task, error, fix) core learning API
- Conflict detection: opposite relations auto-detected and stored in conflicts table

**Schema**:
```sql
CREATE TABLE nodes (entity TEXT UNIQUE, entity_type TEXT, description TEXT, source TEXT, confidence REAL, accessed_at REAL, access_count INTEGER);
CREATE TABLE edges (source_entity TEXT REFERENCES nodes(entity), relation TEXT, target_entity TEXT REFERENCES nodes(entity), context TEXT, confidence REAL);
CREATE VIRTUAL TABLE knowledge_fts USING fts5(entity, description, context, source);
```

**CLI**: `apex knowledge query "text"`, `apex knowledge stats`

## 5. Token预算银行 (Token Budget Bank)

**Status**: Fully implemented

**Key files**: apex/economy/__init__.py

**How it works**:
- 11 predefined model routes with cost per 1K tokens and quality scores
- classify_task(task) -> keyword matching to task types
- select_model(task, budget) -> cheapest adequate model within budget
- BudgetManager with accounts, transactions, balance checks
- TokenRouter as the public API
- Alerts when budget crosses thresholds (80%/100%)

**Route table (11 entries)**:
| Type | Model | Provider | Cost/1K in | Quality |
|------|-------|----------|-----------|---------|
| simple-reply | llama3-8b | ollama | $0 | 3 |
| architecture | claude-sonnet | anthropic | $0.003 | 10 |
| code-review | deepseek-chat | deepseek | $0.0005 | 8 |
| vision | claude-sonnet | anthropic | $0.003 | 9 |
| default | deepseek-chat | deepseek | $0.0005 | 7 |

**CLI**: apex economy status, apex economy classify "task"

## 6. MCP全家桶 (MCP All)

**Status**: Fully implemented (4 built-in tools)

**Key files**: apex/mcp/hub.py

**How it works**:
- MCPHub global registry with register(tool) and call(name, **kwargs)
- 4 built-in handlers: FileSystemMCP, ShellMCP, KnowledgeMCP, HTTPSMCP
- Handlers follow BaseMCPHandler interface
- Tools exportable as OpenAI function-calling format via to_openai_tools()

**Extending**:
```python
from apex.mcp.hub import hub
hub.register(MCPTool(name="my-tool", handler=my_handler))
```

## 7. One-Click Company (OCC)

**Status**: Fully implemented (5 templates)

**Key files**: apex/cli/commands/company.py

**How it works**:
- apex company create "name" -i saas loads COMPANY_TEMPLATES dict
- Creates all agent profiles from matching template
- Initializes Kanban board with SOP steps as tasks
- Saves company config JSON to ~/.apex/companies/{name}.json
- apex company start "name" "goal" loads company, decomposes goal into Kanban tasks

**5 industry templates**: saas, ai_product, content, ecommerce, freelance

**CLI**:
```
apex company create 羽球宝AI -i saas    # 5 profiles + kanban + sop
apex company start 羽球宝AI "build MVP"  # auto-decompose into tasks
apex company list                         # list all companies
```
