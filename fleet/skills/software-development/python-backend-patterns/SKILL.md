---
name: python-backend-patterns
description: "FastAPI/Starlette patterns: route ordering, form parsing, numpy serialization, SQLite migration, and service-provider marketplace architecture."
version: 1.2.0
metadata:
  hermes:
    tags: [fastapi, sqlite, numpy, api, backend, patterns]
    pitfall_count: 9
    pattern_count: 3
---

# Python Backend Patterns

Hard-won FastAPI/Starlette patterns from building production APIs. NOT project-specific — reusable across any Python backend.

## Triggers

- Building or extending a FastAPI/Starlette backend
- Debugging 422/500 errors on FastAPI endpoints
- Adding routes with path parameters alongside static routes
- Working with ML/numpy data in FastAPI JSON responses
- Evolving a live SQLite schema shared across multiple modules

## Pitfall 1: Route Ordering — Static Before Parameterized

FastAPI matches routes in definition order. A path parameter like `{id}` captures ANY segment — including static route names like `bookings`, `service-types`, `pricing`.

**Symptom**: `GET /api/assessor/service-types` returns `{"detail": "Input should be a valid integer, unable to parse string as an integer"}` — the `{assessor_id}` route is eating `service-types` as an ID.

```python
# ❌ WRONG — GET /coach/bookings → 422 (captured by {coach_id})
# ❌ WRONG — GET /assessor/service-types → int parsing error
@router.get("/coach/{coach_id}")
@router.get("/coach/bookings")

# ✅ RIGHT — static routes first, parameterized last
@router.get("/coach/bookings")    # 1. static
@router.get("/coach/booking")     # 2. static
@router.post("/coach/booking")    # 3. static POST
@router.get("/coach/{coach_id}")  # 4. parameterized — goes LAST
```

**Rule**: Every route with a path parameter goes AFTER all static routes under the same prefix. This includes POST endpoints — `POST /coach/booking` must come before `GET /coach/{id}` too.

**Checklist for new routers**: Before declaring `GET /prefix/{id}`, scan all routes to ensure every `GET /prefix/something-static` and `POST /prefix/something-static` comes first. If the wildcard is already somewhere in the middle, cut it out and paste it at the very end of the file.

## Pitfall 2: Form Parsing — `request.form()` vs `Form(...)`

Complex multipart POST endpoints with `Form(...)` parameters can get 422 "Input should be a valid dictionary" errors. Switch to manual parsing:

```python
# ❌ May break
@router.post("/booking")
def booking(
    provider_type: str = Form(...),
    provider_id: int = Form(...),
): ...

# ✅ Reliable — manual form parsing
from fastapi import Request  # must be imported

@router.post("/booking")
async def booking(request: Request):
    form = await request.form()
    provider_type = form.get("provider_type", "coach")
    provider_id = int(form.get("provider_id", 0))
```

Also add `Request` to the FastAPI import line.

## Pitfall 3: Numpy Serialization — `_to_native()` Converter

MediaPipe/PyTorch/NumPy produce scalar types (`np.float64`, `np.int32`, `np.bool_`) that FastAPI's `jsonable_encoder` cannot serialize, causing 500 errors with `"numpy.bool object is not iterable"`.

Solution — recursive converter, applied to every return value that touches numpy:

```python
def _to_native(obj):
    import numpy as np
    if isinstance(obj, (np.integer,)):    return int(obj)
    if isinstance(obj, (np.floating,)):   return float(obj)
    if isinstance(obj, (np.bool_,)):      return bool(obj)
    if isinstance(obj, np.ndarray):       return obj.tolist()
    if isinstance(obj, dict):             return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):    return [_to_native(v) for v in obj]
    return obj

# Use on return:
return _to_native({"score": score, "passed": passed, "detail": detail_dict})
```

Place `_to_native()` before the first endpoint that uses it. It handles nested dicts and lists automatically.

## Pitfall 5: FastAPI endpoint param drift — forward-compat pattern

When a function called from inside a FastAPI route handler evolves its signature (gains new kwargs), the route calling code doesn't get updated automatically. This causes `TypeError: _assess_video() got an unexpected keyword argument 'face_bbox'`.

**Pattern**: Use `**kwargs` passthrough for the internal function, and extract only the params you need:

