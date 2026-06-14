# Apex Command Center v6 — Architecture & Dev Patterns

> Built: 2026-06-07 | 3794 lines | Single-file HTML | 40+ API endpoints

## Dashboard UX Paradigm: "总分 + 点击弹窗编辑"

Every view follows the same pattern:
1. **Summary** (总): KPI cards + compact list at the top
2. **Click** (点击): Click any item → right-side Drawer slides in
3. **Edit** (弹窗编辑): Drawer contains full detail + editable form + Save/Cancel/Delete buttons

## Architecture

```
Single-page HTML (3794 lines)
  Sidebar (230px) + 14 views + Drawer + AI Chat
  All data from REST APIs (localhost:8080)
  Auto-refresh: runtime every 15s, full data every 30s
```

## 14 Views

| View | Key API | Drawer Editing |
|------|---------|---------------|
| 指挥中心 | /api/command-center | — |
| 项目作战室 | /api/projects/:name | Goal+Modules+Sub-functions |
| 审批审计 | /api/audit/queue | Approve/Reject buttons |
| Pipeline | /api/pipeline/:project | Move task status |
| AI舰队 | /api/fleet/profiles/list | SOUL+Config+Model edit |
| 自治引擎 | /api/autonomous | L0-L3 config |
| 知识图谱 | /api/knowledge | Skill distribution |
| 数据流时序 | /api/flow/timeline | Project flow |
| 模块市场 | /api/modules | Template edit |
| SKILL进化 | /api/skills/leaderboard | XP award |
| 成本中心 | /api/command-center | — |
| 系统状态 | /api/environment | — |
| GPU资源 | /api/gpu/status | — |

## Design Tokens

```css
/* Dark theme (default) */
--bg:#0a0d12; --bg2:#11151c; --bg3:#161b24; --bg4:#1c2330;
--teal:#2dd4bf; --violet:#a78bfa; --amber:#fbbf24; --green:#34d399; --red:#f87171; --blue:#60a5fa;
--r:10px; --r-s:7px; --r-l:14px;
--sp-xs:4px; --sp-sm:8px; --sp-md:14px; --sp-lg:20px; --sp-xl:28px;
--sh-sm/md/lg; --tr-fast/base/slow;
--disp:'Sora'; --body:'Manrope'; --mono:'IBM Plex Mono';

/* Light theme: [data-theme="light"] */
--bg:#f8fafc; --bg2:#ffffff; --bg3:#f1f5f9; --bg4:#e2e8f0;
```

## Key Pitfalls

1. **Flask template caching**: Must restart server after HTML edit
2. **Canvas API: NO CSS variables** — use hex colors only
3. **el() helper: must handle numbers** — convert to textContent, don't .forEach()
4. **Subagent HTML escaping**: Over-escaped JS strings (\\\\\\\" → \") need fix with `node -e`
5. **Flask route collision**: /api/items (list) vs /api/items/<name> (detail) — use /api/items/list
6. **Route dedup**: Never have two @app.route("/cc") — Flask won't warn but will fail silently

## Startup Pattern

```bash
lsof -ti :8080 | xargs kill -9 2>/dev/null; sleep 1
cd ~/Desktop/2026AIAPP/Apex && source .venv/bin/activate
python3 -c "from apex.interface.web import run_dashboard; run_dashboard(port=8080)" &
```

## URL Convention

Single entry point: `http://localhost:8080/` (root path, no aliases)
All legacy routes (/v4, /v5, /cc, /cost) deleted.
