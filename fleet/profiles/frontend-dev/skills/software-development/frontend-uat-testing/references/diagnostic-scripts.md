# UAT 诊断脚本集合

## 1. API 全量审计脚本

```python
from hermes_tools import terminal
import json

base = 'http://localhost:8080'

def fetch(ep):
    r = terminal(f"curl -s {base}{ep}")
    try:
        return json.loads(r['output'])
    except:
        return {'_raw': r['output'][:200]}

endpoints = [
    '/api/status', '/api/health', '/api/profiles', '/api/tasks',
    '/api/autonomous', '/api/knowledge', '/api/environment',
    '/api/fleet/profiles/list', '/api/fleet/teams/list',
    '/api/ops/agents/workloads', '/api/ops',
    '/api/live/runtime', '/api/live/projects',
    '/api/auth/stats', '/api/auth/audit?days=7&limit=5',
    '/api/command-center',
]

issues = []
for ep in endpoints:
    r = terminal(f"curl -s -w '\\n%{{http_code}}' {base}{ep}")
    lines = r['output'].strip().split('\n')
    http_code = lines[-1].strip()
    body = '\n'.join(lines[:-1])
    data = None
    try:
        data = json.loads(body)
        has_error = isinstance(data, dict) and 'error' in data
    except: pass
    status = 'OK' if http_code == '200' and not has_error else 'ISSUE'
    print(f"{'✅' if status=='OK' else '❌'} {http_code} {ep}")
```

## 2. 数据内容深度检查

```python
# Profiles: 检查 role, model, skills 字段
profiles = fetch('/api/profiles')
for p in profiles:
    if not p.get('role'): issues.append(f"Profile '{p.get('name')}' missing ROLE")
    if not p.get('model'): issues.append(f"Profile '{p.get('name')}' missing MODEL")

# Tasks: 检查 assignee 分布
tasks = fetch('/api/tasks')
unassigned = sum(1 for t in tasks if not t.get('assignee'))
statuses = {}
for t in tasks:
    s = t.get('status','?')
    statuses[s] = statuses.get(s,0)+1

# Workloads: 负载分布
wl = fetch('/api/ops/agents/workloads')
agents = wl.get('agents', [])
idle = sum(1 for a in agents if (a.get('load',0) or a.get('saturation',0)) < 0.1)
busy = sum(1 for a in agents if 0.1 <= (a.get('load',0) or a.get('saturation',0)) < 0.7)
over = sum(1 for a in agents if (a.get('load',0) or a.get('saturation',0)) >= 0.7)

# Live runtime: session详情
rt = fetch('/api/live/runtime')
for s in rt.get('sessions', [])[:3]:
    print(f"  {s.get('source')} | {s.get('model')} | {s.get('runtime_min')}m")
```

## 3. 浏览器渲染状态探测

```javascript
// 批次检查所有视图元素
JSON.stringify({
  // Dashboard
  kpiRow: document.getElementById('kpiRow')?.textContent?.slice(0,80),
  gpuGrid: document.getElementById('gpuGrid')?.children?.length,
  
  // Fleet
  fleetKpis: document.getElementById('fleetKpis')?.innerHTML?.length || 0,
  fleetGrid_cards: document.querySelectorAll('#fleetGrid .fleet-card').length,
  
  // Board
  boardModal_on: document.getElementById('boardModal')?.classList?.contains('on'),
  ceo_select: document.getElementById('bmCeo')?.value,
  humans: document.querySelectorAll('#humanList .board-member').length,
  
  // State
  view: state?.view,
  profiles: state?.data?.profiles?.length,
  connected: state?.connected,
  workloads_type: typeof state?.data?.workloads
})
```

## 4. 数组/对象陷阱检测

```javascript
// 快速检测 workloads 是数组还是对象
JSON.stringify({
  type: typeof state.data.workloads,
  isArray: Array.isArray(state.data.workloads),
  keys: state.data.workloads ? Object.keys(state.data.workloads) : 'null',
  agents_count: state.data.workloads?.agents?.length
})
// 预期: {type:"object", isArray:false, keys:["agents","summary",...], agents_count:0}
// → workloads 是对象，不是数组！全站 .filter() 都会静默失败！
```

## 5. 函数存在性批量检查

```bash
# 检查所有关键JS函数是否在模板中定义
for fn in renderFleet renderDashboard renderApprovals renderAutonomy \
         renderKnowledge renderCost renderSystem renderFlow \
         openAgent openChat sendChat decomposeGoal applyPlan \
         openHire doHire openBoardManager saveBoard \
         approveRequest rejectRequest renderReclamation autoReclaim; do
  count=$(curl -s http://localhost:8080/cc | grep -c "function $fn")
  echo "$count $fn"
done
```

## 6. 手动触发渲染验证

```javascript
// 有时 auto-refresh 之后才渲染，手动触发看是否报错
try {
  renderFleet();
  'SUCCESS - fleetGrid has ' + document.getElementById('fleetGrid').innerHTML.length + ' bytes'
} catch(e) {
  'ERROR: ' + e.message
}
```
