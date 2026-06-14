# GPU Auto-Shutdown: Agent-Driven Pattern

## Problem

AutoDL GPU instances cost ¥0.08/min (4090). They stay running after training completes. A pure cron script can't distinguish "training complete" from "loading data between epochs" — both show GPU 0%.

## Solution

A Hermes Cron job running under the `ops-engineer` profile, with LLM-level judgment:

```
Cron (every 10 min) → ops-engineer → SSH → check → decide → act
```

## Implementation

### 1. Profile Setup

```bash
# ops-engineer needs config.yaml and .env
cat > ~/.hermes/profiles/ops-engineer/config.yaml << 'EOF'
model:
  default: deepseek-chat
  provider: deepseek
  base_url: https://api.deepseek.com/v1
agent:
  max_turns: 10
EOF

# Copy API key from main profile
grep DEEPSEEK_API_KEY ~/.hermes/.env >> ~/.hermes/profiles/ops-engineer/.env
```

### 2. Cron Job

```bash
hermes cron create "*/10 * * * *" \
  --name "GPU守夜Agent" \
  --skills monitoring-system \
  --model "deepseek-chat" \
  --prompt "You are the GPU night-watch agent for the 羽球宝AI搭子 project.

Your job every 10 minutes:
1. SSH to AutoDL: ssh -o ConnectTimeout=5 -p 32581 root@connect.bjb2.seetacloud.com
2. Run: nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader
3. Run: nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader
4. Decision tree:
   - If GPU > 5%: training active. Log and exit silently.
   - If GPU < 5% AND process list shows python: training loading data. Log and exit.
   - If GPU < 5% AND no processes:
     - 15 min idle: send WeChat to 老卢 'GPU idle 15min, ¥X wasted. Still need it?'
     - 25 min idle: send urgent WeChat '5 min until auto-shutdown'
     - 30 min idle: execute 'autodl shutdown', send WeChat 'GPU shut down, saved ¥X today'
5. Track idle minutes in a file on AutoDL: ~/monitor/idle_minutes.txt
6. After shutdown, also update Apex Dashboard via API if running.

IMPORTANT: Check process list BEFORE shutting down. GPU 0% with python processes running = still training."
```

### 3. Dashboard Integration

Add GPU status panel to Apex Dashboard V3 by calling Hermes Bridge API:

```
GET /api/gpu/status → {gpu_util, memory_used, idle_minutes, is_training, cost_today}
```

### 4. Key Decision Logic

| GPU % | Processes | Action |
|-------|-----------|--------|
| >5% | Any | Training — do nothing |
| <5% | python running | Loading — do nothing |
| <5% | None, <15min | Idle — track time |
| <5% | None, 15min | Warning WeChat |
| <5% | None, 25min | Urgent WeChat |
| <5% | None, 30min | Auto shutdown |

## Why Agent > Script

A bash script can check nvidia-smi, but can't:
- Read process names and reason about whether they indicate training
- Decide if a stuck process should be force-killed
- Compose a natural-language WeChat message with cost context
- Adapt thresholds based on time of day (老卢 trains 8pm-11pm)
- Ask for confirmation when ambiguous
