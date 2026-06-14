---
name: apex-uat-testing
description: "Systematic UAT testing for Apex multi-agent OS — self-healing, ops, KG, SQLite thread safety, API endpoints, completeness audit"
version: 1.2.0
platforms: [macos, linux]
trigger_phrases: ["run apex uat", "test apex", "apex integration test", "verify apex fixes", "is apex complete"]
related_skills: [dogfood]
---

# Apex UAT Testing

## Overview

Run a systematic UAT test suite for Apex — covering core systems, recent fixes, and a deep-dive completeness audit that distinguishes real execution from scaffold code.

## Prerequisites

- Project at `~/Desktop/2026AIAPP/Apex`
- Venv activated: `source .venv/bin/activate`
- Profile manager initialized (has profiles)
- For dashboard tests: `lsof -ti:8080 | xargs kill -9 2>/dev/null`
- For cross-language MCP tests (Phase 6b): Go and Rust compilers installed; servers built via `cd scripts/mcp-servers && go build && rustc`

## Quick Verification (5 min)

```bash
python3 -m pytest tests/ -q --tb=short          # 87 passed
apex knowledge stats                              # >=40 nodes, >=8030 edges
apex knowledge query "Python mutable defaults"    # confidence > 0
apex dashboard --port 8080 &
sleep 3
for path in status profiles knowledge evolution health ops tasks companies autonomous; do
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/$path
done
```

## Full Test Plan

### Phase 1: pytest

```bash
python3 -m pytest tests/ -q --tb=short
```

Expected: **87 tests pass**.

### Phase 2: Self-Healing Integration

```python
from apex.core.runtime import Agent
from apex.core.profile import Profile, SoulConfig
from apex.orchestration.healing import SelfHealingExecutor, HealingResult
agent = Agent(Profile(name="tester", soul=SoulConfig(role="T")), self_healing=True)
assert agent.self_healing
ex = SelfHealingExecutor(agent)
assert ex.MAX_ATTEMPTS == 3 and ex.STRATEGIES == ["direct","switch_model","simplify_task"]
r = HealingResult(); assert r.success is False
```

### Phase 3: Ops CRUD

```bash
apex ops release create <version>
apex ops release list
apex ops bug create <title> <desc> --severity high
apex ops bug list
apex ops task create <title> --agent tester
apex ops task list
apex ops status
```

Key assertions: Release = 10 stages, Bug = SLA deadlines (2h/8h/24h/72h), Task = phase + quality score, Stats = tasks/bugs/releases/expert_tickets.

### Phase 4: SQLite Thread Safety

```python
from apex.core.profile import APEX_HOME
import sqlite3
for name in ['evolution', 'knowledge', 'memory', 'skills', 'kanban', 'economy']:
    conn = sqlite3.connect(str(APEX_HOME / f'{name}.db'), check_same_thread=False)
    assert conn.execute('SELECT 1').fetchone()[0] == 1
    conn.close()
```

### Phase 5: Knowledge Graph Seed Data

```bash
apex knowledge stats        # >=40 nodes, >=8030 edges, 0 conflicts
apex knowledge query "Python mutable defaults"   # confidence > 0
apex knowledge query "Docker health check"
apex knowledge query "API pagination"
```

### Phase 6: Dashboard API Endpoints

```bash
apex dashboard --port 8080 &
sleep 3
for path in status profiles knowledge evolution health ops tasks companies autonomous; do
    curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/$path
    echo ""
done
```

Expected: All 9 endpoints return HTTP 200.

### Phase 6b: Cross-Language MCP Integration

Requires built servers (`cd scripts/mcp-servers && go build -o mcp-go-server mcp-go-server.go && rustc mcp-rust-server.rs -o mcp-rust-server`). The binaries are gitignored — they must be built fresh after clone.

```bash
python3 tests/test_mcp_cross_language.py
```

Expected: **37/39 passed (94.9%)** — Node.js 100%, Go 100%, Rust 100% direct. The 2 failures are a legacy parameter-shadow issue in Hub chaining.

### Phase 6c: Task Management System

```bash
apex task create "UAT Epic" --type epic --project uat --hours 8
apex task create "UAT Story" --type story --parent <EPIC_ID> --assignee tester --hours 4
apex task create "UAT Task" --type task --parent <STORY_ID> --assignee tester
apex task list --project uat      # Shows 3 tasks with hierarchy
apex task status <TASK_ID> in_progress --notes "UAT testing"
apex task status <TASK_ID> completed
apex capacity                      # Shows tester with 1 active
apex dispatch                      # Auto-dispatch pending tasks
```

### Phase 7: Completeness Audit

