---
name: command-center-dashboard
description: Build multi-view SPA command center dashboards for multi-agent systems — fleet cards, board management, approval queues, single-file HTML pattern.
version: 1.0.0
author: frontend-dev
metadata:
  hermes:
    tags: [frontend, dashboard, agent-monitoring, spa, flask]
    related_skills: [writing-plans, subagent-driven-development]
---

# Command Center Dashboard Development

## Overview

Build and extend multi-view single-page-application (SPA) dashboards for multi-agent orchestration systems. The target is a single HTML file with embedded CSS + JS that connects to a Flask backend (`/api/*` endpoints). Pattern proven on the Apex Command Center (`/cc`).

## When to Use

- Building or extending a real-time agent monitoring dashboard
- Adding fleet/agent status cards with live data
- Implementing board management (human + agent role assignment)
- Adding approval queues with approve/reject actions
- Creating multi-view navigation with drawers and modals

## Architecture Pattern

### Single-File SPA Structure

```
<style>...</style>        # All CSS rules
<html>...</html>          # All HTML views
  .side                  # Sidebar navigation
  .main > .scroll        # View sections (one per page)
  #chat / #agentDrawer   # Drawers (slide-in panels)
  #hireModal / #boardModal # Modals (centered dialogs)
  #scrim                 # Backdrop overlay
<script>...</script>      # All JS logic
```

### CSS Variable System

```css
:root {
  --bg:#0a0d12; --bg2:#11151c; --bg3:#161b24; --bg4:#1c2330;
  --line:rgba(255,255,255,.07); --line2:rgba(255,255,255,.14);
  --tx:#e7ecf3; --tx2:#95a2b6; --tx3:#5d6878;
  --teal:#2dd4bf; --violet:#a78bfa; --amber:#fbbf24;
  --green:#34d399; --red:#f87171; --blue:#60a5fa;
  --r:10px; --r-s:7px; --r-l:14px;
}
```

Use `var(--teal-d)` for dark backgrounds and `var(--teal)` for text/accents. Every color has a `-d` (dark) variant for backgrounds.

### View Navigation Pattern

```javascript
const VIEW_TITLES = { dashboard:['指挥中心','Dashboard'], ... };

function go(v) {
  state.view = v;
  $$('.nav').forEach(n => n.classList.toggle('on', n.dataset.view === v));
  $$('.view').forEach(s => s.classList.remove('on'));
  $('#v-'+v).classList.add('on');
  $('#crumb').innerHTML = VIEW_TITLES[v][0] + ' <span>· '+VIEW_TITLES[v][1]+'</span>';
  renderActiveView();
}
```

## Fleet Agent Card Pattern

### Data Source Combination

Combine three data sources into a unified agent card array:

1. **Hermes live sessions** (`/api/live/runtime` → `rt.sessions[]`) — running processes with tokens/cost/runtime
2. **Apex profiles** (`/api/profiles`) — configured agents with roles/skills
3. **Hermes profiles** (`/api/fleet/profiles/list`) — fleet configurations with SOUL/config status

Cross-reference Apex profiles with workloads (`/api/ops/agents/workloads`) and tasks (`/api/tasks`) for load/task breakdown.

### Card Fields per Agent Type

| Field | Hermes Session | Apex Profile | Hermes Profile |
|-------|---------------|-------------|----------------|
| Status dot | 🟢 running | 🟢/⚪ based on load | ⚪ configured |
| Load bar | tokens/10k % | workload.load_pct % | N/A |
| Task queue | tokens count | done/running/pending/blocked | N/A |
| Can accept | load < 50% | load < 70% + no blocked | always true |
| Skills chips | model name | profile.skills[] | N/A |
| Meta line | runtime + cost | -- | SOUL/config status |

### Card HTML Structure

```html
<div class="fleet-card" onclick="openAgent(...)">
  <div class="fcan">{可接单|忙碌}</div>
  <div class="fh">
    <span class="fstatus" style="background:{dotColor}"></span>
    <div>
      <div class="fname">{name}</div>
      <div class="frole">{role tag} · {model}</div>
    </div>
  </div>
  <div class="fbar"><i style="width:{load}%;background:{color}"></i></div>
  <div class="fmeta">{stats}</div>
  <div class="ftasks">{task breakdown}</div>
  {skills chips}
</div>
```

## Board Management Pattern

### State Structure

```javascript
state.board = {
  humans: [{ id, name, role, init }],
  ceoAgent: 'ceo',
  authAgent: 'auth',
  auditAgent: 'audit'
};
```

### Sidebar Crew Rendering

Priority order: Board humans → Core agents (CEO/Auth/Audit) → Active sessions.

### Board Manager Modal

Two-panel layout:
- Left: Human board members (add/remove with inline inputs)
- Right: Core agent role selectors (dropdown from all known agent names)

All agent names sourced from `[...fleetProfiles.map(p=>p.name), ...apexProfiles.map(p=>p.name), ...reserved]`.

## Approval Queue Pattern

