# 项目作战室 V2 — 5层布局完整参考

## 设计目标

将原来"KPI+Kanban+负载+报告+Pipeline 全挤在一起"的单一视图，重构为自上而下 5 层结构。

参考源: Linear (Hero + Tabs), Plane (左栏项目列表+主视图切换), Taiga (Scrum看板+泳道)

## 完整 HTML 结构

```html
<!-- VIEW 2: 项目作战室 V2 — 5层布局 -->
<section class="view" id="v-project">
  <!-- L1: 项目选择栏 -->
  <div class="card" id="pjTopBar">
    <select id="pjSwitch" onchange="loadProjectView()">...</select>
    <input id="pjSearch" placeholder="搜索模块/Agent..." oninput="filterProjectView()">
    <button onclick="openProjectDrawer()">编辑</button>
    <button onclick="loadStandup()">站会报告</button>
    <button id="pjLiveBtn" onclick="toggleAutoRefresh()"><span id="pjLiveDot"></span>Live</button>
  </div>

  <!-- L2: Hero 仪表盘 (5-KPI 条) -->
  <div class="grid" style="grid-template-columns:2fr 1.5fr 1fr 1fr 0.8fr;gap:10px" id="pjHeroKpis"></div>

  <!-- L3: 三列瀑布流 -->
  <div class="pj-tricol" id="pjTriCol">
    <!-- 列1: 模块树 (30%) -->
    <div class="card" id="pjModCol">
      <div class="sec-h" style="position:sticky;top:0">模块架构</div>
      <div id="pjModTree"></div>
    </div>
    <!-- 列2: Agent编队 (30%) -->
    <div class="card" id="pjAgentCol">
      <div class="sec-h" style="position:sticky;top:0">Agent 编队 <span id="pjAgentCount"></span></div>
      <div id="pjAgentList"></div>
    </div>
    <!-- 列3: Pipeline (40%) -->
    <div class="card" id="pjPipeCol">
      <div class="sec-h" style="position:sticky;top:0">Pipeline <span id="pjPipeCount"></span></div>
      <div id="pjPipeStages"></div>
    </div>
  </div>

  <!-- L4: Sprint 时间线 (可折叠) -->
  <div class="card" id="pjSprintCard" style="display:none">
    <div class="sec-h" onclick="this.parentElement.querySelector('#pjSprintBody').classList.toggle('hidden')">Sprint Pipeline</div>
    <div id="pjSprintBody"></div>
  </div>

  <!-- L5: 活动提要 -->
  <div class="grid" style="grid-template-columns:repeat(3,1fr);gap:10px">
    <div class="card">最近提交 <div id="pjCommits"></div></div>
    <div class="card">站会摘要 <div id="pjStandupMini"></div></div>
    <div class="card">AI 建议 <div id="pjSuggestions"></div></div>
  </div>
</section>
```

**注意**: 三列的 `sec-h` 必须 `position:sticky;top:0;background:var(--bg);z-index:1` 以保证列头在滚动时固定。

## 关键 CSS 类

