"""
AgentArk Fleet API — 多机舰队互联

Remote node management + API proxy + IP whitelist + token auth.
Supports LAN and internet connections through server-side proxying.
"""
from __future__ import annotations

import json
import ipaddress
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Blueprint, jsonify, request, Response
import urllib.request
import urllib.error

from agentark.core.profile import AGENTARK_HOME

fleet_bp = Blueprint("fleet", __name__)

FLEET_CONFIG = AGENTARK_HOME / "fleet_nodes.json"

# Default config
DEFAULT_CONFIG = {
    "nodes": [],
    "whitelist": {
        "enabled": False,
        "allowed_ips": ["127.0.0.1", "192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12"],
    },
    "local_token": None,  # token this machine requires from incoming proxy requests
}


def _load_config() -> dict:
    """Load fleet config, creating default if missing."""
    if FLEET_CONFIG.exists():
        try:
            with open(FLEET_CONFIG, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_CONFIG.copy()


def _save_config(config: dict):
    """Save fleet config to disk."""
    FLEET_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with open(FLEET_CONFIG, "w") as f:
        json.dump(config, f, indent=2, default=str)


def _check_ip_whitelist(remote_ip: str, config: dict) -> bool:
    """Check if an IP is allowed by whitelist rules."""
    wh = config.get("whitelist", {})
    if not wh.get("enabled", False):
        return True  # whitelist disabled — allow all

    allowed = wh.get("allowed_ips", [])
    if not allowed:
        return True

    try:
        ip = ipaddress.ip_address(remote_ip)
        for cidr in allowed:
            if ip in ipaddress.ip_network(cidr, strict=False):
                return True
    except ValueError:
        pass
    return False


def _probe_remote(host: str, port: int, token: Optional[str] = None, timeout: int = 5) -> dict:
    """Probe remote agentark instance at host:port and return status info."""
    url = f"http://{host}:{port}/api/version"
    headers = {}
    if token:
        headers["X-Fleet-Token"] = token

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            return {
                "reachable": True,
                "version": data.get("version", "unknown"),
                "name": data.get("name", "unknown"),
                "description": data.get("description", ""),
                "python": data.get("python", ""),
                "error": None,
            }
    except urllib.error.HTTPError as e:
        return {"reachable": False, "error": f"HTTP {e.code}", "version": None, "name": None}
    except urllib.error.URLError as e:
        return {"reachable": False, "error": str(e.reason), "version": None, "name": None}
    except Exception as e:
        return {"reachable": False, "error": str(e), "version": None, "name": None}


def _proxy_remote(host: str, port: int, path: str, token: Optional[str] = None, timeout: int = 10) -> tuple:
    """Proxy a request to remote agentark and return (body, status_code, content_type)."""
    url = f"http://{host}:{port}{path}"
    headers = {"Accept": "application/json"}
    if token:
        headers["X-Fleet-Token"] = token

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode()
            content_type = resp.headers.get("Content-Type", "application/json")
            return body, resp.status, content_type
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode()
        except:
            body = json.dumps({"error": f"Remote returned {e.code}"})
        return body, e.code, "application/json"
    except Exception as e:
        return json.dumps({"error": str(e)}), 502, "application/json"


# ══════════════════════════════════════════════════════
# Fleet Node CRUD
# ══════════════════════════════════════════════════════


@fleet_bp.route("/api/fleet/nodes", methods=["GET"])
def list_nodes():
    """List all registered fleet nodes with current status (auto-probe)."""
    config = _load_config()
    nodes = config.get("nodes", [])

    # Auto-probe each node for live status
    for node in nodes:
        result = _probe_remote(
            node.get("host", ""),
            node.get("port", 8080),
            token=node.get("token"),
            timeout=3,
        )
        node["_probe"] = result
        if result["reachable"]:
            node["last_seen"] = datetime.now().isoformat()
            node["status"] = "online"
            node["remote_version"] = result.get("version")
            node["remote_name"] = result.get("name")
        else:
            node["status"] = node.get("status", "offline")

    _save_config(config)
    return jsonify({"nodes": nodes})


@fleet_bp.route("/api/fleet/nodes", methods=["POST"])
def add_node():
    """Register a new remote fleet node."""
    data = request.get_json(silent=True) or {}

    host = (data.get("host") or "").strip()
    port = data.get("port", 8080)
    name = (data.get("name") or host or f"node-{int(time.time())}").strip()
    token = (data.get("token") or "").strip() or None
    nickname = (data.get("nickname") or name).strip()

    if not host:
        return jsonify({"error": "host is required"}), 400

    # Validate port
    try:
        port = int(port)
        if port < 1 or port > 65535:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "port must be 1-65535"}), 400

    config = _load_config()
    nodes = config.get("nodes", [])

    # Check duplicate
    for n in nodes:
        if n.get("host") == host and n.get("port") == port:
            return jsonify({"error": f"Node {host}:{port} already exists", "id": n["id"]}), 409

    node_id = f"node-{int(time.time())}"
    node = {
        "id": node_id,
        "name": name,
        "nickname": nickname,
        "host": host,
        "port": port,
        "token": token,
        "added_at": datetime.now().isoformat(),
        "last_seen": None,
        "status": "unknown",
        "remote_version": None,
        "remote_name": None,
    }

    # Immediate probe
    result = _probe_remote(host, port, token=token, timeout=5)
    node["_probe"] = result
    if result["reachable"]:
        node["status"] = "online"
        node["last_seen"] = datetime.now().isoformat()
        node["remote_version"] = result.get("version")
        node["remote_name"] = result.get("name")

    nodes.append(node)
    config["nodes"] = nodes
    _save_config(config)

    return jsonify(node), 201


