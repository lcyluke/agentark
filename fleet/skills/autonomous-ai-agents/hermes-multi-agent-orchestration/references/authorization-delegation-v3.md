# Authorization Engine v3 — Delegation + Dual Approval + Audit Guardian

Built June 2026. Supersedes the v2 single-approver model.

## Core file

`~/Desktop/2026AIAPP/Apex/apex/orchestration/authorization.py` (~1200 lines)

## Architecture

```
                    ⚓ Origin (default) — AuthorizationEngine owner
                    │
    ┌───────────────┼─── Delegations ───────────┐
    │               │                           │
    ▼               ▼                           ▼
  apex-pm         badminton-pm                   content-marketing
  [project:apex:*] [project:badminton:*]    [project:shenzhen:*]
  7 scopes         7 scopes                 3 scopes
    │               │                           │
    │    audit-guardian (Origin's read-only clone)
    │    [audit:read:*, audit:verify:chain, audit:report:generate]
    │    Directly under Origin, cannot approve, only inspect
    │
    └── Approval boundaries ──┘
         project:* in-scope → PM single-approve ✅
         project:* out-of-scope → Origin pre-approve → target PM final-approve 🔒
         cross-project:* → Origin pre-approve → Origin final-approve 🔴
         system:* → Origin only 🔴
```

## Scope namespace

| Level | Class | Who approves |
|-------|-------|-------------|
| `project:{proj}:*` | Project-internal | PM (single approve) |
| `cross-project:*` | Cross-project | Origin pre → Origin final |
| `system:*` | System | Origin only |
| `audit:*` | Audit read-only | audit-guardian (self) |

## Delegation registry (in code, synced to DB)

```python
DELEGATIONS = {
    "apex-pm":          {"scopes": ["project:apex:*", "autodl:ssh:shutdown", "autodl:api:stop", ...]},
    "badminton-pm":          {"scopes": ["project:badminton:*", "autodl:ssh:shutdown", ...]},
    "content-marketing": {"scopes": ["project:shenzhen:*", "project:shenzhen:model:assign", ...]},
    "audit-guardian":   {"scopes": ["audit:read:*", "audit:verify:chain", "audit:report:generate"]},
}
```

Modify via `AuthorizationEngine.modify_delegation(delegator, delegate, scopes)` → persisted to `grants.db.delegations` table.

## Dual-approval flow

```
1. Agent.engine.request(agent, scope, purpose)
   → returns {"dual_auth_required": True/False, ...}

2. If dual needed:
   a. engine.origin_pre_approve(request_code) → status="origin_approved"
   b. engine.approve(request_code, approved_by=<final_approver>) → status="approved"

3. engine.check(agent, scope) → verify before executing

4. engine.consume(grant_id) → mark used (one-shot)
```

## Audit guardian profile

```
Profile: audit-guardian
SOUL.md: ~/.hermes/profiles/audit-guardian/SOUL.md
Role: Read-only inspector — verifies hash chain, scans grants.db, generates audit reports
AutonomousEngine task: "🔍 审计分身巡检" every 60m
Cannot: approve, modify delegations, execute system commands
```

## REST endpoints (18 total)

```
GET    /api/auth/scopes            — scope definitions
GET    /api/auth/stats             — grant statistics
GET    /api/auth/verify            — hash chain verification
POST   /api/auth/request           — request authorization
POST   /api/auth/approve           — approve (single or dual final)
POST   /api/auth/deny              — deny
GET    /api/auth/check?agent=&scope= — check if authorized
POST   /api/auth/consume           — mark grant as used
POST   /api/auth/revoke            — revoke grant
GET    /api/auth/grants            — list grants (filterable)
GET    /api/auth/audit             — audit log
GET    /api/auth/delegations       — delegation matrix
GET    /api/auth/delegations/list  — list delegation records
POST   /api/auth/delegations/modify — modify delegation (Origin only)
POST   /api/auth/delegations/revoke — revoke delegation (Origin only)
GET    /api/auth/delegations/check?delegate=&scope= — check scope
POST   /api/auth/origin-pre-approve — dual-auth step 1
```

## CLI wrapper

`~/.hermes/scripts/authorization_engine.py` — thin wrapper, delegates to `apex.orchestration.authorization.AuthorizationEngine`.

## Key pitfalls

- **Dual auth needed but never pre-approved**: `approve()` on a `pending` grant by a non-Origin PM will fail for out-of-scope scopes. Must call `origin_pre_approve()` first.
- **cross-project scopes require Origin for BOTH steps**: PM cannot final-approve `cross-project:*`. Only `default` / `luke`.
- **Delegation modifications are Origin-only**: `modify_delegation()` checks `delegator == "default"`.
- **audit-guardian cannot approve**: `can_approve("audit-guardian", "system:config:modify")` → False. It only approves `audit:*` scopes.
- **DB migration**: v3 automatically adds `origin_approved_by` and `origin_approved_at` columns to existing `grants` table on first init.