```css
/* 三列瀑布流 */
.pj-tricol{display:grid;grid-template-columns:1.8fr 2fr 3fr;gap:10px;align-items:start}

/* 模块树节点 — 左边框 + hover色变 */
.pj-mod-item{padding:8px 10px;border-left:3px solid var(--violet);margin-bottom:4px;
  background:var(--bg2);border-radius:0 6px 6px 0;cursor:pointer}
.pj-mod-item:hover{border-left-color:var(--teal);background:var(--bg3)}

/* 模块进度条 */
.pj-mod-item .mod-bar{height:3px;background:var(--line);border-radius:2px;margin-top:4px}
.pj-mod-item .mod-bar i{display:block;height:100%;background:var(--violet)}

/* 子功能项 — 缩进 + 状态圆点 */
.pj-sf-item{padding:4px 0 4px 22px;font-size:11px;cursor:pointer}
.pj-sf-dot{width:5px;height:5px;border-radius:50%;background:var(--tx3)}
.pj-sf-dot.done{background:var(--green)}

/* Agent 行 */
.pj-agent-row{display:flex;align-items:center;gap:8px;padding:6px 8px;cursor:pointer}
.pj-agent-row:hover{background:var(--bg2)}
.pj-agent-avatar{width:28px;height:28px;border-radius:50%;display:grid;place-items:center;
  font-size:11px;font-weight:700;flex-shrink:0}
.pj-agent-load{height:3px;background:var(--line);border-radius:2px}
.pj-agent-load i{display:block;height:100%}

/* Pipeline 阶段 */
.pj-pipe-stage{margin-bottom:8px}
.pj-pipe-stage-h{font-size:11px;font-weight:600;color:var(--tx2);text-transform:uppercase}
.pj-pipe-stage-h .count{font-size:10px;background:var(--bg3);padding:1px 6px;border-radius:8px}

/* Pipeline 任务卡片 */
.pj-pipe-task{padding:6px 8px;margin-bottom:3px;background:var(--bg2);
  border-left:2px solid var(--line);cursor:pointer}
.pj-pipe-task:hover{border-left-color:var(--teal)}
.pj-pipe-task .prio{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.pj-pipe-task .prio.high{background:var(--red)}
.pj-pipe-task .prio.med{background:var(--amber)}
.pj-pipe-task .task-title{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

/* 空状态 */
.pj-empty-state{text-align:center;padding:32px 16px;color:var(--tx3);font-size:12px}
.pj-empty-state i{font-size:32px;display:block;margin-bottom:8px;opacity:.3}

/* Live 按钮脉冲动画 */
@keyframes pulse-dot{0%,100%{opacity:1}50%{opacity:.3}}

/* 响应式回退 */
@media(max-width:920px){.pj-tricol{grid-template-columns:1fr}}
```

## KPI Hero 行渲染

```javascript
$('#pjHeroKpis').innerHTML =
  kpiGoal + kpiProgress + kpiAgents + kpiCost + kpiRisk;
```

5 张 KPI 卡片：目标摘要、进度条(%)、Agent 编队(在线/忙碌)、今日成本($)、风险(绿/黄)。

每张用 `.kpi` 容器 + `.lbl`/`.num`/`.sub` 三层。进度 KPI 内嵌 `.bar > i` 进度条。

## 渲染入口函数

```javascript
function renderProject() {
  const pj = state.liveProject;
  if (!pj) { /* 三列显示 empty state */ return; }

  // L2: KPI Hero row
  $('#pjHeroKpis').innerHTML = buildHeroKpis(pj);

  // L3: Module tree
  renderModuleTree(pj.modules);

  // L3: Agent roster
  renderAgentRoster(pj.agents);

  // L3: Pipeline (async fetch + fallback)
  fetchAndRenderPipeline();

  // L4: Sprint (conditional)
  if (state.data.sprints?.length) renderSprintTimeline();

  // L5: Activity
  renderActivityFeed();
}
```

## 关键 JS 模式

### Pipeline 异步加载 + 缓存

```javascript
if (state.selectedProject && !state._pipeFetched) {
  state._pipeFetched = true;
  fetchJSON('/api/pipeline/' + encodeURIComponent(state.selectedProject)).then(pipe => {
    state._pipeData = pipe;
    renderPipelineColumn(pipe);
  });
}
// 项目切换时重置: state._pipeFetched = false (在 loadProjectView 中)
```

### 模块树点击 → Drawer

```javascript
// 模块节点: onclick="openModuleDrawer(mi)"
// 子功能: onclick="event.stopPropagation();openSubFunctionDrawer(mi, sfName)"
```

`event.stopPropagation()` 防止触发父级模块的 Drawer。

### 搜索过滤（零网络请求）

```javascript
function filterProjectView() {
  const q = ($('#pjSearch')?.value || '').toLowerCase();
  if (!q) { $$('.pj-mod-item,.pj-agent-row,.pj-pipe-task').forEach(el => el.style.display=''); return; }
  $$('.pj-mod-item,.pj-agent-row,.pj-pipe-task').forEach(el => {
    el.style.display = el.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}
```

纯 CSS display 切换，不触发 API 请求。

## 数据流

```
loadProjectView()
  ├── GET /api/projects/approved     → state.liveProjects (下拉框填充)
  ├── GET /api/projects/<name>       → state.liveProject   (模块/Agent/Goal)
  ├── GET /api/tasks                 → state.data.tasks    (任务进度计算)
  ├── GET /api/ops/agents/workloads  → state.data.workloads
  ├── GET /api/sprint/list           → state.data.sprints  (L4 时间线)
  └── renderProject()
        ├── renderPipelineColumn()   ← GET /api/pipeline/<project> (异步)
        └── renderActivityFeed()
```