@fleet_bp.route("/api/fleet/nodes/<node_id>", methods=["DELETE"])
def remove_node(node_id: str):
    """Remove a fleet node."""
    config = _load_config()
    nodes = config.get("nodes", [])
    filtered = [n for n in nodes if n.get("id") != node_id]
    if len(filtered) == len(nodes):
        return jsonify({"error": f"Node '{node_id}' not found"}), 404
    config["nodes"] = filtered
    _save_config(config)
    return jsonify({"deleted": node_id})


@fleet_bp.route("/api/fleet/nodes/<node_id>/test", methods=["POST"])
def test_node(node_id: str):
    """Probe a specific fleet node for connectivity."""
    config = _load_config()
    node = next((n for n in config.get("nodes", []) if n.get("id") == node_id), None)
    if not node:
        return jsonify({"error": f"Node '{node_id}' not found"}), 404

    result = _probe_remote(
        node.get("host", ""),
        node.get("port", 8080),
        token=node.get("token"),
        timeout=5,
    )

    node["_probe"] = result
    if result["reachable"]:
        node["status"] = "online"
        node["last_seen"] = datetime.now().isoformat()
        node["remote_version"] = result.get("version")
        node["remote_name"] = result.get("name")
    else:
        node["status"] = "offline"

    _save_config(config)
    return jsonify({"node_id": node_id, "probe": result})


# ══════════════════════════════════════════════════════
# Remote Proxy — fetch remote node's API
# ══════════════════════════════════════════════════════


@fleet_bp.route("/api/fleet/nodes/<node_id>/proxy/<path:proxy_path>")
def proxy_remote_api(node_id: str, proxy_path: str):
    """Proxy API calls to a remote fleet node. 
    
    Calls like GET /api/fleet/nodes/node-xxx/proxy/api/status 
    are forwarded to http://remote-host:port/api/status.
    """
    config = _load_config()
    node = next((n for n in config.get("nodes", []) if n.get("id") == node_id), None)
    if not node:
        return jsonify({"error": f"Node '{node_id}' not found"}), 404

    # Check whitelist
    client_ip = request.remote_addr or "127.0.0.1"
    if not _check_ip_whitelist(client_ip, config):
        return jsonify({"error": f"IP {client_ip} not in whitelist"}), 403

    # Forward query params
    query_string = request.query_string.decode()
    full_path = f"/{proxy_path}"
    if query_string:
        full_path += f"?{query_string}"

    body, status, content_type = _proxy_remote(
        node.get("host", ""),
        node.get("port", 8080),
        full_path,
        token=node.get("token"),
    )

    return Response(body, status=status, content_type=content_type)


@fleet_bp.route("/api/fleet/nodes/<node_id>/status")
def node_status(node_id: str):
    """Get full remote node status (aggregated API calls)."""
    config = _load_config()
    node = next((n for n in config.get("nodes", []) if n.get("id") == node_id), None)
    if not node:
        return jsonify({"error": f"Node '{node_id}' not found"}), 404

    host = node.get("host", "")
    port = node.get("port", 8080)
    token = node.get("token")

    # Fetch remote /api/status, /api/version, /api/profiles
    results = {}
    for label, api_path in [
        ("version", "/api/version"),
        ("status", "/api/status"),
        ("health", "/api/health"),
    ]:
        body, code, _ = _proxy_remote(host, port, api_path, token=token)
        try:
            results[label] = json.loads(body) if body else {"error": "empty response"}
        except json.JSONDecodeError:
            results[label] = {"raw": body[:200]}

    # Fetch remote profiles (lightweight list)
    body, code, _ = _proxy_remote(host, port, "/api/profiles", token=token)
    try:
        profiles_data = json.loads(body) if body else []
        results["profiles_count"] = len(profiles_data) if isinstance(profiles_data, list) else 0
    except json.JSONDecodeError:
        results["profiles_count"] = 0

    # Build aggregated status
    remote_status = results.get("status", {})
    remote_version = results.get("version", {})

    return jsonify({
        "node_id": node_id,
        "host": host,
        "port": port,
        "nickname": node.get("nickname", host),
        "connected": True,
        "version": remote_version.get("version", "unknown"),
        "name": remote_version.get("name", "AgentArk"),
        "remote_status": {
            "profiles": remote_status.get("profiles", results.get("profiles_count", 0)),
            "tasks": len(remote_status.get("tasks", [])),
            "recent_tasks": remote_status.get("recent_tasks", [])[:5],
            "uptime_seconds": remote_status.get("uptime_seconds", 0),
            "knowledge_nodes": remote_status.get("knowledge_nodes", 0),
            "patterns": remote_status.get("patterns", 0),
        },
        "health": results.get("health", {}),
        "last_probe": datetime.now().isoformat(),
    })


