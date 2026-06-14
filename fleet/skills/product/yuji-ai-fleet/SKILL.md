---
name: yuji-ai-fleet
description: "羽迹AI舰队 — 小卢（船长秘书）管理的多智能体团队。涵盖技术/商业/融资全链条，所有角色通过 Hermes Profiles + Kanban 协作。"
version: 1.1.0
metadata:
  hermes:
    tags: [kanban, multi-agent, fleet, team]
    related_skills: [badminton-pm, yuji-life-map]
author: Luke & 小卢
---

# 🚢 羽迹AI舰队组织架构

## 依赖

> **前置技能**：`hermes-multi-agent-orchestration` — 如果不知道如何创建Profile/Kanban/注入SOUL，先加载那个技能。

## 核心理念

> 小卢是**船长秘书/项目经理**，老卢是**CEO/产品决策者**。
> 每个AI Agent是一个独立Profile，有明确的角色、职责、技能和模型偏好。
> 任务由小卢分解→Kanban分派→各Agent独立执行→小卢汇总→报告给老卢。

## 组织架构图

```
                    👑 老卢（CEO/产品决策者）
                          │
              ┌───────────┴───────────┐
              │      🧑‍✈️ 小卢         │
              │   (船长秘书/项目经理)   │
              └───────────┬───────────┘
                          │
    ┌─────────┬─────────┬┴┬─────────┬──────────┐
    │         │         │ │         │          │
  💻开发线    🤖AI线    │ 📢商业线   🔒合规线   💰资本线
    │         │         │ │         │          │
  ┌─┴──┐   ┌─┴──┐  ┌──┴──┐   ┌──┴──┐    ┌───┴───┐
  │前端 │   │视觉 │  │内容 │   │安全 │    │融资   │
  │小哥 │   │专家 │  │推广 │   │合规 │    │路演   │
  ├─────┤   ├─────┤  ├─────┤   ├─────┤    ├───────┤
  │架构 │   │算法 │  │销售 │   │     │    │决策   │
  │师   │   │专家 │  │专家 │   │     │    │专家   │
  ├─────┤   ├─────┤  │     │   │     │    │       │
  │模型 │   │     │  │     │   │     │    │       │
  │优化 │   │     │  │     │   │     │    │       │
  └─────┘   └─────┘  └─────┘   └─────┘    └───────┘
```

## 角色职责详表

### 🧑‍✈️ 核心管理

| 角色 | Profile名 | 模型建议 | 职责 |
|------|----------|---------|------|
| 👑 **CEO 老卢** | — | — | 产品方向决策、最终拍板、对外商务 |
  | 🧑‍✈️ **小卢（船长秘书/项目经理）** | `default` | DeepSeek | 分解任务、派发到Kanban、汇总结果、向老卢汇报 |

### 💻 开发线

| 角色 | Profile名 | 模型建议 | 核心技能 | 职责 |
|------|----------|---------|---------|------|
| 💻 **前端小哥** | `frontend-dev` | DeepSeek/Claude（轻量） | 微信小程序、WXML/CSS/JS、地图SDK、UI设计 | 小程序页面开发、时间线展示、地图标注、UI交互 |
| 🏗️ **架构师** | `architect` | Claude（强推理） | 系统设计、技术选型、数据库设计、API设计 | 整体技术架构设计、扩展性规划、技术债务管理 |
| 🐧 **运维小哥** | `ops-engineer` | DeepSeek（轻量） | Nginx、Docker、Linux、域名/HTTPS、CDN | 服务器部署、Nginx配置、监控、CI/CD |

### 🤖 AI线

| 角色 | Profile名 | 模型建议 | 核心技能 | 职责 |
|------|----------|---------|---------|------|
| 👁️ **视觉专家** | `ai-vision` | Claude（强视觉）/GPT-4V | MediaPipe、YOLO、图片分类、OCR | 球馆照片→自动识别、姿态分析、视频处理 |
| 🧠 **算法专家** | `ai-algorithm` | Claude（强推理） | 推荐系统、协同过滤、NLP、数据挖掘 | 智能推荐引擎、用户画像、人生报告生成 |
| ⚡ **模型优化专家** | `ai-optimizer` | 本地模型（免费） | 模型量化、ONNX、蒸馏、端侧部署 | 模型压缩、手机端推理优化、成本控制 |

### 📢 商业线

| 角色 | Profile名 | 模型建议 | 核心技能 | 职责 |
|------|----------|---------|---------|------|
| ✍️ **内容专家** | `content-writer` | DeepSeek/Claude | 公众号写作、小红书文案、SEO、品牌调性 | 公众号文章、小红书笔记、产品文案、品牌故事 |
| 🚀 **推广专家** | `growth-hacker` | DeepSeek | 用户增长、裂变策略、社群运营、ASO | 获客策略、活动设计、数据驱动增长 |
| 🤝 **销售BD专家** | `sales-bd` | DeepSeek | 商务谈判、合作方案、定价策略 | 商家合作洽谈、折扣谈判、合作伙伴管理 |

