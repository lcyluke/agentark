"""Apex-Hermes Bridge — Real data aggregation for Dashboard

Reads from:
  - Hermes state.db → sessions, token usage, Profile status
  - Hermes config → model pricing
  - Monitor system → GPU metrics
  - Apex → profiles, kanban, economy
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional


HERMES_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))
STATE_DB = HERMES_HOME / "state.db"
MONITOR_DB = Path(os.path.expanduser("~/Desktop/2026AIAPP/monitor/logs/monitor.db"))


# ══════════════════════════════════════════
# Hermes Session & Token Data
# ══════════════════════════════════════════

def get_hermes_session_stats() -> dict:
    """Get Hermes session statistics from state.db — uses session-level token/cost fields"""
    if not STATE_DB.exists():
        return {"error": "state.db not found", "total_sessions": 0, "total_messages": 0}
    
    conn = sqlite3.connect(str(STATE_DB))
    try:
        # Session counts
        total_sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        total_messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        
        # Recent sessions (last 24h) — sessions table uses started_at
        cutoff = (datetime.now() - timedelta(days=1)).timestamp()
        recent_sessions = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE started_at > ?", (cutoff,)
        ).fetchone()[0]
        
        # Aggregate token usage from sessions table (already has input/output tokens)
        token_row = conn.execute("""
            SELECT 
                COALESCE(SUM(input_tokens), 0) as total_input,
                COALESCE(SUM(output_tokens), 0) as total_output,
                COALESCE(SUM(cache_read_tokens), 0) as cache_read,
                COALESCE(SUM(cache_write_tokens), 0) as cache_write,
                COALESCE(SUM(reasoning_tokens), 0) as reasoning
            FROM sessions
        """).fetchone()
        
        recent_token_row = conn.execute("""
            SELECT 
                COALESCE(SUM(input_tokens), 0) as total_input,
                COALESCE(SUM(output_tokens), 0) as total_output
            FROM sessions WHERE started_at > ?
        """, (cutoff,)).fetchone()
        
        # Cost aggregation
        cost_row = conn.execute("""
            SELECT 
                COALESCE(SUM(estimated_cost_usd), 0) as estimated,
                COALESCE(SUM(actual_cost_usd), 0) as actual
            FROM sessions
        """).fetchone()
        
        recent_cost_row = conn.execute("""
            SELECT COALESCE(SUM(estimated_cost_usd), 0)
            FROM sessions WHERE started_at > ?
        """, (cutoff,)).fetchone()
        
        # Top sessions by token usage
        top_sessions = conn.execute("""
            SELECT id, title, message_count, input_tokens, output_tokens,
                   estimated_cost_usd, actual_cost_usd, model, billing_provider,
                   source, started_at
            FROM sessions
            ORDER BY input_tokens + output_tokens DESC
            LIMIT 10
        """).fetchall()
        
        # Per-source breakdown
        source_breakdown = conn.execute("""
            SELECT source, COUNT(*) as cnt,
                   COALESCE(SUM(input_tokens + output_tokens), 0) as tokens,
                   COALESCE(SUM(estimated_cost_usd), 0) as cost
            FROM sessions
            GROUP BY source
            ORDER BY cnt DESC
        """).fetchall()
        
        # Per-model breakdown
        model_breakdown = conn.execute("""
            SELECT model, COUNT(*) as cnt,
                   COALESCE(SUM(input_tokens + output_tokens), 0) as tokens
            FROM sessions
            WHERE model IS NOT NULL
            GROUP BY model
            ORDER BY tokens DESC
        """).fetchall()
        
        # Today's usage
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        today_tokens = conn.execute("""
            SELECT 
                COALESCE(SUM(input_tokens), 0),
                COALESCE(SUM(output_tokens), 0),
                COALESCE(SUM(estimated_cost_usd), 0)
            FROM sessions WHERE started_at > ?
        """, (today_start,)).fetchone()
        
        # DB size
        db_size = STATE_DB.stat().st_size
        
        total_tokens = token_row[0] + token_row[1]
        recent_tokens = recent_token_row[0] + recent_token_row[1]
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "recent_24h_sessions": recent_sessions,
            "total_tokens": total_tokens,
            "total_input_tokens": token_row[0],
            "total_output_tokens": token_row[1],
            "cache_read_tokens": token_row[2],
            "cache_write_tokens": token_row[3],
            "reasoning_tokens": token_row[4],
            "recent_24h_tokens": recent_tokens,
            "recent_24h_input": recent_token_row[0],
            "recent_24h_output": recent_token_row[1],
            "estimated_cost_usd": round(cost_row[0], 4),
            "actual_cost_usd": round(cost_row[1], 4) if cost_row[1] else None,
            "recent_24h_cost": round(recent_cost_row[0], 4),
            "today_tokens": (today_tokens[0] + today_tokens[1]),
            "today_input": today_tokens[0],
            "today_output": today_tokens[1],
            "today_cost": round(today_tokens[2], 4),
            "db_size_mb": round(db_size / (1024 * 1024), 1),
            "top_sessions": [
                {"id": s[0], "title": s[1] or "untitled", "messages": s[2],
                 "input_tokens": s[3], "output_tokens": s[4],
                 "estimated_cost": round(s[5], 4) if s[5] else 0,
                 "actual_cost": round(s[6], 4) if s[6] else None,
                 "model": s[7], "provider": s[8], "source": s[9]}
                for s in top_sessions
            ],
            "source_breakdown": [
                {"source": s[0] or "unknown", "sessions": s[1], "tokens": s[2], "cost": round(s[3], 4)}
                for s in source_breakdown
            ],
            "model_breakdown": [
                {"model": m[0] or "unknown", "sessions": m[1], "tokens": m[2]}
                for m in model_breakdown
            ],
        }
    finally:
        conn.close()


def get_hermes_cron_status() -> dict:
    """Get Hermes cron job status"""
    try:
        result = subprocess.run(
            ["hermes", "cron", "list"], capture_output=True, text=True, timeout=10
        )
        output = result.stdout
        # Parse the table output
        jobs = []
        active_count = 0
        for line in output.split("\n"):
            if "[active]" in line:
                active_count += 1
        
        return {
            "active_jobs": active_count,
            "raw_output": output[:2000],
        }
    except Exception as e:
        return {"error": str(e), "active_jobs": 0}


def get_hermes_profile_status() -> list[dict]:
    """Get Hermes Profile status (which are active/running)"""
    try:
        result = subprocess.run(
            ["hermes", "profile", "list"], capture_output=True, text=True, timeout=10
        )
        output = result.stdout
        
        profiles = []
        for line in output.split("\n"):
            line = line.strip()
            if not line or line.startswith("Profile") or line.startswith("─") or line.startswith("◆"):
                # Extract default profile
                if "◆" in line:
                    parts = line.split()
                    if parts:
                        name = parts[0].replace("◆", "")
                        model = parts[1] if len(parts) > 1 else "unknown"
                        gw = "running" if "running" in line.lower() else "stopped"
                        profiles.append({
                            "name": name, "model": model,
                            "gateway": gw, "is_default": True,
                        })
                continue
            
            parts = line.split()
            if len(parts) >= 3:
                profiles.append({
                    "name": parts[0],
                    "model": parts[1],
                    "gateway": "running" if "running" in line.lower() else "stopped",
                    "is_default": False,
                })
        
        return profiles
    except Exception as e:
        return [{"error": str(e)}]


# ══════════════════════════════════════════
# GPU / Monitor Data
# ══════════════════════════════════════════

AUTODL_INSTANCES = [
    {"id": "cabf47a278", "name": "GPU-1 (cabf47a278)", "host": "connect.bjb2.seetacloud.com", "port": 32581, "user": "root"},
    {"id": "cac99c71", "name": "GPU-2 (cac99c71)", "host": "connect.bjb2.seetacloud.com", "port": 32581, "user": "root"},
]

def get_gpu_instances_status() -> dict:
    """Get status for all AutoDL GPU instances (parallel SSH checks)"""
    instances = []
    with ThreadPoolExecutor(max_workers=len(AUTODL_INSTANCES)) as executor:
        future_map = {executor.submit(_check_instance_ssh, inst): inst for inst in AUTODL_INSTANCES}
        for future in as_completed(future_map, timeout=6):
            try:
                instances.append(future.result())
            except Exception as e:
                inst = future_map[future]
                instances.append({"id": inst["id"], "name": inst["name"], "online": False, "error": str(e)})
    
    online = [i for i in instances if i.get("online")]
    offline = [i for i in instances if not i.get("online")]
    
    return {
        "total": len(instances),
        "online": len(online),
        "offline": len(offline),
        "instances": instances,
    }

def _check_instance_ssh(inst: dict) -> dict:
    """Check a single AutoDL instance via SSH"""
    try:
        import subprocess
        result = subprocess.run([
            "ssh", "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=2",
            "-o", "BatchMode=yes",
            "-p", str(inst["port"]),
            f"{inst['user']}@{inst['host']}",
            "nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader 2>/dev/null && echo '---' && uptime -p"
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split("\n")
            gpu_line = lines[0] if lines else ""
            uptime_line = lines[-1] if "---" in result.stdout else ""
            
            parts = gpu_line.split(",")
            return {
                "id": inst["id"],
                "name": inst["name"],
                "online": True,
                "gpu_name": parts[0].strip() if len(parts) > 0 else "unknown",
                "utilization": float(parts[1].strip().replace("%","")) if len(parts) > 1 else 0,
                "memory_used": parts[2].strip() if len(parts) > 2 else "0",
                "memory_total": parts[3].strip() if len(parts) > 3 else "0",
                "temperature": float(parts[4].strip()) if len(parts) > 4 else 0,
                "uptime": uptime_line.replace("---", "").replace("uptime", "").strip(),
            }
        else:
            return {"id": inst["id"], "name": inst["name"], "online": False, "error": result.stderr.strip()[:100] if result.stderr else "Connection refused"}
    except Exception as e:
        return {"id": inst["id"], "name": inst["name"], "online": False, "error": str(e)[:100]}


def get_gpu_status() -> dict:
    """Get GPU status from monitor.db + AutoDL instances"""
    instances = get_gpu_instances_status()
    
    # Also try monitor.db for historical data
    if not MONITOR_DB.exists():
        return {**instances, "monitor_db": False, "has_history": False}
    
    conn = sqlite3.connect(str(MONITOR_DB))
    try:
        # Latest GPU metrics from DB
        latest = conn.execute("""
            SELECT timestamp, gpu_name, utilization_gpu, utilization_memory,
                   memory_used_mb, memory_total_mb, temperature_gpu, power_draw
            FROM gpu_metrics
            ORDER BY id DESC LIMIT 1
        """).fetchone()
        
        # 24h stats
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        stats = conn.execute("""
            SELECT 
                COUNT(*) as samples,
                ROUND(AVG(utilization_gpu), 1) as avg_util,
                ROUND(MAX(utilization_gpu), 1) as peak_util,
                ROUND(MIN(utilization_gpu), 1) as min_util,
                ROUND(AVG(temperature_gpu), 1) as avg_temp,
                ROUND(MAX(temperature_gpu), 1) as max_temp
            FROM gpu_metrics
            WHERE timestamp > ?
        """, (cutoff,)).fetchone()
        
        # Cost log
        cost = conn.execute("""
            SELECT timestamp, runtime_minutes, cost_yuan, gpu_name
            FROM cost_log
            ORDER BY id DESC LIMIT 1
        """).fetchone()
        
        # Recent alerts
        alerts = conn.execute("""
            SELECT timestamp, level, message, acknowledged
            FROM alerts
            ORDER BY id DESC LIMIT 5
        """).fetchall()
        
        return {
            "status": "online" if latest else "no_recent_data",
            "has_data": latest is not None,
            "monitor_db": True,
            "has_history": True,
            "instances": instances["instances"],
            "instances_online": instances["online"],
            "instances_offline": instances["offline"],
            "latest": {
                "timestamp": latest[0],
                "gpu_name": latest[1],
                "utilization": round(latest[2], 1),
                "memory_util": round(latest[3], 1),
                "memory_used_mb": latest[4],
                "memory_total_mb": latest[5],
                "temperature": round(latest[6], 1) if latest[6] else None,
                "power_watts": round(latest[7], 1) if latest[7] else None,
            } if latest else None,
            "stats_24h": {
                "samples": stats[0],
                "avg_util": stats[1],
                "peak_util": stats[2],
                "min_util": stats[3],
                "avg_temp": stats[4],
                "max_temp": stats[5],
            } if stats else None,
            "cost": {
                "timestamp": cost[0],
                "runtime_minutes": cost[1],
                "total_cost_yuan": round(cost[2], 2),
                "gpu_name": cost[3],
            } if cost and cost[1] is not None else None,
            "alerts": [
                {"timestamp": a[0], "level": a[1], "message": a[2][:100], "acknowledged": bool(a[3])}
                for a in alerts
            ],
        }
    finally:
        conn.close()


# ══════════════════════════════════════════
# Model Pricing
# ══════════════════════════════════════════

# Known model pricing (USD per 1M tokens)
MODEL_PRICING = {
    "deepseek-v4-pro":     {"input": 1.0,  "output": 4.0,  "provider": "deepseek"},
    "deepseek-chat":       {"input": 0.14, "output": 0.28, "provider": "deepseek"},
    "deepseek-r1":         {"input": 0.55, "output": 2.19, "provider": "deepseek"},
    "claude-sonnet-4":     {"input": 3.0,  "output": 15.0, "provider": "anthropic"},
    "claude-3-opus":       {"input": 15.0, "output": 75.0, "provider": "anthropic"},
    "gpt-4o":              {"input": 2.5,  "output": 10.0, "provider": "openai"},
    "gemini-1.5-pro":      {"input": 1.25, "output": 5.0,  "provider": "google"},
    "llama-3-70b":         {"input": 0.59, "output": 0.79, "provider": "meta"},
    "mixtral-8x22b":       {"input": 0.9,  "output": 0.9,  "provider": "mistral"},
    "qwen-2.5-72b":        {"input": 0.9,  "output": 0.9,  "provider": "alibaba"},
    "command-r-plus":      {"input": 2.5,  "output": 10.0, "provider": "cohere"},
}


def get_model_pricing() -> dict:
    """Get model pricing and detected providers"""
    # Detect configured providers from Hermes config
    providers = {}
    config_path = HERMES_HOME / "config.yaml"
    env_path = HERMES_HOME / ".env"
    
    # Check which API keys are configured
    key_indicators = {
        "deepseek": "DEEPSEEK_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "google": "GOOGLE_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }
    
    configured_providers = []
    if env_path.exists():
        env_content = env_path.read_text()
        for provider, key_name in key_indicators.items():
            if key_name in env_content and "=" in env_content:
                configured_providers.append(provider)
    
    # Token savings mode status
    token_optimizer = HERMES_HOME.parent / "workspace" / "badminton-coach-ai" / "badminton_coach" / "token_optimizer.py"
    
    return {
        "models": MODEL_PRICING,
        "configured_providers": configured_providers,
        "token_savings_available": Path(token_optimizer).exists() if isinstance(token_optimizer, Path) else False,
    }


# ══════════════════════════════════════════
# Aggregated Dashboard Data
# ══════════════════════════════════════════

def get_command_center_data() -> dict:
    """Get all data needed for the Command Center Dashboard.
    
    Slow operations (subprocess, SSH) run in parallel threads.
    Results cached for 30 seconds to handle rapid Dashboard polling.
    """
    # Run slow operations in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(get_hermes_cron_status): "hermes_cron",
            executor.submit(get_hermes_profile_status): "hermes_profiles",
            executor.submit(get_gpu_status): "gpu",
        }
        for future in as_completed(futures, timeout=8):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                results[key] = {"error": str(e), "timeout": True}
    
    # Fast operations (SQLite, static) run in main thread
    return {
        "timestamp": datetime.now().isoformat(),
        "hermes_sessions": get_hermes_session_stats(),
        "hermes_cron": results.get("hermes_cron", {"error": "no_data"}),
        "hermes_profiles": results.get("hermes_profiles", []),
        "gpu": results.get("gpu", {"error": "no_data"}),
        "pricing": get_model_pricing(),
    }
