# Cron Inspector — 精简 Profile 模板

## 问题

Cron Job 每个 run 注入完整 System Prompt（SOUL.md + Memory + 89 Skills 列表），
~20,000 tokens/run。实际巡检 prompt 只需 ~300 tokens。

**浪费率: 98.5%**

## 解决方案

创建专用 `cron-inspector` Profile，只包含最小必要内容。

### SOUL.md

```markdown
# 📡 Cron Inspector — Lightweight Monitor Profile

You are a fleet inspection agent. Your ONLY job: run a monitoring check and report status concisely.

## Rules
1. Execute the monitoring task directly. No exploration, no deep thinking.
2. Output in 3-6 lines max. Use emoji + key data only.
3. If everything is normal, reply [SILENT] or one line.
4. No memory writes. No skill loading. No file creation.
5. Format: emoji [Project] Status: brief finding

## Pricing Context
- Input: $1/M tokens
- Output: $4/M tokens
- Budget-conscious: every token counts
```

### config.yaml

```yaml
model:
  default: deepseek-v4-pro
  provider: deepseek
  base_url: https://api.deepseek.com/anthropic
providers:
  deepseek:
    base_url: https://api.deepseek.com/anthropic
agent:
  max_turns: 10
  skills: []
```

### 关键配置说明

| 配置项 | 值 | 原因 |
|:--|:--|:--|
| `skills: []` | 空列表 | 不注入任何 skill，省 15K tokens |
| `max_turns: 10` | 极小值 | 巡检不需要多轮对话 |
| SOUL.md | 560 字节 | 仅状态报告格式说明 |

## 效果

| 指标 | 切换前 (default) | 切换后 (cron-inspector) | 节省 |
|:--|:--|:--|:--|
| System Prompt | ~20,000 tokens | ~500 tokens | 97.5% |
| 羽球宝PM日报 均次 | ~27,797 tokens | ~8,000 tokens | 71% |
| 羽球宝PM日报 均次成本 | $0.053 | $0.016 | 70% |
| 8个Cron月成本 | ~$6.89 | ~$2.00 | 71% |

## 部署步骤

```bash
# 1. 创建 profile 目录
mkdir -p ~/.hermes/profiles/cron-inspector

# 2. 写入 SOUL.md 和 config.yaml（内容见上）

# 3. 切换 cron job
hermes cron update <job_id> --profile cron-inspector

# 4. 验证
hermes cron list | grep cron-inspector
```
