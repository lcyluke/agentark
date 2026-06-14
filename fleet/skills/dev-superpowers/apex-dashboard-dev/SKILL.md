---
name: apex-dashboard-dev
description: Apex Dashboard 全栈扩展模式 — 如何给 Fleet Manager Tab 添加新按钮/功能，涵盖后端 fleet_manager.py → web.py API 路由 → dashboard_v5.html 前端三层的完整模板。
category: dev-superpowers
triggers:
  - Apex Dashboard 添加新功能/按钮
  - Fleet Manager Tab 扩展
  - dashboard_v5.html 修改
  - 用户说"给 Dashboard 加个按钮"
  - Apex profile/team CRUD 操作
---

# 🦅 Apex Dashboard 全栈扩展模式

## 唯一入口

**`command_center.html` 是唯一的 Dashboard 文件。** 旧版 (dashboard.html/v4/v5/daily/auth) 已清理。

| 路由 | 模板 | 架构 |
|:--|:--|:--|
| `/` | `command_center.html` | **主力** — 根路径直指 |
| `/cc` | `command_center.html` | 别名，向后兼容 |

## 12 视图总览

侧边栏三组：**运营**(指挥中心/项目作战室/审批审计/Pipeline) · **智能**(AI舰队/自治引擎/知识图谱/数据流时序/模块市场/SKILL进化) · **资源**(成本中心/系统状态/GPU资源中心)

| 视图 | ID | API 数据源 | 说明 |
|:--|:--|:--|:--|
| 指挥中心 | v-dashboard | command-center + live/runtime | KPI + GPU + 活动流 |
| 项目作战室 | v-project | projects/approved + projects/<name> | 立项审批+模块架构+Agent弹窗 |
| 审批审计 | v-approvals | — | 审批队列 |
| Pipeline | v-pipeline | pipeline/<project> | 7阶段流水线+评价 |
| AI舰队 | v-fleet | profiles + fleet/profiles | Profile卡片+组织架构 |
| 自治引擎 | v-autonomy | autonomous + cron | 引擎+Cron+进化 |
| 知识图谱 | v-knowledge | knowledge + profiles | Canvas+Skill搜索 |
| 数据流时序 | v-flow | — | 静态设计 |
| 模块市场 | v-modules | modules | 5类20+可复用模板 |
| SKILL进化 | v-skills | skills/leaderboard | XP排行榜+6级进化 |
| 成本中心 | v-cost | command-center pricing | Token+Model定价 |
| 系统状态 | v-system | environment | OS/Python/工具 |
| GPU资源 | gpu-view | gpu/status | AutoDL双实例 |

## Dashboard Evolution (V3→V6)

```
V3 (假数据Demo) → V4 (单页真数据) → V5 (8舱横向Tab) → V6 (侧边栏14视图+总分弹窗)
```

### Lessons per version

| Transition | Lesson |
|:-----------|:-------|
| V3→V4 | 真实数据比华丽UI更重要，先用API接真数据再打磨 |
| V4→V5 | 单页信息过载→分舱，但横向Tab不专业 |
| V5→V6 | 侧边栏+视图路由是专业Dashboard的标准模式（参考AgentCorp-OS/Dify） |

### File Management Principles

- **一个入口**：所有Dashboard功能在单一HTML文件中（`command_center.html`）
- **单一URL**：只保留根路径`/`，删掉所有别名（`/cc` `/v4` `/v5`）
- **定期清理旧版**：旧版Dashboard文件是负债，功能稳定后立即删除

## Reference Designs

| Project | Stars | 借鉴点 |
|---------|-------|--------|
| **AgentCorp-OS** | 参考设计 | 侧边栏+视图路由+drawer+董事会 |
| **Dify** | 144K | 语义化设计Token+渐变背景+操作按钮hover显现 |
| **Langflow** | 149K | shadcn/ui风格+HSL颜色变量+弹性动画 |
| **OpenWebUI** | 140K | 自研SVG图表+可拖拽侧边栏+极简KPI |

## 设计系统 Token

