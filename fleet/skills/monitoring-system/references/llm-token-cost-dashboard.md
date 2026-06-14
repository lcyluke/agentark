# LLM Token Cost Tracking Dashboard

> Added 2026-06-07 — companion to GPU cost monitor, covers LLM API token costs from Hermes state.db

## Architecture

```
Hermes state.db (sessions table)
    │  source=cron/weixin/cli/webui
    │  input_tokens, output_tokens, estimated_cost_usd
    ▼
apex/cost_tracker.py (Python module, 7 query functions)
    │  get_summary(), get_cron_costs(), get_agent_costs(),
    │  get_source_breakdown(), get_timeline(), get_full_snapshot()
    ▼
Flask API (apex/interface/web.py)
    │  /api/cost/summary, /api/cost/cron, /api/cost/agents,
    │  /api/cost/sources, /api/cost/projects, /api/cost/timeline,
    │  /api/cost/full
    ▼
Dashboard (/cost) — standalone HTML with auto-refresh
    │  4 tabs: Cron Costs, Agent Costs, Project Costs, Trends
    │  Donut chart (sources), bar+line chart (7-day trend)
```

## Quick Start

```bash
# Dashboard
open http://localhost:8080/cost

# API — summary
curl http://localhost:8080/api/cost/summary

# API — per-cron breakdown
curl http://localhost:8080/api/cost/cron?days=30
```

## Cron Job Cost Extraction

Cron jobs store sessions with IDs like `cron_<job_id>_<date>_<time>`. Extract job ID via regex:

```python
import re
job_id = re.match(r'cron_([a-f0-9]+)_', session_id).group(1)
```

Then cross-reference with `hermes cron list` output for human-readable names.

## Key Metrics

| Metric | Source | Query Pattern |
|:--|:--|:--|
| Per-cron cost | state.db sessions WHERE source='cron' | Parse job_id from session ID, aggregate |
| Per-agent cost | state.db sessions | GROUP BY handoff_platform or source |
| Source breakdown | state.db sessions | GROUP BY source |
| Timeline | state.db sessions | GROUP BY date/hour of started_at |
| Projects | Heuristic | Keyword match on title + system_prompt |

## Pricing

| Model | Input (per 1M) | Output (per 1M) |
|:--|:--|:--|
| deepseek-v4-pro | $1.00 | $4.00 |
| deepseek-chat | $0.14 | $0.28 |
| claude-sonnet-4 | $3.00 | $15.00 |

## Optimization Playbook

### 1. Identify waste

The dashboard's Cron tab shows all jobs sorted by 30-day cost. Focus on the top 3.

### 2. Reduce frequency

```bash
hermes cron update <job_id> --schedule "every 10m"  # was 5m
```

### 3. Switch to lightweight profile

Cron jobs inject the full system prompt (~20K tokens of SOUL + Memory + Skills).
Create a `cron-inspector` profile with empty skills list and minimal SOUL (~500 tokens):

```bash
mkdir -p ~/.hermes/profiles/cron-inspector
# Write SOUL.md and config.yaml (see token-optimization skill)
hermes cron update <job_id> --profile cron-inspector
```

### 4. Convert to no-agent script

For pure data collection with no reasoning, use `no_agent=true` + script:

```bash
hermes cron update <job_id> --no-agent --script "my_collector.py"
```

## Real-world Results (2026-06-07)

- 16 active cron jobs, 30-day cost: $6.85
- After optimization (bridge-sync 5m→10m + 7 LLM crons → cron-inspector profile): estimated $2.00/month
- Savings: 71% ($4.85/month, ~$58/year)
- Top cost driver: weixin interactive sessions (55%), not cron (25%)
