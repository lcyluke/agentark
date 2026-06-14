# Sprint Pipeline Pattern — MVP Closed-Loop Development

> Reference for `hermes-multi-agent-orchestration` skill.
> Captured 2026-06-04 from the Sprint Pipeline feature build.

## Pattern Summary

A 5-phase state machine that drives an MVP from idea to iteration, with exactly 2 human approval gates.

```
📝 PLAN ──👤 设计审批 ──→ ⚙️ BUILD ──🤖──→ 🧪 VERIFY ──👤 发版审批 ──→ 🚀 SHIP ──🤖──→ 🔄 LEARN
```

## Design Rules (hard-won)

1. **5 phases is the sweet spot.** More = drag. Less = no sense of pipeline.
2. **Exactly 2 manual gates.** 设计审批 (PLAN→BUILD) and 发版审批 (VERIFY→SHIP). Every other gate auto-advances.
3. **Solo vs swarm is a mode, not a phase.** `--mode solo` = fullstack-dev alone. `--mode swarm` = frontend + backend with API contract.
4. **Dashboard visibility is mandatory.** Sprint progress must render on the main Dashboard (project war room view).
5. **Merge define+design into PLAN.** Don't separate PRD from tech design — architect reads PRD and produces API contract in one go.
6. **Merge feedback+iterate into LEARN.** User feedback IS the input to the next sprint iteration.

## Implementation Blueprint

### Core module: `apex/orchestration/sprint_pipeline.py`

```python
class SprintManager:
    def __init__(self, db_path=None)     # SQLite-backed
    def create(goal, mode="solo") -> Sprint
    def get(sprint_id) -> Sprint
    def complete_phase(id, hours, output) -> dict
    def approve(id) -> dict              # Manual gate
    def reject(id, reason) -> dict       # Manual gate
    def advance_auto(id) -> dict         # Auto gate
    def list_all(status=None) -> list[Sprint]
```

### Data model

```python
class Sprint:
    id, goal, mode, current_phase, iteration, status
    phases: list[PhaseRecord]
    progress_pct, total_hours, current_gate

class PhaseRecord:
    name, status, agent, hours_spent, output
    gate: "auto" | "manual"
    gate_status: "pending" | "approved" | "rejected"
    gate_name: str
```

### CLI commands

```bash
apex sprint create "goal" --mode solo|swarm
apex sprint status [id]
apex sprint approve [id]
apex sprint reject [id] --reason "..."
apex sprint complete [id] --hours N --output "..."
apex sprint list
```

### REST API (5 endpoints)

```
GET  /api/sprint/list
GET  /api/sprint/<id>
POST /api/sprint/create        {"goal": "...", "mode": "solo"}
POST /api/sprint/<id>/complete {"hours": 2.0, "output": "..."}
POST /api/sprint/<id>/approve
```

### Dashboard integration

Card in the "项目作战室" view. JS function `renderSprintCard()` fetches `/api/sprint/list` and renders progress bars, phase icons, and approval buttons.

### Tests

15 tests in `tests/test_sprint_pipeline.py` covering: create (solo/swarm), complete→approve, reject, auto-advance, manual-gate blocking, full 5-phase flow, list/filter, progress calculation, gate detection, phase constants.

## Pitfalls

1. **Manual gate blocks auto-advance even before phase is done.** `advance_auto()` checks gate type first — if manual, it returns "waiting for approval" regardless of phase status.
2. **DB path must be configurable for tests.** SprintManager takes optional `db_path` parameter; tests use `tmp_path`.
3. **PhaseConstants must stay in sync with PHASE_META.** Tests verify that all phases have metadata and exactly 2 manual / 3 auto gates.