```css
:root{
  /* Surface */ --bg→bg4, --line→line2
  /* Text */   --tx→tx3
  /* Brand */  --teal/--violet/--amber/--green/--red/--blue + -d dark variants
  /* Radius */ --r(10px) --r-s(7px) --r-l(14px)
  /* Spacing */ --sp-xs(4) --sp-sm(8) --sp-md(14) --sp-lg(20) --sp-xl(28)
  /* Shadows */ --sh-sm --sh-md --sh-lg --sh-glow
  /* Transitions */ --tr-fast(.12s) --tr-base(.2s) --tr-slow(.35s cubic-bezier)
  /* Typography */ --disp:'Sora' --body:'Manrope' --mono:'IBM Plex Mono'
  /* Font sizes */ --fs-xs(10) --fs-sm(12) --fs-base(14) --fs-lg(16) --fs-xl(20) --fs-2xl(28)
}

/* Light theme: */
[data-theme="light"]{ /* flips all surface/text colors, dark→light */ }
```

**图标**: Tabler Icons CDN (`ti ti-*`)，全站零 emoji。

## 架构三层

```
后端逻辑层:    apex/interface/fleet_manager.py 或 gpu_manager.py
    ↓ (import)
API 路由层:    apex/interface/web.py
    ↓ (fetch)
前端展示层:    apex/interface/templates/command_center.html  ← 主力
```

**关键路径：** `~/Desktop/2026AIAPP/Apex/apex/interface/`

### Data Bridge: Hermes → Apex

| 数据 | 来源 | 关键注意 |
|:-----|:-----|:---------|
| Token/成本 | `state.db` sessions表 | sessions表已含 `input_tokens`/`output_tokens`/`estimated_cost_usd`，用 `started_at` 而非 `created_at` |
| Session/消息 | `state.db` messages表 | content字段可能含JSON工具调用结果，需try-parse |
| Profile列表 | `hermes profile list` CLI | 通过 hermes_bridge.py 调用 |
| GPU指标 | SSH → nvidia-smi | 并行化 + BatchMode=yes |
| 运行时进程 | `ps aux` | 通过 live_status.py |

## ⚠️ JS 安全编码规则 (CRITICAL)

**在 command_center.html 中写 JS 时，永远避免模板字符串（反引号）生成 HTML。**

❌ 危险 — patch 工具可能截断多行模板字符串：
```javascript
return `<div class="${cardClass}" onclick="...">
  <div class="fcan">${canTag}</div>
</div>`;
```

✅ 安全 — 字符串拼接永远不会被截断：
```javascript
return '<div class="'+cardClass+'" onclick="...">' +
  '<div class="fcan">'+canTag+'</div>' +
  '</div>';
```

**原因：** patch 工具的 `old_string`/`new_string` 匹配可能意外截断模板字符串的反引号，导致后续 HTML 标签被 JS 解析器当作语法错误。

## 修改后验证流程 (MANDATORY)

每次修改 JS 后必须执行：

```bash
# 1. 验证 JS 语法
curl -s --max-time 5 http://localhost:8080/cc -o /tmp/cc_test.html
# Extract <script>...</script> and run:
node --check /tmp/cc_js.js

# 2. 如果 node --check 报错 → git checkout 恢复 → 重新干净修改
cd ~/Desktop/2026AIAPP/Apex
git checkout -- apex/interface/templates/command_center.html
# 然后重新 apply 你的改动

# 3. 语法通过后 → 重启服务器
kill $(lsof -ti:8080)
cd ~/Desktop/2026AIAPP/Apex && .venv/bin/python3 -c "from apex.interface.web import run_dashboard; run_dashboard()" &

# 4. 浏览器验证
open http://localhost:8080/cc
```

## /cc 添加新视图的完整模板

### Phase 1: 后端逻辑

新建或扩展 `apex/interface/xxx_manager.py`，返回 dict。惯例：
- 成功: `{"ok": True, ...}`
- 失败: `{"error": "message"}`

### Phase 2: API 路由 (web.py)

在 `create_app()` 内添加路由。务必检查函数名不重复。新增路由加在现有 fleet 路由之后、Task Management 之前。

### Phase 3: 前端 (command_center.html)

三步走：

**A. 侧栏入口** — 在 `<aside class="side">` 的对应分区添加 nav：
```html
<div class="nav" data-view="gpu" onclick="go('gpu')"><i class="ti ti-xxx"></i>名称</div>
```

