# 关键词匹配与调优指南

## 核心规则

### ❌ 禁止：Python regex `\b` 在中文关键词上

```python
# 错误 — 中文关键词永远匹配不到
re.compile(r"\b骨骼\b|\b标注\b|\b准确率\b")

# 正确 — 纯子串匹配
re.compile("骨骼|标注|准确率")
```

**原理**: Python `re` 模块的 `\b` (word boundary) 只认 `[a-zA-Z0-9_]` 为 word char。中文字符在 `\W` 中，所以 "的骨骼标注" 中 "的" 和 "骨" 都是 `\W`，中间无 boundary。

**验证方法**:
```python
import re
# 这个会返回 None
re.search(r"\b骨骼\b", "羽毛球骨骼分析")
# 这个会正常匹配
re.search("骨骼", "羽毛球骨骼分析")
```

### `dict.get` 不能当 `max()` key

```python
# 错误
max(scores, key=scores.get)

# 正确
max(scores, key=lambda k: scores[k])
```

## 假阳性治理

| 问题词 | 误判场景 | 修复 |
|:--|:--|:--|
| `识别` | "项目识别" 被送到 vision | → `图像识别` |
| `模型` | 同时匹配 ai-ml 和 architecture | → 靠匹配密度加权 |
| `api` | 任何 HTTP 话题都命中 development | → 配合项目限定范围 |

## 关键词密度评分

```
score = 匹配数 / max(1, 消息词数 × 0.08)
```

- score > 0.5 → 强信号，直接采纳
- score 0.2-0.5 → 弱信号，结合项目上下文
- score < 0.2 → 降级到 general

## 新增关键词规范

- 中文关键词 ≥ 2 字符（避免单字误判）
- 英文关键词有区分度（"log" vs "blog"）
- 项目关键词和类别关键词不重叠（避免模糊）
