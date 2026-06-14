# Apex Command Center — Architecture & API Reference

## URL: http://localhost:8080/cc
## File: apex/interface/templates/command_center.html (~1012 lines)

## Architecture

```
Sidebar (230px)                 Main Content Area
┌─────────────────┐    ┌─────────────────────────────────────┐
│ ⚡ Apex 指挥中心  │    │ Top Bar: breadcrumb + pulse + AI按钮 │
│ Multi-Agent OS   │    ├─────────────────────────────────────┤
├─────────────────┤    │ View (8 views, toggled by .on)      │
│ 运营             │    │  ┌───────────────────────────────┐  │
│  指挥中心        │    │  │ KPI cards / GPU / Activity     │  │
│  项目作战室      │    │  └───────────────────────────────┘  │
│  审批审计        │    │                                     │
│ 智能             │    │  Drawer (440px, slides from right)  │
│  AI舰队          │    │  ┌──────────────────────────┐      │
│  自治引擎        │    │  │ Detail / Chat / PM Report │      │
│  知识图谱        │    │  └──────────────────────────┘      │
│ 资源             │    │                                     │
│  成本中心        │    │  Toast (bottom-center)              │
│  系统状态        │    │                                     │
├─────────────────┤    └─────────────────────────────────────┘
│ 董事会           │
│  default · idle  │
│  ai-algorithm    │
│  ...             │
└─────────────────┘
```

## 8 Views

| View ID | Name | Primary APIs |
|---------|------|-------------|
| v-dashboard | 指挥中心 | /api/command-center, /api/profiles, /api/tasks |
| v-project | 项目作战室 | /api/tasks, /api/ops/agents/workloads, /api/ops/standup |
| v-approvals | 审批审计 | /api/auth/stats |
| v-fleet | AI舰队 | /api/fleet/profiles/list, /api/profiles, /api/ops/agents/workloads |
| v-autonomy | 自治引擎 | /api/autonomous, /api/command-center (cron) |
| v-knowledge | 知识图谱 | /api/knowledge, /api/profiles |
| v-cost | 成本中心 | /api/command-center (sessions, pricing, gpu) |
| v-system | 系统状态 | /api/environment |

## Key Design Patterns

1. **View routing**: `<section class="view on">` → visible, `<section class="view">` → hidden
2. **Sidebar click**: `onclick="go('dashboard')"` → removes `.on` from all views, adds to target
3. **Drawer**: `<aside class="drawer on">` → slides in from right
4. **Toast**: `showToast('message')` → animates from bottom
5. **Data load**: `Promise.allSettled` fires all API fetches in parallel, renders active view

## CSS Variables (Professional Dark Theme)

```
--bg:#0a0d12, --bg2:#11151c, --bg3:#161b24, --bg4:#1c2330
--line:rgba(255,255,255,.07), --line2:rgba(255,255,255,.14)
--tx:#e7ecf3, --tx2:#95a2b6, --tx3:#5d6878
--teal:#2dd4bf, --violet:#a78bfa, --amber:#fbbf24
--green:#34d399, --red:#f87171, --blue:#60a5fa
```

## Dependencies

- Tabler Icons CDN: `https://cdnjs.cloudflare.com/ajax/libs/tabler-icons/3.30.0/tabler-icons.min.css`
- Google Fonts: Sora, Manrope, IBM Plex Mono
