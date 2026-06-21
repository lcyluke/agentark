"""Apex Multi-Mac Fleet Manager — 单仓库舰队编排 (v2)

Architecture:
  lcyluke/apex (唯一仓库)
  ├── apex/          ← 代码
  ├── scripts/       ← 工具脚本
  ├── fleet/         ← 舰队配置 + 节点心跳
  │   ├── config.yaml
  │   ├── SOUL.md
  │   ├── skills/
  │   ├── profiles/
  │   └── nodes/
  └── docs/

   Mac-A (Origin) ←── git push/pull ──→ Mac-B (Worker)
   所有配置通过 Apex 仓库同步，无需额外仓库。
"""

from __future__ import annotations

import json
import os
import subprocess
import socket
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional


# ─── Paths (all inside Apex project) ────────────────────────
def _apex_root() -> Path:
    """Find Apex project root (where fleet/ lives)."""
    # Try environment, then relative to this file, then common locations
    env = os.environ.get("APEX_HOME")
    if env:
        return Path(env)
    # This file is at apex/interface/fleet_multi_mac.py → go up 2 levels
    return Path(__file__).resolve().parent.parent.parent


APEX_ROOT = _apex_root()
FLEET_DIR = APEX_ROOT / "fleet"
NODES_DIR = FLEET_DIR / "nodes"
FLEET_CONFIG_FILE = FLEET_DIR / "fleet.json"
HERMES_HOME = Path(os.path.expanduser("~/.hermes"))
GPU_STATE_FILE = Path("/tmp/apex_gpu_state.json")


# ══════════════════════════════════════════
# Identity
# ══════════════════════════════════════════

def get_machine_id() -> str:
    hostname = socket.gethostname()
    return f"{hostname}-{os.getlogin()}"


def get_fleet_config() -> dict:
    if FLEET_CONFIG_FILE.exists():
        with open(FLEET_CONFIG_FILE) as f:
            return json.load(f)
    return {
        "fleet_name": "老卢舰队",
        "role": None,
        "machine_id": get_machine_id(),
        "projects": [],
        "joined_at": None,
        "last_sync": None,
    }


def save_fleet_config(cfg: dict):
    FLEET_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FLEET_CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False, default=str)


# ══════════════════════════════════════════
# Fleet Init (Origin) — v2: inside Apex repo
# ══════════════════════════════════════════

def fleet_init(
    fleet_name: str = "老卢舰队",
    force: bool = False,
) -> dict:
    """Initialize this Mac as fleet Origin. Uses Apex repo's git."""
    cfg = get_fleet_config()
    if cfg["role"] and not force:
        return {"error": f"Already a {cfg['role']} node. Use --force to re-init."}

    results = []
    git_dir = APEX_ROOT / ".git"

    if not git_dir.exists():
        return {"error": "Apex project is not a git repo. Clone from GitHub first."}

    # 1. Ensure fleet/ directory
    FLEET_DIR.mkdir(parents=True, exist_ok=True)
    NODES_DIR.mkdir(parents=True, exist_ok=True)
    results.append("✅ fleet/ 目录就绪")

    # 2. Sync config from ~/.hermes/ → fleet/
    _sync_hermes_to_fleet()
    results.append("✅ ~/.hermes/ → fleet/ 同步")

    # 3. Git commit fleet/
    subprocess.run(["git", "add", "fleet/"], cwd=APEX_ROOT, capture_output=True)
    r = subprocess.run(
        ["git", "commit", "-m", f"⚓ Fleet init — Origin {get_machine_id()}"],
        cwd=APEX_ROOT, capture_output=True, text=True,
    )
    if r.returncode == 0 or "nothing to commit" in r.stdout:
        results.append("✅ fleet/ 已提交")
    else:
        results.append(f"⚠️ commit: {r.stderr[:100]}")

    # 4. Save fleet config
    cfg["role"] = "origin"
    cfg["fleet_name"] = fleet_name
    cfg["projects"] = ["badminton-coach-ai", "apex", "finopsai", "shenzhen-badminton"]
    cfg["joined_at"] = datetime.now().isoformat()
    cfg["origin_machine"] = get_machine_id()
    save_fleet_config(cfg)
    results.append("✅ Fleet Origin 已注册")

    return {
        "success": True,
        "role": "origin",
        "fleet_name": fleet_name,
        "machine_id": get_machine_id(),
        "steps": results,
    }


