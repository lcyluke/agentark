# API Data Shape Pitfalls — Frontend-Backend Integration

## Critical Pattern: Object-vs-Array

The `/api/ops/agents/workloads` endpoint returned `{agents:[], summary:{}}` but the frontend
assumed `[]`. This caused `.filter()` to crash silently, leaving entire views empty.

### Root Cause
Apex backend stores workloads as a dict with nested `agents` key for grouping + summary stats.
The frontend expected a flat array. Mismatched assumptions across subagent boundaries.

### Fix Pattern
Always normalize at the usage site:
```javascript
// Before: crash-prone — assumes array, crashes on object
const workloads = data.workloads || [];

// After: defensive normalization
const workloads = (data.workloads?.agents) || (Array.isArray(data.workloads) ? data.workloads : []);
```

### Detection
When a fleet view renders 0 cards but the API returns 200:
1. Check `typeof state.data.workloads` in browser console
2. Check `Array.isArray(state.data.workloads)`
3. If it's an object, find whether data is in `.agents`, `.items`, `.data`, etc.

### All Known Offenders in Apex Dashboard
| API | Frontend Expected | Actual (from backend) | Fix |
|-----|-------------------|----------------------|-----|
| `/api/ops/agents/workloads` | `[...]` | `{agents:[...], summary:{}}` | `.agents \|\| []` |
| `/api/fleet/teams/list` | `[...]` | `{teams:{...}}` | `.teams \|\| {}` |

### Verification Command
```bash
curl -s http://localhost:8080/api/ops/agents/workloads | python3 -c "
import sys,json; d=json.load(sys.stdin)
print('TYPE:', type(d).__name__, '→ OK' if isinstance(d,list) else '⏚ OBJECT → check .agents')
if isinstance(d,dict): print('KEYS:', list(d.keys()))"
```
