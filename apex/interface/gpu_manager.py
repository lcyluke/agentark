"""
Apex GPU 资源中心 — GPU 状态监控 / 项目绑定 / 关机授权

职责:
  - 读取 GPU 实时状态 (SSH nvidia-smi + 本地状态文件)
  - 项目-GPU 实例绑定管理
  - 关机授权流程: request → confirm
"""

from __future__ import annotations

import json, os, subprocess, secrets
from pathlib import Path
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))

# ── 路径 ───────────────────────────────────────
STATE_FILE = Path("/tmp/autodl_gpu_state.json")
PROJECTS_FILE = Path("/tmp/autodl_gpu_projects.json")
AUTH_FILE = Path("/tmp/autodl_gpu_auth.json")

# ── SSH 配置 ────────────────────────────────────
SSH_HOST = "connect.westb.seetacloud.com"
SSH_PORT = 16786
SSH_USER = "root"
PASS_FILE = Path(os.path.expanduser("~/.hermes/.autodl_west_pass"))


# ═══════════════════════════════════════════════
# GPU 实时状态
# ═══════════════════════════════════════════════

def get_gpu_status() -> dict:
    """返回 GPU 完整状态，优先读实时数据，降级读缓存"""
    result = {
        "online": False,
        "gpu_name": "unknown",
        "gpu_util_pct": 0,
        "memory_used_mb": 0,
        "memory_total_mb": 0,
        "temperature_c": 0,
        "fan_pct": 0,
        "power_w": 0,
        "uptime": "",
        "disk_used_pct": 0,
        "inference_busy": False,
        "idle_minutes": 0,
        "idle_cycles": 0,
        "last_check": None,
        "error": None,
    }

    # 1. 尝试 SSH 获取实时数据
    live = _ssh_nvidia_smi()
    if live:
        result.update(live)
        result["online"] = True
        result["last_check"] = datetime.now(TZ).isoformat()

    # 2. 叠加状态文件（闲置计数等）
    state = _load_state()
    result["idle_cycles"] = state.get("idle_cycles", 0)
    result["idle_minutes"] = state.get("idle_cycles", 0) * 5
    result["inference_busy"] = _check_inference_busy()
    result["pending_shutdown"] = state.get("confirmed_shutdown", False)

    # 3. 读取授权状态
    auth = _load_auth()
    result["auth_pending"] = auth.get("pending", False)
    result["auth_code"] = auth.get("code", "") if auth.get("pending") else ""

    return result


def _ssh_nvidia_smi() -> dict | None:
    """SSH 登录 AutoDL 获取 nvidia-smi 数据"""
    try:
        passwd = PASS_FILE.read_text().strip()
    except Exception:
        return None

    cmd = (
        f"sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=8 "
        f"-p {SSH_PORT} {SSH_USER}@{SSH_HOST} "
        f"\"nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu,fan.speed,power.draw "
        f"--format=csv,noheader,nounits 2>/dev/null || echo 'ERROR'\""
    )

    try:
        env = os.environ.copy()
        env["SSHPASS"] = passwd
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15, env=env)
        output = result.stdout.strip()

        if not output or "ERROR" in output:
            return None

        # 取第一行（单GPU场景）
        line = output.split("\n")[0].strip()
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 7:
            return None

        return {
            "gpu_name": parts[0],
            "gpu_util_pct": int(parts[1]) if parts[1].isdigit() else 0,
            "memory_used_mb": int(parts[2]) if parts[2].isdigit() else 0,
            "memory_total_mb": int(parts[3]) if parts[3].isdigit() else 0,
            "temperature_c": int(parts[4]) if parts[4].isdigit() else 0,
            "fan_pct": int(parts[5]) if parts[5].isdigit() else 0,
            "power_w": float(parts[6]) if parts[6].replace(".","").isdigit() else 0,
        }
    except Exception:
        return None


def _check_inference_busy() -> bool:
    """检查本地 :8765 是否有活跃连接"""
    try:
        result = subprocess.run(
            ["lsof", "-i", ":8765", "-s", "TCP:ESTABLISHED"],
            capture_output=True, text=True, timeout=3
        )
        lines = result.stdout.strip().split("\n")
        return len([l for l in lines[1:] if "ESTABLISHED" in l and l.strip()]) > 0
    except Exception:
        return False


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"idle_cycles": 0, "last_active": None, "confirmed_shutdown": False}


