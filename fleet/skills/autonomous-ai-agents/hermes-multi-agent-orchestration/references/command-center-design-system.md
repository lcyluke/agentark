# Apex Command Center — Dashboard Design System

> Built: June 2026 | UI stack: Sora/Manrope/Mono + Tabler Icons + 12-view SPA
> Reference analysis: Dify(144K⭐) + Langflow(149K⭐) + OpenWebUI(140K⭐) + AgentCorp-OS

## Architecture

```
command_center.html (single-file, 2900+ lines)
├── Sidebar (230px): 3 sections (运营/智能/资源) + crew list
├── Top bar: breadcrumb + live pulse + AI Commander + theme toggle
├── 12 views: .view class toggled by .on
├── AI Chat drawer: 440px right-side slide-in
├── Agent drawer: profile + skills + chat history + model comparison
└── Light/dark theme: [data-theme] CSS variable swap + localStorage
```

## Design Token System

```css
:root {
  /* Surface */
  --bg:#0a0d12; --bg2:#11151c; --bg3:#161b24; --bg4:#1c2330;
  /* Text */
  --tx:#e7ecf3; --tx2:#95a2b6; --tx3:#5d6878;
  /* Brand */
  --teal:#2dd4bf; --violet:#a78bfa; --amber:#fbbf24; --green:#34d399; --red:#f87171; --blue:#60a5fa;
  /* Radius */
  --r:10px; --r-s:7px; --r-l:14px;
  /* Spacing */
  --sp-xs:4px; --sp-sm:8px; --sp-md:14px; --sp-lg:20px; --sp-xl:28px;
  /* Shadows */
  --sh-sm:0 1px 3px rgba(0,0,0,.3); --sh-md:0 4px 12px rgba(0,0,0,.4); --sh-lg:0 8px 24px rgba(0,0,0,.5);
  --sh-glow:0 0 20px rgba(45,212,191,.08);
  /* Transitions */
  --tr-fast:.12s ease; --tr-base:.2s ease; --tr-slow:.35s cubic-bezier(.4,0,.2,1);
  /* Typography */
  --disp:'Sora',sans-serif; --body:'Manrope',sans-serif; --mono:'IBM Plex Mono',monospace;
  /* Font sizes */
  --fs-xs:10px; --fs-sm:12px; --fs-base:14px; --fs-lg:16px; --fs-xl:20px; --fs-2xl:28px;
}

/* Light theme */
[data-theme="light"] {
  --bg:#f8fafc; --bg2:#ffffff; --bg3:#f1f5f9; --bg4:#e2e8f0;
  --tx:#0f172a; --tx2:#475569; --tx3:#94a3b8;
}
```

## Theme Toggle Implementation

```javascript
function toggleTheme(){
  const html=document.documentElement;
  const isLight=html.getAttribute('data-theme')==='light';
  html.setAttribute('data-theme',isLight?'':'light');
  $('#themeIcon').className='ti '+(isLight?'ti-sun':'ti-moon');
  localStorage.setItem('apex-theme',isLight?'':'light');
}
// Persist on load
if(localStorage.getItem('apex-theme')==='light')
  document.documentElement.setAttribute('data-theme','light');
```

## 12 Views

| View | Route | Key APIs |
|------|-------|----------|
| 指挥中心 | v-dashboard | /api/command-center, /api/live/runtime |
| 项目作战室 | v-project | /api/projects/approved, /api/projects/<name>, /api/ops/agents/workloads |
| 审批审计 | v-approvals | Audit queue (placeholder) |
| Pipeline | v-pipeline | /api/pipeline/<project> |
| AI舰队 | v-fleet | /api/fleet/profiles/list, /api/profiles |
| 自治引擎 | v-autonomy | /api/autonomous, /api/command-center(cron) |
| 知识图谱 | v-knowledge | /api/knowledge, /api/ops/knowledge/search |
| 数据流时序 | v-flow | Sequence diagram (static) |
| 模块市场 | v-modules | /api/modules |
| SKILL进化 | v-skills | /api/skills/leaderboard, /api/skills/<agent> |
| 成本中心 | v-cost | /api/command-center(pricing, sessions, gpu) |
| 系统状态 | v-system | /api/environment |

## Backend API Inventory

| Module | File | Endpoints |
|--------|------|-----------|
| hermes_bridge | hermes_bridge.py | /api/command-center, /api/gpu/status, /api/hermes/*, /api/models/pricing, /api/environment |
| fleet_manager | fleet_manager.py | /api/fleet/profiles/*, /api/fleet/teams/* |
| project_ops | project_ops.py | /api/ops/agents/workloads, /api/ops/agents/match, /api/ops/standup, /api/ops/knowledge/* |
| live_status | live_status.py | /api/live/runtime, /api/live/projects, /api/live/project/<name> |
| project_registry | project_registry.py | /api/projects/*, /api/agents/* |
| project_factory | project_factory.py | /api/modules, /api/skills/*, /api/pipeline/<project> |

## UI Pitfalls (Hard-Won)

1. **Canvas API cannot use CSS variables.** Use hex: `ctx.fillStyle='#3b82f6'` NOT `var(--accent)`. CSS vars in style= attributes are fine.

2. **Subagent over-escapes JS strings.** When delegate_task writes innerHTML with onclick handlers, quote escaping cascades: `\\\\\\\"` instead of `\"`. Fix with `node -e "html.replace(/\\\\\\\\\\\\\\\"/g, '\"')"` and validate with `node --check`.

3. **Flask route collision.** `/api/items` GET (list) and `/api/items/<name>` GET (detail) collide. Use `/api/items/list` or merge into one handler.

4. **View switching needs event binding audit.** New nav buttons added via HTML patches may not be found by `querySelectorAll` if the script runs before the DOM update.

5. **Flask template caching.** After editing dashboard HTML, kill and restart the Flask server — hard browser refresh is insufficient.