def _sync_hermes_to_fleet():
    """Copy ~/.hermes/ config → fleet/ (脱敏: 不含 .env)"""
    files = ["config.yaml", "SOUL.md"]
    dirs = ["skills", "profiles"]

    for f in files:
        src = HERMES_HOME / f
        dst = FLEET_DIR / f
        if src.exists():
            shutil.copy2(src, dst)

    for d in dirs:
        src = HERMES_HOME / d
        dst = FLEET_DIR / d
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)


def _sync_fleet_to_hermes():
    """Copy fleet/ config → ~/.hermes/ (保留本地 .env)"""
    env_backup = None
    local_env = HERMES_HOME / ".env"
    if local_env.exists():
        env_backup = local_env.read_text()

    files = ["config.yaml", "SOUL.md"]
    dirs = ["skills", "profiles"]

    for f in files:
        src = FLEET_DIR / f
        if src.exists():
            shutil.copy2(src, HERMES_HOME / f)

    for d in dirs:
        src = FLEET_DIR / d
        dst = HERMES_HOME / d
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

    if env_backup:
        local_env.write_text(env_backup)


# ══════════════════════════════════════════
# Fleet Join (Worker) — v2: clone Apex → sync fleet/
# ══════════════════════════════════════════

def fleet_join(force: bool = False) -> dict:
    """Join fleet as Worker. Syncs fleet/ config from Apex repo to ~/.hermes/."""
    cfg = get_fleet_config()
    if cfg["role"] and not force:
        return {"error": f"Already a {cfg['role']} node."}

    results = []

    # 1. Git pull latest (Apex repo should already be cloned)
    git_dir = APEX_ROOT / ".git"
    if not git_dir.exists():
        return {"error": "Apex not cloned. Run: git clone https://github.com/lcyluke/apex.git"}

    r = subprocess.run(
        ["git", "pull", "origin", "main"],
        cwd=APEX_ROOT, capture_output=True, text=True, timeout=60,
    )
    if r.returncode == 0:
        results.append("✅ Apex 已更新到最新")
    else:
        results.append(f"⚠️ pull: {r.stderr[:80]}")

    # 2. Sync fleet/ → ~/.hermes/
    if FLEET_DIR.exists():
        _sync_fleet_to_hermes()
        results.append("✅ fleet/ → ~/.hermes/ 配置同步完成")
    else:
        return {"error": "fleet/ 目录不存在。Origin 尚未初始化舰队。"}

    # 3. Register
    cfg["role"] = "worker"
    cfg["joined_at"] = datetime.now().isoformat()
    cfg["worker_machine"] = get_machine_id()
    save_fleet_config(cfg)
    results.append("✅ Worker 已注册")

    return {
        "success": True,
        "role": "worker",
        "machine_id": get_machine_id(),
        "steps": results,
        "next": "运行 'apex fleet sync --pull' 拉取最新配置",
    }


# ══════════════════════════════════════════
# Fleet Sync — v2: git pull/push fleet/
# ══════════════════════════════════════════

def fleet_sync(direction: str = "pull") -> dict:
    """Sync fleet config via Apex repo git."""
    cfg = get_fleet_config()
    if not cfg.get("role"):
        return {"error": "Not in a fleet."}

    results = []

    if direction == "pull":
        r = subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            cwd=APEX_ROOT, capture_output=True, text=True, timeout=60,
        )
        if r.returncode == 0:
            _sync_fleet_to_hermes()
            cfg["last_sync"] = datetime.now().isoformat()
            save_fleet_config(cfg)
            results.append("✅ 配置已同步至 ~/.hermes/")
        else:
            results.append(f"⚠️ {r.stderr[:100]}")

    elif direction == "push":
        # First sync ~/.hermes/ → fleet/
        _sync_hermes_to_fleet()
        subprocess.run(["git", "add", "fleet/"], cwd=APEX_ROOT, capture_output=True)
        r = subprocess.run(
            ["git", "commit", "-m", f"🔄 Fleet sync — {datetime.now().strftime('%m/%d %H:%M')}"],
            cwd=APEX_ROOT, capture_output=True, text=True,
        )
        r2 = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=APEX_ROOT, capture_output=True, text=True, timeout=60,
        )
        if r2.returncode == 0:
            cfg["last_sync"] = datetime.now().isoformat()
            save_fleet_config(cfg)
            results.append("✅ fleet/ 已推送")
        else:
            results.append(f"⚠️ {r2.stderr[:100]}")

    return {
        "success": True,
        "direction": direction,
        "steps": results,
    }


