---
name: token-optimization
description: 集成 LLMLingua + 规则压缩，降低 API token 消耗 20-70%
author: Luke
trigger: inject at startup
---

# Token 优化技能 — 压缩 Prompt 降成本

## 用途
每次发送 API 请求前，使用规则压缩 + LLMLingua 压缩 prompt，
降低 token 消耗 20-70%。

## 压缩层级

| 级别 | 方法 | 节省 | 依赖 |
|:---:|:----|:---:|:----|
| 1 | 规则压缩（移除冗余、缩短常用词） | 18-25% | ❌ 无 |
| 2 | LLMLingua（小模型逐token评估） | 50-70% | ✅ 需下载模型 |

## 集成方式

放在 backend 项目 `badminton_coach/token_optimizer.py`

### 1. 调用 API 前压缩

```python
from badminton_coach.token_optimizer import TokenOptimizer

opt = TokenOptimizer(level=1)  # level=1 零依赖，level=2 需要 LLMLingua 模型

# 压缩完整的 prompt（系统指令 + 用户输入 + 上下文）
result = opt.compress(
    system_prompt="系统指令模板",
    user_input="用户问题",
    rag_context="检索到的上下文",
    condition="任务类型说明",  # 帮助 LLMLingua 保持关键信息
)

# 用压缩后的 prompt 调用 API
api_result = call_llm_api(result.compressed_prompt)
print(f"节省了 {result.savings_pct}% token")
```

### 2. Hermes Agent 集成（在 AGENTS.md 或 skill 中）

在每次发送给 LLM 前，调用压缩：

```python
# 在 llm.call() 前插入
from badminton_coach.token_optimizer import optimize_prompt

compressed = optimize_prompt(
    system_prompt=system_prompt,
    user_input=user_message,
)
prompt_to_send = compressed.compressed_prompt
```

### 3. 一次性压缩系统指令模板

系统指令每次请求都发送，可以一次性压缩后缓存：

```python
# 只做一次
opt = TokenOptimizer(level=1)
compressed_system = opt.compress_system_only(
    "你是一个专业的羽毛球技能评估专家..."
)
# 之后每次复用 compressed_system.compressed_prompt
```

## 验证命令

```bash
cd ~/Desktop/2026AIAPP/workspace/badminton-coach-ai
./venv/bin/python3 -c "
from badminton_coach.token_optimizer import TokenOptimizer
opt = TokenOptimizer(level=1)
r = opt.compress(system_prompt='测试用系统指令模板文本', user_input='用户问题')
print(f'节省: {r.savings_pct}% | 延迟: {r.metadata[\"latency_ms\"]}ms')
"
```

## Pitfalls

1. BUG: LLMLingua 默认模型 gpt2 (~500MB) 在部分网络环境下下载很慢 — 优先用 level=1 规则压缩
2. BUG: 规则压缩可能过度缩短，导致系统指令失去精确性 — 重要数字/名称不要写在可替换模式中。压缩效果看实测: sys指令243tok→198tok(18.5%), 2ms延迟
3. 中文场景下 LLMLingua 的 gpt2 模型效果不如英文好，建议先用规则压缩
4. 压缩后的 prompt 不可读性增加，调试时可先关闭压缩
5. **HuggingFace 镜像问题**: 国内网络下 `HF_ENDPOINT=https://hf-mirror.com` 需要环境变量提前设置，在 Python 代码内设 `os.environ['HF_ENDPOINT']` 可能被 transformers 的 lazy import 时序问题覆盖。建议在 terminal 启动前 export: `export HF_ENDPOINT=https://hf-mirror.com && python3 ...`
6. **模型下载超时**: LLMLingua 默认加载 gpt2 (~500MB PyTorch checkpoint)，国内下载可能 2-5 分钟超时。实测 `curl -sL` 到 hf-mirror 的 config.json 可达但 pytorch_model.bin 下载超时。解决: 预先用 `huggingface-cli download gpt2 --resume-download` 下载好，或直接降级到 level=1 规则压缩
7. **规则压缩的 token 估算**: 中文 ≈ 1.5 token/字，英文 ≈ 0.25 token/字符。`_count_tokens()` 方法使用此估算公式，非精确 token 计数

## Cron 巡检成本优化

Cron Job 成本大头不在 prompt，而在 **System Prompt 注入** — 每次 run 注入完整 SOUL+Memory+Skills(~20K tokens)，实际巡检 prompt 只需 ~300 tokens。

### 优化三板斧

| 优先级 | 手段 | 效果 | 操作 |
|:--|:--|:--|:--|
| 1 | 降频 | 频率减半→成本减半 | `hermes cron update <id> --schedule "every 10m"` |
| 2 | 精简 Profile | 系统注入 20K→500 tokens | 创建 `cron-inspector` Profile (见 references) |
| 3 | 关 Skills | 去除非必需 skill 注入 | `hermes cron update <id> --skills ""` |

### 成本诊断命令

```bash
# 从 state.db 解析每个 cron job 的成本
sqlite3 ~/.hermes/state.db "
  SELECT id, input_tokens, output_tokens, estimated_cost_usd 
  FROM sessions WHERE source='cron' AND started_at > $(date -v-30d +%s)
" | python3 -c "
import sys, re
jobs={}
for l in sys.stdin:
  m=re.match(r'cron_([a-f0-9]+)_',l)
  if m:
    jid=m.group(1)
    parts=l.split('|')
    jobs[jid]=jobs.get(jid,0)+float(parts[3] or 0)
for jid,cost in sorted(jobs.items(),key=lambda x:-x[1])[:10]:
  print(f'{jid[:12]} \${cost:.4f}')
"
```

### 精简 Profile 模板

见 `references/cron-inspector-profile.md` — 完整 SOUL.md + config.yaml 模板，直接复制到 `~/.hermes/profiles/<name>/`。

### Cron → Profile 批量切换

```bash
# 查看哪些 cron 是 LLM 驱动（非 no-agent）
hermes cron list | grep -B5 "prompt_preview" 

# 批量切换
for jid in <job_ids>; do
  hermes cron update $jid --profile cron-inspector
done
```
