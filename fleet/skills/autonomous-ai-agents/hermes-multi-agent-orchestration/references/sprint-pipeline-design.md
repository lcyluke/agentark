# Sprint Pipeline — MVP Closed-Loop Development in Apex

> **Added:** 2026-06-04  
> **Status:** Implemented, tested (15/15 pass)

## Overview

Sprint Pipeline is Apex's built-in end-to-end MVP development pipeline. One command starts a sprint, two manual gates require user approval, everything else auto-advances via AI agents.

## Architecture

```
📝 PLAN ──👤 design-approval ──→ ⚙️ BUILD ──🤖──→ 🧪 VERIFY ──👤 ship-approval ──→ 🚀 SHIP ──🤖──→ 🔄 LEARN
```

5 phases, 2 manual gates (design + ship), 3 auto gates (build→verify→learn).

### Dual Mode

| Mode | Agent(s) | Use Case | API Contract |
|:-----|:---------|:---------|:------------|
| **solo** | fullstack-dev ×1 | Simple CRUD, single page | ❌ |
| **swarm** | frontend-dev + backend-dev ×2 | Multi-page, complex API | ✅ OpenAPI 3.0 |

## Implementation Files

| File | Purpose |
|:-----|:--------|
| `apex/orchestration/sprint_pipeline.py` | Core state machine + SQLite storage |
| `apex/cli/commands/sprint.py` | CLI rendering |
| `apex/interface/web.py` | 5 REST API endpoints |
| `apex/interface/templates/command_center.html` | Dashboard Sprint card |
| `tests/test_sprint_pipeline.py` | 15 unit tests |

## CLI Commands

```bash
apex sprint create "User Login MVP" --mode solo|swarm
apex sprint status [id]
apex sprint approve [id]    # Approve current manual gate
apex sprint reject [id] --reason "..."
apex sprint complete [id] --hours 2.0 --output "summary"
apex sprint list
```

## API Endpoints

```
GET  /api/sprint/list          — All sprints
GET  /api/sprint/<id>          — Sprint detail with phases, progress%, gate status
POST /api/sprint/create        — {goal, mode} → new sprint
POST /api/sprint/<id>/complete — {hours, output} → complete phase + auto-advance if possible
POST /api/sprint/<id>/approve  — Approve manual gate
```

## Design Decisions

### Why 5 phases (not 7)?
DEFINE+DESIGN merged into PLAN. FEEDBACK+ITERATE merged into LEARN. Reduces friction while keeping the sense of progress.

### Why only 2 manual gates?
User-specified: design approval (PLAN→BUILD) and ship approval (VERIFY→SHIP). These are the only two decisions that truly need human judgment. Everything else is mechanical and can be auto-gated.

### Why solo/swarm modes?
Simple MVPs don't need API contracts or frontend-backend separation. A fullstack agent is faster. Complex MVPs need the contract to keep frontend and backend aligned while working in parallel.

## Testing Pattern

```python
def test_full_pipeline_flow(self, tmp_path):
    mgr = SprintManager(db_path=tmp_path / "sprints.db")
    sprint = mgr.create("Full flow")
    
    # Plan → approve → build → auto → verify → auto → ship → approve → learn → auto → done
    mgr.complete_phase(sprint.id, hours=1); mgr.approve(sprint.id)       # plan done
    mgr.complete_phase(sprint.id, hours=4); mgr.advance_auto(sprint.id) # build done
    mgr.complete_phase(sprint.id, hours=1); mgr.advance_auto(sprint.id) # verify done
    mgr.complete_phase(sprint.id, hours=0.5); mgr.approve(sprint.id)     # ship done
    mgr.complete_phase(sprint.id, hours=1); mgr.advance_auto(sprint.id) # learn done
    
    assert sprint.status == "completed"
    assert sprint.total_hours == 7.5
```
