# FastAPI Middleware Gzip Pitfall + UAT State Contamination

## Gzip Middleware 500 on Starlette memoryview

### Symptom
All POST endpoints return `500 Internal Server Error` when the client sends `Accept-Encoding: gzip`. The same endpoints return 200 without gzip. Replacing the response body with gzip-compressed bytes fails silently.

### Root Cause
Starlette's `response.body` can be a `memoryview` object (not `bytes`). `gzip.compress(memoryview)` raises an unhandled exception that FastAPI converts to 500. The `memoryview` type appears when responses are built from certain Starlette internals (streaming, file responses, etc.).

### Reproduction
```bash
# Returns 500
curl -s -H "Accept-Encoding: gzip" -X POST http://127.0.0.1:8000/api/auth/wechat \
  -H "Content-Type: application/json" -d '{"code":"test"}'

# Returns 200
curl -s -H "Accept-Encoding: identity" -X POST http://127.0.0.1:8000/api/auth/wechat \
  -H "Content-Type: application/json" -d '{"code":"test"}'
```

### Fix Options

**Option A: Wrap in try/except (safe, keeps compression)**
```python
if "gzip" in accept_encoding and response.body:
    try:
        body = response.body
        if isinstance(body, memoryview):
            body = bytes(body)
        elif isinstance(body, str):
            body = body.encode()
        compressed = gzip.compress(body, compresslevel=6)
        if len(compressed) < len(body):
            response.headers["Content-Encoding"] = "gzip"
            response.headers["Content-Length"] = str(len(compressed))
            response.body = compressed
    except Exception:
        pass  # Fail silently, serve uncompressed
```

**Option B: Disable middleware gzip entirely (simplest)**
Comment out the gzip block. Let nginx/CDN handle compression in production.

### Detection
```bash
# Test with and without gzip header
for enc in "identity" "gzip"; do
  echo "=== Accept-Encoding: $enc ==="
  curl -s -w "HTTP %{http_code}\n" -H "Accept-Encoding: $enc" \
    -X POST http://127.0.0.1:8000/api/auth/wechat \
    -H "Content-Type: application/json" -d '{"code":"test"}'
done
```

## UAT State Contamination — Unique Test Codes

### Symptom
UAT tests that worked in isolation fail when re-run because previous test runs left database state (claimed milestones, consumed daily limits, existing users with the same mock code).

### Root Cause
WeChat mock login uses `code` as the unique identifier. When two test runs use the same code (e.g., `"uat_milestone"`), they retrieve the SAME user from the database, inheriting state from the first run.

### Fix: Timestamp-Unique Codes
```python
import time
TS = str(int(time.time()))
code = f"uat_{TS}_testname"  # e.g., "uat_1781032000_loyalty"
```

### Safe Request Wrapper
```python
def safe_req(fn, *args, **kwargs):
    """Call fn, return (ok: bool, result_or_error_body: str)"""
    try:
        return (True, fn(*args, **kwargs))
    except urllib.error.HTTPError as e:
        return (False, f"HTTP {e.code}: {e.read().decode()[:200]}")
```

### Affected Tests
- Milestone tests: claim is idempotent per user — repeat calls return None (correct) but test asserts for reward presence
- Earn tests: daily limits persist across runs — second run hits "已达上限"
- Redeem tests: monthly limits, balance depletion
- Catalog tests: pricing varies by user level (discount), which changes during test

## SQL Subquery Without Parent Record — 500 Pattern

### Symptom
`Internal Server Error` when a function uses `(SELECT column FROM parent_table WHERE id=?)` as a subquery value, but the parent record doesn't exist yet.

### Example (loyalty_engine.py)
```python
# ❌ BROKEN — user_points may not exist yet
c.execute(
    "INSERT INTO points_history(user_id, action, amount, balance_after, created_at, meta) "
    "VALUES(?, 'milestone', 0, (SELECT balance FROM user_points WHERE user_id=?), ?, ?)",
    (user_id, user_id, now, meta_json),
)
```

### Fix: Ensure Parent Record First
```python
# ✅ Call _get_or_create_points before executing subquery
_get_or_create_points(user_id)
```

### Detection
```bash
# Check for users with user_tiers but no user_points
sqlite3 users.db "
SELECT u.user_id FROM user_tiers u 
LEFT JOIN user_points p ON u.user_id = p.user_id 
WHERE p.user_id IS NULL
"
```