# ══════════════════════════════════════════
# Node Heartbeat — v2: writes to fleet/nodes/
# ══════════════════════════════════════════

def fleet_report() -> dict:
    """Write node status → fleet/nodes/<id>.json → git push."""
    cfg = get_fleet_config()
    if not cfg.get("role"):
        return {"error": "Not in a fleet."}

    # Pull first
    subprocess.run(
        ["git", "pull", "--rebase", "origin", "main"],
        cwd=APEX_ROOT, capture_output=True, timeout=60,
    )

    # Write node status
    NODES_DIR.mkdir(parents=True, exist_ok=True)
    status = fleet_status()
    status["reported_at"] = datetime.now().isoformat()
    # Use configured machine_id for stable identity across network changes
    mid = cfg.get("machine_id") or get_machine_id()
    status["machine_id"] = mid

    node_file = NODES_DIR / f"{mid}.json"
    node_file.write_text(json.dumps(status, indent=2, ensure_ascii=False, default=str))

    # Commit + push
    subprocess.run(
        ["git", "add", f"fleet/nodes/{get_machine_id()}.json"],
        cwd=APEX_ROOT, capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", f"📡 {get_machine_id()} ({cfg['role']})"],
        cwd=APEX_ROOT, capture_output=True,
    )
    r = subprocess.run(
        ["git", "push", "origin", "main"],
        cwd=APEX_ROOT, capture_output=True, text=True, timeout=60,
    )

    cfg["last_report"] = datetime.now().isoformat()
    save_fleet_config(cfg)

    return {
        "success": r.returncode == 0,
        "machine_id": get_machine_id(),
        "role": cfg["role"],
        "push_ok": r.returncode == 0,
    }


def get_all_nodes() -> list[dict]:
    """Read all node files from fleet/nodes/."""
    nodes = []
    if not NODES_DIR.exists():
        return nodes
    for f in sorted(NODES_DIR.glob("*.json")):
        if f.name == ".gitkeep":
            continue
        try:
            node = json.loads(f.read_text())
            node["is_local"] = (node.get("machine_id") == get_machine_id())
            nodes.append(node)
        except Exception:
            pass
    return nodes


# ══════════════════════════════════════════
# GPU Monitoring — built into fleet_status()
# ══════════════════════════════════════════

def _probe_gpu() -> dict:
    """Probe local GPU via nvidia-smi."""
    try:
        r = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,name",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return {}
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
        if not gpus:
            return {}
        utils = [g["util_pct"] for g in gpus]
        return {
            "gpu_count": len(gpus),
            "gpu_names": [g["name"] for g in gpus],
            "util_pct": round(sum(utils) / len(utils), 1),
            "mem_used_mb": sum(g["mem_used_mb"] for g in gpus),
            "mem_total_mb": sum(g["mem_total_mb"] for g in gpus),
            "mem_pct": round(sum(g["mem_used_mb"] for g in gpus) / sum(g["mem_total_mb"] for g in gpus) * 100, 1) if sum(g["mem_total_mb"] for g in gpus) else 0,
            "temp_c": max(g["temp_c"] for g in gpus),
            "per_gpu": gpus,
        }
    except (FileNotFoundError, Exception):
        return {}


MAX_GPU_ALERTS_PER_DAY = 7