```javascript
// Approval queue with approve/reject buttons
stats.pending_items.forEach(item => `
  <div class="card">
    <div class="ic" style="background:var(--amber-d);color:var(--amber)">
      <i class="ti ti-gavel"></i>
    </div>
    <div>${item.title} / ${item.reason}</div>
    <button class="btn sm danger" onclick="rejectRequest('${id}')">驳回</button>
    <button class="btn sm primary" onclick="approveRequest('${id}')">批准</button>
  </div>
`);
```

Attempt API calls (`/api/auth/approve/{id}`, `/api/auth/reject/{id}`) but degrade gracefully if endpoints are unavailable.

## Chat Decomposition Engine

Keyword-based NLP routing to generate task DAGs:

```javascript
function decomposeGoal(goal) {
  if (/成本|预算/.test(goal)) → cost optimization plan (4 steps)
  if (/代码|开发/.test(goal)) → dev plan (4 steps)
  if (/客服/.test(goal)) → support plan (4 steps)
  else → growth plan (4 steps)
  // Each step: { n, a (assignee), t (task), gate (optional) }
  // Render as .plan > .step with gate tags
}
```

"Apply plan" button creates tasks via `POST /api/tasks`.

## Verification Checklist

After making changes to the dashboard:

1. `wc -l command_center.html` — file should grow linearly
2. `grep -c '<script>'` and `grep -c '</script>'` — each must be exactly 1
3. `grep -c '<style>'` and `grep -c '</style>'` — each must be exactly 1
4. Start server: `python -m apex dashboard --port 8080`
5. `curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/cc` → must return 200
6. Browser: navigate, click each nav item, check console for JS errors
7. Browser test: open board manager, add human, save → verify sidebar update

## Data Seeding Patterns

### Apex REST API vs CLI Demo

`apex demo` seeds **Hermes-layer** data (profiles in `~/.hermes/profiles/`). Apex REST API reads **Apex-layer** storage (`~/.apex/`). They are separate. To seed Apex dashboard data, POST directly:

```bash
# Create profiles
curl -X POST http://localhost:8080/api/profiles \
  -H 'Content-Type: application/json' \
  -d '{"name":"frontend-dev","role":"Frontend Developer","skills":["react","typescript"],"model":"deepseek-v4-pro"}'

# Create tasks (project name in [brackets] for auto-discovery)
curl -X POST http://localhost:8080/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"[羽球宝AI] 用户注册页面","assignee":"frontend-dev","priority":1}'

# Update task status
curl -X PUT http://localhost:8080/api/tasks/<task_id> \
  -H 'Content-Type: application/json' \
  -d '{"status":"in_progress"}'
```

**Live projects** are auto-discovered from task titles matching `[ProjectName] pattern. No separate project creation needed.

### Knowledge Graph Seeding

```bash
curl -X POST http://localhost:8080/api/knowledge \
  -H 'Content-Type: application/json' \
  -d '{"action":"learn","entity":"羽毛球AI助手","source":"seed"}'
```

### Fleet Teams

Teams file: `~/.hermes/fleet_teams.json`. Path depends on `HERMES_HOME` env var — the Flask server inherits its environment. Verify with:
```bash
curl -s http://localhost:8080/api/fleet/teams/list | python3 -c "import sys,json;d=json.load(sys.stdin);print(len(d.get('teams',{})))"
```

### Parallel Subagent Seeding

For filling multiple backend data gaps simultaneously, delegate 3 parallel workers:
1. **Profiles + Tasks**: POST `/api/profiles` ×N + `/api/tasks` ×M + PUT status updates
2. **Knowledge + Autonomous**: POST `/api/knowledge` + `apex autonomous start`
3. **Fleet Teams**: Write `fleet_teams.json` directly

## Pitfalls

- **CRITICAL: workloads API returns object, not array**: `/api/ops/agents/workloads` returns `{agents: [...], summary: {}, total_active_tasks: 0, total_agents: 0}` — NOT a bare array. Calling `.filter()` or `.length` on this object causes silent failure (no console error, blank fleet grid). **Always unpack:** `const wl = (data.workloads?.agents) || (Array.isArray(data.workloads) ? data.workloads : []);`. Apply this in `renderFleet()`, `renderReclamation()`, and `loadProjectView()`.
- **Patch order matters**: Add CSS before HTML before JS. New JS functions referencing DOM elements must come after those elements exist in the file.
- **Quote escaping in template literals**: When embedding data attributes with JSON in onclick handlers, escape single quotes with `&#39;` and double quotes with `&quot;`.
- **closeAll must handle modals**: `$$('.modal').forEach(m => m.classList.remove('on'))` in addition to drawers.
- **State must be initialized**: New state properties (like `state.board`) must be added to the initial state object or render functions will see `undefined`.
- **Data source fallbacks**: Always check `if (sessions.length)` before rendering; fall back to `state.data` arrays.
- **Non-critical API failures should not block rendering**: Use `.catch(() => {})` on optional API calls and show fallback UI.
- **Apex CLI `demo` does not fill Apex REST data**: `demo` creates Hermes profiles and a few demo tasks in a separate DB. Use REST API POSTs to populate the dashboard-visible data.