## Agent 分类标签系统

当 API 返回的 Agent 数据缺少 role 字段时，基于命名约定自动分类。

### 完整分类表 (15 类)

| key | pattern | icon | label | color | tier |
|-----|---------|------|-------|-------|------|
| origin | `^(origin\|default)$` | ⚓ | 始祖 | #a78bfa | 0 (总司令) |
| pm | `-(pm)$\|^pm-` | 📋 | PM | #60a5fa | 1 (管理) |
| audit | `audit\|guardian\|approval` | 🔍 | 审批审计 | #f59e0b | 1 (闸门) |
| cron | `cron\|watchdog\|monitor\|巡检\|定时` | ⏰ | 定时巡检 | #8b5cf6 | 2 (自动) |
| architect | `architect` | 🏛️ | 架构 | #06b6d4 | 2 (设计) |
| ai | `ai-\|algorithm\|ml-\|training` | 🧠 | AI/ML | #ec4899 | 2 (算法) |
| vision | `vision` | 👁️ | 视觉 | #14b8a6 | 2 (识别) |
| security | `security\|sec-` | 🔒 | 安全 | #ef4444 | 2 (合规) |
| ops | `ops\|deploy\|devops\|bridge` | 🚀 | 运维 | #0ea5e9 | 2 (部署) |
| frontend | `frontend\|ui-\|ux-` | 🎨 | 前端 | #f472b6 | 3 (开发) |
| backend | `backend\|api-\|server` | ⚙️ | 后端 | #34d399 | 3 (开发) |
| content | `content\|copywriter\|marketing\|推广` | ✍️ | 内容 | #fb923c | 3 (创作) |
| funding | `fundraising\|融资\|pitch` | 💰 | 融资 | #facc15 | 3 (路演) |
| data | `data\|analyst\|report\|报表` | 📊 | 数据 | #6366f1 | 3 (分析) |
| general | `.*` | 🤖 | 通用 | #9ca3af | 4 (兜底) |

**Tier 含义**: 0=总司令, 1=管理层(PM/审批), 2=专业岗(巡检/AI/架构/安全/运维), 3=执行岗(前后端/内容/融资/数据), 4=未分类

### classifyAgent(name)

```javascript
function classifyAgent(name) {
  if (!name) return AGENT_CATEGORIES.find(c => c.key === 'general');
  const lower = name.toLowerCase();
  for (const cat of AGENT_CATEGORIES) {
    if (cat.pattern.test(lower)) return cat;
  }
  return AGENT_CATEGORIES.find(c => c.key === 'general');
}
```

**注意**：`general` 必须在数组最后（`/.*/` 匹配一切），分类按数组顺序优先匹配。

### categorizeAgents(agents)

```javascript
function categorizeAgents(agents) {
  const cats = {};
  AGENT_CATEGORIES.forEach(c => { cats[c.key] = { ...c, count: 0, names: [] }; });
  agents.forEach(a => {
    const name = a.agent_id || a.name || '';
    const cls = classifyAgent(name);
    cats[cls.key].count++;
    cats[cls.key].names.push(name);
  });
  return cats;
}
```

返回 `{ key: { count, names[], icon, label, color, bg, subtitle, tier } }` — 用于渲染顶部分类汇总条。

### Agent 汇总栏 HTML

```html
<div class="pj-agent-summary">
  <span class="pj-agent-badge origin">⚓ 始祖 1</span>
  <span class="pj-agent-badge pm">📋 PM 2</span>
  ...
</div>
```

### Agent 行增强渲染

```javascript
const cls = classifyAgent(agentId);
return `<div class="pj-agent-row" onclick="openAgentDetail('${agentId}')" style="border-left:3px solid ${cls.color}">
  <div class="pj-agent-avatar" style="background:var(--${loadColor}-d);color:${loadColor}">${initial}</div>
  <div class="pj-agent-info">
    <div class="pj-agent-name">${agentId} <span class="pj-agent-tag" style="background:${cls.bg};color:${cls.color}">${cls.icon} ${cls.label}</span></div>
    <div class="pj-agent-role">${a.role || cls.subtitle || '—'}</div>
    <div class="pj-agent-load"><i style="width:${loadPct}%;background:${loadColor}"></i></div>
  </div>
