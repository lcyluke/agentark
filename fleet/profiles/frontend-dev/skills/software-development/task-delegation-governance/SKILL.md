---
name: task-delegation-governance
description: "任务委派治理体系：指派规则、追踪监控、反馈协作、授权申请"
version: 1.1.0
author: frontend-dev
---

# 任务委派治理体系 (Task Delegation Governance)

## 一、指派规则 (Assignment Rules)

### R1: 项目归属 (Project Affiliation)
一个 Agent 只处理其所属项目的任务。

```
匹配逻辑:
  task.project ∈ agent.teams[].project
```

**当前项目-Agent映射：**
| 项目 | 前端 | 后端 | QA | DevOps | 安全 | 数据 |
|------|------|------|-----|--------|------|------|
| Apex | frontend-dev | backend-dev | — | — | security-auditor | — |
| 羽球宝AI | frontend-dev | backend-dev | qa-agent | devops | — | — |
| 深圳羽球地图 | — | — | — | — | security-auditor | data-analyst |

**越界规则：**
- 若目标项目无可用Agent，自动向 PM 申请跨项目借调
- 借调需附理由 → 等待 PM 签核

### R2: 技能匹配 (Skill Matching)
Agent 技能集必须覆盖任务所需技术栈。

```
匹配逻辑:
  task.required_skills ⊆ agent.skills  （至少80%覆盖）
```

| Agent | 核心技能 |
|-------|---------|
| backend-dev | Python, FastAPI, PostgreSQL, Redis, Docker, API Design |
| devops | Docker, K8s, CI/CD, GitHub Actions, deployment |
| qa-agent | Playwright, Vitest, Jest, Postman |
| data-analyst | SQL, Pandas, NumPy |
| security-auditor | OWASP, SAST, DAST, SBOM |

### R3: 负载均衡 (Load Balance)
单Agent并发任务上限 = 3。超限自动找同技能同项目替代。

```
匹配逻辑:
  if agent.active_tasks >= 3:
    fallback = find_alternative(project, required_skills)
    if not fallback: escalate_to_PM("无可用Agent")
```

**当前负载快照（实时从 /api/tasks 计算）：**
```
Agent           | in_progress | ready | 总负载 | 可接单
----------------|-------------|-------|--------|--------
frontend-dev   | 1           | 0     | 1      | ✅
backend-dev    | 0           | 0     | 0      | ✅
qa-agent       | 0           | 0     | 0      | ✅
devops         | 0           | 1     | 1      | ✅
```

### R4: 上下文传递 (Context Passing)
委派时必须携带完整上下文，接收Agent无需猜测。

**上下文包 (Context Package)：**
```
1. 项目概述 (Project Context)
   - 项目名、目标、技术栈
   - 相关文件路径、API端点
2. 前置工作 (Preceding Work)
   - 谁做了什么、产出是什么
   - 接口契约（API 签名、数据格式）
3. 当前任务 (Task Definition)
   - 具体要做什么、验收标准
   - 输入/输出定义
4. 约束条件 (Constraints)
   - 预算限制、时间限制
   - 护栏规则
5. 相关Agent (Related Agents)
   - 谁在前、谁在后
   - 如何协作
```

### R5: 顺序依赖 (Sequential Dependency)
前端完成 → 后端（提供API契约）→ QA → DevOps。不可跳跃。

```
流水线:
  frontend-dev ──(API契约)──→ backend-dev ──(API实现)──→ qa-agent ──(测试报告)──→ devops ──(部署)
```

### R6: 授权闸门 (Authorization Gate)
以下情况必须向 PM/创始人申请授权：
| 触发条件 | 类型 | 审批人 |
|---------|------|--------|
| 跨项目借调Agent | 资源 | PM |
| 任务超过预算阈值 | 成本 | PM |
| 修改生产配置/部署 | 危险操作 | 创始人 |
| 对外通讯（邮件/API外呼） | 安全 | 创始人 |

---

## 二、任务状态变迁 (Task State Machine)

```
        创建
         ↓
      [ready] ──指派──→ [in_progress] ──完成──→ [done]
         ↓                  ↓                      ↑
      [blocked] ←──阻塞───┘                      │
         ↓                                       │
      [gate] ──审批通过──→ [in_progress] ────────┘
```

**状态定义：**
| 状态 | 含义 | 触发条件 |
|------|------|---------|
| ready | 待指派 | 任务创建、依赖满足 |
| in_progress | 执行中 | Agent开始处理 |
| blocked | 阻塞 | 缺依赖、缺信息、等审批 |
| gate | 待审批 | 命中授权闸门 |
| done | 已完成 | 验收通过 |

---

## 三、追踪监控 (Tracking & Monitoring)

### 检查点 (Checkpoints)
每30秒轮询 `/api/tasks`，追踪：

1. **进度异常** — in_progress 超时（默认30分钟无更新 → 升级报警）
2. **阻塞检测** — blocked 任务超3个 → 通知 PM
3. **闲置检测** — ready 任务有可用Agent但未指派 → 自动建议委派
4. **质量回归** — done 任务被重新打开 → 通知 QA

