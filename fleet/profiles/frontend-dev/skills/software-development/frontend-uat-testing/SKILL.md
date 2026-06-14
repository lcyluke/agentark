---
name: frontend-uat-testing
description: "三层UAT验收：API审计→数据内容→浏览器渲染。发现前端烂数据、后端缺口、逻辑断裂。"
version: 1.0.0
author: frontend-dev
tags: [testing, uat, frontend, dashboard, debugging, browser]
related_skills: [systematic-debugging, writing-plans]
---

# 前端 UAT 验收测试

## 概述

对多Agent Dashboard等复杂前端页面进行全量验收。三层递进：

1. **API层** — 所有端点200？返回数据结构正确？
2. **数据内容层** — 字段非空？数组有元素？状态值合理？
3. **浏览器渲染层** — HTML元素存在？JS无错误？交互功能可用？

## 触发条件

- 完成Dashboard/指挥中心前端功能开发后
- 用户要求"测试"、"验收"、"UAT"、"检查"
- 发现渲染空白但无明显JS报错

## 三层验收流程

### 第一层：API审计（Python脚本）

```python
from hermes_tools import terminal
import json

base = 'http://localhost:8080'
endpoints = ['/api/status','/api/profiles','/api/tasks', ...]

for ep in endpoints:
    r = terminal(f"curl -s -w '\\n%{{http_code}}' {base}{ep}")
    lines = r['output'].strip().split('\n')
    http_code = lines[-1].strip()
    body = '\n'.join(lines[:-1])
    data = json.loads(body) if body else None
    has_error = isinstance(data, dict) and 'error' in data
    
    status = 'OK' if http_code == '200' and not has_error else 'ISSUE'
    print(f"{'✅' if status=='OK' else '❌'} {http_code} {ep} → {type(data).__name__}")
```

### 第二层：数据内容检查

不仅要HTTP 200，还要检查数据是否有意义：

```python
profiles = fetch('/api/profiles')
if len(profiles) == 0:
    issues.append("❌ Profiles=0 → 舰队/项目Agent全部空白")

tasks = fetch('/api/tasks')
unassigned = sum(1 for t in tasks if not t.get('assignee'))
if unassigned > len(tasks) * 0.5:
    issues.append(f"❌ {unassigned} tasks无assignee")

auto = fetch('/api/autonomous')
if auto.get('status') != 'running':
    issues.append("⚠️ 自治引擎未运行")
```

### 第三层：浏览器渲染验证

⚠️ **关键技巧：`browser_console` + `expression` 比 curl grep 可靠。**  
curl 只能检查模板源码中有无 `<div id="xxx">`，不能检验 JS 是否实际渲染了内容。

```javascript
// 检查元素是否存在且非空
JSON.stringify({
  grid_len: document.getElementById('fleetGrid').innerHTML.length,
  cards: document.querySelectorAll('#fleetGrid .fleet-card').length,
  kpis: document.getElementById('fleetKpis').innerHTML.length
})
```

## 常见陷阱

### 陷阱1：API返回对象而非数组

**症状：** 页面渲染空白，但无 console error。`.filter()` 静默失败。

**根因：** API 返回 `{agents: [...], summary: {}}` 而代码期望 `[...]`。

```javascript
// ❌ 炸了但不出错
const idle = workloads.filter(w => w.load < 0.3).length;

// ✅ 防御性化解
const wl = (data.workloads?.agents) || (Array.isArray(data.workloads) ? data.workloads : []);
const idle = wl.filter(w => (w.load||0) < 0.3).length;
```

**检测方法：** 浏览器控制台执行 `typeof state.data.workloads` → 如果返回 `"object"` 且 `Array.isArray()` 返回 `false`，就是对象。

### 陷阱2：JS错误不出现在 browser_console errors 数组

**症状：** `browser_console` 返回 `js_errors: []`，但页面不渲染。

**根因：** 部分运行时错误（如 `.filter is not a function`）被吞掉或以 `exception` 类型出现。

**检测方法：** 用 `expression` 手动执行可疑函数并检查渲染后状态：
```javascript
// Step 1: Check data shape
JSON.stringify({
  type: typeof state.data.workloads,
  isArray: Array.isArray(state.data.workloads),
  keys: Object.keys(state.data.workloads || {})
})

// Step 2: If it's an object like {agents:[], summary:{}}, the fix is:
// const wl = (d.workloads?.agents) || (Array.isArray(d.workloads) ? d.workloads : []);

// Step 3: Manually trigger the render and check result
renderFleet();
JSON.stringify({
  grid_len: document.getElementById('fleetGrid').innerHTML.length,
  cards: document.querySelectorAll('#fleetGrid .fleet-card').length
})
```

**已知的 API 形状陷阱：**

| API | 预期类型 | 实际类型 | 修复 |
|-----|---------|---------|------|
| `/api/ops/agents/workloads` | `[...]` 数组 | `{agents:[], summary:{}}` 对象 | `workloads.agents \|\| []` |
| `/api/live/projects` | `[...]` 数组 | `[...]` 数组 ✅ | 无需修复 |

### 陷阱4：并行子Agent数据播种

**场景：** UAT 发现多个后端 API 返回空数据（0 profiles, 0 tasks, 0 teams...）。

**错误做法：** 逐个手动 POST——慢且易遗漏。

**正确做法：** 用 `delegate_task` 派 3 个并行子Agent：

```
Worker 1: Profiles + Tasks
  POST /api/profiles ×N + POST /api/tasks ×M + PUT status updates

Worker 2: Knowledge + Autonomous  
  POST /api/knowledge learn ×N + apex autonomous start

Worker 3: Fleet Teams
  写入 ~/.hermes/fleet_teams.json
```

**关键：** 播种时服务必须运行中（REST API 可用）。不要在播种过程中重启服务器。播种完成后用 `execute_code` 一键验证所有端点。

### 陷阱3：模板源码存在 ≠ 渲染成功

**症状：** `curl | grep "kpiRow"` 返回2次匹配，但浏览器中该元素 innerHTML 为空。

**根因：** curl 检查的是模板源码（HTML+JS），浏览器中的 innerHTML 才是 JS 渲染后的结果。

**正确方法：** 永远用 `browser_console` + `expression` 检查渲染后状态。

## 缺陷分类标准

| 级别 | 标记 | 含义 | 示例 |
|------|------|------|------|
| P0 | 🔴 Critical | 页面瘫痪 | `.filter()` 对对象调用 |
| P1 | 🟡 Blocking | 核心功能空白 | Profiles=0 导致所有Agent卡片空 |
| P2 | 🟠 Improvement | UI/UX退化 | 三种card类型混排无分类 |

## 输出格式

```markdown
| 类别 | 数量 | 严重程度 |
|------|------|---------|
| 前端Bug | N | 🔴/🟡/🟠 |
| 后端数据缺口 | N | 🟡 |
| 前端逻辑问题 | N | 🟠 |

### 缺陷明细
| ID | API/元素 | 当前值 | 影响 | 修复方案 |
|----|---------|--------|------|---------|

### 修复优先级
P0: 立即修复 ✗
P1: 安排对应agent ✗
P2: 排期迭代 ✗
P3: 按需 ✗
```

## 记住

```
三层递进：API(200?) → 数据(非空?) → 渲染(可见?)
browser_console + expression > curl grep
typeof + Array.isArray 检查数组
只检查模板源码 = 自欺欺人
缺陷标记：🔴瘫痪 🟡阻塞 🟠退化
```