# ═══════════════════════════════════════════════
# 项目-GPU 绑定
# ═══════════════════════════════════════════════

def get_gpu_projects() -> dict:
    """返回项目-GPU绑定列表"""
    if PROJECTS_FILE.exists():
        try:
            return json.loads(PROJECTS_FILE.read_text())
        except Exception:
            pass
    default = {
        "projects": {
            "羽球宝AI": {"instance": "westb", "gpu": "RTX 4090", "bound_at": None},
            "Apex": {"instance": "westb", "gpu": "RTX 4090", "bound_at": None},
        },
        "instances": [
            {"id": "westb", "host": SSH_HOST, "port": SSH_PORT, "gpu_type": "RTX 4090 24GB"}
        ]
    }
    _save_projects(default)
    return default


def bind_project(project_name: str, instance_id: str) -> dict:
    """绑定项目到 GPU 实例"""
    data = get_gpu_projects()
    instance = next((i for i in data["instances"] if i["id"] == instance_id), None)
    if not instance:
        return {"error": f"实例 '{instance_id}' 不存在"}

    data["projects"][project_name] = {
        "instance": instance_id,
        "gpu": instance["gpu_type"],
        "bound_at": datetime.now(TZ).isoformat(),
    }
    _save_projects(data)
    return {"ok": True, "project": project_name, "instance": instance_id}


def _save_projects(data: dict):
    PROJECTS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


# ═══════════════════════════════════════════════
# 关机授权
# ═══════════════════════════════════════════════

def request_shutdown(project_name: str = "") -> dict:
    """发起关机请求 → 生成授权码"""
    code = secrets.token_hex(3).upper()[:6]  # 6位授权码
    auth = {
        "pending": True,
        "code": code,
        "project": project_name,
        "requested_at": datetime.now(TZ).isoformat(),
        "expires_at": (datetime.now(TZ) + timedelta(minutes=30)).isoformat(),
    }
    _save_auth(auth)
    return {
        "status": "pending_approval",
        "code": code,
        "message": f"关机需授权，请确认码 {code}",
        "expires_in_minutes": 30,
    }


def confirm_shutdown(code: str) -> dict:
    """确认授权码 → 执行关机"""
    auth = _load_auth()
    if not auth.get("pending"):
        return {"error": "没有待审批的关机请求"}

    if auth.get("code", "").upper() != code.upper():
        return {"error": "授权码不匹配"}

    # 标记已确认
    auth["pending"] = False
    auth["confirmed"] = True
    auth["confirmed_at"] = datetime.now(TZ).isoformat()
    _save_auth(auth)

    # 执行安全关机
    return _execute_shutdown()


def _execute_shutdown() -> dict:
    """SSH 执行安全关机"""
    try:
        passwd = PASS_FILE.read_text().strip()
    except Exception as e:
        return {"error": f"无法读取密码: {e}"}

    shutdown_cmd = (
        "kill $(pgrep -f '/root/miniconda3/bin/python') 2>/dev/null; "
        "sync; shutdown -h +0.5"
    )

    cmd = (
        f"sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "
        f"-p {SSH_PORT} {SSH_USER}@{SSH_HOST} \"{shutdown_cmd}\""
    )

    try:
        env = os.environ.copy()
        env["SSHPASS"] = passwd
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20, env=env)
        return {
            "ok": True,
            "action": "shutdown",
            "message": "GPU 服务器将在 30 秒后关机",
            "output": result.stdout.strip()[-200:],
        }
    except subprocess.TimeoutExpired:
        return {"ok": True, "action": "shutdown", "message": "关机指令已发送（SSH超时但可能已生效）"}
    except Exception as e:
        return {"error": str(e)}


def _load_auth() -> dict:
    if AUTH_FILE.exists():
        try:
            return json.loads(AUTH_FILE.read_text())
        except Exception:
            pass
    return {"pending": False, "code": "", "confirmed": False}


def _save_auth(data: dict):
    AUTH_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