</div>`;
```

### 新增 CSS

```css
.pj-agent-summary{display:flex;flex-wrap:wrap;gap:4px;padding:4px 0 10px 0;
  border-bottom:1px solid var(--line2);margin-bottom:8px}
.pj-agent-badge{font-size:10px;padding:2px 7px;border-radius:10px;font-weight:500;
  white-space:nowrap;cursor:default}
.pj-agent-tag{display:inline-block;vertical-align:middle}
```

---

## Agent 组织层级树 (Org Hierarchy)

在 Agent 分类汇总条和 Agent 列表之间插入一个紧凑的组织层级树，展示"谁管谁"的关系。

### buildAgentOrgTree(agents)

```javascript
const PROJECT_PM_MAP = {
  '羽球宝AI': 'badminton-pm', '羽球宝AI搭子': 'badminton-pm',
  'Apex': 'apex-pm', 'Apex Dashboard': 'apex-pm',
  'FinOps AI': 'finops-pm',
  '深圳羽球地图': 'shenzhen-pm'
};

function buildAgentOrgTree(agents) {
  if (!agents || agents.length < 2) return '';
  const hasOrigin = agents.some(a => {
    const n = (a.agent_id || a.name || '').toLowerCase();
    return n === 'origin' || n === 'default';
  });
  const pmAgents = agents.filter(a => classifyAgent(a.agent_id || a.name || '').key === 'pm');
  const auditAgents = agents.filter(a => classifyAgent(a.agent_id || a.name || '').key === 'audit');
  const cronAgents = agents.filter(a => classifyAgent(a.agent_id || a.name || '').key === 'cron');

  let tree = '';
  if (hasOrigin) {
    tree += `<div class="pj-org-node root"><span class="pj-org-dot" style="background:#a78bfa"></span>⚓ Origin → `;
    tree += `<span style="color:var(--tx2);font-size:10px">督管 PM: ${pmAgents.map(a=>a.agent_id||a.name||'?').join(', ') || '—'}</span></div>`;
  }
  if (auditAgents.length > 0) {
    tree += `<div class="pj-org-node audit"><span class="pj-org-dot" style="background:#f59e0b"></span>🔍 审批审计 → <span style="color:var(--tx2);font-size:10px">监控所有 Agent · 人在环闸门</span></div>`;
  }
  if (cronAgents.length > 0) {
    tree += `<div class="pj-org-node cron"><span class="pj-org-dot" style="background:#8b5cf6"></span>⏰ 定时巡检 → <span style="color:var(--tx2);font-size:10px">22 个 Cron 任务 · 自主运行</span></div>`;
  }
  const teamCount = agents.length - pmAgents.length - auditAgents.length - cronAgents.length - (hasOrigin?1:0);
  if (teamCount > 0) {
    tree += `<div class="pj-org-node team"><span class="pj-org-dot" style="background:#60a5fa"></span>👥 执行团队 → <span style="color:var(--tx2);font-size:10px">${teamCount} 个 Agent · 按模块分工</span></div>`;
  }
  return tree || '';
}
```

### getReportingLine(agentName, projectName)

每个 Agent 行底部显示汇报关系：

```javascript
function getReportingLine(agentName, projectName) {
  if (!agentName || !projectName) return '';
  const lower = agentName.toLowerCase();
  if (lower === 'origin' || lower === 'default') return '';       // Origin 无上级
  const cat = classifyAgent(agentName);
  if (cat.key === 'pm') return '↳ ⚓ Origin';                      // PM → Origin
  if (cat.key === 'audit') return '↳ 董事会';                       // 审批 → 董事会
  if (cat.key === 'cron') return '⏰ 自主定时';                     // Cron 独立运行
  const pmName = PROJECT_PM_MAP[projectName];
  if (pmName && lower !== pmName.toLowerCase()) return '↳ ' + pmName;  // → PM
  return '';
}
```

### Org 树 CSS

```css
.pj-org-tree{padding:6px 0 8px 0;border-bottom:1px solid var(--line2);margin-bottom:8px}
.pj-org-node{display:flex;align-items:center;gap:6px;padding:3px 0;font-size:11px}
.pj-org-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.pj-org-arrow{color:var(--tx3);font-size:9px;margin:0 2px}
```