**B. 视图容器** — 在最后一个 `</section>` 之后、`</div></main>` 之前添加：
```html
<section class="view" id="v-gpu">
  <div class="sec-h">标题</div>
  <div class="kpis" id="gpuKpis"></div>
  <!-- ... -->
</section>
```

**C. JS 函数** — 添加三处：
1. `VIEW_TITLES` 字典: `gpu: ['GPU 资源中心', 'GPU Resource Center']`
2. `renderActiveView()` switch: `case 'gpu': renderGPU(); break;`
3. 视图函数: 在 `/* ========== Events ========== */` 之前添加 `async function renderGPU() { ... }`

JS 中生成 HTML 用字符串拼接，不用模板字符串。

### Phase 1 示例: 后端逻辑 (fleet_manager.py)

在 `fleet_manager.py` 中添加纯函数，返回 dict：

```python
def my_action(name: str) -> dict:
    """Action description"""
    pdir = PROFILES_DIR / name
    if not pdir.exists():
        return {"error": f"Profile '{name}' not found"}
    
    # ... 业务逻辑 ...
    
    return {"ok": True, "profile": name, "result": "..."}
```

**惯例：**
- 返回值统一用 `{"ok": True, ...}` 或 `{"error": "..."}`
- 函数间用 `# ═══════` 分隔
- `import shutil` 可以放在函数内部（避免顶层导入未使用警告）

### Phase 2: API 路由 (web.py)

在 `web.py` 的 fleet 路由区块中添加：

