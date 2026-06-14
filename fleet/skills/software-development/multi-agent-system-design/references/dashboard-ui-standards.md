# Apex Dashboard UI Standards

Rigid design rules learned from 老卢's iterative feedback. Apply to ALL dashboard HTML files.

## Design System

| Element | Rule |
|---------|------|
| **Layout** | Sidebar (230px) + main content area. Sidebar has nav sections (运营/智能/资源) and crew list at bottom |
| **Routing** | View-based: `<section class="view" id="v-X">` toggled by `.on` class. No horizontal tabs. |
| **Sidebar nav** | Each item: `<div class="nav" data-view="X" onclick="go('X')"><i class="ti ti-icon"></i>Label</div>` |
| **Colors** | `--bg:#0a0d12 --bg2:#11151c --bg3:#161b24 --bg4:#1c2330 --teal:#2dd4bf --violet:#a78bfa --amber:#fbbf24 --green:#34d399 --red:#f87171 --blue:#60a5fa` |
| **Fonts** | Sora (headings), Manrope (body), IBM Plex Mono (code/numbers) |
| **Icons** | Tabler Icons via CDN: `<link href="https://cdnjs.cloudflare.com/ajax/libs/tabler-icons/3.30.0/tabler-icons.min.css">` |
| **Cards** | `border-radius:var(--r-l)` (14px), `background:var(--bg2)`, `border:1px solid var(--line)` |
| **Transitions** | View switching: `opacity:0→1 + translateY(8px→0)` fade animation |
| **KPI cards** | `.kpi` — label at top, large number, sub-text. 4-column grid |

## ABSOLUTE RULES (老卢 enforced)

1. **NO emoji in UI chrome** — no emoji in section headers, buttons, labels, badges, or any static HTML. Emoji allowed ONLY in dynamic data strings from APIs.
2. **ALL icons use Tabler** — `<i class="ti ti-icon-name">` for every icon. No Unicode/emoji icons.
3. **Status dots use CSS** — `<span class="st run/gate/idle">` not 🟢🟡🔴
4. **Medal/star badges use Tabler** — `<i class="ti ti-medal/star-filled">` not 🥇★
5. **Alert/warning icons use Tabler** — `<i class="ti ti-alert-triangle">` not ⚠️

## Reference Templates

- Full reference design: `~/Downloads/AgentCorp-OS/AgentCorp-OS.html` (897 lines)
- Our implementation: `~/Desktop/2026AIAPP/Apex/apex/interface/templates/command_center.html` (2771 lines)

## View Hierarchy

```
运营: 指挥中心 → 项目作战室 → 审批审计 → Pipeline
智能: AI舰队 → 自治引擎 → 知识图谱 → 数据流时序 → 模块市场 → SKILL进化
资源: 成本中心 → 系统状态 → GPU资源中心
```

## API Integration Pattern

```javascript
// Data loading
const state = { commandCenter: null, profiles: [], tasks: [], /* ... */ };

async function fetchJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error('HTTP ' + r.status);
  return await r.json();
}

async function loadAll() {
  const settled = await Promise.allSettled([
    fetchJSON('/api/command-center').then(d => ({key:'commandCenter', data:d})),
    fetchJSON('/api/profiles').then(d => ({key:'profiles', data:d})),
    // ... more endpoints
  ].map(p => p));
  for (const r of settled) {
    if (r.status === 'fulfilled') state[r.value.key] = r.value.data;
  }
  renderActiveView();
}

// Auto-refresh: 30s full, 15s runtime pulse
setInterval(loadAll, 30000);
```

## Key Conventions

- All API fetches use `fetchJSON()` wrapper with error handling
- State stored as global `state` object with typed keys
- Render functions named `renderTabX()` or `renderViewName()`
- View switching: CSS class `.on` on `<section>`, not display:none
- Data shown as "Loading..." during fetch, "No data" when empty
