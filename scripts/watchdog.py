#!/usr/bin/env python3
"""
Failover Watchdog — parsimo001 (GB10 Worker)
═══════════════════════════════════════════════
Monitors Mac-A heartbeat via GitHub fleet/nodes/.
If Mac-A (origin) is unreachable for >5 minutes, parsimo001 auto-promotes to primary.

Runs as a cron job on parsimo001 every 1 minute:
  */1 * * * * cd ~/Desktop/2026AIAPP/apex && python3 ~/watchdog.py

Architecture:
  1. git pull --rebase origin main   → fetch latest heartbeats
  2. Scan fleet/nodes/*.json         → find ALL origin nodes (role == "origin")
  3. Pick MOST RECENT origin         → handle hostname changes
  4. Calculate age: now - reported_at → CST timezone
  5. If age > 5min → promote self: update fleet.json role="origin"
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

FLEET_DIR = Path(os.path.expanduser("~/Desktop/2026AIAPP/apex/fleet"))
NODES_DIR = FLEET_DIR / "nodes"
FLEET_JSON = FLEET_DIR / "fleet.json"
THRESHOLD_MINUTES = 5
CST = timezone(timedelta(hours=8))
HOSTNAME = socket.gethostname()


def git_pull() -> bool:
    try:
        r = subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            cwd=FLEET_DIR.parent,
            capture_output=True, text=True, timeout=30
        )
        return r.returncode == 0
    except Exception:
        return False


def find_origins() -> list[dict]:
    origins = []
    if not NODES_DIR.exists():
        return origins
    for node_file in NODES_DIR.glob("*.json"):
        try:
            data = json.loads(node_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("role") == "origin":
            origins.append(data)
    origins.sort(key=lambda d: d.get("reported_at", ""), reverse=True)
    return origins


def parse_cst_time(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.astimezone(CST)
        elif "+" in ts or ts.count("-") > 2:
            return datetime.fromisoformat(ts).astimezone(CST)
        else:
            return datetime.fromisoformat(ts).replace(tzinfo=CST)
    except (ValueError, TypeError):
        return None


def check_origin_age(origin: dict) -> float | None:
    ts = (
        origin.get("reported_at")
        or origin.get("last_report")
        or origin.get("timestamp")
        or ""
    )
    dt = parse_cst_time(ts)
    if dt is None:
        return None
    now = datetime.now(CST)
    age = (now - dt).total_seconds() / 60.0
    return age


def promote_self_to_origin(reason: str) -> bool:
    try:
        if FLEET_JSON.exists():
            fleet = json.loads(FLEET_JSON.read_text())
        else:
            fleet = {}
        fleet["role"] = "origin"
        fleet["promoted_at"] = datetime.now(CST).isoformat()
        fleet["promoted_reason"] = reason
        fleet["machine_id"] = f"{HOSTNAME}-parsimo001"
        fleet["hostname"] = HOSTNAME
        fleet["fleet_name"] = "老卢舰队"
        FLEET_JSON.write_text(json.dumps(fleet, indent=2, ensure_ascii=False))
        return True
    except Exception as e:
        print(f"[ERROR] Failed to promote self: {e}", file=sys.stderr)
        return False


def main() -> int:
    pulled = git_pull()
    if not pulled:
        print("[WARN] git pull failed — using cached fleet data", file=sys.stderr)

    origins = find_origins()
    if not origins:
        print("[WARN] No origin nodes found in fleet/nodes/", file=sys.stderr)
        return 0

    latest_origin = origins[0]
    origin_name = latest_origin.get("machine_id", latest_origin.get("hostname", "unknown"))
    age = check_origin_age(latest_origin)

    if age is None:
        print(f"[WARN] Cannot parse origin '{origin_name}' timestamp", file=sys.stderr)
        return 0

    if age > THRESHOLD_MINUTES:
        reason = (
            f"Origin '{origin_name}' last seen {age:.1f} min ago "
            f"(threshold: {THRESHOLD_MINUTES} min)"
        )
        print(f"[FAILOVER] {reason}")
        promoted = promote_self_to_origin(reason)
        if promoted:
            print("[FAILOVER] Self-promoted to origin successfully")
        return 0 if promoted else 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
