---
name: apex-message-router
description: 智能消息路由 — 自动识别用户消息所属项目/任务类别/Agent角色，分配执行，统一结构化输出格式 [项目] [Agent角色] [类别]
category: collaboration
triggers:
  - 用户问题自动路由分配
  - 需要识别项目归属时
  - 通知输出需要结构化格式时
---

# 🔀 Apex 智能消息路由器

## 概述

当用户发来任何消息/问题/需求时，自动经过三层分析后分配执行：

1. **项目识别** — FinOps AI / 羽球宝AI搭子 / Apex Dashboard / 深圳羽球地图 / 通用
2. **类别分类** — PM / 开发 / 架构 / AI-ML / 视觉 / 前端 / 运维 / 安全 / 内容 / 商业
3. **Agent映射** — 匹配 Hermes Profile → 执行

## 使用方式

### A. 自动路由（推荐 — 嵌入回复格式）

每次回复用户前，先调用路由分析，在消息前加上结构化标签：

```
[📦 🏸 羽球宝AI搭子] [🧠 算法专家] [AI/ML]

{实际回复内容}
```

### B. API 调用（精准模式）

```bash
# 分析但不执行
curl -X POST http://127.0.0.1:8080/api/router/analyze \
  -H "Content-Type: application/json" \
  -d '{"message": "羽球宝的骨骼标注模型准确率需要提升"}'

# 快速分析（GET）
curl "http://127.0.0.1:8080/api/router/quick?msg=AutoDL服务器断连了"

# 获取完整矩阵
curl http://127.0.0.1:8080/api/router/matrix

# 分析+分发执行
curl -X POST http://127.0.0.1:8080/api/router/dispatch \
  -H "Content-Type: application/json" \
  -d '{"message": "修复小程序训练页接口", "execute": false}'
```

### C. 命令行

```bash
cd ~/Desktop/2026AIAPP/Apex
.venv/bin/python3 -m apex.orchestration.message_router "骨骼标注模型准确率"
.venv/bin/python3 -m apex.orchestration.message_router matrix
.venv/bin/python3 -m apex.orchestration.message_router quick "你的消息"
```

## 输出格式

```
[📦 {项目emoji} {项目名}] [{角色emoji} {角色名}] [{类别emoji} {类别名}]
{内容}
```

## 路由矩阵

| 项目 | 类别 | Agent Profile | 角色 |
|:--|:--|:--|:--|
| 🏸 羽球宝AI搭子 | PM | badminton-pm | 🎯 PM |
| 🏸 羽球宝AI搭子 | 开发/架构 | architect | 🏛️ 架构师 |
| 🏸 羽球宝AI搭子 | AI/ML | ai-algorithm | 🧠 算法专家 |
| 🏸 羽球宝AI搭子 | 视觉 | ai-vision | 👁️ 视觉专家 |
| 🏸 羽球宝AI搭子 | 前端 | frontend-dev | 🎨 前端开发 |
| 🏸 羽球宝AI搭子 | 内容 | content-marketing | ✍️ 内容推广 |
| 🦅 Apex | 全部 | default | ⚓ 始祖·总指挥 |
| 🦅 Apex | 运维 | ops-engineer | 🔧 运维工程师 |
| 🗺️ 深圳羽球地图 | 内容/商业 | content-marketing | ✍️ 内容推广 |
| 💰 FinOps AI | PM | finops-pm | 🎯 PM |
| 💰 FinOps AI | 架构 | finops-architect | 🏛️ 架构师 |
| 💰 FinOps AI | 后端 | finops-backend | ⚙️ 后端开发 |
| 💰 FinOps AI | 前端 | finops-frontend | 🎨 前端开发 |
| 💰 FinOps AI | 运维 | finops-devops | 🔧 DevOps |
| 💰 FinOps AI | 安全 | finops-security | 🔒 安全合规 |

## 代码位置

- 引擎: `~/Desktop/2026AIAPP/Apex/apex/orchestration/message_router.py`
- API: `~/Desktop/2026AIAPP/Apex/apex/interface/web.py` → `/api/router/*`
- 通知集成: `~/.hermes/scripts/notification_dispatcher.py`
- 关键词调优: `references/keyword-matching.md`
- PM 日报模板: `templates/pm-report-format.md`
- Cron wrapper 示例: `~/.hermes/scripts/notify_health.py`, `~/.hermes/scripts/notify_origin.py`

## 通知系统集成

notification_dispatcher 的 PM/始祖通知已支持结构化输出格式，自动带项目+角色标识。

## Pitfalls

- **中文关键词不能用 `\b`**: Python regex `\b` 只认 ASCII word chars，中文全被当作 non-word。必须用纯 substring matching (`re.compile("关键词1|关键词2")` 不加 `\b`) 才能在中文文本中命中。误用会导致所有中文关键词静默失败，全降级到 general 类别。详见 `references/keyword-matching.md`。
- **`dict.get` 不能当 `max()` 的 key**: `max(d, key=d.get)` 在某些 Python 版本触发类型错误，必须写 `max(d, key=lambda k: d[k])`。
- **假阳性**: 过于泛用的单字 ("识别") 会抢匹配，改用多字组合 ("图像识别") 降低误判。
- **置信度基准**: 无关键词匹配时 confidence=0.1，有匹配但项目不确定时用 prefer_project + 0.3 防全降级。

## Cron 集成注意事项

本 skill 的通知和 PM 日报依赖 Hermes cron。关键教训：

- **cron `script` 参数不支持带参数的脚本名**: `script: "dispatcher.py health"` 会被当成整体文件名查找而失败。必须创建 wrapper 脚本 (见 `~/.hermes/scripts/notify_health.py`)。
- **LLM 模式的 prompt 必须自包含**: 每次 cron 触发是独立 session，无上下文。prompt 必须包含：项目路径、信息源 (session_search/git)、输出格式标签。

## 扩展方法

新增项目/类别时编辑 `message_router.py` 中的:
- `PROJECTS` 字典 — 添加项目定义 (key, name, emoji, keywords)
- `CATEGORY_PATTERNS` 列表 — 添加类别 (category, agent_profile, keywords)
- `AGENT_ROLE` / `AGENT_EMOJI` 字典 — 补角色名和emoji

修改后运行 `python3 -m apex.orchestration.message_router matrix` 验证。