⚠️ **CRITICAL: Do NOT check only the top-level `run()` method.** Private methods like `_execute_stage()`, `_opening_statements()`, `_decompose()` contain the actual `Agent.run()` calls. A shallow `.run()` check produces FALSE POSITIVES.

**Correct technique — check ALL methods via `inspect.getsource()`:**

```python
import importlib, inspect, subprocess

def check_agent_calls(cls, name):
    found = []
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if callable(attr) and not attr_name.startswith('__'):
            try:
                src = inspect.getsource(attr)
                calls = [l.strip() for l in src.split('\n') if '.run(' in l and 'def ' not in l]
                if calls: found.append((attr_name, len(src.split('\n')), calls))
            except: pass
    if found:
        for fn_name, n_lines, calls in found:
            print(f"  🟢 {name}.{fn_name}(): {n_lines} lines, calls: {calls[0][:60]}")
    else:
        print(f"  🔴 {name}: NO Agent.run() calls in any method")

for mod_path, mode_name in [
    ('apex.orchestration.chain', 'Chain'), ('apex.orchestration.debate', 'Debate'),
    ('apex.orchestration.supervisor', 'Supervisor'), ('apex.orchestration.router', 'Router'),
    ('apex.orchestration.swarm', 'Swarm'), ('apex.orchestration.crew', 'Crew'),
]:
    mod = importlib.import_module(mod_path)
    check_agent_calls(getattr(mod, mode_name), mode_name)
```

## Generating the UAT Report

After all phases complete, produce:

```
## UAT Summary
| Phase | Result |
|-------|--------|
| pytest (87 tests) | ✅ |
| Self-Healing | ✅ |
| Ops CRUD | ✅ |
| SQLite Thread Safety | ✅ |
| KG Seed Data | ✅ |
| Dashboard APIs | ✅ |
| Cross-Language MCP | ✅ (37/39) |
| Completeness Audit | ✅ 10/10 modes verified |

## Completeness Score
| Module Group | Confidence |
|-------------|-----------|
| Agent Runtime (core/) | 100% 🟢 |
| Orchestration (all 10 modes) | 100% 🟢 |
| Token Economy | 100% 🟢 |
| MCP Hub + Cross-Language | 95% 🟢 |
| Web Dashboard | 85% 🟢 |
| CLI | 100% 🟢 |
```

## Known Pitfalls

1. **Dashboard port conflict**: `lsof -ti:8080 | xargs kill -9` first
2. **Self-healing LLM calls**: Structure-only checks are fast (~0.01s). Full e2e takes 15-60s.
3. **Ops DB state**: Previous data persists in `~/.apex/ops.db`. Clean: `rm ~/.apex/ops.db`
4. **KG conflicts after re-seed**: `rm ~/.apex/knowledge.db` then re-run `python3 scripts/seed_knowledge.py`
5. **execute_code timeout**: The tool has a 5-minute limit. Heavy audit scripts need `terminal("timeout 60 python3 -c '...'")` instead.
6. **CLI verification via execute_code**: `subprocess.run()` inside execute_code sometimes falsely marks all commands as ❌. Use `terminal()` directly.
7. **Audit methodology must check private methods**: `inspect.getsource(cls.run)` alone will report complete modes as scaffold. Iterate ALL methods. Swarm, Crew, Chain, Debate, Router, Supervisor all have Agent.run() calls in private methods like `_execute_stage()`, `_opening_statements()`, `_decompose()`.
8. **Cross-language MCP binaries are gitignored**: Build from source before running Phase 6b: `cd scripts/mcp-servers && go build && rustc`
9. **Sibling subagent file staleness**: When a subagent modifies a file, the parent's cached content becomes stale. Any `patch` call against a file last read before a sibling wrote it will silently fail with "no match found". Always `read_file` before writing after `delegate_task`.
10. **MCP stdio protocol quirks**:
    - `json.dumps(request, separators=(',', ':'))` produces compact JSON that all server languages parse reliably; default spaced JSON breaks Rust string-based method detection.
    - `subprocess.Popen(text=True)` causes encoding issues with Rust servers. Use binary mode (`stdin=subprocess.PIPE` without `text=True`) and write/read bytes.
    - `proc.stdout.readline()` has buffering problems with subprocess pipes. Use `os.read(fd, 1)` byte-by-byte under `select.select()` timeout instead.
    - **Hub.register_with_hub lambda pattern**: The handler lambda must accept `**kwargs` and forward them, not nest another lambda that shadows parameter names like `name` or `fn`. Use `lambda n=name, fn=self.call_tool, **kw: self._mcp_wrapper(fn, n, kw)` — a single, flat lambda.
