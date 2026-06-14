# PM Agent 4-Stage Orchestration Pattern

## When to use

- Building a PM/Orchestrator agent that manages multiple sub-agents
- User says a project name with no additional context → they likely want the PM agent, not a full project rebuild
- Need a meta-agent that: collects data from N agents → synthesizes → prioritizes → issues governance actions

## The Pattern

```
Stage 1  🏴 SCOUT      — Run all sub-agents in sequence, collect reports
Stage 2  📊 SYNTHESIZE  — Aggregate results, fleet health score, risk register
Stage 3  🎯 STRATEGIZE  — Generate prioritized action items (immediate/week/evaluate)
Stage 4  ⚡ ACT         — Apply governance gates, issue instructions, save history
```

## Core Architecture

```python
class PMAgent:
    AGENT_REGISTRY = [
        ("agent_name", "emoji", AgentClass, "category"),
        ...
    ]

    def run(self, dry_run=True) -> dict:
        self.scout()        # Stage 1
        synthesis = self.synthesize()   # Stage 2
        self.strategize()   # Stage 3
        result = self.act(dry_run)      # Stage 4
        result["synthesis"] = synthesis
        result["agent_reports"] = [...] # standardized per-agent summary
        return result
```

## Report Parsing Adapter Pattern

Each sub-agent returns a different result shape. The PM must normalize them:

```python
def _parse_result(self, name: str, result: dict) -> tuple:
    """Return (findings_count, savings, risk_level, top_finding)"""
    # Per-agent parsing logic — each agent has different result shapes
    if name == "idle":
        findings = len([a for a in result if a.get("success")])
        savings = sum(a.get("estimated_savings", 0) for a in result)
        ...
    elif name == "token":
        opps = result.get("opportunities", [])
        savings = sum(o.get("monthly_saving_estimate", 0) for o in opps)
        ...
    return findings, savings, risk, top
```

## Fleet Health Scoring

```python
fleet_health = 100
fleet_health -= len(failed_agents) * 10           # -10 per failed agent
fleet_health -= 5 * warning_count                  # -5 per warning
fleet_health -= 15 * critical_count                # -15 per critical
fleet_health = max(fleet_health, 0)                # floor at 0

status = "🟢 全舰正常" if >= 90 else "🟡 需要关注" if >= 70 else "🔴 紧急干预"
```

## Action Prioritization

| Priority | Label | Criteria |
|----------|-------|----------|
| 1 | 🔴 立即执行 | Critical severity, active cost anomaly |
| 2 | 🟡 本周 | Warning severity, savings > $50 |
| 3 | 🟢 评估 | Low severity, small savings, needs more data |

## Four-Gate Governance

```
Gate 1 — Static Policy: OPA-style tag/role checks (auto-pass for low-risk)
Gate 2 — Business Impact: Simulate SLA/perf impact before executing
Gate 3 — Human Approval:  L1 ($50-500) / L2 ($500+) / auto (<$50)
Gate 4 — Canary Deploy:   Gradual rollout with auto-rollback
```

## Pitfalls

1. **Sub-agent `run()` signature incompatibility**: Some agents accept `dry_run`, others don't. Use `inspect.signature()` to detect:
```python
import inspect
sig = inspect.signature(agent.run)
if "dry_run" in sig.parameters:
    result = agent.run(dry_run=True)
else:
    result = agent.run()
```

2. **User says project name → means PM agent, not full rebuild**. When a user says "finopsai" or "badminton" with no other context, they mean "the PM agent for that project." Do NOT rebuild the entire project from scratch. Check if a PM agent / profile already exists first, then create one if not.

3. **Report normalization is critical**: Different agents return `list`, `dict`, or `str` results. Always wrap parsing in try/except and default to `(0, 0, "healthy", "")` on parse failure.

4. **Don't create actions for zero-savings findings**: Skip action items where `estimated_savings <= 0` unless there's a non-monetary risk (e.g., security, compliance).

## Verification

```bash
# PM agent should run all sub-agents without errors
python agents/finops_pm_agent.py
# Expected: 7 agents report, fleet health score, prioritized actions

# API endpoint should return structured JSON
curl -X POST http://localhost:3000/api/agents/pm/run \
  -H 'Content-Type: application/json' -d '{"dry_run": true}'
# Expected: {"agent":"finops-pm","status":"success","result":{...}}
```
