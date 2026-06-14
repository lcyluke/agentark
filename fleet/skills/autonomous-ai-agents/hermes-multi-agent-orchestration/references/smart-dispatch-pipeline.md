# Smart Dispatch Pipeline

Dual-flow task pipeline: normal (decompose→dispatch→monitor) + direct (route→agent→execute).

## Architecture

```
User message → message_router (project ID)
            → pipeline.smart_route() (intent recognition)
                ├── Normal: decompose → create epic + N tasks → dispatch
                └── Direct: route to agent → create single task → execute
            → AutonomousEngine (auto-execute)
            → completion_monitor (cron, notify on done)
```

## CLI Commands

```bash
# Normal flow — full decomposition
apex pipeline normal "finopsai needs multi-tenant dashboard" -p finopsai

# Direct flow — fast path to specific agent
apex pipeline direct "fix billing API timeout" -a finops-backend -p finopsai

# Smart route — auto-detect intent
apex dispatch-smart "finops-backend, fix the auth bug" -p finopsai
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/pipeline/normal` | POST | Full decomposition pipeline |
| `/api/pipeline/direct` | POST | Direct agent dispatch |
| `/api/pipeline/smart` | POST | Auto-detect intent → choose flow |
| `/api/dispatch/smart` | POST | Legacy alias for smart route |

## Intent Recognition Rules

| Message Pattern | Detected As | Flow |
|----------------|------------|------|
| `@agent_name task` | Direct mention | ⚡ Direct |
| `agent_name, task` | Comma dispatch | ⚡ Direct |
| `让agent_name做task` | Delegate | ⚡ Direct |
| `需要做/实现/开发/搭建 X` | Requirement | 📋 Normal |
| Default | Fallback | 📋 Normal |

## Key Files

- `apex/orchestration/pipeline.py` — Dual-flow state machine + intent recognition
- `apex/orchestration/task_decomposer.py` — Requirement → structured task list + agent matching
- `apex/cli/commands/pipeline_cmds.py` — CLI renderers
- `apex/cli/commands/task_mgmt.py` — `dispatch_smart_cmd`
- `apex/interface/web.py` — 3 pipeline API endpoints
- `~/.hermes/scripts/finops_completion_monitor.py` — Completion watchdog

## Pitfalls

1. **Keyword-only decomposition is a fallback.** The `_keyword_decompose()` uses domain keyword matching. For LLM-powered decomposition, run in a Hermes session with `_build_decomposition_prompt()`.
2. **Agent missing from PROJECT_AGENTS → task falls to PM.** Check `AGENT_SKILL_PROFILES` and `PROJECT_AGENTS` in `task_decomposer.py` when new agents don't receive tasks.
3. **Direct flow needs exact agent name.** Use `resolve_agent()` for fuzzy matching (e.g. "backend" → "finops-backend").