def _gpu_alerts(gpu: dict, prev_state: dict) -> list[str]:
    """Dual-threshold GPU alerts with daily cap (MAX_GPU_ALERTS_PER_DAY)."""
    if not gpu:
        return []
    alerts = []
    util = gpu["util_pct"]
    pg = prev_state.get("gpu", {})

    # ── Daily alert cap ──
    today = str(__import__('datetime').date.today())
    if pg.get("alert_date") != today:
        pg["alert_date"] = today
        pg["alert_count"] = 0
        pg["alert_capped"] = False
    count = pg.get("alert_count", 0)
    if count >= MAX_GPU_ALERTS_PER_DAY:
        if not pg.get("alert_capped"):
            alerts.append(
                f"🔇 GPU 告警已达每日上限 ({MAX_GPU_ALERTS_PER_DAY}次)，今天不再提醒"
            )
            pg["alert_capped"] = True
        prev_state["gpu"] = pg
        return alerts

    if util >= 90 and not pg.get("alert_sent_overload"):
        alerts.append(
            f"🔴 GPU 高负载 {util:.0f}% | 显存 {gpu['mem_pct']:.0f}% | {gpu['temp_c']}°C\n"
            f"   GPU: {', '.join(gpu['gpu_names'][:2])}"
        )
        pg["alert_sent_overload"] = True
    elif util < 90:
        pg["alert_sent_overload"] = False

    # Idle: <30% — use timestamp, not cycle counter
    if util < 30:
        if pg.get("idle_since") is None:
            pg["idle_since"] = int(__import__('time').time())
        idle_secs = int(__import__('time').time()) - pg["idle_since"]
        idle_mins = idle_secs // 60
        pg["idle_minutes"] = idle_mins

        if idle_mins >= 30 and not pg.get("alert_sent_idle_crit"):
            alerts.append(f"🔴 GPU 严重空闲 {util:.0f}% — {idle_mins}分钟\n   💡 检查训练状态")
            pg["alert_sent_idle_crit"] = True
        elif idle_mins >= 15 and not pg.get("alert_sent_idle_warn"):
            alerts.append(f"⚠️ GPU 空闲 {util:.0f}% — {idle_mins}分钟")
            pg["alert_sent_idle_warn"] = True
    else:
        pg["idle_since"] = None
        pg["idle_minutes"] = 0
        pg["alert_sent_idle_warn"] = False
        pg["alert_sent_idle_crit"] = False

    # ── Increment daily alert count ──
    if alerts:
        pg["alert_count"] = count + len(alerts)

    prev_state["gpu"] = pg
    return alerts


def fleet_status() -> dict:
    """Current node status — includes GPU info."""
    cfg = get_fleet_config()

    git_status = "unknown"
    git_dir = APEX_ROOT / ".git"
    if git_dir.exists():
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=APEX_ROOT, capture_output=True, text=True,
        )
        if r.returncode == 0:
            dirty = len([l for l in r.stdout.split("\n") if l.strip()])
            git_status = "clean" if dirty == 0 else f"{dirty} files modified"

    profiles_dir = HERMES_HOME / "profiles"
    profile_count = len([d for d in profiles_dir.iterdir() if d.is_dir()]) if profiles_dir.exists() else 0

    skills_dir = HERMES_HOME / "skills"
    skill_count = len(list(skills_dir.rglob("SKILL.md"))) if skills_dir.exists() else 0

    # GPU
    gpu = _probe_gpu()
    prev_state = {}
    if GPU_STATE_FILE.exists():
        try:
            prev_state = json.loads(GPU_STATE_FILE.read_text())
        except Exception:
            pass
    gpu_alerts_list = _gpu_alerts(gpu, prev_state) if gpu else []

    if gpu:
        try:
            GPU_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            GPU_STATE_FILE.write_text(json.dumps(prev_state))
        except Exception:
            pass

    return {
        "machine_id": cfg.get("machine_id") or get_machine_id(),
        "hostname": socket.gethostname(),
        "display_name": cfg.get("display_name", ""),
        "role": cfg.get("role") or "unconfigured",
        "fleet_name": cfg.get("fleet_name", "unknown"),
        "projects": cfg.get("projects", []),
        "joined_at": cfg.get("joined_at"),
        "last_sync": cfg.get("last_sync"),
        "git_status": git_status,
        "profiles": profile_count,
        "skills": skill_count,
        "gpu": gpu,
        "gpu_alerts": gpu_alerts_list,
    }