```python
@app.route("/api/fleet/profiles/<name>/my-action", methods=["POST"])
def api_fleet_my_action(name: str):
    """API description"""
    try:
        from apex.interface.fleet_manager import my_action
        data = request.get_json(force=True) or {}
        return jsonify(my_action(name, **data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

**Pitfall:** 路由函数名不能重复。LSP 会报 `jsonify`/`request` 未绑定 — 这是误报，Flask 闭包内可用。路由需在 `create_app()` 函数体内注册。

### Phase 3: 前端 (dashboard_v5.html)

#### CSS
添加按钮样式到 `<style>` 块（在 `.fleet-status-dot` 样式之后）：

```css
.fleet-btn.my-action{background:var(--xxx-bg);color:var(--xxx);border-color:var(--xxx)}
.fleet-btn.my-action:hover{background:var(--xxx);color:#fff}
```

变量系统：
- `--green`/`--green-bg` — 成功/启用
- `--red`/`--red-bg` — 危险/禁用
- `--accent`/`--accent-glow` — 编辑/主要操作
- `--cyan`/`--cyan-bg` — 复制
- `--yellow`/`--yellow-bg` — 警告
- `--purple`/`--purple-bg` — 特殊

#### JS 函数
在 `deleteFleetProfile` 函数之后添加异步函数：

```javascript
async function myFleetAction(name){
  try{
    const r=await fetch('/api/fleet/profiles/'+encodeURIComponent(name)+'/my-action',{method:'POST'});
    if(!r.ok)throw new Error('HTTP '+r.status);
    const data=await r.json();
    addLog('success','Action on '+name+' completed');
    loadAll();  // 刷新数据
  }catch(e){
    addLog('error','Action failed: '+e.message);
    alert('Failed: '+e.message);
  }
}
```

#### 卡片按钮
在 `renderTab8()` 的 profile card 渲染中添加按钮（在 `.profile-actions` div 内）：

```javascript
el('button',{class:'fleet-btn my-action',onclick:function(e){
  e.stopPropagation();  // 防止触发卡片点击
  myFleetAction(p.name);
}},'🎯 Label'),
```

**Pitfall:** `default` profile 不应有破坏性按钮（toggle/delete）。用三元表达式跳过：
```javascript
p.is_default?'':el('button',...)
```
并用 `.filter(Boolean)` 过滤掉空值。

## 已验证的模式

### Enable/Disable 模式
- 后端: `.disabled` 标记文件 → `toggle_profile()` 
- 前端: `isDisabled` 状态 → 灰化卡片(opacity:0.5) + 按钮文字切换
- 卡片 class: `profile-card disabled`

### Copy 模式
- 后端: `shutil.copytree()` + SOUL.md 名称替换 + 移除 `.disabled`
- 前端: `prompt()` 获取新名称 → POST 请求 → `loadAll()` 刷新

### Team 操作按钮
Team 卡片按钮放在 `ftc-name` 同级 flex 容器中，使用 `.fleet-btn` 样式。

## 重启 Dashboard

```bash
# 找到并杀死旧进程
kill $(lsof -ti:8080)

# 启动（必须用 run_dashboard，不能在 -m 下直接启动）
cd ~/Desktop/2026AIAPP/Apex && .venv/bin/python3 -c "
from apex.interface.web import run_dashboard
run_dashboard()
" &

# 确认运行
sleep 2 && lsof -ti:8080
```

**Pitfall:** `python3 -m apex.interface.web` 不能直接启动，因为 web.py 没有 `if __name__ == "__main__"` 块，必须显式调用 `run_dashboard()`。

## 性能优化模式

### API 并行化 (ThreadPoolExecutor)

当 `/api/command-center` 聚合多个慢操作（subprocess、SSH、DB查询）时，必须并行化。**不要串行调用。**

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_command_center_data() -> dict:
    results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(get_hermes_cron_status): "hermes_cron",   # subprocess ~1s
            executor.submit(get_gpu_status): "gpu",                   # SSH ~2s
            executor.submit(get_hermes_profile_status): "hermes_profiles",  # subprocess ~1s
        }
        for future in as_completed(futures, timeout=8):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                results[key] = {"error": str(e), "timeout": True}
    
    return {
        "hermes_sessions": get_hermes_session_stats(),  # SQLite ~50ms, main thread
        "hermes_cron": results.get("hermes_cron", {}),
        "gpu": results.get("gpu", {}),
        # ...
    }
```

**效果**: 6s (串行) → 1.4s (并行)。SSH 实例检查也应在 `get_gpu_instances_status()` 内部并行。

### SSH 超时优化

```python
# ❌ 慢: ConnectTimeout=5 + 两台实例 = 10s+
["ssh", "-o", "ConnectTimeout=5", ...]

# ✅ 快: ConnectTimeout=2 + BatchMode=yes + 并行 = 2s 天花板
["ssh", "-o", "ConnectTimeout=2", "-o", "BatchMode=yes", ...]
```

`BatchMode=yes` 阻止 SSH 等待密码输入，立即失败返回。

## 验证

```bash
# 检查 JS 语法 (每次修改后必须)
curl -s http://localhost:8080/ -o /tmp/cc.html
python3 -c "import re,subprocess;html=open('/tmp/cc.html').read();m=re.search(r'<script>(.*?)</script>',html,re.DOTALL);js=m.group(1);open('/tmp/cc_js.js','w').write(js);r=subprocess.run(['node','--check','/tmp/cc_js.js'],capture_output=True,text=True);print(r.stderr or '✅ OK')"

# 检查 API + 计时
time curl -s -o /dev/null -w "HTTP %{http_code} | %{time_total}s\n" http://localhost:8080/api/command-center

# 浏览器验证 (唯一入口)
open http://localhost:8080/
```

### ⚠️ Flask 模板缓存陷阱

`render_template()` 在 Flask debug=False 时会缓存模板。**修改 command_center.html 后必须重启服务器**，否则浏览器收到的是旧版 HTML。

```bash
# 完整重启流程
kill $(lsof -ti:8080)
sleep 1
cd ~/Desktop/2026AIAPP/Apex && .venv/bin/python3 -c "
from apex.interface.web import run_dashboard
run_dashboard()
" &
sleep 3
# 验证新版生效
curl -s http://localhost:8080/ | grep "你的新代码特征串"
```

### ⚠️ 模板字符串转义 (Template Literal Escaping)

在 `command_center.html` 的 JS 中用模板字符串生成 HTML onclick 属性时，`.replace(/'/g, ...)` 的转义极易出错。

**❌ 错误** — `\"\\\\'\"` 会被浏览器 JS 解析器当作语法错误，导致整个 `<script>` 不执行：
```javascript
`...onclick="fn('${x.replace(/'/g,\"\\\\'\" )}')">`
```

**✅ 正确** — `"\\'"` 在模板字符串中产生字符串 `\'`：
```javascript
`...onclick="fn('${x.replace(/'/g,"\\'")}')">`
```

**检测方法**: 如果页面加载后 `state` 变量未定义（`typeof state === 'undefined'`），说明 JS 脚本根本没执行 → 语法错误。用 `node --check` 提取的 JS 文件定位具体行号。

**修复方法**: 用 Python 二进制模式读写文件，精确替换字节序列，避免 shell escaping 问题：
```python
with open(path, 'rb') as f:
    content = f.read()