### 渲染顺序

Agent 列从上到下：
1. **分类汇总条** — `categorizeAgents()` 生成的 badge 标签
2. **组织层级树** — `buildAgentOrgTree()` 生成的 org-node 行
3. **Agent 列表** — 每行带分类标签 + 汇报线

---

## 实时自动刷新 (Live Auto-Refresh)

项目作战室选中项目后，定时轮询 API 更新任务状态和 Pipeline，无需手动刷新。

### State 字段

```javascript
let state = {
  // ...
  autoRefresh: true,       // live refresh toggle
  refreshInterval: 15,     // seconds between auto-refreshes
  lastRefresh: null,       // timestamp of last data fetch
  _refreshTimer: null,     // setInterval handle
};
```

### Live 按钮 HTML

```html
<button class="btn sm" id="pjLiveBtn" onclick="toggleAutoRefresh()">
  <span id="pjLiveDot" style="width:7px;height:7px;border-radius:50%;
    background:var(--green);display:inline-block;margin-right:4px;
    animation:pulse-dot 2s infinite"></span>Live
</button>
```

### 核心函数

```javascript
function toggleAutoRefresh() {
  state.autoRefresh = !state.autoRefresh;
  const dot = $('#pjLiveDot');
  if (state.autoRefresh) {
    dot.style.background = 'var(--green)';
    dot.style.animation = 'pulse-dot 2s infinite';
    startAutoRefresh();
  } else {
    dot.style.background = 'var(--tx3)';
    dot.style.animation = 'none';
    stopAutoRefresh();
  }
}

function startAutoRefresh() {
  stopAutoRefresh();
  if (!state.autoRefresh) return;
  state._refreshTimer = setInterval(async () => {
    if (!state.autoRefresh || state.view !== 'project' || !state.selectedProject) return;
    try {
      const [tasks, pipe] = await Promise.all([
        fetchJSON(API + '/tasks'),
        fetchJSON(API + '/pipeline/' + encodeURIComponent(state.selectedProject))
      ]);
      if (tasks) state.data.tasks = tasks;
      if (pipe) { state._pipeData = pipe; renderPipelineColumn(pipe); }
      state.lastRefresh = Date.now();
      // Update KPI progress bar in-place
      if (state.liveProject && tasks) {
        const done = tasks.filter(t => t.status === 'done').length;
        const pct = tasks.length > 0 ? Math.round(done/tasks.length*100) : 0;
        const kpiNums = $$('#pjHeroKpis .num');
        if (kpiNums[1]) kpiNums[1].textContent = pct + '%';
      }
    } catch(e) { /* silent */ }
  }, state.refreshInterval * 1000);
}

function stopAutoRefresh() {
  if (state._refreshTimer) { clearInterval(state._refreshTimer); state._refreshTimer = null; }
}
```

### 启动/停止时机

```javascript
// loadProjectView() 末尾启动:
renderProject();
state.lastRefresh = Date.now();
startAutoRefresh();

// go() 切视图时停止:
function go(v) {
  if (state.view !== v) stopAutoRefresh();
  // ...
}
```

**注意**: 只刷新 Pipeline 列和 KPI 进度条，不重新渲染整个视图（避免滚动位置丢失）。Agent 负载更新可在后续版本添加。

### 交互表

| 元素 | 动作 | 目标 |
|------|------|------|
| 项目下拉框 | change → loadProjectView() | 切换项目 |
| 搜索框 | input → filterProjectView() | 实时过滤三列 |
| Live 按钮 | click → toggleAutoRefresh() | 切换实时刷新 |
| 模块节点 | click → openModuleDrawer(idx) | 编辑模块详情 |
| 子功能点 | click → openSubFunctionDrawer() | 分配 Agent |
| Agent 行 | click → openAgentDetail(agentId) | Agent 弹窗(能力/对话/Model) |
| Pipeline 任务 | click → openTaskDrawer(taskId) | 任务详情 Drawer |
| Hero KPI 目标卡 | click → openProjectDrawer() | 编辑项目目标 |
| 站会报告按钮 | click → loadStandup() | 生成站会报告 |
| Sprint 头 | click → toggle | 展开/收起时间线 |