### 🔒 合规线

| 角色 | Profile名 | 模型建议 | 核心技能 | 职责 |
|------|----------|---------|---------|------|
| 🛡️ **安全合规专家** | `security-compliance` | Claude（强推理） | 数据安全法、个人信息保护法、GDPR、网络安全 | 隐私政策、用户数据保护、合规审查、安全审计 |
| ⚖️ **法务顾问** | `legal-advisor` | DeepSeek | 合同审查、知识产权、ICP备案法规 | 用户协议、商家合同、知识产权保护 |

### 💰 资本线

| 角色 | Profile名 | 模型建议 | 核心技能 | 职责 |
|------|----------|---------|---------|------|
| 📊 **融资专家** | `fundraising` | Claude（强推理） | BP撰写、财务模型、估值分析 | 商业计划书、财务预测、投资人deck |
| 🎤 **路演专家** | `pitch-master` | DeepSeek | 演讲技巧、故事叙述、PPT设计 | 路演稿撰写、投资人沟通脚本、演示材料 |
| 📈 **决策分析师** | `decision-analyst` | Claude（强推理） | 数据分析、市场研究、竞品分析 | 市场分析报告、数据驱动决策建议、风险评估 |

## 模型使用策略

| 任务类型 | 推荐模型 | 月费估算 |
|---------|---------|---------|
| 🟢 日常对话/简单编码 | DeepSeek | ~5-15元 |
| 🟡 复杂推理/架构设计 | Claude Sonnet | ~50-100元 |
| 🔴 视觉识别/视频分析 | Claude/GPT-4V | ~100-300元 |
| ⚪ 本地小任务/定时脚本 | 本地LLM（免费） | 0元 |

## 实战工作流（Apex Team Template — 推荐）

> 2026年6月起，新项目用 `apex team template` 一键创建团队，不再手动创建Profile

### 一键创建项目组

```bash
cd ~/Desktop/2026AIAPP/Apex && source .venv/bin/activate

# 选择模板
apex team template list
# webapp    Web Application Team    product-manager, frontend-dev, backend-dev, devops
# startup   Startup MVP Team        ceo-pm, fullstack-dev, designer, growth-marketer

# 创建团队（一步完成4个Agent）
apex team template startup
# → 创建 ceo-pm, fullstack-dev, designer, growth-marketer
# → 每个有 SOUL.md + config.yaml + ~/.local/bin/<name> 包装脚本

# 打开4个终端, 各跑一个
# 终端1: ceo-pm chat      → "👑 CEO/PM" 
# 终端2: fullstack-dev chat → "💻 Fullstack Developer"
# 终端3: designer chat     → "🎨 Designer"
# 终端4: growth-marketer chat → "🚀 Growth Marketer"
```

### 任务层级管理（Epic → Story → Task → Subtask）

```bash
# PM创建Epic
apex task create "MVP v1" --type epic --project startup --hours 120

# 拆Story
apex task create "Landing page" --type story --parent <EPIC_ID> \
  --assignee fullstack-dev --hours 16

# 拆Task
apex task create "Hero section" --type task --parent <STORY_ID> \
  --assignee fullstack-dev --hours 6

# 查看完整树
apex task epic "MVP v1"
# → 🏗️ MVP v1 [in_progress] ████████░░ 80%
#    ├─ 📖 Landing page ✅ completed
#    │  ├─ 📋 Hero section ✅
#    │  └─ 📋 CTA section ✅
#    └─ 📖 Waitlist signup 🔄 in_progress
```

### 跨Agent求助（PM审批）

```bash
# Fullstack需要Designer帮助
apex help-request designer "Need hero section mockup" --task <TASK_ID>

# PM审批、指派
apex help-approve <REQUEST_ID> --agent designer --notes "Create 3 variants"

# 查看Agent负载
apex capacity
```

## 团队调用流程（传统方式）

```
老卢微信说："小卢，帮我把打卡地图做了"
    ↓
小卢(项目经理)：
  1️⃣ 分析任务：前端地图页面 + 后端地图API(已有) + 地图SDK接入
  2️⃣ 拆分子任务：
     - 🏗️ 架构师：设计地图页面数据流（30min）
     - 💻 前端小哥：实现地图页面（2h）
     - 🐧 运维小哥：备案后部署（30min）
  3️⃣ 推送到Kanban看板
  4️⃣ 各Agent领取任务→独立执行
  5️⃣ 小卢汇总→报告给老卢
```

## 优先级排期

