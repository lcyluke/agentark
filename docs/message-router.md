# 🔀 智能消息路由器 v2

## 概览

当用户发送任何消息/问题/需求，系统自动进行三层分析后分配执行：

```
用户消息 → [项目识别] → [类别分类] → [Agent映射] → 结构化输出
```

**输出格式**: `[📦 项目emoji 项目名] [角色emoji 角色名] [类别]` + 内容

## 路由矩阵

| 项目 | 类别 | Agent Profile | 角色 |
|:--|:--|:--|:--|
| 🏸 羽球宝AI搭子 | PM/进度/排期 | yuji-pm | 🎯 PM·羽迹 |
| 🏸 羽球宝AI搭子 | 开发/API/后端 | architect | 🏛️ 架构师 |
| 🏸 羽球宝AI搭子 | 架构/设计/DB | architect | 🏛️ 架构师 |
| 🏸 羽球宝AI搭子 | AI/ML/模型/标注 | ai-algorithm | 🧠 算法专家 |
| 🏸 羽球宝AI搭子 | 视觉/视频/图像 | ai-vision | 👁️ 视觉专家 |
| 🏸 羽球宝AI搭子 | 前端/UI/界面 | frontend-dev | 🎨 前端开发 |
| 🏸 羽球宝AI搭子 | 运维/部署/隧道 | ops-engineer | 🔧 运维工程师 |
| 🏸 羽球宝AI搭子 | 安全/权限/密码 | security-compliance | 🔒 安全合规 |
| 🏸 羽球宝AI搭子 | 内容/公众号/品牌 | content-marketing | ✍️ 内容推广 |
| 🏸 羽球宝AI搭子 | 商业/融资/营收 | fundraising-pitch | 💰 融资路演 |
| 🦅 Apex Dashboard | 全部 (默认) | default | ⚓ 始祖·总指挥 |
| 🦅 Apex Dashboard | 运维/部署 | ops-engineer | 🔧 运维工程师 |
| 🗺️ 深圳羽球地图 | 全部 | content-marketing | ✍️ 内容推广 |

## API 端点

| 端点 | 方法 | 说明 |
|:--|:--|:--|
| `/api/router/analyze` | POST | 分析消息，返回路由结果（不执行） |
| `/api/router/dispatch` | POST | 分析+分发到 Agent 执行 |
| `/api/router/matrix` | GET | 完整项目-类别-Agent 映射矩阵 |
| `/api/router/quick` | GET | 快速一行分析（`?msg=...`） |

## 集成点

### 1. Hermes Skill (`apex-message-router`)
加载后自动路由消息 → 在回复中加结构化标签

### 2. 通知引擎 (`notification_dispatcher.py` v2.1)
每条通知自动带 `[📦 项目] [角色] [类别]` 前缀

### 3. Apex Dashboard
`/api/router/*` 端点，供外部系统调用

## 验证

```bash
# 命令行测试
cd ~/Desktop/2026AIAPP/Apex
.venv/bin/python3 -m apex.orchestration.message_router "骨骼标注模型的准确率"

# API 测试
curl "http://127.0.0.1:8080/api/router/quick?msg=小程序前端UI调整"

# 查看完整矩阵
curl http://127.0.0.1:8080/api/router/matrix | python3 -m json.tool
```
