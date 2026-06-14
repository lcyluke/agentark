# Token Optimizer Backend Integration — 羽球宝AI搭子

## 项目路径
```
~/Desktop/2026AIAPP/workspace/badminton-coach-ai/badminton_coach/token_optimizer.py
```

## 文件结构

| 类/函数 | 作用 |
|:--------|:-----|
| `TokenOptimizer` | 主类，级别1-3 |
| `TokenOptimizer.compress()` | 完整压缩：system + user + RAG |
| `TokenOptimizer.compress_system_only()` | 仅压缩系统指令 |
| `optimize_prompt()` | 便捷函数，一键压缩 |
| `estimate_tokens()` | 估算 token 数 |

## 使用场景

### 场景1: 规则压缩（推荐默认）
```python
from badminton_coach.token_optimizer import TokenOptimizer
opt = TokenOptimizer(level=1)
result = opt.compress(
    system_prompt="你是一个羽毛球教练...",
    user_input="我的动作哪里有问题",
    rag_context="检索到的技术分析..."
)
# result.savings_pct → 18-25%
# result.compressed_tokens → 减少后的tokens
# result.compressed_prompt → 压缩后文本
```

### 场景2: 预压缩系统指令（一次压缩，永久复用）
```python
opt = TokenOptimizer(level=1)
compressed_sys = opt.compress_system_only(SYSTEM_PROMPT)
# 之后每次调用复用 compressed_sys.compressed_prompt
```

### 场景3: LLMLingua 压缩（需先下载模型）
```bash
# 先确保模型可下载
export HF_ENDPOINT=https://hf-mirror.com
huggingface-cli download gpt2 --resume-download
```
```python
opt = TokenOptimizer(level=2)  # 自动使用缓存模型
result = opt.compress(system_prompt=..., user_input=..., condition="羽毛球技术评估")
```

## 实测数据

| 级别 | 耗时 | 节省 | 依赖 |
|:---:|:----:|:----:|:----:|
| 1 (规则) | 2ms | 18.5% | 无 |
| 2 (LLMLingua) | ~500ms | 50-70% | gpt2 模型 ~500MB |

## AGENTS.md 配置

项目根目录 `AGENTS.md` 已包含 token 优化指令，Hermes 会自动加载。

## 验证命令

```bash
cd ~/Desktop/2026AIAPP/workspace/badminton-coach-ai
./venv/bin/python3 -c "
from badminton_coach.token_optimizer import TokenOptimizer
opt = TokenOptimizer(level=1)
r = opt.compress(system_prompt='测试系统指令模板', user_input='用户问题')
print(f'节省: {r.savings_pct}% | 延迟: {r.metadata[\"latency_ms\"]}ms')
"
```
