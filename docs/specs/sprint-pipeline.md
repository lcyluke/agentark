# Apex Sprint Pipeline — MVP 闭环流水线

> **版本:** v2.0  
> **状态:** 📝 Design  
> **作者:** 小卢 (Hermes Origin Agent)  
> **日期:** 2026-06-04

---

## 一、产品概述

**Sprint Pipeline** 是 Apex 内建的 MVP 端到端自动化流水线。从需求到上线到迭代，一条命令启动，两个人工审批点，其余全部由 AI Agent 自动推进。

**核心理念:** 一个人 + AI 舰队 = 完整的软件开发团队。

---

## 二、流水线架构

```
📝 PLAN ──👤 设计审批 ──→ ⚙️ BUILD ──🤖──→ 🧪 VERIFY ──👤 发版审批 ──→ 🚀 SHIP ──🤖──→ 🔄 LEARN
```

### Phase 详解

| Phase | Agent(s) | 输入 | 产出 | Gate |
|:------|:---------|:-----|:-----|:----:|
| **📝 PLAN** | product-manager + architect | 一句话需求 | PRD + API Contract + Task List | 👤 **设计审批** |
| **⚙️ BUILD** | solo: fullstack-dev ∥ swarm: frontend + backend | API Contract + Task List | 代码提交 | 🤖 契约测试通过 |
| **🧪 VERIFY** | qa-engineer + test-agent | 代码仓库 | 测试报告 | 📊 覆盖率>80% + 0严重bug |
| **🚀 SHIP** | devops / ops-engineer | 通过测试的代码 | 部署预览 | 👤 **发版审批** |
| **🔄 LEARN** | session-scout + apex-pm | 用户反馈 | 下一轮 Sprint Plan | 🤖 自动循环 |

### 两个人工 Gate

| Gate | 位置 | 老卢决策 | 审批内容 |
|:-----|:-----|:---------|:---------|
| **设计审批** | PLAN → BUILD | 方案对不对？ | PRD + API 设计 + 任务拆解 |
| **发版审批** | VERIFY → SHIP | 能不能发？ | 测试报告 + 变更摘要 |

其余 3 个 Gate 全部由 AI 自动判断推进。

---

## 三、BUILD Phase 双模式

```bash
# 简单 MVP — 一个全栈 Agent
apex sprint create "用户登录" --mode solo

# 复杂 MVP — 前后端分离，API 契约为桥梁
apex sprint create "打卡地图" --mode swarm
```

| 模式 | Agent | 适用 | API 契约 | 并行 |
|:-----|:------|:-----|:--------|:----:|
| **solo** | fullstack-dev ×1 | 简单 CRUD、单页面 | ❌ | — |
| **swarm** | frontend-dev + backend-dev ×2 | 多页面、复杂 API | ✅ OpenAPI 3.0 | ✅ 并行 |

### Swarm 模式下的 API 契约机制

```
architect 产出 api_contract.yaml
        │
   ┌────┴────┐
   │         │
frontend-dev  backend-dev
 读契约      读契约
 调 mock    实现 API
   │         │
   └────┬────┘
   契约测试: 请求/响应 完全一致 ✅
```

---

## 四、CLI 命令

```bash
# 启动 Sprint
apex sprint create "打卡地图 MVP" --mode swarm
# → 创建 Sprint #1, 进入 PLAN phase
# → 自动调用 product-manager + architect 产出方案

# 查看进度
apex sprint status
# → 当前 Phase, Agent 状态, 工时, 下一步 Gate

# 审批 Gate
apex sprint approve          # 审批当前人工 Gate
apex sprint reject --reason  # 驳回, 回到当前 Phase 重做

# 查看历史
apex sprint list             # 所有 Sprint
apex sprint report <id>      # 完整报告
```

---

## 五、Dashboard 集成

在 Dashboard「项目作战室」视图中新增 Sprint 进度卡片：

```
┌──────────────────────────────────────────────┐
│  🏃 Sprint #3: 打卡地图 MVP                   │
│  ████████████░░░░░░░░  60% (3/5 phases)      │
│                                              │
│  ✅ PLAN    2.3h  老卢已审批                   │
│  ✅ BUILD   4.1h  swarm: frontend + backend   │
│  🔄 VERIFY  —     qa-engineer 测试中...        │
│  ⏳ SHIP    —     等待发版审批                  │
│  ⏳ LEARN   —     未开始                        │
│                                              │
│  📊 迭代 V3  |  累计: 10.5h  |  速度: 2.1h/p  │
│  🚦 下一 Gate: 👤 发版审批 (等待老卢)           │
└──────────────────────────────────────────────┘
```

---

## 六、数据模型

```python
class Sprint:
    id: str               # "sprint_3"
    goal: str             # "打卡地图 MVP"
    mode: str             # "solo" | "swarm"
    current_phase: str    # "plan"|"build"|"verify"|"ship"|"learn"
    phases: list[Phase]   # 已完成 phase 记录
    created_at: datetime
    iteration: int        # 第几轮迭代

class Phase:
    name: str
    status: str           # "pending"|"active"|"done"|"rejected"
    agent: str            # 负责的 Agent
    started_at: datetime
    completed_at: datetime
    hours_spent: float
    output: str           # 产出摘要
    gate: str             # "auto"|"manual"
    gate_status: str      # "pending"|"approved"|"rejected"
```

存储: `~/.apex/sprints.db` (SQLite)

---

## 七、自动决策引擎

每个 Auto Gate 的 exit_criteria：

| Gate | 条件 | 检查方法 |
|:-----|:-----|:---------|
| BUILD → VERIFY | 契约测试通过 | `diff(api_contract.yaml, actual_responses) == 0` |
| VERIFY → SHIP | 覆盖率>80% + 无严重bug | `pytest --cov` + bug count |
| SHIP → LEARN | 部署成功 | HTTP 200 + 预览 URL 可达 |

---

## 八、实现范围

### Phase 1: 核心 (本次)
- `apex/orchestration/sprint_pipeline.py` — Sprint 状态机
- CLI: `apex sprint create/status/approve`
- Dashboard: Sprint 进度卡片
- API Contract 生成器

### Phase 2: 增强 (后续)
- WeChat 审批通知
- Sprint 速度统计分析
- 多项目并行 Sprint