broken = b'\\"\\\\\\\\\'\\"'  # \"\\\\'\"
correct = b'"\\\\\'"'        # "\\'"
content = content.replace(broken, correct)
with open(path, 'wb') as f:
    f.write(content)
```

## 文件位置

| 层 | 文件 |
|:--|:--|
| 前端 | `apex/interface/templates/command_center.html` (**唯一**) |
| API 路由 | `apex/interface/web.py` |
| Hermes 数据桥 | `apex/interface/hermes_bridge.py` |
| Fleet 管理 | `apex/interface/fleet_manager.py` |
| 项目注册 | `apex/interface/project_registry.py` |
| 项目工厂 | `apex/interface/project_factory.py` |
| 项目协作 | `apex/interface/project_ops.py` |
| 实时状态 | `apex/interface/live_status.py` |

## 视图重构: 5 层布局模式 (War Room V2)

当视图"所有内容挤在一起"需要重新排版时，采用自上而下 5 层结构：

| 层 | 角色 | 典型内容 | 占比 |
|:--|:--|:--|:--|
| **L1** 选择栏 | 上下文切换 | 项目下拉 + 搜索框 + 操作按钮 | 1 行 |
| **L2** Hero KPI | 一屏总览 | 5-6 张 KPI 卡片（目标/进度条/人员/成本/风险） | 1-2 行 |
| **L3** 瀑布流 | 核心数据 | 3 列 grid（模块树\|Agent表\|Pipeline），各自可滚动 | 屏幕主体 |
| **L4** 时间线 | 时间维度 | 可折叠 Sprint/甘特迷你图 | 按需展开 |
| **L5** 活动提要 | 上下文 | 最近提交/站会摘要/AI建议，3 卡片 | 1 行 |

### 三列瀑布流 CSS

```css
.pj-tricol{display:grid;grid-template-columns:1.8fr 2fr 3fr;gap:10px;align-items:start}
/* 移动端回退为单列 */
@media(max-width:920px){.pj-tricol{grid-template-columns:1fr}}
```

每列是一个 `.card`，`max-height:70vh;overflow:auto`，列头 `position:sticky;top:0`。

### 模块树模式

树节点用左边框色 + 进度条 + 缩进子项：
```css
.pj-mod-item{border-left:3px solid var(--violet);cursor:pointer}
.pj-mod-item:hover{border-left-color:var(--teal)}
.pj-sf-item{padding-left:22px}  /* 缩进子功能 */
.pj-sf-dot{width:5px;height:5px;border-radius:50%}  /* 状态圆点 */
.pj-sf-dot.done{background:var(--green)}
```

### 实时搜索过滤

```javascript
function filterProjectView() {
  const q = ($('#pjSearch')?.value || '').toLowerCase();
  if (!q) { /* show all */ return; }
  $$('.pj-mod-item, .pj-agent-row, .pj-pipe-task').forEach(el => {
    el.style.display = el.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}
```

### Pipeline 列渲染

从 `/api/pipeline/<project>` 获取 stages，按阶段分组显示任务卡片：
```javascript
function renderPipelineColumn(pipe) {
  const stages = pipe.stages || [];
  $('#pjPipeStages').innerHTML = stages.map(st => 
    `<div class="pj-pipe-stage">
      <div class="pj-pipe-stage-h">${st.name} <span class="count">${st.tasks.length}</span></div>
      ${st.tasks.map(t => `<div class="pj-pipe-task" onclick="openTaskDrawer('${t.id}')">
        <span class="prio ${t.priority}"></span>${t.title}
      </div>`).join('')}
    </div>`
  ).join('');
}
```

### Agent 分类标签系统

当 Agent 数据显示稀疏（name/role 为 `?`）时，用命名约定自动分类并标注。

```javascript
// 15 类分类器，按优先级匹配（general 兜底）
const AGENT_CATEGORIES = [
  { key: 'origin',   pattern: /^(origin|default)$/i,         icon: '⚓', label: '始祖',   color: '#a78bfa', tier: 0 },
  { key: 'pm',       pattern: /-(pm)$|^pm-/i,                icon: '📋', label: 'PM',     color: '#60a5fa', tier: 1 },
  { key: 'audit',    pattern: /audit|guardian|approval/i,     icon: '🔍', label: '审批审计', color: '#f59e0b', tier: 1 },
  { key: 'cron',     pattern: /cron|watchdog|monitor|巡检|定时/i, icon: '⏰', label: '定时巡检', color: '#8b5cf6', tier: 2 },
  { key: 'ai',       pattern: /ai-|algorithm|ml-|training/i,  icon: '🧠', label: 'AI/ML',  color: '#ec4899', tier: 2 },
  // ... + 10 more categories (architect, vision, frontend, backend, content, funding, security, data, ops, general)
  { key: 'general',  pattern: /.*/,  icon: '🤖', label: '通用', color: '#9ca3af', tier: 4 }
];

function classifyAgent(name) {
  for (const cat of AGENT_CATEGORIES) {
    if (cat.pattern.test(name.toLowerCase())) return cat;
  }
}

function categorizeAgents(agents) {
  // Returns { key: { count, names[], icon, label, color, ... } }
  // Used for mini summary bar at top of Agent column
}
```

**Agent 行渲染** — 每行加左边框色条 + 分类标签：

```javascript
const cls = classifyAgent(agentId);
return `<div class="pj-agent-row" style="border-left:3px solid ${cls.color}">
  <div class="pj-agent-name">${agentId} <span class="pj-agent-tag" style="background:${cls.bg};color:${cls.color}">${cls.icon} ${cls.label}</span></div>
</div>`;
```

**汇总栏 CSS**: `.pj-agent-summary{display:flex;flex-wrap:wrap;gap:4px}` `.pj-agent-badge{font-size:10px;padding:2px 7px;border-radius:10px}`

完整分类表 + 渲染逻辑见 `references/war-room-layout.md`。

### 子功能 Drawer 分配 Agent

点击模块树的子功能项 → 打开编辑 Drawer，可分配 Agent：
```javascript
function openSubFunctionDrawer(mi, sfName) {
  const sf = window._pjModules[mi].sub_functions.find(s => s.name === sfName);
  openDrawerEdit('子功能: ' + sfName, mod.name, 'ti-subtask',
    `<input id="sfAgentInput" value="${sf.assigned_agent||''}" placeholder="输入 Agent 名称">`,
    async () => {
      await apiPost('/api/projects/subfunction', {
        project: state.selectedProject, module_idx: mi,
        subfunction: sfName, assigned_agent: $('#sfAgentInput').value
      });
      closeAll(); loadProjectView();
    }, null, '保存', null
  );
}
```

完整布局规范 + Agent 分类系统 + 组织层级树 + 实时自动刷新 见 `references/war-room-layout.md`。

## 设计参考

见 `references/dashboard-design-patterns.md` — Dify/Langflow/OpenWebUI 顶级设计精华。
见 `references/dashboard-perf-debugging.md` — 性能问题诊断与修复完整食谱（API并行化、SSH超时、JS转义、模板缓存）。
见 `references/war-room-layout.md` — 项目作战室 V2 5层布局完整 HTML/CSS/JS 参考。
见 `references/security-mcp-panel.md` — 系统状态视图添加 MCP 状态面板的完整模式（API端点+HTML卡片+JS渲染）。

## 项目下拉切换 Bug 模式 (CRITICAL)

当 `loadProjectView()` 重建 `<select>` 的 innerHTML 后恢复选择时，**用户的当前选择 (`currentVal`) 必须优先于 `state.selectedProject`（上次记忆值）**，否则切 A→B 永远回到 A。

### ❌ 错误 — stale state 覆盖新选择

```javascript
// 先检查 state.selectedProject（旧值）→ 永远赢过 currentVal（新值）
if (state.selectedProject) {
    sel.value = state.selectedProject;   // ← BUG: 总是恢复到上次项目
} else if (currentVal && ...) {
    sel.value = currentVal;
}
```

### ✅ 正确 — 用户操作优先

```javascript
// currentVal 来自 onchange 事件 → 是用户刚点的值，优先级最高
if (currentVal && currentVal !== '' && currentVal !== 'all'
    && projects.some(p => p.name === currentVal)) {
    sel.value = currentVal;
    state.selectedProject = currentVal;  // 同步更新记忆
} else if (state.selectedProject && ...) {
    sel.value = state.selectedProject;   // 仅回退时用
}
```

**伴随修复**: 切换项目时清除 `state._pipeData = null`，防止 Pipeline 列显示上一个项目的数据。

## 实时自动刷新模式 (Live Polling)

项目作战室需要每 N 秒自动刷新任务状态，无需整页重载。

### State 扩展

```javascript
let state = {
  autoRefresh: true,       // 开关
  refreshInterval: 15,     // 秒
  lastRefresh: null,       // Date.now()
  _refreshTimer: null,     // setInterval handle
  // ...
};
```

### 核心函数

```javascript
function toggleAutoRefresh() {
  state.autoRefresh = !state.autoRefresh;
  // 更新 Live 按钮: 绿点脉冲动画 ↔ 灰色停止
  if (state.autoRefresh) { startAutoRefresh(); }
  else { stopAutoRefresh(); }
}

function startAutoRefresh() {
  stopAutoRefresh();
  state._refreshTimer = setInterval(async () => {
    if (!state.autoRefresh || state.view !== 'project') return;
    // 静默刷新: 只拉 tasks + pipeline，不重载全页
    const [tasks, pipe] = await Promise.all([
      fetchJSON(API + '/tasks'),
      fetchJSON(API + '/pipeline/' + encodeURIComponent(state.selectedProject))
    ]);
    if (tasks) state.data.tasks = tasks;
    if (pipe) { state._pipeData = pipe; renderPipelineColumn(pipe); }
    state.lastRefresh = Date.now();
    // 更新 KPI 进度数字（不重建 DOM）
    const kpiNums = $$('#pjHeroKpis .num');
    // kpiNums[1] = 进度% ...
  }, state.refreshInterval * 1000);
}

function stopAutoRefresh() {
  if (state._refreshTimer) { clearInterval(state._refreshTimer); state._refreshTimer = null; }
}
```

### 启动/停止时机

```javascript
// loadProjectView() 末尾
renderProject();
state.lastRefresh = Date.now();
startAutoRefresh();  // 进入项目视图时启动

// go() 切换视图时
function go(v) {
  if (state.view !== v) stopAutoRefresh();  // 离开项目视图时停止
  // ...
}
```

### Live 按钮 CSS

```css
@keyframes pulse-dot{0%,100%{opacity:1}50%{opacity:.3}}
```

按钮 HTML: `<button id="pjLiveBtn" onclick="toggleAutoRefresh()"><span id="pjLiveDot" style="animation:pulse-dot 2s infinite"></span>Live</button>`

### 组织层级树 (Org Hierarchy)

Agent 编队列顶部显示 4 层汇报结构:

```javascript
function buildAgentOrgTree(agents) {
  const hasOrigin = names.includes('origin');
  const pmAgents = agents.filter(a => classifyAgent(name).key === 'pm');
  const auditAgents = agents.filter(a => classifyAgent(name).key === 'audit');
  const cronAgents = agents.filter(a => classifyAgent(name).key === 'cron');
  // 渲染: ⚓ Origin → 督管 PMs | 🔍 审批审计 → 人在环闸门 | ⏰ 定时巡检 → Cron | 👥 执行团队 → N个Agent
}
```

每行加汇报链: `getReportingLine(agentName, projectName)` → `↳ ⚓ Origin` / `↳ badminton-pm` / `⏰ 自主定时`

项目→PM 映射表:
```javascript
const PROJECT_PM_MAP = {
  '羽球宝AI': 'badminton-pm', 'Apex': 'apex-pm',
  'FinOps AI': 'finops-pm', '深圳羽球地图': 'shenzhen-pm'
};
```