### 监控看板 (Monitor Dashboard)
实时在 `/cc` 系统状态页显示：

```
项目       | ready | in_progress | blocked | done | 健康度
-----------|-------|-------------|---------|------|--------
羽球宝AI   | 4     | 2           | 0       | 1    | 🟢 86%
Apex       | 6     | 0           | 1       | 35   | 🟡 83%
```


## 四、反馈协作 (Feedback & Collaboration)

### 4.1 结构化汇报 (Structured Reports)

**任务启动汇报** → PM：
```
📋 [项目] 新任务启动
Agent: backend-dev
任务: [羽球宝AI] 球场预约API接口
预计: 15min
上下文: 前端已定义 API 契约 (GET/POST /api/courts)
状态: in_progress
```

**任务完成汇报** → PM + 创始人：
```
✅ [项目] 任务完成
Agent: backend-dev
任务: [羽球宝AI] 球场预约API接口
耗时: 12min | Token: 8,200 | 成本: $0.02
产物: /api/courts CRUD (4 endpoints)
下一站: → qa-agent (集成测试)
```

**阻塞汇报** → PM：
```
🚫 [项目] 任务阻塞
Agent: frontend-dev
任务: [Apex] Dashboard性能优化
原因: 需要 backend-dev 先完成 /api/analytics 端点
请求: 请调度 backend-dev 优先处理
```

### 4.2 授权申请 (Authorization Request)

**格式：**
```
🔐 授权申请
类型: [资源借调/预算/部署/对外通讯]
项目: 羽球宝AI
Agent: frontend-dev
请求: 跨项目借用 data-analyst（深圳羽球地图→羽球宝AI）
原因: 羽球宝AI 需要用户行为分析，本队无数据Agent
影响: 深圳羽球地图项目延后1个任务
请审批: [批准] [驳回]
```


## 五、执行流程 (Execution Workflow)

### 标准流水线 (Standard Pipeline)

```
1. 前端完成 → 产出 API 契约 (OpenAPI spec)
2. 委派后端 → 携带契约 + 前端上下文
3. 后端完成 → 产出 API 实现 + 自测报告
4. 委派 QA → 携带 API 文档 + 测试用例清单
5. QA 完成 → 产出测试报告 + bug列表
6. 委派 DevOps → 携带部署配置 + 测试通过证明
7. DevOps 完成 → 部署上线 + 监控就绪
```

### 委派命令模板

使用 `delegate_task`：
```
goal: "实现[羽球宝AI]球场预约API接口"
context: "
项目: 羽球宝AI (AI羽毛球助手)
前端已完成: 预约页面组件 (CourtBooking.tsx)
API契约:
  GET /api/courts → {courts: [{id, name, address, price}]}
  POST /api/bookings → {court_id, user_id, time_slot} → {booking_id, status}
技术栈: Python/FastAPI/PostgreSQL
约束: 响应时间<200ms, 需参数校验
上一站: frontend-dev (我)
下一站: qa-agent (集成测试)
"
```

### ⚠️ 子Agent工作验证 (Mandatory Post-Delegation Check)

委派后必须验证子Agent的产出，不可信任其自报的结果。常见子Agent引入的问题：

| 问题 | 检测方法 | 影响 |
|------|---------|------|
| 重复API路由 | `grep -c "@app.route('/api/xxx')" ` >1 | Flask启动失败 |
| 未闭合模板字符串 | 服务器HTML中反引号计数奇偶校验 | 整页JS静默失效 |
| 未导入模块 | 查看Flask启动日志中ImportError | 新路由返回500 |
| 数据格式变更 | `curl` 检查API返回结构 | 前端数据阵列断层 |

