<div align="center">
  <img src="https://img.shields.io/badge/版本-0.1.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/许可-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Python-3.10%2B-orange" alt="Python">
</div>

# ⚡ Apex — 多Agent操作系统

> **让一个人拥有一个公司的能力，让一个公司拥有一个宇宙的潜力。**
>
> *One person, infinite capacity.*

Apex 是全世界最先进的多Agent操作系统。它吸收了 CrewAI、LangGraph、CAMEL、MetaGPT、AutoGen、Hermes 的全部优点，同时拥有7大核心创新。

---

## ✨ 为什么用 Apex？

| 问题 | Apex 方案 |
|------|----------|
| 😤 **碎片化** — 需要3-5个框架拼凑 | 一体化平台。`pip install apex` |
| 💸 **太贵** — 10个Agent并行=10倍费用 | **Token Economy** — 智能路由省95%费用 |
| 📚 **学习曲线陡** | 3分钟上手。`apex run "部署我的应用"` |
| 🤖 **Agent永远不会变聪明** | **进化引擎** — 每次执行都在变强 |
| 🏗️ **组队复杂** | **零点击组队** — AI自动设计团队 |
| 🔌 **绑定厂商** | **MCP原生** — 任意Provider随时切换 |

---

## 🚀 快速开始

```bash
# 安装
pip install apex

# 创建项目
apex init 我的项目
cd 我的项目

# 单Agent执行
apex run "写一个登录页面"

# Swarm模式（并行→验证→合成）
apex run "开发一个完整网站" --swarm

# Crew模式（角色协作）
apex crew create "设计一个社交应用" --members pm,frontend,backend

# 一行命令创建AI公司
apex company create 羽球宝AI -i saas
apex company start 羽球宝AI "开发MVP"
```

---

## 🏆 7大核心创新

### 1️⃣ 动态技能进化
Agent从每次执行中学习。100次迭代后相同错误概率降低90%+。

```bash
apex evolution agent frontend  # 查看进化报告
```

### 2️⃣ 零点击组队
只需描述目标，Apex自动设计最优团队。

```bash
apex crew create "开发一个React仪表盘"
# → 自动分配：PM + 前端 + 后端 + 运维
```

### 3️⃣ 自愈工作流
三振出局规则：重试 → 换模型 → 简化任务 → 通知人类。

### 4️⃣ 知识图谱记忆
基于图结构的共享记忆。教会一个Agent = 教会所有Agent。

### 5️⃣ Token预算银行
智能路由按任务价值分配模型。省95%费用。

```bash
apex economy status            # 预算看板
apex economy classify "设计系统架构"  # 查看路由结果
```

### 6️⃣ MCP全家桶
跨语言、跨机器、跨框架。Python ↔ Java ↔ Rust Agent无缝协作。

### 7️⃣ One-Click Company
一行命令创建一家AI公司。

```bash
apex company create 羽球宝AI -i saas
# → 自动创建5个Profile + SOP + Kanban
```

---

## 📋 全部命令

| 命令 | 说明 |
|------|------|
| `apex init <名称>` | 初始化项目 |
| `apex run "<任务>"` | 执行任务（单Agent） |
| `apex run "<任务>" --swarm` | Swarm模式 |
| `apex crew create "<目标>"` | Crew模式 |
| `apex crew create "<目标>" --members a,b,c` | 指定成员Crew |
| `apex team create <名称>` | 创建Agent |
| `apex team list` | 列出所有Agent |
| `apex template list` | 浏览5个模板 |
| `apex template use <名称>` | 从模板创建Agent |
| `apex status` | 系统状态 |
| `apex economy status` | Token经济看板 |
| `apex knowledge query "<问题>"` | 查询知识图谱 |
| `apex evolution agent <名称>` | Agent进化报告 |
| `apex company create <名称>` | 创建AI公司 |
| `apex company start <名称> <目标>` | 启动公司 |
| `apex dashboard` | Web UI (8080端口) |

---

## 🖥️ 内置模板

| 模板 | 角色 | 专长 |
|------|------|------|
| 💻 `frontend` | 前端开发工程师 | React/Vue/小程序/Tailwind |
| ⚙️ `backend` | 后端架构师 | FastAPI/Go/PostgreSQL/K8s |
| 📋 `pm` | 产品经理 | PRD/用户研究/数据决策 |
| ✍️ `content` | 内容运营专家 | 文案/SEO/社媒/多语言 |
| 🔧 `devops` | 运维工程师 | Docker/CI/CD/监控/安全 |

---

## 🗺️ 路线图

- **v0.1** (当前) — 核心功能全齐
- **v0.2** — Web UI v2 / 插件系统 / LangSmith集成
- **v0.3** — 企业版：多租户 / RBAC / 审计日志
- **v1.0** — 生产就绪 / GUI工作流设计器

---

## 从今天开始，一个人就是一个公司。

```bash
pip install apex
apex init my-startup
apex run "hello world"
```
