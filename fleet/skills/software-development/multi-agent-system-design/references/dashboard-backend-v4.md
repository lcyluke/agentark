# Dashboard Backend Architecture (v4)

## Overview

Apex Dashboard v4 serves as the unified backend for Dashboard frontend (another agent's work), Hermes Agent integration, and OpenClaw integration. 39 REST endpoints + 2 SSE streams.

## Module Layout

```
apex/interface/
├── web.py                 # Flask app factory, 39 routes
├── middleware.py           # CORS, auth (X-API-Key), error handlers, request logging
├── event_stream.py         # In-memory pub/sub for SSE/WebSocket
├── hermes_bridge.py        # Hermes state.db queries (sessions, tokens, GPU, pricing)
├── openclaw_bridge.py      # 6 consumable tools + 4 workflows
└── templates/
    ├── dashboard.html      # Original dark theme SPA
    └── dashboard_v4.html   # Enhanced v4 (if present)
```

## Endpoint Categories

| Group | Count | Prefix |
|-------|-------|--------|
| System | 5 | `/api/health`, `/api/version`, `/api/config`, `/api/status`, `/api/environment` |
| Profiles | 4 | `/api/profiles` (CRUD) |
| Tasks (Kanban) | 5 | `/api/tasks` (CRUD) |
| Execution | 2 | `/api/run`, `/api/run/swarm` |
| Intelligence | 5 | `/api/knowledge` (GET/POST), `/api/evolution`, `/api/economy` |
| Analytics | 2 | `/api/analytics/costs`, `/api/analytics/executions` |
| Operations | 5 | `/api/ops`, `/api/companies`, `/api/autonomous`, `/api/gpu/status`, `/api/models/pricing` |
| Hermes | 3 | `/api/hermes/status`, `/api/hermes/tokens`, `/api/command-center` |
| OpenClaw | 4 | `/api/openclaw/status`, `/api/openclaw/tools`, `/api/openclaw/run`, `/api/openclaw/workflows` |
| Task Manager | 9 | `/api/taskmgr/create`, `/api/taskmgr/list`, `/api/taskmgr/<id>`, etc. |
| Help System | 3 | `/api/help/request`, `/api/help/approve`, `/api/capacity` |
| Streaming | 5 | `/api/stream/logs`, `/api/stream/events`, `/api/logs`, `/api/events`, `/api/ping` |

Total: **~50 endpoints** (39 original + 11 from Task Mgr + Help + Capacity)

## Middleware

### CORS
- Added to all responses via `@app.after_request`
- All origins allowed by default (configurable via `cors_headers()`)
- OPTIONS preflights handled via `@app.before_request`

### Auth
- Optional `X-API-Key` header check via `require_api_key()` decorator
- Disabled when `APEX_API_KEY` env var is not set

### Error Handlers
- 400, 404, 500 → JSON responses with `{"error": "...", "detail": "..."}`

### Request Logging
- `@request_logger` decorator logs method, path, HTTP code, duration in ms
- Logs pushed to `middleware.LOG_BUFFER` (consumed by SSE stream)

## Event Stream

In-memory pub/sub system (`event_stream.py`):
- `push_event(type, data)` — pushes to subscribers and buffer
- `subscribe(type, callback)` — returns unsubscribe function
- `get_recent_events(limit=N, type=T)` — readback
- SSE: `format_sse(event)` — formats as `event: type\ndata: {...}\n\n`

## SSE Endpoints

- `/api/stream/logs` — real-time log entries (polling every 1s)
- `/api/stream/events` — all system events (polling every 0.5s)
- Both use Flask `stream_with_context` with `Response(mimetype="text/event-stream")`

## Key Implementation Patterns

### Flask app factory
```python
def create_app():
    app = Flask(__name__)
    register_error_handlers(app)
    # ... route definitions ...
    app._start_time = time.time()
    return app
```

### Request logging
```python
@app.route("/api/health")
@request_logger
def api_health():
    return jsonify({"status": "ok"})
```

### SSE generator pattern
```python
def generate():
    seen = set()
    yield "event: connected\ndata: {}\n\n"
    while True:
        for event in get_recent_events(limit=50):
            if id(event) not in seen:
                yield format_sse(event)
                seen.add(id(event))
        time.sleep(0.5)
return Response(stream_with_context(generate()), mimetype="text/event-stream")
```

## Cross-Origin Access

All endpoints include `Access-Control-Allow-Origin: *` so the frontend (on any port) can call them freely.

## Start

```python
from apex.interface.web import run_dashboard
run_dashboard(host="127.0.0.1", port=8080)
```
