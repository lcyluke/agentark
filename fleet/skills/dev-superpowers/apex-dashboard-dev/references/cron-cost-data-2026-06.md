# Cron Job Cost Data (sampled 2026-06-07, 30-day window)

Source: Hermes state.db sessions table, parsed per cron job ID.
Model: deepseek-v4-pro ($1/M input, $4/M output)

## Cron Cost Ranking (30 days, descending)

| 排名 | 任务名 | 频率 | 运行次数 | Tokens | 30天成本 | 均次成本 |
|:--|:--|:--|:--|:--|:--|:--|
| 1 | apex-bridge-sync | every 5m | 982 | 1.6M | $4.25 | $0.004 |
| 2 | 重点项目脉搏 (2h) | 0 9-21/2 | 23 | 361K | $0.70 | $0.031 |
| 3 | FinOps AI 任务监控 | every 30m | 69 | 191K | $0.43 | $0.006 |
| 4 | 羽迹舰队晨报 | 0 9 * * * | 8 | 337K | $0.36 | $0.045 |
| 5 | 羽球宝PM暮报 | 5 21 * * * | 4 | 125K | $0.23 | $0.058 |
| 6 | 监控日报推送 | 0 21 * * * | 5 | 82K | $0.18 | $0.037 |
| 7 | fleet-status-collector | every 15m | 8 | 81K | $0.17 | $0.021 |
| 8 | 羽球宝PM日报 | 30 9 * * * | 3 | 83K | $0.16 | $0.053 |
| 9 | FinOps AI PM日报 | 0 9 * * * | 1 | 46K | $0.09 | $0.085 |
| 10 | 羽球宝数据库每日备份 | 0 3 * * * | 7 | 116K | $0.08 | $0.011 |
| 11 | evidence-collector | every 30m | 1 | 33K | $0.07 | $0.068 |
| 12 | 羽球宝数据库每日备份2 | 0 3 * * * | 7 | 64K | $0.05 | $0.007 |
| 13 | Apex PM日报 | 0 10 * * * | 3 | 21K | $0.05 | $0.015 |
| 14 | skill-eval-full | 0 2 * * * | 3 | 17K | $0.04 | $0.013 |
| 15 | 舰队巡检报告 (2h) | 0 9-21/2 | 7 | 7K | $0.02 | $0.002 |

**16 cron jobs total: $6.89/30 days, $0.23/day**

## Source Channel Breakdown

| Source | Sessions | Cost (30d) | % |
|:--|:--|:--|:--|
| webui | 7 | $40.47 | 56% |
| weixin | 53 | $15.27 | 21% |
| cli | 108 | $8.97 | 13% |
| cron | 1133 | $6.89 | 10% |

## Key Insight

PM cron jobs consume ~25-45K tokens per run, but most is the Hermes system prompt (SOUL.md + MEMORY + USER + Skills ~20K). The actual monitoring task is ~500-1000 tokens.