```python
# The handler:
@router.post("/assess/evaluate-person")
async def evaluate_person(...):
    # Some processing...
    
    # Pass only what the inner function expects
    result = _assess_video(video_path, user_level=user_level, action_type=action_type)

# The inner function:
def _assess_video(video_path, **kwargs):
    user_level = kwargs.get("user_level", 5)
    action_type = kwargs.get("action_type", "smash")
    # ... implementation
```

Alternatively, if the handler constructs a kwargs dict, use explicit construction:
```python
assess_kwargs = {"action_type": action_type, "user_level": user_level}
if has_face_bbox:
    assess_kwargs["face_bbox"] = face_bbox  # only add if needed
```

But cleaner: keep the inner function signature stable and use a config dict or named params only.

## Pitfall 6: Backend restarts and OOM kills

FastAPI on local Mac (Apple M1 Pro, 16GB unified memory) can get OOM-killed (exit 137) after heavy MediaPipe processing tasks. MediaPipe's GL context + TFLite delegate uses ~2-3GB per inference.

**Mitigation**: 
- Always run the backend in background mode (not foreground): `terminal(background=true)`
- After restart, verify: `curl -s http://127.0.0.1:8000/api/avatar/skills`
- The backend process shows "Killed: 9" in logs on exit 137 — that's the OS reclaiming memory, not a Python crash

## Pitfall 4: SQLite Schema Migration — ALTER TABLE

```python
def init_tables():
    with _conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS training_progress (...)")

        # Compatibility: add columns that other modules expect
        existing = {row[1] for row in c.execute("PRAGMA table_info(training_progress)")}
        for col_name, col_def in [
            ("total_reps",     "INTEGER NOT NULL DEFAULT 0"),
            ("last_practiced", "INTEGER"),
        ]:
            if col_name not in existing:
                c.execute(f"ALTER TABLE training_progress ADD COLUMN {col_name} {col_def}")
```

Check which columns already exist before ALTER — `IF NOT EXISTS` does NOT work for columns in SQLite.

## Pitfall 7: SQLite `lastrowid` — Must Capture Cursor, Not Connection

`sqlite3.Connection.execute()` returns a **Cursor**, and `lastrowid` is a property of the Cursor, not the Connection. Accessing `conn.lastrowid` raises `AttributeError` or silently returns wrong data.

```python
# ❌ WRONG — c is the Connection, no lastrowid attribute
with _conn() as c:
    c.execute("INSERT INTO checkins (...) VALUES (...)", params)
    new_id = c.lastrowid  # AttributeError

# ✅ RIGHT — capture the Cursor from execute(), read lastrowid from it
with _conn() as c:
    cur = c.execute("INSERT INTO checkins (...) VALUES (...)", params)
    new_id = cur.lastrowid  # Returns the rowid of the last INSERT
```

This is a Python sqlite3 API design quirk — `Connection.execute()` is a convenience shortcut that creates and returns a cursor, but the cursor object is discarded if you don't capture it.

## Pitfall 9: Gzip Middleware — `memoryview` Body Crash (Starlette/Uvicorn)

When building custom middleware that reads and replaces `response.body`, Starlette may store the body as a `memoryview` instead of `bytes`. Calling `gzip.compress(memoryview)` raises a `TypeError` that FastAPI surfaces as a 500 with no body.

**Symptom**: API returns 200 in curl but 500 from browsers/WeChat DevTools. The difference: browsers send `Accept-Encoding: gzip`, which triggers the middleware.

```python
# ❌ BROKEN — gzip.compress fails on memoryview
class OptimizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" in accept_encoding and response.body:
            body = response.body
            if isinstance(body, str):
                body = body.encode()
            compressed = gzip.compress(body, compresslevel=6)  # TypeError if memoryview!
            if len(compressed) < len(body):
                response.body = compressed
                response.headers["Content-Encoding"] = "gzip"
```

**Fix A**: Wrap in try/except, convert `memoryview` to `bytes`:

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
        pass  # compression failure → serve uncompressed
