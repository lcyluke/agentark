#!/usr/bin/env python3
"""
AgentArk Fleet Heartbeat — LAN + GitHub Dual-Channel Pulse
═══════════════════════════════════════════════════════════
Designed to run as a cron job every 1-5 minutes on every fleet Mac.

Flow:
  1. mDNS scan LAN for other AgentArk nodes
  2. SSH connectivity check to each peer
  3. Probe local resources (CPU/GPU/RAM/Disk)
  4. Write heartbeat to fleet/nodes/<machine_id>.json
  5. Git push to GitHub (best effort)
  6. If GitHub fails, LAN peers still see each other via mDNS

Usage:
  # Run once
  python3 scripts/fleet_heartbeat.py

  # As cron job (every 2 minutes)
  hermes cron create "every 2m" --name "Fleet心跳" \
    --script scripts/fleet_heartbeat.py --no-agent \
    --toolsets terminal
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ─── Config ────────────────────────────────────────────────
APEX_ROOT = Path(os.environ.get("AGENTARK_HOME", os.path.expanduser("~/.hermes")))
# Try multiple locations for the fleet config
FLEET_DIRS = [
    Path(__file__).resolve().parent.parent / "fleet",
    Path(os.path.expanduser("~/Desktop/2026workspace/agentark/fleet")),
    APEX_ROOT / "fleet",
]
FLEET_DIR = None
for d in FLEET_DIRS:
    if d.exists():
        FLEET_DIR = d
        break
if FLEET_DIR is None:
    FLEET_DIR = Path(os.path.expanduser("~/.apex/fleet"))
    FLEET_DIR.mkdir(parents=True, exist_ok=True)

NODES_DIR = FLEET_DIR / "nodes"
NODES_DIR.mkdir(parents=True, exist_ok=True)
SSH_TIMEOUT = 5
GPU_STATE_FILE = Path("/tmp/apex_gpu_state.json")


# ═══════════════════════════════════════════════════════════
# Identity
# ═══════════════════════════════════════════════════════════

def get_machine_id() -> str:
    hostname = socket.gethostname()
    try:
        user = os.getlogin()
    except Exception:
        user = os.environ.get("USER", "unknown")
    return f"{hostname}-{user}"


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ═══════════════════════════════════════════════════════════
# Resource Probe
# ═══════════════════════════════════════════════════════════

def probe_resources() -> dict:
    """Probe local system resources."""
    info = {
        "machine_id": get_machine_id(),
        "hostname": socket.gethostname(),
        "ip": get_local_ip(),
        "os": "macos" if os.uname().sysname == "Darwin" else "linux",
        "timestamp": datetime.now().isoformat(),
    }

    # CPU
    import multiprocessing
    info["cpu_cores"] = multiprocessing.cpu_count()
    try:
        import psutil
        info["cpu_usage_pct"] = psutil.cpu_percent(interval=1)
        vmem = psutil.virtual_memory()
        info["ram_total_mb"] = int(vmem.total / 1024 / 1024)
        info["ram_free_mb"] = int(vmem.available / 1024 / 1024)
    except ImportError:
        info["cpu_usage_pct"] = 0.0
        info["ram_total_mb"] = 0
        info["ram_free_mb"] = 0

    # Disk
    import shutil
    usage = shutil.disk_usage(os.path.expanduser("~"))
    info["disk_total_gb"] = round(usage.total / 1e9, 1)
    info["disk_free_gb"] = round(usage.free / 1e9, 1)

    # GPU
    try:
        r = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,name",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            lines = r.stdout.strip().split("\n")
            gpus = []
            for line in lines:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 5:
                    try:
                        gpus.append({
                            "name": parts[4],
                            "util_pct": float(parts[0]),
                            "mem_used_mb": int(parts[1]),
                            "mem_total_mb": int(parts[2]),
                            "temp_c": int(parts[3]),
                        })
                    except (ValueError, IndexError):
                        continue
            if gpus:
                utils = [g["util_pct"] for g in gpus]
                info["gpu"] = {
                    "gpu_count": len(gpus),
                    "gpu_names": [g["name"] for g in gpus],
                    "util_pct": round(sum(utils) / len(utils), 1),
                    "mem_used_mb": sum(g["mem_used_mb"] for g in gpus),
                    "mem_total_mb": sum(g["mem_total_mb"] for g in gpus),
                    "mem_pct": round(sum(g["mem_used_mb"] for g in gpus) / max(1, sum(g["mem_total_mb"] for g in gpus)) * 100, 1),
                    "temp_c": max(g["temp_c"] for g in gpus),
                }
    except (FileNotFoundError, Exception):
        pass

    # Fleet stats
    hermes_home = Path(os.path.expanduser("~/.hermes"))
    profiles_dir = hermes_home / "profiles"
    info["profiles"] = len([d for d in profiles_dir.iterdir() if d.is_dir()]) if profiles_dir.exists() else 0

    skills_dir = hermes_home / "skills"
    info["skills"] = len(list(skills_dir.rglob("SKILL.md"))) if skills_dir.exists() else 0

    return info


# ═══════════════════════════════════════════════════════════
# LAN Peers
# ═══════════════════════════════════════════════════════════

def discover_lan_peers(resources: dict) -> list[dict]:
    """Discover other AgentArk nodes on LAN via mDNS + SSH test."""
    peers = []

    try:
        from zeroconf import ServiceBrowser, Zeroconf
    except ImportError:
        return peers

    SERVICE_TYPE = "_agentark-fleet._tcp.local."
    found = {}
    zc = Zeroconf()

    class Listener:
        def add_service(self, zc, type_, name):
            try:
                info = zc.get_service_info(type_, name)
                if info is None:
                    return
            except Exception:
                return

            props = {}
            for k, v in info.properties.items():
                key = k.decode() if isinstance(k, bytes) else k
                val = v.decode() if isinstance(v, bytes) else (v or "")
                props[key] = val

            mid = props.get("machine_id", name)
            if mid == resources["machine_id"]:
                return

            ip = socket.inet_ntoa(info.addresses[0]) if info.addresses else "unknown"
            peer = {
                "machine_id": mid,
                "hostname": props.get("hostname", "unknown"),
                "role": props.get("role", "unknown"),
                "ip": ip,
                "profiles": int(props.get("profiles", 0)),
                "skills": int(props.get("skills", 0)),
                "has_gpu": props.get("has_gpu", "false") == "true",
                "gpu_names": [n for n in props.get("gpu_names", "").split(",") if n],
                "seen_at": datetime.now().isoformat(),
            }

            # SSH connectivity test
            host = peer["hostname"]
            try:
                t0 = time.monotonic()
                r = subprocess.run(
                    ["ssh", "-o", "ConnectTimeout=3",
                     "-o", "StrictHostKeyChecking=accept-new",
                     "-o", "BatchMode=yes",
                     host, "echo", "pong"],
                    capture_output=True, timeout=SSH_TIMEOUT + 2,
                )
                peer["ssh_ok"] = r.returncode == 0 and b"pong" in r.stdout
                peer["ssh_latency_ms"] = round((time.monotonic() - t0) * 1000, 1)
            except Exception:
                peer["ssh_ok"] = False
                peer["ssh_latency_ms"] = 0

            found[mid] = peer

        def remove_service(self, *args):
            pass

        def update_service(self, *args):
            pass

    browser = ServiceBrowser(zc, SERVICE_TYPE, Listener())

    # Wait for discovery
    time.sleep(4)
    zc.close()

    return list(found.values())


# ═══════════════════════════════════════════════════════════
# Heartbeat Write
# ═══════════════════════════════════════════════════════════

def write_heartbeat(resources: dict, peers: list[dict]):
    """Write heartbeat to fleet/nodes/ and push to GitHub."""
    mid = resources["machine_id"]

    # Add peers
    resources["lan_peers"] = peers
    resources["lan_peer_count"] = len(peers)
    resources["lan_ssh_peers"] = len([p for p in peers if p.get("ssh_ok")])

    # Write node file
    node_file = NODES_DIR / f"{mid}.json"
    blob = json.dumps(resources, indent=2, ensure_ascii=False, default=str)
    node_file.write_text(blob)

    # Try git push
    git_dir = None
    for d in [FLEET_DIR.parent, Path(os.path.expanduser("~/Desktop/2026workspace/agentark"))]:
        if (d / ".git").exists():
            git_dir = d
            break

    if git_dir:
        try:
            subprocess.run(
                ["git", "add", str(node_file)],
                cwd=git_dir, capture_output=True, timeout=10,
            )
            subprocess.run(
                ["git", "commit", "-m", f"📡 {mid}"],
                cwd=git_dir, capture_output=True, timeout=10,
            )
            r = subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=git_dir, capture_output=True, text=True, timeout=30,
            )
            resources["git_push_ok"] = r.returncode == 0
        except Exception as e:
            resources["git_push_ok"] = False
            resources["git_push_error"] = str(e)[:200]

    return resources


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════

def main():
    resources = probe_resources()
    peers = discover_lan_peers(resources)
    result = write_heartbeat(resources, peers)

    # Output summary
    mid = result["machine_id"]
    lan = result.get("lan_peer_count", 0)
    ssh = result.get("lan_ssh_peers", 0)
    gpu = result.get("gpu", {})
    git = "✅" if result.get("git_push_ok") else "❌"

    print(f"📡 {mid[:40]}")
    print(f"   CPU: {result.get('cpu_cores', '?')}c {result.get('cpu_usage_pct', 0):.0f}% | "
          f"RAM: {result.get('ram_free_mb', 0)}MB free")
    if gpu:
        print(f"   GPU: {gpu['util_pct']:.0f}% {', '.join(gpu.get('gpu_names', ['?']))}")
    print(f"   LAN peers: {lan} found, {ssh} SSH reachable")
    print(f"   GitHub push: {git}")

    return 0 if result.get("git_push_ok") else 0  # Always exit 0 (git push is best-effort)


if __name__ == "__main__":
    sys.exit(main())