| 优先级 | 角色 | 创建时间 | 理由 |
|--------|------|---------|------|
| 🅿️0 | 💻 前端小哥 | ✅ 已就绪 | 小程序页面开发 |
| 🅿️0 | 👁️ 视觉专家 | ✅ 已就绪 | 图片识别是打卡核心能力 |
| 🅿️1 | 🏗️ 架构师 | ✅ 已就绪 | 系统扩展性规划 |
| 🅿️1 | 🧠 算法专家 | ✅ 已就绪 | 推荐引擎设计 |
| 🅿️2 | ✍️ 内容专家 | ✅ 已就绪 | 内容运营 |
| 🅿️2 | 🛡️ 安全合规 | ✅ 已就绪 | 安全合规审查 |
| 🅿️3 | 💰 融资/路演 | ✅ 已就绪 | 融资需要时启动 |

> **2026-06-04 更新**：全舰队 33 Agent 已统一升级到 deepseek-v4-pro。6 个监控 Agent（fleet-commander/gpu-sentinel/token-guardian/session-scout/cron-medic/profile-syncer）已创建 Hermes Profile，实现 Apex-Hermes 双向集成。

## 舰队协同工具

| 工具 | 用途 |
|------|------|
| 📋 **Kanban看板** (`board: yuji`) | 任务分配与追踪（8个P0任务已创建） |
| 📚 **Skills共享** | 公共知识库（各Agent写入） |
| 🗄️ **共享文件系统** | 代码/文档共享 |
| 📝 **Memory** | 跨会话记忆 |
| ⏰ **Cron Jobs** | 定时任务（数据采集/报告） |

## 🧑‍✈️ 新增角色：PM Agent (`badminton-pm`)

| 角色 | Profile名 | 模型建议 | 职责 |
|------|----------|---------|------|
| 🧑‍✈️ **PM Agent** | `badminton-pm` | DeepSeek | 维护 ROADMAP + ITERATION + VERSION_GUIDE + UAT + RELEASE_NOTES |

**PM Agent = 小卢的项目管理分身。** 技能 `badminton-pm` 定义了完整工作流。Profile 创建于 `~/.hermes/profiles/badminton-pm/`，Kanban board `yuji` 已初始化含8个P0任务。

## 实战工作流：批量创建Profile

当需要同时创建多个Agent Profile时，使用 `delegate_task` 并行执行（受 `delegation.max_concurrent_children` 限制，默认3个并发）。

### 步骤（已验证可行）

1. **确定角色清单** — 列出所有要创建的Profile名称
2. **分批提交** — 每批不超过 max_concurrent_children 个
3. **每个子任务包含**：
   - `hermes profile create <name>`
   - 写入 `~/.hermes/profiles/<name>/SOUL.md`（角色灵魂注入）
   - 验证创建成功（`hermes profile list | grep <name>`）
4. **确认全员就位** — 最后跑一次 `hermes profile list` 全量检阅

### 已知坑点

- **新创建的Profile不会立即出现在Kanban assignee列表**，需要先运行一次 `hermes kanban init` 或在gateway中激活才会被发现。如果 dispatcher 找不到，手动触发一次即可。
- **每个Profile默认无API Key**，会继承shell环境变量。独立配置需运行 `<profile-name> setup`。
- **SOUL.md 必须手动创建**（`hermes profile create` 不会自动生成），这是角色定制的关键步骤。

### 任务分派流程

```
老卢微信说"做XX"
    ↓
小卢(项目经理)：
  1. 分析任务 → 拆子任务
  2. 确定需要的角色（前端/视觉/算法/...）
  3. 推到Kanban：hermes kanban create --assignee <profile-name>
  4. 启动对应Profile：terminal(background=True, command="<profile-name> chat -q '任务描述'")
  5. 汇总结果 → 报告老卢
```

## 📦 羽球宝数据库备份

> **详细文档**：`references/backup-system.md` — 备份架构、cron 配置、验证方法。

| 关键事实 | 值 |
|---------|-----|
| 备份脚本真实路径 | `/Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai/daily_backup.sh` |
| 备份验证正确方式 | 先 `gunzip -k` 解压到临时文件，再 `sqlite3 <file> ".tables"` |
| 验证陷阱 | `gunzip -c \| sqlite3 :memory:` 不可靠（.tables 返回空） |
| cron 冗余 | 两个 job（`a64ab8981d29` 旧路径 + `22ed3110b7a0` 正确路径），建议只保留后者 |

## 💡 多Agent协作原则

1. **小卢永远是老卢的唯一接口** — 所有Agent的输出由小卢汇总后汇报，不给老卢造成多个声音的混乱
2. **每个Agent只干自己领域的事** — 前端小哥不碰服务器，视觉专家不改数据库
3. **Kanban是唯一的任务分派通道** — 不用私聊派活，所有任务走看板可追溯
4. **遇到阻塞及时上报** — Agent卡住超过15分钟，主动向小卢预警