```

**Fix B**: Disable middleware gzip — use Uvicorn's native `--proxy-headers` or a reverse proxy (nginx/Caddy) for compression.

**Debugging tip**: To test, send the same request with and without `Accept-Encoding: gzip`:
```bash
# 200 — no gzip trigger
curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8000/api/endpoint -d '{...}'

# 500 — gzip middleware crash
curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8000/api/endpoint \
  -H "Accept-Encoding: gzip" -d '{...}'
```
If the gzip variant returns 500 and the plain one doesn't, the middleware compression is the culprit.

## Pitfall 8: Module-Level Constants and Local Reassignment

Reassigning a module-level constant inside a function creates a **local variable** that shadows the module-level one. Any reference to the name BEFORE the reassignment raises `UnboundLocalError`, even if the module-level constant exists.

```python
# ❌ BROKEN — Python sees local assignment and treats all refs as local
_VENUE_CSV = "/path/to/venues.csv"

def load_venues():
    if not os.path.isfile(_VENUE_CSV):        # UnboundLocalError!
        alt = os.path.join(...)
        if os.path.isfile(alt):
            _VENUE_CSV = alt                  # This makes _VENUE_CSV local

# ✅ FIX A — use global (side-effect, less clean)
def load_venues():
    global _VENUE_CSV
    if not os.path.isfile(_VENUE_CSV):
        ...

# ✅ FIX B — use a local variable (clean, preferred)
def load_venues():
    csv_path = _VENUE_CSV                      # read module constant into local
    if not os.path.isfile(csv_path):
        alt = os.path.join(...)
        if os.path.isfile(alt):
            csv_path = alt                     # reassign local, not module
    with open(csv_path) as f:                  # use local throughout
        ...

## Pattern: Agent Runner Architecture

When building a backend that schedules multiple AI agents with consistent lifecycle (observe→reason→simulate→act), use a unified runner pattern:

```python
# ─── Cached agent instances + unified runner ───
_agent_cache: Dict[str, Any] = {}

def _run_agent(agent_name: str, agent_class, dry_run: bool = True, **kwargs) -> Dict:
    """Generic agent runner with instance caching."""
    if agent_name not in _agent_cache:
        _agent_cache[agent_name] = agent_class()
    
    agent = _agent_cache[agent_name]
    start = time.time()
    try:
        result = agent.run(dry_run=dry_run, **kwargs)
        elapsed = round(time.time() - start, 2)
        return {
            "agent": agent_name,
            "status": "success",
            "elapsed_seconds": elapsed,
            "result": result,
        }
    except Exception as e:
        return {
            "agent": agent_name,
            "status": "error",
            "elapsed_seconds": round(time.time() - start, 2),
            "error": str(e),
        }
```

Per-agent endpoints follow a uniform shape:
```python
@app.post("/api/agents/{name}/run")
def run_agent(req: AgentRunRequest):
    return _run_agent("name", AgentClass, dry_run=req.dry_run)
```

Dashboard aggregation with `run-all` scans all agents and tallies `total_monthly_savings` / `total_improvement_opportunity` from each result dict.

MCP interface: a separate `/mcp/tools` (list available tool names + descriptions) and `/mcp/call` (dispatch to agent by tool name) — useful for LLM-driven orchestration where an external model decides which agent to invoke.

## Pattern: Service Provider Marketplace

For coach/therapist/any-provider systems — build one, then copy-and-adapt. The API template works across all provider types:

```
POST /api/{type}/register         — provider applies (status=pending)
GET  /api/{type}/my               — their own profile + approval status
GET  /api/{type}s                 — public listing (approved only, paginated)
GET  /api/{type}/{id}             — detail view
GET  /api/admin/{type}s/pending   — admin review queue
POST /api/admin/{type}/{id}/review — admin approve/reject
POST /api/coach/booking           — unified booking (provider_type field)
GET  /api/coach/bookings          — user's bookings (joins provider name)
POST /api/coach/booking/{id}/cancel — cancel
```

Key design choices:
- Single `appointments` table with `provider_type` + `provider_id` columns (not separate booking tables per type)
- Admin auth via token set (upgrade to JWT roles in production)
- Phone number stripped from public responses: `row.pop("phone", None)`
- Duplicate-registration guard: `SELECT id FROM {table} WHERE user_id=?` before INSERT
- Provider name joined at query time in booking list, not stored redundantly
