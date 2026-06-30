"""Apex — Dashboard middleware: CORS, auth, error handling, request logging."""

from __future__ import annotations

import time
import functools
import os
from pathlib import Path


def cors_headers(response, origins: str = "*") -> None:
    """Add CORS headers to a Flask response."""
    response.headers["Access-Control-Allow-Origin"] = origins
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-API-Key"
    response.headers["Access-Control-Max-Age"] = "86400"


def handle_cors_preflight():
    """Return 200 for OPTIONS preflight requests."""
    import flask
    resp = flask.jsonify({"ok": True})
    cors_headers(resp)
    return resp


def require_api_key(api_key: str = None):
    """Decorator: require X-API-Key header matching configured key."""
    if api_key is None:
        api_key = os.environ.get("APEX_API_KEY", "")
    if not api_key:
        # No key configured — pass through
        return lambda f: f

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            import flask
            key = flask.request.headers.get("X-API-Key", "")
            if key != api_key:
                return flask.jsonify({"error": "Unauthorized"}), 401
            return f(*args, **kwargs)
        return wrapper
    return decorator


def request_logger(f):
    """Decorator: log request method, path, duration."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        import flask
        start = time.time()
        try:
            result = f(*args, **kwargs)
            duration = time.time() - start
            _log("api", f"{flask.request.method} {flask.request.path} -> 200 ({duration*1000:.0f}ms)")
            return result
        except Exception as e:
            duration = time.time() - start
            _log("error", f"{flask.request.method} {flask.request.path} -> {e} ({duration*1000:.0f}ms)")
            raise
    return wrapper


def register_error_handlers(app):
    """Register JSON error handlers for common HTTP codes."""
    @app.errorhandler(400)
    def bad_request(e):
        import flask
        resp = flask.jsonify({"error": "Bad request", "detail": str(e)})
        cors_headers(resp)
        return resp, 400

    @app.errorhandler(404)
    def not_found(e):
        import flask
        resp = flask.jsonify({"error": "Not found", "path": flask.request.path})
        cors_headers(resp)
        return resp, 404

    @app.errorhandler(500)
    def server_error(e):
        import flask
        resp = flask.jsonify({"error": "Internal server error"})
        cors_headers(resp)
        return resp, 500


def _log(level: str, message: str):
    """Log a message to the Apex event stream."""
    timestamp = time.strftime("%H:%M:%S")
    log_entry = {"level": level, "message": message, "time": timestamp}
    # Push to global event buffer if available
    try:
        from agentark.interface.event_stream import push_event
        push_event("log", log_entry)
    except (ImportError, Exception):
        pass  # Silently ignore if event_stream not available


# Log buffer for SSE streaming
LOG_BUFFER = []
MAX_LOG_BUFFER = 500


def log_event(level: str, message: str, source: str = "api"):
    """Write to the in-memory log buffer consumed by SSE."""
    entry = {
        "level": level,
        "message": message,
        "source": source,
        "time": time.time(),
    }
    LOG_BUFFER.append(entry)
    if len(LOG_BUFFER) > MAX_LOG_BUFFER:
        LOG_BUFFER.pop(0)

    # Also push to event stream
    try:
        from agentark.interface.event_stream import push_event
        push_event("log", entry)
    except (ImportError, Exception):
        pass


def get_log_buffer(limit: int = 100) -> list[dict]:
    """Get recent log entries."""
    return list(LOG_BUFFER[-limit:])
