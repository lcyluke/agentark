# Dashboard V4 — Command Center Architecture

> Built 2026-06-03. Replaces Dashboard V3 (synthetic data) with real data from Hermes state.db, monitor.db, and Apex APIs.

## File Layout

```
apex/interface/
├── web.py                    # Flask app — 20 routes including new Command Center APIs
├── hermes_bridge.py          # Data aggregation layer — reads Hermes state.db, monitor.db, CLI
└── templates/
    ├── dashboard.html        # Original V3 (synthetic data)
    └── dashboard_v4.html     # V4 Command Center (real data, 1200+ lines)
```

## New API Endpoints (added to `web.py`)

| Endpoint | Method | Description | Data Source |
|---|---|---|---|
| `/api/hermes/status` | GET | Sessions, cron, profile status | state.db + CLI |
| `/api/hermes/tokens` | GET | Token stats: total, 24h, today, per-source, per-model | state.db |
| `/api/gpu/status` | GET | GPU utilization, memory, temp, cost | monitor.db |
| `/api/models/pricing` | GET | Model pricing table + configured providers | built-in + .env |
| `/api/command-center` | GET | All above in one call + profile list | aggregated |

## Hermes state.db Schema (relevant fields)

### sessions table
```
input_tokens       INTEGER   — total input tokens for the session
output_tokens      INTEGER   — total output tokens
cache_read_tokens  INTEGER   — prompt caching reads (can be huge)
cache_write_tokens INTEGER   — prompt caching writes
reasoning_tokens   INTEGER   — reasoning/thinking tokens
estimated_cost_usd REAL      — estimated cost in USD
actual_cost_usd    REAL      — actual billed cost
started_at         REAL      — Unix timestamp
model              TEXT      — model name used
billing_provider   TEXT      — provider billed through
source             TEXT      — 'cli', 'weixin', 'cron', 'webui', etc.
message_count      INTEGER
title              TEXT
```

Key insight: **Use sessions table for token/cost stats, NOT messages.token_count.** The sessions table already aggregates per-session totals.

## monitor.db Schema

### gpu_metrics
```
utilization_gpu     REAL
utilization_memory  REAL
memory_used_mb      REAL
memory_total_mb     REAL
temperature_gpu     REAL
power_draw          REAL
```

### cost_log
```
cost_yuan           REAL      — cost in CNY (NOT USD)
runtime_minutes     REAL
gpu_name            TEXT
task_name           TEXT
```

## Model Pricing (USD per 1M tokens)

```
deepseek-v4-pro:  $1.00 input / $4.00 output
deepseek-chat:    $0.14 input / $0.28 output
deepseek-r1:      $0.55 input / $2.19 output
claude-sonnet-4:  $3.00 input / $15.00 output
claude-3-opus:    $15.00 input / $75.00 output
gpt-4o:           $2.50 input / $10.00 output
gemini-1.5-pro:   $1.25 input / $5.00 output
```

## Pitfalls from Build

1. **Flask template caching**: After editing dashboard HTML, you MUST restart the Flask process. Browser hard-refresh won't help.
2. **Canvas API + CSS variables**: Canvas 2D context cannot parse `var(--accent)`. Always use hex colors: `#3b82f6`.
3. **el() number handling**: JS helper that builds DOM elements must handle non-string/non-array children (numbers, null).
4. **monitor.db column names**: `cost_yuan` and `runtime_minutes`, not `total_cost` or `running_minutes`.
5. **state.db column names**: `started_at` not `created_at`. Use session-level `input_tokens`/`output_tokens`, not per-message `token_count`.
6. **`hermes profile list` parsing**: Default profile marked with `◆`, gateway status is "running" or "stopped" in the table.