# ══════════════════════════════════════════════════════
# Fleet Config (whitelist, local token)
# ══════════════════════════════════════════════════════


@fleet_bp.route("/api/fleet/config", methods=["GET"])
def get_fleet_config():
    """Get fleet security configuration (no secrets exposed)."""
    config = _load_config()
    wh = config.get("whitelist", {})
    return jsonify({
        "whitelist_enabled": wh.get("enabled", False),
        "allowed_ips": wh.get("allowed_ips", []),
        "local_token_set": bool(config.get("local_token")),
        "nodes_count": len(config.get("nodes", [])),
    })


@fleet_bp.route("/api/fleet/config", methods=["PUT"])
def update_fleet_config():
    """Update fleet configuration (whitelist toggle, allowed IPs, local token)."""
    data = request.get_json(silent=True) or {}
    config = _load_config()

    if "whitelist_enabled" in data:
        wh = config.setdefault("whitelist", {})
        wh["enabled"] = bool(data["whitelist_enabled"])
        config["whitelist"] = wh

    if "allowed_ips" in data and isinstance(data["allowed_ips"], list):
        # Validate CIDRs
        valid = []
        for cidr in data["allowed_ips"]:
            try:
                ipaddress.ip_network(str(cidr), strict=False)
                valid.append(str(cidr))
            except ValueError:
                pass
        config.setdefault("whitelist", {})["allowed_ips"] = valid or DEFAULT_CONFIG["whitelist"]["allowed_ips"]
        config["whitelist"] = config["whitelist"]

    if "local_token" in data:
        token = str(data["local_token"]).strip()
        config["local_token"] = token if token else None

    _save_config(config)
    return jsonify({"saved": True})


# ══════════════════════════════════════════════════════
# Remote fleet-wide aggregated dashboard
# ══════════════════════════════════════════════════════


@fleet_bp.route("/api/fleet/dashboard")
def fleet_dashboard():
    """Aggregated view: local stats + all online remote nodes."""
    config = _load_config()
    nodes = config.get("nodes", [])

    # Local stats from existing endpoints
    from agentark.core.profile import ProfileManager
    pm = ProfileManager()
    local_profiles = len(pm.list())

    # Probe all nodes in parallel-like fashion
    remote_summary = []
    online_count = 0
    total_remote_agents = 0
    total_remote_tasks = 0

    for node in nodes:
        result = _probe_remote(
            node.get("host", ""),
            node.get("port", 8080),
            token=node.get("token"),
            timeout=3,
        )
        summary = {
            "id": node["id"],
            "nickname": node.get("nickname", node.get("host")),
            "host": node.get("host"),
            "port": node.get("port"),
            "reachable": result["reachable"],
            "error": result.get("error"),
        }

        if result["reachable"]:
            online_count += 1
            summary["version"] = result.get("version")
            summary["name"] = result.get("name")
            # Quick task/profile count from remote
            body, _, _ = _proxy_remote(
                node["host"], node["port"], "/api/status",
                token=node.get("token"), timeout=3,
            )
            try:
                remote_data = json.loads(body)
                summary["profiles"] = remote_data.get("profiles", 0)
                summary["tasks"] = len(remote_data.get("tasks", []))
                total_remote_agents += summary["profiles"]
                total_remote_tasks += summary["tasks"]
            except:
                summary["profiles"] = 0
                summary["tasks"] = 0

        remote_summary.append(summary)

    return jsonify({
        "local": {
            "profiles": local_profiles,
            "version": "0.5.1",
            "name": "AgentArk",
        },
        "fleet": {
            "total_nodes": len(nodes),
            "online_nodes": online_count,
            "total_remote_agents": total_remote_agents,
            "total_remote_tasks": total_remote_tasks,
            "nodes": remote_summary,
        },
        "whitelist_enabled": config.get("whitelist", {}).get("enabled", False),
    })
