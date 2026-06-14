# 🦅 Apex Agent Fleet — 完整舰队编制

> **Apex 多 Agent 操作系统 · 33 Agent 编制**
> 一个人的公司，一支 AI 舰队。

---

## 舰队架构

```
                    ⚓ Origin (舰队总司令)
                    ┌───────┼───────┐
                    │       │       │
              🧭 监控层    📋 PM层   🔧 执行层
              (6 Agent)   (5 Agent)  (22 Agent)
                    │       │       │
              ┌─────┤   ┌───┤   ┌───┼───────┐
              │     │   │   │   │   │       │
            舰队   GPU  PM  项目 开发  AI   安全/内容
            指挥  哨兵  Agent Agent Agent Agent Agent
```

---

## 一、🧭 舰队管理层（Monitoring Fleet）

自动化运维，24×7 值守。6 个 Agent 通过 Apex AutonomousEngine + Hermes Cron 协同工作。

| Agent | 角色 | 职能 | Apex YAML | Hermes Profile |
|-------|------|------|-----------|----------------|
| **fleet-commander** | 🧭 舰队司令 | 全舰队状态汇总、异常预警 | ✅ | ✅ |
| **gpu-sentinel** | ⚡ GPU 哨兵 | GPU 利用率/成本/闲时关机 | ✅ | ✅ |
| **token-guardian** | 💰 Token 守卫 | API 用量统计/预算预警 | ✅ | ✅ |
| **session-scout** | 🔍 会话斥候 | 新会话发现/分类/登记 | ✅ | ✅ |
| **cron-medic** | 🛡️ Cron 军医 | 定时任务健康巡检 | ✅ | ✅ |
| **profile-syncer** | 📡 通讯兵 | Profile 状态同步 Apex↔Hermes | ✅ | ✅ |

---

## 二、📋 项目管理线（PM Fleet）

产品方向决策、需求管理、授权审批。

| Agent | 角色 | 职能 | Apex YAML | Hermes Profile |
|-------|------|------|-----------|----------------|
| **apex-pm** | 🦅 Apex PM | Apex 平台总管、授权引擎、里程碑 | ❌ | ✅ |
| **yuji-pm** | 🎯 羽球宝 PM | 羽球宝AI搭子项目管理 | ❌ | ✅ |
| **product-manager** | 📋 产品经理 | 通用 PRD/用户研究/路线图 | ✅ | ✅ |
| **project-manager** | 📊 项目经理 | 跨项目 Kanban/资源调度 | ❌ | ✅ |
| **requirements-analyst** | 📝 需求分析师 | 需求拆解/用例分析 | ❌ | ✅ |

---

## 三、💻 开发线（Dev Fleet）

### 3.1 前端

| Agent | 角色 | 核心技能 | Apex YAML | Hermes Profile |
|-------|------|---------|-----------|----------------|
| **frontend-dev** | 💻 前端开发 | React/Vue/小程序/Tailwind | ✅ | ✅ |
| **fullstack-dev** | 👨‍💻 全栈开发 | React+FastAPI+部署 | ❌ | ✅ |

### 3.2 后端

| Agent | 角色 | 核心技能 | Apex YAML | Hermes Profile |
|-------|------|---------|-----------|----------------|
| **backend-dev** | ⚙️ 后端开发 | FastAPI/Python/数据库 | ✅ | ✅ |
| **architect** | 🏛️ 架构师 | 系统

# Apex — Multi-Agent Operating System

## Project Overview
Apex 是一个多Agent操作系统，让单个开发者通过AI Agent舰队完成整个项目的设计、开发、测试和部署。

## Architecture
- **apex/core**: Profile管理、Runtime引擎、KnowledgeGraph、EvolutionEngine
- **apex/orchestration**: Kanban任务系统、Swarm并行执行、Crew团队协作、Autonomous自治引擎
- **apex/interface**: Flask Web Dashboard (/cc, /v5), REST API, Hermes Bridge
- **apex/cli**: Click-based CLI commands (chat, run, task, team, etc.)

## Current Status
- Dashboard `/cc` 已上线，10个视图 + 5个交互模块
- 6个Apex Agent Profiles已创建 (frontend-dev, backend-dev, devops, qa-agent, data-analyst, security-auditor)
- 3个项目团队 (Apex, 羽球宝AI, 深圳羽球地图)
- 11个任务在Kanban中

## Team Members
| Agent | Role | Team |
|-------|------|------|
| frontend-dev | Frontend Architect | Apex, 羽球宝AI |
| backend-dev | Core Engine | Apex, 羽球宝AI |
| qa-agent | QA Tester | 羽球宝AI |
| devops | DevOps | 羽球宝AI |
| security-auditor | Security | Apex, 深圳羽球地图 |
| data-analyst | Data Pipeline | 深圳羽球地图 |

## Active Technologies
- Python 3.11+ / FastAPI / Click / Rich
- Flask (Web Dashboard)
- SQLite (state.db, kanban.db, knowledge.db)
- Hermes (Agent runtime, ~/.hermes/)
- Tabler Icons (UI), Sora/Manrope fonts

## Code Paths
- Project root: /Users/Mac/Desktop/2026AIAPP/Apex
- Dashboard: apex/interface/templates/command_center.html
- API: apex/interface/web.py
- CLI: apex/cli/main.py
- Hermes profiles: ~/.hermes/profiles/


## Current Project Tasks (Kanban)

- 🔄 [1] **羽球宝AI_pm**: [羽球宝AI] 需求分析 → PRD
- 📋 [1] **test-company_pm**: [test-company] Requirements Analysis → PRD
- 📋 [1] **devops**: [Apex Demo] Backend — API Health Check System
- 📋 [1] **default**: [Apex Demo] PM — Sprint Plan & Task Breakdown
- ⏳ [1] **backend-dev**: [羽球宝AI] 球场预约API - 实现CRUD端点 (接班frontend-dev)
- ⏳ [1] **qa-agent**: [羽球宝AI] 球场预约API集成测试 (接班backend-dev)
- ⏳ [1] **frontend-dev**: [Apex Demo] Frontend — Build Welcome Dashboard
- ⏳ [1] **devops**: [Apex Demo] Backend — API Health Check System
- ⏳ [1] **default**: [Apex Demo] PM — Sprint Plan & Task Breakdown
- 📋 [2] **羽球宝AI_frontend**: [羽球宝AI] 架构设计 → 技术方案
- 📋 [2] **羽球宝AI_backend**: [羽球宝AI] 前后端并行开发 → 代码
- 📋 [2] **羽球宝AI_devops**: [羽球宝AI] 集成测试 → 测试报告
- 📋 [2] **羽球宝AI_content**: [羽球宝AI] 部署上线 → 生产环境
- 📋 [2] **羽球宝AI_pm**: [羽球宝AI] 内容发布 → 官网/文档
- 📋 [2] **羽球宝AI_frontend**: [羽球宝AI] 监控运维 → 运维报告

## Project Teams & Agents

- **羽球宝AI**: frontend-dev (Frontend), backend-dev (Backend), qa-agent (QA), devops (DevOps)
- **Apex**: frontend-dev (Frontend Architect), backend-dev (Core Engine), security-auditor (Security)
- **深圳羽球地图**: data-analyst (Data Pipeline), security-auditor (Security Audit)
