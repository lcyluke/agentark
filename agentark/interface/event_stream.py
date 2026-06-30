"""Apex — Event stream: in-memory pub/sub for WebSocket and SSE streaming."""

from __future__ import annotations

import json
import time
import threading
from typing import Callable

# ── In-memory event bus ─────────────────────────────────────────

_subscribers: dict[str, list[Callable]] = {}
_lock = threading.Lock()
_event_buffer: list[dict] = []
MAX_EVENTS = 500


def subscribe(event_type: str, callback: Callable) -> Callable:
    """Subscribe to an event type. Returns an unsubscribe function."""
    with _lock:
        if event_type not in _subscribers:
            _subscribers[event_type] = []
        _subscribers[event_type].append(callback)

    def unsubscribe():
        with _lock:
            if event_type in _subscribers and callback in _subscribers[event_type]:
                _subscribers[event_type].remove(callback)

    return unsubscribe


def push_event(event_type: str, data: dict) -> None:
    """Push an event to subscribers and buffer."""
    event = {
        "type": event_type,
        "data": data,
        "timestamp": time.time(),
    }

    # Buffer
    _event_buffer.append(event)
    if len(_event_buffer) > MAX_EVENTS:
        _event_buffer.pop(0)

    # Notify subscribers
    with _lock:
        callbacks = list(_subscribers.get(event_type, []))
        callbacks_all = list(_subscribers.get("*", []))

    for cb in callbacks + callbacks_all:
        try:
            cb(event)
        except Exception:
            pass


def get_recent_events(limit: int = 50, event_type: str = None) -> list[dict]:
    """Get recent events from buffer."""
    if event_type:
        return [e for e in _event_buffer[-limit:] if e["type"] == event_type]
    return list(_event_buffer[-limit:])


def clear() -> None:
    """Clear all events and subscribers."""
    with _lock:
        _event_buffer.clear()
        _subscribers.clear()


# ── SSE (Server-Sent Events) helpers ────────────────────────────

def format_sse(event: dict) -> str:
    """Format an event dict as SSE message."""
    lines = []
    if event.get("type"):
        lines.append(f"event: {event['type']}")
    lines.append(f"data: {json.dumps(event, default=str)}")
    lines.append("")
    return "\n".join(lines)


# ── WebSocket helpers ───────────────────────────────────────────

def format_ws(event: dict) -> str:
    """Format an event dict as WebSocket JSON message."""
    return json.dumps(event, default=str)
