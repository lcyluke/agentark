#!/usr/bin/env python3
"""GB10 Remote Probe — SSH-based WAN node monitoring for AgentArk Fleet
====================================================================
Since GB10 is WAN (not LAN), we can't use mDNS discovery.
Instead: SSH in, collect stats, write to the same fleet/nodes/ format.

Run as cron on Mac every 5 minutes:
  hermes cron create "every 5m" --name "GB10远程探针" \
    --script scripts/gb10_probe.py --no-agent --toolsets terminal
"""

import json, os, subprocess, sys, time
from datetime import datetime
from pathlib import Path

GB10_HOST = "pm02@16.146.125.163"
GB10_PORT = "6023"
SSH_KEY = os.path.expanduser("~/Desktop/2026Parsimo/spark.pem")
SSH_BASE = f"ssh -o ConnectTimeout=8 -o StrictHostKeyChecking=no -i {SSH_KEY} -p {GB10_PORT} {GB10_HOST}"
GPU_CMD = "nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader 2>/dev/null"

# Output same format as fleet_heartbeat.py
FLEET_DIR = Path(os.path.expanduser("~/.apex/fleet"))
FLEET_DIR.mkdir(parents=True, exist_ok=True)
NODES_DIR = FLEET_DIR / "nodes"
NODES_DIR.mkdir(parents=True, exist_ok=True)

def ssh(cmd, timeout=10):
    r = subprocess.run(f"{SSH_BASE} '{cmd}'", shell=True, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.returncode

def probe_gb10():
    info = {
        "machine_id": "gb10-nvidia",
        "hostname": "gb10",
        "ip": "16.146.125.163",
        "os": "linux",
        "role": "gpu-server",
        "timestamp": datetime.now().isoformat(),
        "ssh_ok": False,
    }

    # SSH connectivity
    out, rc = ssh("echo OK", 8)
    if "OK" not in out:
        info["error"] = "SSH failed"
        write_heartbeat(info)
        return info
    info["ssh_ok"] = True

    # GPU
    out, _ = ssh(GPU_CMD, 12)
    gpus = []
    for line in out.split('\n'):
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 5:
            try:
                gpus.append({
                    "name": parts[0], "util_pct": float(parts[1]),
                    "mem_used_mb": int(parts[2]), "mem_total_mb": int(parts[3]),
                    "temp_c": int(parts[4])
                })
            except ValueError:
                continue
    if gpus:
        utils = [g["util_pct"] for g in gpus]
        info["gpu"] = {
            "gpu_count": len(gpus),
            "gpu_names": [g["name"] for g in gpus],
            "util_pct": round(sum(utils)/len(utils), 1),
            "mem_used_mb": sum(g["mem_used_mb"] for g in gpus),
            "mem_total_mb": sum(g["mem_total_mb"] for g in gpus),
            "temp_c": max(g["temp_c"] for g in gpus),
        }

    # Training status
    out, _ = ssh("ls -1t ~/gb10-training/logs/ 2>/dev/null | head -1; ls -lt ~/gb10-training/checkpoints/ 2>/dev/null | head -3", 10)
    info["training"] = {"latest_log": out.split('\n')[0] if out else "none"}

    # Badminton ML pipeline
    out, _ = ssh("ls -1t ~/badminton-ml/data/labeled/ 2>/dev/null | wc -l; echo '---'; ls -1t ~/badminton-ml/data/features.csv 2>/dev/null | head -1", 10)
    parts_out = out.split('---')
    info["badminton_ml"] = {
        "labeled_samples": parts_out[0].strip() if len(parts_out) > 0 else "0",
    }

    # Git status
    out, _ = ssh("cd ~/badminton-ml && git log --oneline -3 2>/dev/null", 10)
    info["git_recent"] = out[:200] if out else "no git"

    write_heartbeat(info)
    return info

def write_heartbeat(info):
    node_file = NODES_DIR / "gb10-nvidia.json"
    node_file.write_text(json.dumps(info, indent=2, ensure_ascii=False, default=str))

def main():
    t0 = time.monotonic()
    info = probe_gb10()
    elapsed = round((time.monotonic() - t0) * 1000)

    gpu = info.get("gpu", {})
    status = "🟢" if info.get("ssh_ok") else "🔴"
    gpu_str = f"GPU {gpu.get('util_pct', '?')}% {gpu.get('temp_c', '?')}°C" if gpu else "no GPU"
    print(f"📡 GB10 {status} {gpu_str} | {elapsed}ms")

if __name__ == "__main__":
    main()