验证命令模板：
```bash
# 1. 重启服务器
lsof -ti:8080 | xargs kill -9; sleep 2; python -m apex dashboard --port 8080 &

# 2. 检查启动日志无错误
sleep 4; curl -s http://localhost:8080/api/health

# 3. 检查新增路由正常工作
curl -s http://localhost:8080/api/<new-endpoint>

# 4. 检查前端JS无语法错误（反引号奇偶）
curl -s http://localhost:8080/cc | python3 -c "import sys; t=sys.stdin.read(); b=t.count('`'); print('JS OK' if b%2==0 else 'JS BROKEN')"
```

**子Agent成果不可直接合并。必须重启服务并验证后才报告完成。**

---

## 六、PM/创始人视角 (Management View)

在 `/cc` 项目作战室中选择项目即可看到完整的流水线可视化（状态分布条 + 看板列 + Agent泳道）。

详细实现参见 `references/pipeline-flow-view.md`。

---

## 七、apex chat — 统一Agent启动命令

### 命令格式

```
apex chat <agent_name>              # 启动Agent对话
apex chat --list                    # 列出所有可用Agent
apex chat <agent_name> -q "..."     # 带初始消息
apex chat <agent_name> -c "..."     # 注入额外上下文
```

### 工作原理

1. **Agent发现** — 三源聚合：Apex Profiles + Hermes Profiles + 预置模板(ROLE_SOULS)
2. **自动同步** — 未同步到Hermes的Agent自动调用 `sync_profile_to_hermes()` 创建 SOUL.md + config.yaml
3. **上下文注入** — 收集项目全局信息注入到 `~/.hermes/profiles/<name>/home/AGENTS.md`：
   - `./AGENTS.md` — 项目总览
   - `./.apex/project_context.md` — Apex项目上下文
   - `kanban.db` — 当前任务摘要
   - `fleet_teams.json` — 团队同伴信息
4. **启动** — `hermes -p <agent_name>` 启动交互式对话

### Agent就绪检查

```bash
apex chat --list  # 显示所有Agent及其同步状态
```

### 上下文共享实现

所有Agent通过同一个项目根目录的 `AGENTS.md` + `.apex/project_context.md` 获得一致的项目认知。Agent启动时自动读取这些文件，确保同一项目内的所有Agent对项目状态、团队结构、当前任务有统一理解。

### 配置文件要求

Agent的Hermes profile目录必须有：
- `SOUL.md` — 角色定义
- `config.yaml` — 模型配置，**必须包含 `provider` 字段**
- `.env` 可选 — API key从全局继承，无需每个Agent单独配置

**⚠️ 缺少 `provider` 字段**会导致Hermes回退到默认provider（如bedrock），报`ValidationException: invalid model identifier`。正确的config.yaml最小模板：

```yaml
model:
  default: deepseek-v4-pro
  provider: deepseek    # ← 此行不可省略

agent:
  max_turns: 100
```

### HERMES_HOME 路径陷阱

HERMES_HOME 可能指向 profile 子目录而非 `~/.hermes` 根目录。sync时profile会被创建在嵌套路径 `~/.hermes/profiles/<current_profile>/profiles/<new_profile>/` 而不是 `~/.hermes/profiles/<new_profile>/`。启动前必须检查 `echo $HERMES_HOME` 并确保配置文件写在了正确位置。

### 子Agent防火墙限制

当前系统 `max_spawn_depth=1`，子Agent无法再委派。且 `delegate_task` 是同步执行的——父会话中断时子任务被取消。**长时间工作（如服务端代码修改+重启验证）不能被委派为一个子任务，需拆分为多步或在父会话中直接执行。**

---

## 八、委派后验证 (Post-Delegation Verification)

委托子Agent完成工作后，**必须**执行交叉验证——尤其是后端Agent修改了共享文件（如 `web.py` 同时包含Python路由和HTML模板的JS内联代码）时。

### 验证清单

1. **服务可用性** — `curl -w '%{http_code}' /api/health` 返回200
2. **页面渲染** — `/cc` 返回完整HTML（>50KB）
3. **JS语法完整** — 页面中的反引号、大括号成对闭合
4. **函数可用** — 浏览器控制台 `typeof renderDashboard === 'function'`
5. **状态存在** — `state.connected === true`
6. **导航可用** — 点击至少3个视图切换无报错

### 常见Bug信号

| 症状 | 根因 |
|------|------|
| `state is not defined` | JS代码块中有未闭合的模板字面量（反引号奇数），整个script块解析失败 |
| 页面显示但无交互 | 子Agent添加了新代码但引入了语法错误 |
| API正常但页面空白 | Flask render_template正常但内联JS执行失败 |

### 反引号奇偶检查

```bash
curl -s http://localhost:8080/cc | python3 -c "
import sys; t=sys.stdin.read()
b=t.count(chr(96))
print('EVEN' if b%2==0 else 'ODD ⚠️ JSBROKEN')
# If ODD: find the last unclosed template literal, add closing backtick + semicolon
"
```

### 大括号平衡检查

```bash
curl -s http://localhost:8080/cc | python3 -c "
import sys; t=sys.stdin.read()
i=t.find('<script>'); j=t.rfind('</script>')
js=t[i+8:j]
o=js.count('{'); c=js.count('}')
print(f'braces: open={o} close={c} {\"OK\" if o==c else \"MISMATCH\"}')
"
```

### 子Agent产出验证命令序列

```bash
# 1. 检查无重复路由
grep -n "@app\.route.*<endpoint>" apex/interface/web.py

# 2. 重启并验证启动无错误
lsof -ti:8080 | xargs kill -9 2>/dev/null; sleep 2
cd /Users/Mac/Desktop/2026AIAPP/Apex && .venv/bin/python -m apex dashboard --port 8080 &
sleep 4; curl -s http://localhost:8080/api/health

# 3. 验证新API端点
curl -s http://localhost:8080/api/<new-endpoint>

# 4. 前端JS语法检查
curl -s http://localhost:8080/cc | python3 -c "
import sys; t=sys.stdin.read(); b=t.count(chr(96))
print('JS OK' if b%2==0 else 'JS BROKEN — odd backtick count='+str(b))"
```
