# Apex Dashboard Architecture — 7-Tab Command Center

## Evolution

| Version | Type | Data | Tabs |
|---|---|---|---|
| V3 | Single-page SPA | Synthetic/mock | 1 (scroll sections) |
| V4 | Single-page SPA | Real (APIs) | 1 (scroll sections) |
| V5 | Multi-tab SPA | Real (APIs) | 7 (show/hide panels) |

## V5 Architecture

```
┌──────────────────────────────────────────────────┐
│  ⚡ Apex Command Center                    Clock │
├──────────────────────────────────────────────────┤
│ 🏠HQ │ 🖥Fleet │ 🤖AI Fleet │ 📋Projects │ 🗂Tasks │ 🧠Knowledge │ 🔐Audit │
├──────────────────────────────────────────────────┤
│                                                  │
│  Current tab panel (others display:none)          │
│  Each panel has its own renderTabX() function     │
│                                                  │
└──────────────────────────────────────────────────┘
```

## Data Sources (all fetched in parallel on load)

| Endpoint | Used By | Contents |
|---|---|---|
| `/api/command-center` | Tabs 1,3,4,6 | Hermes sessions, cron, profiles, GPU, pricing |
| `/api/profiles` | Tabs 3,6 | Apex 23 agent profiles |
| `/api/tasks` | Tabs 4,5 | Kanban tasks |
| `/api/autonomous` | Tabs 1,3 | Engine status, heartbeats, alerts |
| `/api/ops` | Tab 5 | Bugs, releases, quality scores |
| `/api/knowledge` | Tab 6 | KG nodes, edges, distribution |
| `/api/environment` | Tab 2 | OS, Python, Hermes/Apex versions, tools |

## Key Implementation Patterns

### Tab Switching
- All 7 panels exist in HTML, only active tab visible
- Clicking nav tab: `display:block` on target, `display:none` on others
- Each tab has its own `renderTabX()` function called once data loads

### Data Loading
- Single `Promise.allSettled` fetches all 8 endpoints
- Results stored in `state` object
- `loadAll()` → `renderAll()` → per-tab rendering

### Canvas Safety
- Canvas API calls CANNOT use CSS variables (`var(--accent)`)
- Must use hex colors: `#3b82f6`, `#5a6f8a`, `#e8edf5`, etc.
- CSS variables in `style=` strings are fine

### el() Helper
- Must handle strings, numbers, and arrays
- Numbers → `textContent`, arrays → `forEach` append, else → `String()`

## Files

| File | Purpose |
|---|---|
| `apex/interface/hermes_bridge.py` | Data aggregation from Hermes state.db + monitor.db + config |
| `apex/interface/web.py` | Flask app with 21 routes (14 original + 7 new) |
| `apex/interface/templates/dashboard_v5.html` | 7-tab SPA, ~1500 lines |

## Access

```
http://localhost:8080/v5
```
