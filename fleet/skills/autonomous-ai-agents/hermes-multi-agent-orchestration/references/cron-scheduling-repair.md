# Cron Scheduling Repair Pattern

## Context (June 2026)

Luke's 16 cron jobs ran fine but 4+ agent jobs clustered at the same minute caused WeChat rate limiting. Additionally, a PM job with `authorization-contract` skill triggered the security scanner, and an unconfigured DingTalk job errored every run.

## Symptoms

```
⚠ Delivery failed: delivery error: Weixin send failed: iLink sendmessage rate limited: ret=-2
  Status: error: Blocked: prompt matches threat pattern 'destructive_root_rm'
```

## Repair Checklist

### 1. Diagnose — list all jobs with delivery status
```bash
hermes cron list
```
Look for:
- `⚠ Delivery failed` — rate limits or platform errors
- `error:` — security scanner blocks
- Jobs at the same minute — collision candidates

### 2. Stagger delivery windows
Any batch of 3+ agent jobs at the same minute risks WeChat rate limiting. Space them ≥5 min:
```bash
hermes cron edit <job_id> --schedule "5 21 * * *"   # was 0 21 * * *
hermes cron edit <job_id> --schedule "10 21 * * *"  # was 0 21 * * *
```

### 3. Fix security scanner false positives
Skills with security keywords (like `authorization-contract` containing "阿宝") trigger `destructive_root_rm`:
```bash
hermes cron edit <job_id> --clear-skills
```

### 4. Pause unconfigured delivery targets
```bash
hermes cron pause <job_id>    # DingTalk, Slack, etc. not yet wired
```

### 5. Verify
```bash
hermes cron list | grep -E "rate limited|error:|Every"  # no more errors
hermes cron run <job_id>                                 # manual trigger test
```

## Stable Post-Repair Matrix (15 active jobs)

```
🕘 09:00  重点项目脉搏 (2h)     ▸ WeChat
🕤 09:30  羽球宝PM日报          ▸ WeChat  
🕙 10:00  Apex PM日报          ▸ WeChat
🕘 21:00  监控日报推送          ▸ WeChat
🕔 21:05  羽球宝PM暮报          ▸ WeChat  (staggered from 21:00)

🔁 2min   AutoDL 隧道健康     ▸ WeChat  (no_agent script)
🔁 5min   AutoDL 空闲监控     ▸ WeChat  (no_agent script)
🔁 5min   apex-bridge-sync   ▸ local
🔁 60min  健康巡检            ▸ WeChat  (no_agent script)
🔁 120min 始祖舰队巡检        ▸ WeChat  (no_agent script)
🕛 03:00  双数据库备份         ▸ local

⏸️ 早起打气提醒              (paused — DingTalk not configured)
⏸️ 羽迹舰队晨报 → local      (delivery redirected — WeChat rate limited)
```

## Ownership

- **Cron scheduler**: Gateway process (default/始祖 profile's launchd service)
- **Cron health monitoring**: `ops-engineer` profile
- **Cron content (PM日报)**: `badminton-pm` (羽球宝) / `apex-pm` (Apex) / `content-marketing` (深圳地图)
- **Repair operator**: default profile (you) — cron jobs are infrastructure, not specific to one profile
