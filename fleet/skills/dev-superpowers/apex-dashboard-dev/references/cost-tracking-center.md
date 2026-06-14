# Apex Cost Tracking Center (成本追踪引擎)

A dashboard feature within the Apex Command Center — tracks every LLM token's cost, broken down by cron job, agent profile, project, and source channel.

## Architecture

```
Hermes state.db (sessions table)
        │
        ▼
apex/cost_tracker.py          ← Cost query engine
        │
        ├── /api/cost/summary       ← Overview
        ├── /api/cost/cron?days=30  ← Cron detail
        ├── /api/cost/agents        ← Agent detail
        ├── /api/cost/sources       ← Channel breakdown
        ├── /api/cost/projects      ← Project aggregation
        ├── /api/cost/timeline      ← Trends
        └── /api/cost/full          ← Full snapshot
                │
                ▼
/cost (Dashboard)              ← Cost Center HTML
```

## Data Source

- **Hermes state.db** `sessions` table: `input_tokens`, `output_tokens`, `estimated_cost_usd`, `source`, `handoff_platform`
- Session ID format `cron_{job_id}_{date}_{time}` → parseable to cron job ID
- `hermes cron list` → cron job name mapping

## Cron Job Cost Resolution

Session ID format: `cron_b8ede7ee7204_20260530_090050`, where `b8ede7ee7204` is the job ID. Reverse-lookup to `hermes cron list` job name.

### Typical Cost Data (DeepSeek V4 Pro)

| Cron Type | Avg Tokens | Avg Cost | Monthly Estimate |
|:--|:--|:--|:--|
| PM Daily (incl. system prompt) | ~28K | $0.05 | ~$1.50 |
| Task Monitor (30min) | ~2.8K | $0.006 | ~$0.43 |
| Fleet Patrol (no-agent) | ~1K | $0.002 | ~$0.02 |
| High-Freq Sync (5min) | ~1.7K | $0.004 | ~$4.20 |

> PM Daily's token consumption is dominated by System Prompt (SOUL.md + MEMORY + USER.md + Skills list), not monitoring content.

## Pricing Reference

```python
PRICING = {
    "deepseek-v4-pro": {"input": 1.0, "output": 4.0},   # $/1M tokens
    "deepseek-chat":   {"input": 0.14, "output": 0.28},
    "claude-sonnet-4": {"input": 3.0, "output": 15.0},
}
```

## Dashboard Usage

Access `http://localhost:8080/cost`, 4 Tabs:

1. **📋 Cron Cost** — 30-day cost, avg cost, frequency, last run time per cron
2. **🤖 Agent Cost** — By Hermes Profile, showing source distribution
3. **📦 Project Cost** — badminton-coach-ai/Apex/FinOps/Shenzhen-map budget utilization
4. **📈 Trends** — 7-day token volume bars + cost line chart

Top section: 6 Summary Cards (Today/This Week/30 Days/Cumulative/Daily Avg/Est. Monthly), 30s auto-refresh.

## API Quick Reference

```bash
curl http://localhost:8080/api/cost/summary
curl http://localhost:8080/api/cost/cron?days=7
curl http://localhost:8080/api/cost/agents
curl http://localhost:8080/api/cost/projects
curl http://localhost:8080/api/cost/timeline?days=7&granularity=daily
curl http://localhost:8080/api/cost/full
```

## Project Cost Estimation

Keyword heuristic matching on session title/system_prompt:

```python
PROJECT_KEYWORDS = {
    "badminton-coach-ai": {"name": "羽球宝AI搭子", "emoji": "🏸", "budget": 5.0, "keywords": ["badminton", "羽球"]},
    "apex": {"name": "Apex Dashboard", "emoji": "🦅", "budget": 10.0, "keywords": ["apex", "dashboard"]},
    "finopsai": {"name": "FinOps AI", "emoji": "💰", "budget": 5.0, "keywords": ["finops", "billing"]},
    "shenzhen-badminton": {"name": "深圳球地图", "emoji": "🗺️", "budget": 3.0, "keywords": ["深圳", "地图"]},
}
```

## Key Files

| File | Description |
|:--|:--|
| `apex/cost_tracker.py` | Cost query engine (~350 lines) |
| `apex/interface/templates/cost_center.html` | Dashboard view |
| `apex/interface/web.py` | +7 API endpoints + `/cost` route |

## Reference Data

- `references/cron-cost-data-2026-06.md` — Actual cron cost snapshot (2026-06-07), 16 jobs ranked + channel breakdown

## Notes

- Cron session `title` field is usually empty — parse job ID from session ID
- Agent cost grouped by `handoff_platform` (finer than `source`)
- Project cost is heuristic estimate (keyword matching), not exact allocation
- `no_agent=true` crons (pure scripts) produce zero LLM cost — only small tokens on delivery
