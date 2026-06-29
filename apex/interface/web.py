"""AgentArk — Web dashboard: REST API + SSE + OpenClaw + Hermes integration."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

try:
    from flask import Flask, render_template, jsonify, request, Response, stream_with_context
except ImportError:
    Flask = None

from apex.interface.middleware import (
    cors_headers, handle_cors_preflight, request_logger,
    register_error_handlers, log_event, get_log_buffer,
)
from apex.interface.event_stream import push_event, get_recent_events, format_sse


def create_app():
    """Create Flask application with full REST API + streaming."""
    if Flask is None:
        raise ImportError("Flask not installed. Run: pip install flask")

    app = Flask(__name__, template_folder=str(Path(__file__).parent / "templates"))

    # ── Imports ────────────────────────────────────────────────
    from apex.core.profile import ProfileManager, APEX_HOME, Profile, SoulConfig
    from apex.orchestration.kanban import Kanban
    from apex.core.evolution import EvolutionEngine
    from apex.core.knowledge import KnowledgeGraph
    from apex.economy import BudgetManager

    pm = ProfileManager()
    economy_db = APEX_HOME / "economy.db"
    evolution_db = APEX_HOME / "evolution.db"
    knowledge_db = APEX_HOME / "knowledge.db"
    kanban_db = APEX_HOME / "kanban.db"

    def load_evolution():
        return EvolutionEngine(evolution_db) if evolution_db.exists() else None

    def load_kanban():
        return Kanban(kanban_db) if kanban_db.exists() else None

    def load_kg():
        return KnowledgeGraph(knowledge_db) if knowledge_db.exists() else None

    def load_economy():
        return BudgetManager(economy_db) if economy_db.exists() else None

    # ── Register middleware ────────────────────────────────────
    register_error_handlers(app)

    @app.before_request
    def before_request():
        if request.method == "OPTIONS":
            return handle_cors_preflight()

    @app.after_request
    def after_request(response):
        cors_headers(response)
        return response

    # ══════════════════════════════════════════════════════════
    # SECTION 1: Dashboard Pages
    # ══════════════════════════════════════════════════════════

    @app.route("/")
    def index():
        """AgentArk Command Center — 多Agent指挥中心"""
        return render_template("command_center.html")

    # ══════════════════════════════════════════════════════════
    # SECTION 1b: Legacy routes (redirect to command center)
    # ══════════════════════════════════════════════════════════

    @app.route("/logs")
    def logs_page():
        return render_template("command_center.html", page="logs")

    @app.route("/auth")
    def auth_page():
        """🏛️ Authorization Management Dashboard — 审批/记录/审计可视化"""
        return render_template("auth.html")

    # ══════════════════════════════════════════════════════════
    # SECTION 2: System & Health
    # ══════════════════════════════════════════════════════════

    @app.route("/api/health")
    @request_logger
    def api_health():
        return jsonify({"status": "ok", "timestamp": time.time()})

    @app.route("/api/version")
    @request_logger
    def api_version():
        return jsonify({
            "version": "0.5.1",
            "name": "AgentArk",
            "description": "Multi-Agent Operating System",
            "python": __import__("sys").version,
        })

    @app.route("/api/config")
    @request_logger
    def api_config():
        """Expose Apex configuration (safe subset, no secrets)."""
        return jsonify({
            "apex_home": str(APEX_HOME),
            "profiles_count": len(pm.list()),
            "providers": ["deepseek", "ollama"],
            "economy_enabled": economy_db.exists(),
        })

    @app.route("/api/status")
    @request_logger
    def api_status():
        profiles = pm.list()
        k = load_kanban()
        tasks = k.list_tasks() if k else []
        evo = load_evolution()
        kg = load_kg()

        economy_data = {}
        eco = load_economy()
        if eco:
            used, limit, remaining = eco.get_balance("default")
            economy_data["default"] = {
                "used": round(used, 4), "limit": limit,
                "remaining": round(remaining, 4),
                "usage_pct": round(used / limit * 100, 1) if limit > 0 else 0,
            }

        evo_summary = evo.summary() if evo else {"patterns_discovered": 0}
        kg_stats = kg.stats() if kg else {"total_nodes": 0}

        return jsonify({
            "profiles": len(profiles),
            "version": "0.5.1",
            "status": "running",
            "uptime_seconds": time.time() - app._start_time if hasattr(app, "_start_time") else 0,
            "tasks": [{"id": t.id, "title": t.title[:50], "assignee": t.assignee,
                       "status": t.status, "priority": t.priority} for t in tasks[:30]],
            "economy": economy_data,
            "patterns": evo_summary.get("patterns_discovered", 0),
            "knowledge_nodes": kg_stats.get("total_nodes", 0),
            "recent_tasks": [{"id": t.id, "title": t.title[:40], "status": t.status,
                             "assignee": t.assignee} for t in tasks[:5]],
        })

    # ══════════════════════════════════════════════════════════
    # SECTION 3: Agent Profiles
    # ══════════════════════════════════════════════════════════

    @app.route("/api/profiles", methods=["GET", "POST"])
    @request_logger
    def api_profiles():
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            name = data.get("name", f"agent_{uuid.uuid4().hex[:6]}")
            role = data.get("role", "Assistant")
            profile = Profile(name=name, soul=SoulConfig(role=role))
            if data.get("expertise"):
                profile.soul.expertise = data["expertise"]
            if data.get("model"):
                profile.model.default = data["model"]
            if data.get("skills"):
                profile.skills = data["skills"]
            pm.save(profile)
            push_event("profile", {"action": "created", "name": name})
            log_event("info", f"Profile created: {name} ({role})")
            return jsonify({"name": name, "role": role}), 201

        # GET — list all profiles
        profiles = []
        for name in pm.list():
            try:
                p = pm.load(name)
                profiles.append({
                    "name": p.name, "role": p.soul.role,
                    "model": p.model.default, "expertise": p.soul.expertise,
                    "skills": p.skills, "auto_improve": p.auto_improve,
                    "personality": p.soul.personality,
                    "communication": p.soul.communication,
                })
            except Exception as e:
                profiles.append({"name": name, "error": str(e)})
        return jsonify(profiles)

    @app.route("/api/profiles/<name>", methods=["GET", "DELETE"])
    @request_logger
    def api_profile_detail(name: str):
        if request.method == "DELETE":
            try:
                pm.delete(name)
                push_event("profile", {"action": "deleted", "name": name})
                log_event("info", f"Profile deleted: {name}")
                return jsonify({"deleted": name})
            except Exception as e:
                return jsonify({"error": str(e)}), 400
        # GET
        try:
            p = pm.load(name)
            evo = load_evolution()
            evo_data = evo.get_agent_evolution(name) if evo else {}
            return jsonify({
                "name": p.name, "display": p.display,
                "model": {"default": p.model.default, "fallback": p.model.fallback, "vision": p.model.vision},
                "token_budget": p.token_budget,
                "soul": {"role": p.soul.role, "expertise": p.soul.expertise,
                         "personality": p.soul.personality, "communication": p.soul.communication},
                "skills": p.skills, "auto_improve": p.auto_improve,
                "evolution": evo_data,
            })
        except FileNotFoundError:
            return jsonify({"error": f"Profile '{name}' not found"}), 404

    # ══════════════════════════════════════════════════════════
    # SECTION 4: Task Management (Kanban)
    # ══════════════════════════════════════════════════════════

    @app.route("/api/tasks", methods=["GET", "POST"])
    @request_logger
    def api_tasks():
        k = load_kanban()
        if not k:
            return jsonify({"error": "Kanban not initialized"}), 503

        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            title = data.get("title", "Untitled")
            assignee = data.get("assignee", "")
            priority = data.get("priority", 2)
            task = k.create_task(title=title, assignee=assignee, priority=priority)
            push_event("task", {"action": "created", "id": task.id, "title": title})
            log_event("info", f"Task created: {title}")
            return jsonify({"id": task.id, "title": title, "assignee": assignee, "status": "todo"}), 201

        tasks = k.list_tasks()
        return jsonify([{
            "id": t.id, "title": t.title, "assignee": t.assignee,
            "status": t.status, "priority": t.priority,
            "created_at": t.created_at, "completed_at": t.completed_at, "cost": t.cost,
        } for t in tasks])

    @app.route("/api/tasks/<task_id>", methods=["GET", "PUT", "DELETE"])
    @request_logger
    def api_task_detail(task_id: str):
        k = load_kanban()
        if not k:
            return jsonify({"error": "Kanban not initialized"}), 503

        if request.method == "DELETE":
            return jsonify({"deleted": task_id})
        if request.method == "PUT":
            data = request.get_json(silent=True) or {}
            status = data.get("status")
            if status:
                k.update_task(task_id, status=status)
                push_event("task", {"action": "updated", "id": task_id, "status": status})
                log_event("info", f"Task {task_id} -> {status}")
            return jsonify({"id": task_id, "status": status or "unchanged"})

        tasks = k.list_tasks()
        for t in tasks:
            if t.id == task_id:
                return jsonify({"id": t.id, "title": t.title, "assignee": t.assignee,
                               "status": t.status, "priority": t.priority})
        return jsonify({"error": "Task not found"}), 404

    # ══════════════════════════════════════════════════════════
    # SECTION 5: Agent Execution
    # ══════════════════════════════════════════════════════════

    @app.route("/api/run", methods=["POST"])
    @request_logger
    def api_run():
        data = request.get_json(silent=True) or {}
        task = data.get("task", "")
        profile_name = data.get("profile", "default")
        model = data.get("model", "")
        heal = data.get("heal", False)

        if not task:
            return jsonify({"error": "task is required"}), 400

        try:
            prof = pm.load(profile_name)
        except FileNotFoundError:
            prof = pm.create_default(profile_name)

        from apex.core.runtime import Agent
        agent = Agent(prof)
        start = time.time()

        try:
            kwargs = {}
            if model:
                kwargs["model"] = model
            output = agent.run(task, heal=heal, **kwargs)
            duration = int((time.time() - start) * 1000)
            push_event("execution", {"agent": profile_name, "success": True, "task": task[:50]})
            log_event("info", f"Agent {profile_name} completed in {duration}ms")
            return jsonify({
                "success": True, "output": output[:5000],
                "agent": profile_name, "cost": round(agent.context.cost, 6),
                "duration_ms": duration, "steps": len(agent.context.trace),
            })
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            push_event("execution", {"agent": profile_name, "success": False, "task": task[:50]})
            log_event("error", f"Agent {profile_name} failed in {duration}ms: {e}")
            return jsonify({"success": False, "error": str(e)[:500], "duration_ms": duration}), 500

    @app.route("/api/run/swarm", methods=["POST"])
    @request_logger
    def api_run_swarm():
        data = request.get_json(silent=True) or {}
        task = data.get("task", "")
        workers = data.get("workers", 3)
        if not task:
            return jsonify({"error": "task is required"}), 400

        try:
            from apex.orchestration.swarm import Swarm
            worker_profiles = []
            available = pm.list()
            for i in range(min(workers, len(available))):
                worker_profiles.append(pm.load(available[i]))
            if not worker_profiles:
                worker_profiles.append(pm.load("default"))
            swarm = Swarm(worker_profiles)
            start = time.time()
            result = swarm.run(task)
            duration = int((time.time() - start) * 1000)
            output = result.output if hasattr(result, "output") else str(result)
            push_event("execution", {"mode": "swarm", "success": result.success, "task": task[:50]})
            log_event("info", f"Swarm ({workers} workers) completed in {duration}ms")
            return jsonify({
                "success": result.success, "output": str(output)[:5000],
                "workers": workers, "duration_ms": duration,
            })
        except Exception as e:
            log_event("error", f"Swarm failed: {e}")
            return jsonify({"success": False, "error": str(e)[:500]}), 500

    # ══════════════════════════════════════════════════════════
    # SECTION 6: Knowledge Graph
    # ══════════════════════════════════════════════════════════

    @app.route("/api/knowledge", methods=["GET", "POST"])
    @request_logger
    def api_knowledge():
        kg = load_kg()
        if not kg:
            return jsonify({"nodes": 0, "edges": 0})

        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            action = data.get("action", "query")
            if action == "query":
                query = data.get("query", "")
                result = kg.query(query)
                return jsonify({
                    "query": query, "answer": result.answer[:3000],
                    "confidence": result.confidence, "evidence": len(result.evidence),
                })
            elif action == "learn":
                entity = data.get("entity", "")
                source = data.get("source", "api")
                if entity:
                    kg.learn(entity, source=source)
                    return jsonify({"learned": entity})
            return jsonify({"error": f"Unknown action: {action}"}), 400

        stats = kg.stats()
        return jsonify({
            "nodes": stats.get("total_nodes", 0),
            "edges": stats.get("total_edges", 0),
            "conflicts": stats.get("unresolved_conflicts", 0),
            "distribution": stats.get("type_distribution", {}),
        })

    # ══════════════════════════════════════════════════════════
    # SECTION 7: Evolution Engine
    # ══════════════════════════════════════════════════════════

    @app.route("/api/evolution")
    @request_logger
    def api_evolution():
        evo = load_evolution()
        if not evo:
            return jsonify({"total_executions": 0, "patterns": 0})
        return jsonify(evo.summary())

    # ══════════════════════════════════════════════════════════
    # SECTION 8: Economy & Analytics
    # ══════════════════════════════════════════════════════════

    @app.route("/api/economy")
    @request_logger
    def api_economy():
        eco = load_economy()
        if not eco:
            return jsonify({"status": "disabled"})
        used, limit, remaining = eco.get_balance("default")
        return jsonify({
            "used": round(used, 4), "limit": limit,
            "remaining": round(remaining, 4),
            "usage_pct": round(used / limit * 100, 1) if limit > 0 else 0,
        })

    @app.route("/api/analytics/costs")
    @request_logger
    def api_analytics_costs():
        """Token cost time-series (from Hermes sessions)."""
        try:
            from apex.interface.hermes_bridge import get_hermes_session_stats
            stats = get_hermes_session_stats()
            return jsonify({
                "today_cost": stats.get("today_cost", 0),
                "today_tokens": stats.get("today_tokens", 0),
                "total_cost": stats.get("estimated_cost_usd", 0),
                "total_tokens": stats.get("total_tokens", 0),
            })
        except Exception as e:
            return jsonify({"error": str(e), "today_cost": 0})

    @app.route("/api/analytics/executions")
    @request_logger
    def api_analytics_executions():
        """Execution trends from Evolution Engine."""
        evo = load_evolution()
        if not evo:
            return jsonify({"total": 0})
        summary = evo.summary()
        return jsonify({
            "total": summary.get("total_executions", 0),
            "patterns": summary.get("patterns_discovered", 0),
            "agents_with_history": summary.get("agents_with_history", 0),
        })

    # ══════════════════════════════════════════════════════════
    # SECTION 9: Companies
    # ══════════════════════════════════════════════════════════

    @app.route("/api/companies")
    @request_logger
    def api_companies():
        companies_dir = APEX_HOME / "companies"
        if not companies_dir.exists():
            return jsonify([])
        companies = []
        for c_path in sorted(companies_dir.glob("*.json"), reverse=True)[:20]:
            try:
                data = json.loads(c_path.read_text())
                companies.append({
                    "name": data.get("name"), "industry": data.get("industry"),
                    "profiles": data.get("profiles", []), "sop": data.get("sop", {}),
                    "created_at": data.get("created_at", 0),
                })
            except Exception:
                pass
        return jsonify(companies)

    # ══════════════════════════════════════════════════════════
    # SECTION 10: Ops (Release / Bug / Task)
    # ══════════════════════════════════════════════════════════

    @app.route("/api/ops")
    @request_logger
    def api_ops():
        try:
            from apex.orchestration.ops import get_ops
            ops = get_ops()
            stats = ops.get_dashboard_stats()
            bugs = ops.list_bugs(status="open", limit=10)
            releases = ops.list_releases(limit=5)
            tasks = ops.list_tasks(limit=10)
            return jsonify({
                "stats": stats,
                "bugs": [{"id": b.id, "title": b.title[:60], "severity": b.severity.value,
                          "status": b.status.value, "assigned_agent": b.assigned_agent,
                          "sla_remaining_hours": b.sla_remaining_hours,
                          "sla_breached": b.sla_breached} for b in bugs],
                "releases": [{"id": r.id, "version": r.version, "name": r.name,
                              "status": r.status, "progress_pct": round(r.progress_pct * 100),
                              "stages": [{"label": s["label"], "status": s["status"]} for s in r.stages]}
                             for r in releases],
                "tasks_summary": [{"id": t.id, "title": t.title[:50], "phase": t.phase,
                                   "status": t.status.value, "agent_id": t.agent_id,
                                   "test_pass_rate": round(t.test_pass_rate * 100) if hasattr(t, 'test_pass_rate') else 0,
                                   "quality_score": t.quality_score} for t in tasks],
            })
        except Exception as e:
            return jsonify({"error": str(e)})

    # ══════════════════════════════════════════════════════════
    # SECTION 11: Autonomous Engine
    # ══════════════════════════════════════════════════════════

    @app.route("/api/autonomous")
    @request_logger
    def api_autonomous():
        try:
            from apex.orchestration.autonomous import get_engine
            eng = get_engine()
            report = eng.generate_report()
            return jsonify({
                "status": report.engine_status, "uptime": report.uptime_seconds,
                "heartbeats": [{"name": h.agent_name, "status": h.status, "load": h.load,
                                "tasks_completed": h.tasks_completed, "tasks_failed": h.tasks_failed,
                                "message": h.message, "last_active": h.last_active}
                               for h in report.active_agents],
                "scheduled_tasks": len(report.scheduled_tasks),
                "pending_queue": report.pending_queue,
                "total_executed": report.tasks_executed_total,
                "succeeded": report.tasks_succeeded, "failed": report.tasks_failed,
                "knowledge_nodes": report.knowledge_nodes,
                "evolution_patterns": report.evolution_patterns,
                "alerts": report.alerts, "recommendations": report.recommendations,
            })
        except Exception as e:
            return jsonify({"status": "unavailable", "error": str(e)})

    # ══════════════════════════════════════════════════════════
    # SECTION 12: Hermes Integration
    # ══════════════════════════════════════════════════════════

    @app.route("/api/hermes/status")
    @request_logger
    def api_hermes_status():
        try:
            from apex.interface.hermes_bridge import get_hermes_session_stats, get_hermes_cron_status, get_hermes_profile_status
            return jsonify({
                "sessions": get_hermes_session_stats(),
                "cron": get_hermes_cron_status(),
                "profiles": get_hermes_profile_status(),
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/hermes/tokens")
    @request_logger
    def api_hermes_tokens():
        try:
            from apex.interface.hermes_bridge import get_hermes_session_stats
            return jsonify(get_hermes_session_stats())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/gpu/status")
    @request_logger
    def api_gpu_status():
        try:
            from apex.interface.gpu_manager import get_gpu_status
            return jsonify(get_gpu_status())
        except Exception as e:
            return jsonify({"error": str(e), "status": "error"}), 500

    @app.route("/api/models/pricing")
    @request_logger
    def api_models_pricing():
        try:
            from apex.interface.hermes_bridge import get_model_pricing
            return jsonify(get_model_pricing())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ═══ Cost Tracking API ═══

    @app.route("/api/cost/summary")
    @request_logger
    def api_cost_summary():
        """💰 成本总览"""
        try:
            from apex.cost_tracker import get_summary
            return jsonify(get_summary())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/cost/cron")
    @request_logger
    def api_cost_cron():
        """📋 每个Cron任务的成本明细"""
        try:
            from apex.cost_tracker import get_cron_costs
            days = request.args.get("days", 30, type=int)
            costs = get_cron_costs(days)
            return jsonify([c.__dict__ for c in costs])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/cost/agents")
    @request_logger
    def api_cost_agents():
        """🤖 每个Agent Profile的成本明细"""
        try:
            from apex.cost_tracker import get_agent_costs
            days = request.args.get("days", 30, type=int)
            costs = get_agent_costs(days)
            return jsonify([c.__dict__ for c in costs])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/cost/sources")
    @request_logger
    def api_cost_sources():
        """📡 按来源渠道分解"""
        try:
            from apex.cost_tracker import get_source_breakdown
            days = request.args.get("days", 30, type=int)
            return jsonify(get_source_breakdown(days))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/cost/projects")
    @request_logger
    def api_cost_projects():
        """📦 按项目聚合成本"""
        try:
            from apex.cost_tracker import estimate_project_costs
            costs = estimate_project_costs()
            return jsonify([c.__dict__ for c in costs])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/cost/timeline")
    @request_logger
    def api_cost_timeline():
        """📈 成本趋势 (hourly/daily)"""
        try:
            from apex.cost_tracker import get_timeline
            days = request.args.get("days", 7, type=int)
            granularity = request.args.get("granularity", "daily")
            return jsonify(get_timeline(days, granularity))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/cost/full")
    @request_logger
    def api_cost_full():
        """📊 完整成本快照 (Dashboard用)"""
        try:
            from apex.cost_tracker import get_full_snapshot
            return jsonify(get_full_snapshot())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/command-center")
    @request_logger
    def api_command_center():
        try:
            from apex.interface.hermes_bridge import get_command_center_data
            return jsonify(get_command_center_data())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ══════════════════════════════════════════════════════════
    # SECTION 13: 🌉 Apex-Hermes Bridge
    # ══════════════════════════════════════════════════════════

    @app.route("/api/bridge/status")
    def api_bridge_status():
        """Bridge fleet health status"""
        try:
            from apex.cli.commands.bridge import get_bridge_status
            return jsonify(get_bridge_status())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/bridge/sync", methods=["POST"])
    def api_bridge_sync():
        """Trigger a bridge sync cycle"""
        try:
            from apex.cli.commands.bridge import run_bridge_sync
            status = run_bridge_sync()
            push_event("bridge", {"action": "sync", "healthy": status.get("healthy", 0)})
            log_event("info", f"Bridge sync: {status.get('healthy')}/{status.get('total')} healthy")
            return jsonify(status)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/bridge/init", methods=["POST"])
    def api_bridge_init():
        """Create/update bridge agents"""
        try:
            from apex.cli.commands.bridge import init_bridge_agents
            result = init_bridge_agents()
            push_event("bridge", {"action": "init", "created": len(result["created"])})
            log_event("info", f"Bridge init: {len(result['created'])} created, {len(result['updated'])} updated")
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ══════════════════════════════════════════════════════════
    # SECTION 14.5: 🔀 智能消息路由 (Message Router)
    # ══════════════════════════════════════════════════════════

    _router = None

    def get_router():
        nonlocal _router
        if _router is None:
            from apex.orchestration.message_router import MessageRouter
            _router = MessageRouter()
        return _router

    @app.route("/api/router/analyze", methods=["POST"])
    def api_router_analyze():
        """分析消息 → 返回项目/类别/Agent，不执行"""
        data = request.get_json(silent=True) or {}
        message = data.get("message", "")
        prefer_project = data.get("project", "")
        if not message:
            return jsonify({"error": "message is required"}), 400
        try:
            result = get_router().analyze(message, prefer_project=prefer_project)
            return jsonify({
                "project": result.project,
                "project_name": result.project_name,
                "project_emoji": result.project_emoji,
                "category": result.category,
                "category_name": result.category_name,
                "agent_profile": result.agent_profile,
                "agent_role": result.agent_role,
                "agent_emoji": result.agent_emoji,
                "confidence": result.confidence,
                "keywords_matched": result.keywords_matched,
                "reasoning": result.reasoning,
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/router/dispatch", methods=["POST"])
    def api_router_dispatch():
        """分析消息 + 分发到对应 Agent Profile 执行"""
        data = request.get_json(silent=True) or {}
        message = data.get("message", "")
        prefer_project = data.get("project", "")
        execute = data.get("execute", False)  # 是否真正调用 Agent
        if not message:
            return jsonify({"error": "message is required"}), 400
        try:
            router_obj = get_router()
            result = router_obj.analyze(message, prefer_project=prefer_project)

            response = {
                "analysis": {
                    "project": result.project,
                    "project_name": result.project_name,
                    "project_emoji": result.project_emoji,
                    "category": result.category,
                    "category_name": result.category_name,
                    "agent_profile": result.agent_profile,
                    "agent_role": result.agent_role,
                    "agent_emoji": result.agent_emoji,
                    "confidence": result.confidence,
                    "reasoning": result.reasoning,
                },
                "formatted": result.format_output(f"消息已路由至 {result.agent_role}"),
            }

            if execute:
                # 调用 Agent 执行
                try:
                    prof = pm.load(result.agent_profile)
                except FileNotFoundError:
                    prof = pm.create_default(result.agent_profile)
                from apex.core.runtime import Agent
                agent = Agent(prof)
                start = time.time()
                output = agent.run(message)
                duration = int((time.time() - start) * 1000)
                response["execution"] = {
                    "success": True,
                    "output": output[:3000],
                    "agent": result.agent_profile,
                    "duration_ms": duration,
                    "cost": round(agent.context.cost, 6),
                }
                push_event("router", {"action": "dispatched", "project": result.project,
                           "agent": result.agent_profile, "category": result.category})

            return jsonify(response)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/router/matrix")
    def api_router_matrix():
        """返回完整的项目-类别-Agent映射矩阵"""
        try:
            return jsonify(get_router().get_matrix())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/router/quick")
    def api_router_quick():
        """快速分析 (GET参数 ?msg=...)"""
        msg = request.args.get("msg", "")
        if not msg:
            return jsonify({"error": "msg parameter required"}), 400
        try:
            return jsonify({"quick": get_router().quick(msg)})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/origin/overview")
    def api_origin_overview():
        """Fleet overview — all portfolios"""
        try:
            from apex.orchestration.origin import OriginAgent
            return jsonify(OriginAgent().portfolio_overview())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/origin/portfolios", methods=["GET", "POST"])
    def api_origin_portfolios():
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            from apex.orchestration.origin import OriginAgent
            result = OriginAgent().create_portfolio(
                name=data.get("name", ""),
                description=data.get("description", ""),
                strategic_goal=data.get("strategic_goal", ""),
                expected_outcome=data.get("expected_outcome", ""),
                pm_agent=data.get("pm_agent", ""),
            )
            push_event("origin", {"action": "portfolio_created", "name": data.get("name", "")})
            return jsonify(result), 201 if result.get("ok") else 400

        from apex.orchestration.origin import OriginAgent
        return jsonify(OriginAgent().list_portfolios())

    @app.route("/api/origin/portfolios/<portfolio_id>")
    def api_origin_portfolio_detail(portfolio_id: str):
        from apex.orchestration.origin import OriginAgent
        pf = OriginAgent().get_portfolio_status(portfolio_id)
        if "error" in pf:
            return jsonify(pf), 404
        return jsonify(pf)

    @app.route("/api/origin/replicate", methods=["POST"])
    def api_origin_replicate():
        data = request.get_json(silent=True) or {}
        target = data.get("target", "")
        all_agents = data.get("all", False)
        strategy = data.get("strategy", "merge")
        from apex.orchestration.origin import OriginAgent
        origin = OriginAgent()
        if all_agents:
            result = origin.replicate_to_all()
        elif target:
            result = origin.replicate_to(target, strategy=strategy)
        else:
            return jsonify({"error": "请指定target或all=true"}), 400
        push_event("origin", {"action": "replicate", "target": target or "all"})
        return jsonify(result)

    # ══════════════════════════════════════════════════════════
    # SECTION 15: OpenClaw Integration
    # ══════════════════════════════════════════════════════════

    @app.route("/api/openclaw/status")
    @request_logger
    def api_openclaw_status():
        """OpenClaw connectivity and system status."""
        try:
            from apex.interface.openclaw_bridge import get_status_summary
            status = get_status_summary()
            status["openclaw_home"] = str(Path(os.environ.get("OPENCLAW_HOME", "~/.openclaw")).expanduser())
            return jsonify(status)
        except Exception as e:
            return jsonify({"error": str(e), "status": "error"}), 500

    @app.route("/api/openclaw/tools")
    @request_logger
    def api_openclaw_tools():
        """List tools available for OpenClaw to call."""
        try:
            from apex.interface.openclaw_bridge import get_available_tools
            return jsonify(get_available_tools())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/openclaw/run", methods=["POST"])
    @request_logger
    def api_openclaw_run():
        """Execute a tool via OpenClaw bridge."""
        data = request.get_json(silent=True) or {}
        tool = data.get("tool", "")
        params = data.get("params", {})

        from apex.interface.openclaw_bridge import (
            run_agent, run_swarm, query_knowledge, list_profiles, get_status_summary,
        )

        tool_map = {
            "apex.run_agent": lambda: run_agent(**params),
            "apex.run_swarm": lambda: run_swarm(**params),
            "apex.query_knowledge": lambda: query_knowledge(**params),
            "apex.list_profiles": lambda: list_profiles(),
            "apex.get_status": lambda: get_status_summary(),
        }
        handler = tool_map.get(tool)
        if not handler:
            return jsonify({"error": f"Unknown tool: {tool}",
                           "available": list(tool_map.keys())}), 400
        try:
            result = handler()
            push_event("openclaw", {"tool": tool, "success": result.get("success", True)})
            return jsonify(result)
        except Exception as e:
            log_event("error", f"OpenClaw tool '{tool}' failed: {e}")
            return jsonify({"success": False, "error": str(e)[:500]}), 500

    @app.route("/api/openclaw/workflows")
    @request_logger
    def api_openclaw_workflows():
        """List predefined multi-agent workflows."""
        try:
            from apex.interface.openclaw_bridge import get_workflows
            return jsonify(get_workflows())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ══════════════════════════════════════════════════════════
    # SECTION 13.5: 🏛️ Authorization Engine (特权操作授权)
    # ══════════════════════════════════════════════════════════

    _auth_engine = None

    def get_auth_engine():
        nonlocal _auth_engine
        if _auth_engine is None:
            from apex.orchestration.authorization import AuthorizationEngine
            _auth_engine = AuthorizationEngine()
        return _auth_engine

    @app.route("/api/auth/scopes")
    def api_auth_scopes():
        """列出所有授权 scope 定义"""
        try:
            return jsonify(get_auth_engine().get_scopes())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/auth/stats")
    def api_auth_stats():
        """授权统计：总数/待审/活跃/按scope分布"""
        try:
            return jsonify(get_auth_engine().stats())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/auth/verify")
    def api_auth_verify():
        """验证哈希链完整性"""
        try:
            return jsonify(get_auth_engine().verify())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/auth/request", methods=["POST"])
    def api_auth_request():
        """请求授权 — Agent 发起特权操作前"""
        data = request.get_json(silent=True) or {}
        agent = data.get("agent", "")
        scope = data.get("scope", "")
        purpose = data.get("purpose", "")
        ttl_min = data.get("ttl_min")

        if not agent or not scope:
            return jsonify({"error": "agent and scope are required"}), 400

        try:
            result = get_auth_engine().request(
                agent=agent, scope=scope, purpose=purpose or "(未指定)",
                ttl_min=ttl_min,
            )
            if result.get("ok"):
                push_event("auth", {"action": "requested", "request_code": result["request_code"],
                           "agent": agent, "scope": scope})
                log_event("info", f"Auth requested: {agent} → {scope} (#{result['request_code']})")
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/auth/approve", methods=["POST"])
    def api_auth_approve():
        """审批授权 — 老卢通过微信确认码审批"""
        data = request.get_json(silent=True) or {}
        request_code = data.get("request_code", "")

        if not request_code:
            return jsonify({"error": "request_code is required"}), 400

        try:
            result = get_auth_engine().approve(request_code)
            if result.get("ok"):
                push_event("auth", {"action": "approved", "request_code": request_code,
                           "agent": result["agent"], "scope": result["scope"]})
                log_event("info", f"Auth approved: #{request_code} → {result['agent']} / {result['scope']}")
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/auth/deny", methods=["POST"])
    def api_auth_deny():
        """拒绝授权"""
        data = request.get_json(silent=True) or {}
        request_code = data.get("request_code", "")

        if not request_code:
            return jsonify({"error": "request_code is required"}), 400

        try:
            result = get_auth_engine().deny(request_code)
            if result.get("ok"):
                push_event("auth", {"action": "denied", "request_code": request_code})
                log_event("info", f"Auth denied: #{request_code}")
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/auth/check")
    def api_auth_check():
        """检查 Agent 是否有有效授权"""
        agent = request.args.get("agent", "")
        scope = request.args.get("scope", "")

        if not agent or not scope:
            return jsonify({"error": "agent and scope are required"}), 400

        try:
            result = get_auth_engine().check(agent, scope)
            return jsonify({
                "authorized": result.authorized,
                "message": result.message,
                "grant_id": result.grant_id,
                "request_code": result.request_code,
                "remaining_minutes": result.remaining_minutes,
                "scope": result.scope,
                "agent": result.agent,
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/auth/consume", methods=["POST"])
    def api_auth_consume():
        """使用授权 — 执行后标记已用"""
        data = request.get_json(silent=True) or {}
        grant_id = data.get("grant_id", "")

        if not grant_id:
            return jsonify({"error": "grant_id is required"}), 400

        try:
            result = get_auth_engine().consume(grant_id)
            if result.get("ok"):
                push_event("auth", {"action": "consumed", "grant_id": grant_id})
                log_event("info", f"Auth consumed: {grant_id}")
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/auth/revoke", methods=["POST"])
    def api_auth_revoke():
        """吊销授权"""
        data = request.get_json(silent=True) or {}
        grant_id = data.get("grant_id", "")
        reason = data.get("reason", "")

        if not grant_id:
            return jsonify({"error": "grant_id is required"}), 400

        try:
            result = get_auth_engine().revoke(grant_id, reason)
            if result.get("ok"):
                push_event("auth", {"action": "revoked", "grant_id": grant_id})
                log_event("info", f"Auth revoked: {grant_id} — {reason}")
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/auth/grants")
    def api_auth_grants():
        """列出授权记录（支持筛选）"""
        try:
            agent = request.args.get("agent", "")
            scope = request.args.get("scope", "")
            status = request.args.get("status", "")
            limit = request.args.get("limit", 50, type=int)
            grants = get_auth_engine().list_grants(
                agent=agent, scope=scope, status=status, limit=limit,
            )
            return jsonify(grants)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/auth/audit")
    def api_auth_audit():
        """获取审计日志"""
        try:
            days = request.args.get("days", 7, type=int)
            limit = request.args.get("limit", 200, type=int)
            logs = get_auth_engine().get_audit(days=days, limit=limit)
            return jsonify(logs)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ── v3: 委派管理 & 双重审批 ──────────────────────────

    @app.route("/api/auth/delegations")
    def api_auth_delegations():
        """委派矩阵 — 谁可以批什么"""
        try:
            return jsonify(get_auth_engine().get_delegation_matrix())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/auth/delegations/list")
    def api_auth_delegations_list():
        """列出所有委派记录"""
        try:
            delegator = request.args.get("delegator", "")
            delegate = request.args.get("delegate", "")
            delegations = get_auth_engine().list_delegations(delegator, delegate)
            return jsonify(delegations)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/auth/delegations/modify", methods=["POST"])
    def api_auth_delegations_modify():
        """修改委派关系 (仅始祖)"""
        data = request.get_json(silent=True) or {}
        delegator = data.get("delegator", "")
        delegate = data.get("delegate", "")
        scopes = data.get("scopes", [])
        description = data.get("description", "")

        if not delegator or not delegate or not scopes:
            return jsonify({"error": "delegator, delegate, scopes are required"}), 400

        try:
            result = get_auth_engine().modify_delegation(delegator, delegate, scopes, description)
            if result.get("ok"):
                push_event("auth", {"action": "delegation_modified", "delegate": delegate})
                log_event("info", f"Delegation modified: {delegator} → {delegate} ({len(scopes)} scopes)")
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/auth/delegations/revoke", methods=["POST"])
    def api_auth_delegations_revoke():
        """吊销委派"""
        data = request.get_json(silent=True) or {}
        delegator = data.get("delegator", "")
        delegate = data.get("delegate", "")

        if not delegator or not delegate:
            return jsonify({"error": "delegator and delegate are required"}), 400

        try:
            result = get_auth_engine().revoke_delegation(delegator, delegate)
            if result.get("ok"):
                push_event("auth", {"action": "delegation_revoked", "delegate": delegate})
                log_event("info", f"Delegation revoked: {delegate}")
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/auth/delegations/check")
    def api_auth_delegations_check():
        """检查委派范围内的 scope"""
        delegate = request.args.get("delegate", "")
        scope = request.args.get("scope", "")
        if not delegate or not scope:
            return jsonify({"error": "delegate and scope are required"}), 400
        try:
            return jsonify(get_auth_engine().check_delegation_scope(delegate, scope))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/auth/origin-pre-approve", methods=["POST"])
    def api_auth_origin_pre_approve():
        """始祖预批 — 双重审批第一步"""
        data = request.get_json(silent=True) or {}
        request_code = data.get("request_code", "")
        if not request_code:
            return jsonify({"error": "request_code is required"}), 400
        try:
            result = get_auth_engine().origin_pre_approve(request_code)
            if result.get("ok"):
                push_event("auth", {"action": "origin_pre_approved", "request_code": request_code})
                log_event("info", f"Origin pre-approved: #{request_code} → {result.get('next_step', '')}")
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ══════════════════════════════════════════════════════════
    # SECTION 14: Real-time Streaming (SSE)
    # ══════════════════════════════════════════════════════════

    @app.route("/api/stream/logs")
    @request_logger
    def api_stream_logs():
        """SSE stream of log events."""
        def generate():
            last_index = len(get_log_buffer())
            yield "event: connected\ndata: {}\n\n"
            while True:
                logs = get_log_buffer(limit=100)
                if len(logs) > last_index:
                    for entry in logs[last_index:]:
                        yield format_sse({"type": "log", "data": entry})
                    last_index = len(logs)
                time.sleep(1)
        return Response(stream_with_context(generate()), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.route("/api/stream/events")
    @request_logger
    def api_stream_events():
        """SSE stream of all system events."""
        def generate():
            seen = set()
            yield "event: connected\ndata: {}\n\n"
            while True:
                events = get_recent_events(limit=50)
                for event in events:
                    event_id = id(event)
                    if event_id not in seen:
                        yield format_sse(event)
                        seen.add(event_id)
                if len(seen) > 500:
                    seen.clear()
                time.sleep(0.5)
        return Response(stream_with_context(generate()), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.route("/api/logs")
    @request_logger
    def api_logs():
        """Get recent log buffer entries."""
        limit = request.args.get("limit", 100, type=int)
        return jsonify(get_log_buffer(limit=limit))

    @app.route("/api/events")
    @request_logger
    def api_events():
        """Get recent events."""
        limit = request.args.get("limit", 50, type=int)
        event_type = request.args.get("type")
        events = get_recent_events(limit=limit, event_type=event_type)
        return jsonify(events)

    # ══════════════════════════════════════════════════════════
    # SECTION 15: WebSocket via Socket.IO fallback (SSE poll)
    # ══════════════════════════════════════════════════════════

    @app.route("/api/ping")
    def api_ping():
        """Lightweight connectivity check."""
        return jsonify({"pong": True, "time": time.time()})

    # Record start time
    app._start_time = time.time()

    @app.route("/api/environment")
    def api_environment():
        """System environment — OS, Python, Hermes, Apex, installed tools"""
        import platform, sys, subprocess as sp
        info = {
            "os": platform.system(),
            "os_version": platform.mac_ver()[0] if platform.system() == "Darwin" else platform.version(),
            "hostname": platform.node(),
            "python_version": sys.version.split()[0],
            "python_path": sys.executable,
        }
        # Hermes version
        try:
            r = sp.run(["hermes", "--version"], capture_output=True, text=True, timeout=5)
            info["hermes_version"] = r.stdout.strip() or r.stderr.strip()
        except:
            info["hermes_version"] = "unknown"
        # Apex version
        try:
            from apex import __version__ as av
            info["apex_version"] = av
        except:
            info["apex_version"] = "0.5.1"
        # Installed tools
        tools = {}
        for tool in ["git", "node", "npm", "docker", "tmux", "curl"]:
            try:
                r = sp.run(["which", tool], capture_output=True, text=True, timeout=3)
                tools[tool] = r.stdout.strip() if r.returncode == 0 else None
            except:
                tools[tool] = None
        info["installed_tools"] = tools
        # Disk
        try:
            home = Path.home()
            usage = sp.run(["df", "-h", str(home)], capture_output=True, text=True, timeout=5)
            info["disk"] = usage.stdout.strip().split("\n")[-1] if usage.returncode == 0 else "unknown"
        except:
            info["disk"] = "unknown"
        return jsonify(info)

    @app.route("/api/security/mcp-status")
    def api_security_mcp_status():
        """Security scanning MCP status — Semgrep CLI + MCP server + config"""
        import shutil, json as _json, os as _os
        import subprocess as sp
        result = {"ok": True}

        # 1. Semgrep CLI
        semgrep_path = shutil.which("semgrep")
        result["semgrep"] = {
            "installed": semgrep_path is not None,
            "path": semgrep_path or None,
            "version": None,
        }
        if semgrep_path:
            try:
                r = sp.run([semgrep_path, "--version"], capture_output=True, text=True, timeout=10)
                v = r.stdout.strip() or r.stderr.strip()
                for line in v.split("\n"):
                    if line.strip() and not line.startswith("/") and "new version" not in line.lower():
                        result["semgrep"]["version"] = line.strip()
                        break
                if not result["semgrep"]["version"]:
                    result["semgrep"]["version"] = v.split("\n")[0] if v else "unknown"
            except:
                result["semgrep"]["version"] = "error"

        # 2. MCP Server (npm package)
        npm_global = "/opt/homebrew/lib/node_modules"
        mcp_path = _os.path.join(npm_global, "mcp-server-semgrep", "build", "index.js")
        result["mcp_server"] = {
            "installed": _os.path.exists(mcp_path),
            "path": mcp_path if _os.path.exists(mcp_path) else None,
            "version": None,
        }
        if result["mcp_server"]["installed"]:
            try:
                pkg_json = _os.path.join(npm_global, "mcp-server-semgrep", "package.json")
                with open(pkg_json) as f:
                    pkg = _json.load(f)
                result["mcp_server"]["version"] = pkg.get("version")
            except:
                pass

        # 3. Config status
        result["config"] = {"configured": False, "allowed_roots": None}
        try:
            import yaml
            config_path = _os.path.expanduser("~/.hermes/config.yaml")
            if _os.path.exists(config_path):
                with open(config_path) as f:
                    cfg = yaml.safe_load(f)
                mcp = cfg.get("mcp_servers", {})
                semgrep_cfg = mcp.get("semgrep", {})
                if semgrep_cfg:
                    result["config"]["configured"] = True
                    result["config"]["command"] = semgrep_cfg.get("command")
                    result["config"]["args"] = semgrep_cfg.get("args", [])
                    result["config"]["timeout"] = semgrep_cfg.get("timeout", 120)
                    env = semgrep_cfg.get("env", {})
                    result["config"]["allowed_roots"] = env.get("MCP_SERVER_SEMGREP_ALLOWED_ROOTS")
        except:
            pass

        # 4. Available MCP tools
        result["tools"] = [
            {"name": "scan_directory", "desc": "扫描目录中的源代码，发现潜在问题"},
            {"name": "list_rules", "desc": "列出 Semgrep 支持的规则和语言"},
            {"name": "analyze_results", "desc": "详细分析扫描结果"},
            {"name": "create_rule", "desc": "创建自定义 Semgrep 规则"},
            {"name": "filter_results", "desc": "按条件过滤扫描结果"},
            {"name": "export_results", "desc": "导出结果 (JSON/CSV/SARIF)"},
            {"name": "compare_results", "desc": "比较两次扫描结果（修复前后对比）"},
        ]

        return jsonify(result)

    @app.route("/api/fleet/profiles/list")
    def api_fleet_profiles_list():
        """List all Hermes profiles with full details"""
        try:
            from apex.interface.fleet_manager import list_hermes_profiles
            return jsonify(list_hermes_profiles())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/fleet/profiles/<name>", methods=["GET", "PUT", "DELETE"])
    def api_fleet_profile_detail(name: str):
        """Get/Update/Delete a Hermes profile"""
        try:
            from apex.interface.fleet_manager import get_profile_detail, update_profile, delete_profile
            if request.method == "GET":
                return jsonify(get_profile_detail(name))
            elif request.method == "PUT":
                data = request.get_json(force=True) or {}
                return jsonify(update_profile(name, data))
            elif request.method == "DELETE":
                return jsonify(delete_profile(name))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/fleet/profiles/<name>/toggle", methods=["POST"])
    def api_fleet_profile_toggle(name: str):
        """Enable or disable a Hermes profile"""
        try:
            from apex.interface.fleet_manager import toggle_profile
            return jsonify(toggle_profile(name))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/fleet/profiles/<name>/copy", methods=["POST"])
    def api_fleet_profile_copy(name: str):
        """Duplicate a Hermes profile"""
        try:
            from apex.interface.fleet_manager import copy_profile
            data = request.get_json(force=True) or {}
            new_name = data.get("new_name", "")
            if not new_name:
                return jsonify({"error": "new_name is required"}), 400
            return jsonify(copy_profile(name, new_name))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/fleet/profiles/create", methods=["POST"])
    def api_fleet_create_profile():
        """Create a new Hermes profile"""
        try:
            from apex.interface.fleet_manager import create_profile
            data = request.get_json(force=True) or {}
            name = data.get("name", "")
            model = data.get("model", "deepseek-chat")
            soul = data.get("soul", None)
            if not name:
                return jsonify({"error": "name is required"}), 400
            return jsonify(create_profile(name, model, soul))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/fleet/teams/list")
    def api_fleet_teams_list():
        """List all project teams"""
        try:
            from apex.interface.fleet_manager import list_teams
            return jsonify(list_teams())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/fleet/teams/create", methods=["POST"])
    def api_fleet_create_team():
        """Create a new project team"""
        try:
            from apex.interface.fleet_manager import create_team
            data = request.get_json(force=True) or {}
            return jsonify(create_team(
                name=data.get("name", ""),
                description=data.get("description", ""),
                project=data.get("project", ""),
            ))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/fleet/teams/<name>", methods=["GET", "PUT", "DELETE"])
    def api_fleet_team_detail(name: str):
        """Get/Update/Delete a project team"""
        try:
            from apex.interface.fleet_manager import update_team, delete_team, get_team_org_chart
            if request.method == "GET":
                return jsonify(get_team_org_chart(name))
            elif request.method == "PUT":
                data = request.get_json(force=True) or {}
                return jsonify(update_team(name, data))
            elif request.method == "DELETE":
                return jsonify(delete_team(name))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ══════════════════════════════════════════════════════════
    # SECTION 15.5: GPU Resource Center API (projects & shutdown)
    # ══════════════════════════════════════════════════════════

    @app.route("/api/gpu/projects")
    def api_gpu_projects():
        """Get project-GPU bindings"""
        try:
            from apex.interface.gpu_manager import get_gpu_projects
            return jsonify(get_gpu_projects())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/gpu/projects/bind", methods=["POST"])
    def api_gpu_bind_project():
        """Bind a project to a GPU instance"""
        try:
            from apex.interface.gpu_manager import bind_project
            data = request.get_json(force=True) or {}
            project = data.get("project", "")
            instance = data.get("instance", "")
            if not project or not instance:
                return jsonify({"error": "project and instance required"}), 400
            return jsonify(bind_project(project, instance))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/gpu/shutdown/request", methods=["POST"])
    def api_gpu_shutdown_request():
        """Request GPU shutdown → generate auth code"""
        try:
            from apex.interface.gpu_manager import request_shutdown
            data = request.get_json(force=True) or {}
            project = data.get("project", "")
            return jsonify(request_shutdown(project))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/gpu/shutdown/confirm", methods=["POST"])
    def api_gpu_shutdown_confirm():
        """Confirm GPU shutdown with auth code"""
        try:
            from apex.interface.gpu_manager import confirm_shutdown
            data = request.get_json(force=True) or {}
            code = data.get("code", "")
            if not code:
                return jsonify({"error": "auth code required"}), 400
            return jsonify(confirm_shutdown(code))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ══════════════════════════════════════════════════════════
    # SECTION 16: Task Management API
    # ══════════════════════════════════════════════════════════

    @app.route("/api/taskmgr/create", methods=["POST"])
    @request_logger
    def api_taskmgr_create():
        """Create a hierarchical task (epic/story/task/subtask)."""
        try:
            from apex.orchestration.task_manager import get_task_manager
            data = request.get_json(force=True) or {}
            tm = get_task_manager()
            task = tm.create_task(
                title=data.get("title", "Untitled"),
                description=data.get("description", ""),
                task_type=data.get("task_type", "task"),
                phase=data.get("phase", "development"),
                priority=data.get("priority", 2),
                assignee=data.get("assignee", ""),
                parent_id=data.get("parent_id", ""),
                project=data.get("project", ""),
                estimated_hours=data.get("estimated_hours", 0.0),
            )
            push_event("task", {"action": "created", "id": task.id, "title": task.title})
            return jsonify(task.to_dict()), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/taskmgr/list")
    @request_logger
    def api_taskmgr_list():
        """List tasks with optional filters."""
        try:
            from apex.orchestration.task_manager import get_task_manager
            tm = get_task_manager()
            tasks = tm.list_tasks(
                project=request.args.get("project", ""),
                assignee=request.args.get("assignee", ""),
                task_type=request.args.get("type", ""),
                workflow_status=request.args.get("status", ""),
                phase=request.args.get("phase", ""),
                limit=request.args.get("limit", 50, type=int),
            )
            return jsonify([t.to_dict() for t in tasks])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/taskmgr/<task_id>")
    @request_logger
    def api_taskmgr_detail(task_id: str):
        """Get task with optional tree."""
        try:
            from apex.orchestration.task_manager import get_task_manager
            tm = get_task_manager()
            include_tree = request.args.get("tree", "0") == "1"
            depth = request.args.get("depth", 3, type=int)
            if include_tree:
                return jsonify(tm.get_task_tree(task_id, depth=depth))
            task = tm.get_task(task_id)
            if not task:
                return jsonify({"error": "Task not found"}), 404
            return jsonify(task.to_dict())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/taskmgr/<task_id>/status", methods=["PUT"])
    @request_logger
    def api_taskmgr_status(task_id: str):
        """Transition task workflow status."""
        try:
            from apex.orchestration.task_manager import get_task_manager
            data = request.get_json(force=True) or {}
            new_status = data.get("status", "")
            notes = data.get("notes", "")
            tm = get_task_manager()
            task = tm.update_task_status(task_id, new_status, notes=notes)
            push_event("task", {"action": "status", "id": task_id,
                       "from": "", "to": new_status})
            return jsonify(task.to_dict())
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/taskmgr/epics")
    @request_logger
    def api_taskmgr_epics():
        """Get all epic trees."""
        try:
            from apex.orchestration.task_manager import get_task_manager
            tm = get_task_manager()
            epics = tm.get_epic_tree()
            return jsonify(epics)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/capacity")
    @request_logger
    def api_capacity():
        """Get all agent capacity."""
        try:
            from apex.orchestration.task_manager import get_task_manager
            tm = get_task_manager()
            capacities = tm.get_agent_capacity()
            return jsonify([c.to_dict() for c in capacities])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/dispatch", methods=["POST"])
    @request_logger
    def api_dispatch():
        """Auto-dispatch tasks by capacity."""
        try:
            from apex.orchestration.task_manager import get_task_manager
            tm = get_task_manager()
            max_per = request.get_json(force=True) or {}
            actions = tm.auto_dispatch(max_per_cycle=max_per.get("max", 3))
            push_event("dispatch", {"actions": len(actions)})
            return jsonify({"dispatched": len(actions), "actions": actions})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/dispatch/smart", methods=["POST"])
    @request_logger
    def api_dispatch_smart():
        """智能分派: 需求文本 → 拆解 → 创建Task → 自动分配Agent"""
        try:
            data = request.get_json(force=True) or {}
            requirement = data.get("requirement", "").strip()
            project = data.get("project", "finopsai")

            if not requirement:
                return jsonify({"error": "requirement is required"}), 400

            from apex.orchestration.task_decomposer import (
                decompose_requirement, dispatch_tasks,
            )
            # 1. 拆解
            result = decompose_requirement(requirement, project)

            # 2. 创建+分派
            from apex.orchestration.task_manager import get_task_manager
            tm = get_task_manager()
            dispatch_result = dispatch_tasks(result, tm)

            push_event("dispatch", {
                "action": "smart_dispatch",
                "project": project,
                "tasks": len(result.tasks),
                "dispatched": dispatch_result["dispatched"],
            })

            return jsonify({
                "requirement": requirement,
                "project": project,
                "epic_title": result.epic_title,
                "analysis": result.analysis,
                "tasks": [
                    {
                        "title": t.title,
                        "assignee": t.assignee,
                        "hours": t.estimated_hours,
                        "priority": t.priority,
                    }
                    for t in result.tasks
                ],
                "dispatch": dispatch_result,
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/pipeline/normal", methods=["POST"])
    @request_logger
    def api_pipeline_normal():
        """📋 正常流程管线: 需求→拆解→分派"""
        try:
            data = request.get_json(force=True) or {}
            requirement = data.get("requirement", "").strip()
            project = data.get("project", "finopsai")
            auto_confirm = data.get("auto_confirm", True)

            if not requirement:
                return jsonify({"error": "requirement is required"}), 400

            from apex.orchestration.pipeline import run_normal_pipeline
            from apex.orchestration.task_manager import get_task_manager

            run = run_normal_pipeline(
                requirement=requirement,
                project=project,
                auto_confirm=auto_confirm,
                task_manager=get_task_manager(),
            )

            push_event("pipeline", {"action": "normal", "id": run.id, "tasks": run.task_count})
            return jsonify(run.to_dict())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/pipeline/direct", methods=["POST"])
    @request_logger
    def api_pipeline_direct():
        """⚡ 专项直达管线: 指令→Agent→立即执行"""
        try:
            data = request.get_json(force=True) or {}
            task = data.get("task", "").strip()
            project = data.get("project", "finopsai")
            agent = data.get("agent", "").strip()
            priority = data.get("priority", 1)

            if not task or not agent:
                return jsonify({"error": "task and agent are required"}), 400

            from apex.orchestration.pipeline import run_direct_pipeline, resolve_agent
            from apex.orchestration.task_manager import get_task_manager

            resolved = resolve_agent(agent, project)
            run = run_direct_pipeline(
                task=task, project=project, agent=resolved,
                priority=priority, task_manager=get_task_manager(),
            )

            push_event("pipeline", {"action": "direct", "id": run.id, "agent": resolved})
            return jsonify(run.to_dict())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/pipeline/smart", methods=["POST"])
    @request_logger
    def api_pipeline_smart():
        """🧠 智能路由: 自动识别意图→选择流程"""
        try:
            data = request.get_json(force=True) or {}
            message = data.get("message", "").strip()
            project = data.get("project", "finopsai")

            if not message:
                return jsonify({"error": "message is required"}), 400

            from apex.orchestration.pipeline import smart_route
            from apex.orchestration.task_manager import get_task_manager

            result = smart_route(message, project, task_manager=get_task_manager())
            push_event("pipeline", {"action": "smart_route", "mode": result["mode"]})
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/help/request", methods=["GET", "POST"])
    @request_logger
    def api_help_request():
        """Create or list help requests."""
        from apex.orchestration.task_manager import get_task_manager
        tm = get_task_manager()
        if request.method == "POST":
            data = request.get_json(force=True) or {}
            req = tm.request_help(
                requesting_agent=data.get("agent", ""),
                title=data.get("title", "Help needed"),
                description=data.get("description", ""),
                source_task_id=data.get("task_id", ""),
            )
            push_event("help_request", {"id": req.id, "agent": req.requesting_agent})
            return jsonify(req.to_dict()), 201
        # GET
        requests = tm.list_help_requests(status=request.args.get("status", ""))
        return jsonify([r.to_dict() for r in requests])

    @app.route("/api/help/approve", methods=["POST"])
    @request_logger
    def api_help_approve():
        """PM approves a help request."""
        try:
            from apex.orchestration.task_manager import get_task_manager
            data = request.get_json(force=True) or {}
            tm = get_task_manager()
            req = tm.approve_help(
                request_id=data.get("request_id", ""),
                assigned_agent=data.get("agent", ""),
                pm_notes=data.get("notes", ""),
            )
            push_event("help_request", {"action": "approved", "id": req.id})
            return jsonify(req.to_dict())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ══════════════════════════════════════════
    # Project Operations — PM协作引擎
    # ══════════════════════════════════════════

    @app.route("/api/ops/agents/workloads")
    def api_agent_workloads():
        """Agent workload tracking — saturation, free slots, velocity"""
        try:
            from apex.interface.project_ops import get_agent_workloads
            return jsonify(get_agent_workloads())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/ops/agents/match", methods=["POST"])
    def api_match_task():
        """Match a task to the best agent"""
        try:
            from apex.interface.project_ops import match_task_to_agent, auto_assign_task
            data = request.get_json(force=True) or {}
            title = data.get("title", "")
            desc = data.get("description", "")
            auto = data.get("auto_assign", False)
            if auto:
                return jsonify(auto_assign_task(title, desc, data.get("priority", 2)))
            return jsonify(match_task_to_agent(title, desc))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/ops/standup")
    def api_standup():
        """PM standup report — project status + agent load + blockers"""
        try:
            from apex.interface.project_ops import generate_standup_report
            project = request.args.get("project", None)
            return jsonify(generate_standup_report(project))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/ops/knowledge/search")
    def api_knowledge_search():
        """Search known solutions across agents"""
        try:
            from apex.interface.project_ops import search_solutions, get_knowledge_base_stats
            q = request.args.get("q", "")
            if q:
                return jsonify(search_solutions(q))
            return jsonify(get_knowledge_base_stats())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/ops/knowledge/record", methods=["POST"])
    def api_knowledge_record():
        """Record a new solution for cross-agent learning"""
        try:
            from apex.interface.project_ops import record_solution
            data = request.get_json(force=True) or {}
            return jsonify(record_solution(
                problem=data.get("problem", ""),
                solution=data.get("solution", ""),
                solved_by=data.get("solved_by", "unknown"),
                tags=data.get("tags", []),
            ))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ══════════════════════════════════════════
    # Live Status — Real-time Hermes/Project sync
    # ══════════════════════════════════════════

    @app.route("/api/live/runtime")
    def api_live_runtime():
        """Hermes runtime: active sessions, running processes"""
        try:
            from apex.interface.live_status import get_hermes_runtime
            return jsonify(get_hermes_runtime())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/live/projects")
    def api_live_projects():
        """Auto-discovered projects from task titles"""
        try:
            from apex.interface.live_status import list_projects
            return jsonify(list_projects())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/live/project/<project>")
    def api_live_project_dashboard(project: str):
        """Per-project dashboard: tasks, agents, workload, standup"""
        try:
            from apex.interface.live_status import get_project_dashboard
            return jsonify(get_project_dashboard(project))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/live/standup/<task_id>")
    def api_live_task_standup(task_id: str):
        """Standup report when a task completes"""
        try:
            from apex.interface.live_status import generate_task_completion_standup
            return jsonify(generate_task_completion_standup(task_id))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ── Sprint Pipeline API ──

    @app.route("/api/sprint/list")
    def api_sprint_list():
        """List all sprints."""
        try:
            from apex.orchestration.sprint_pipeline import SprintManager
            mgr = SprintManager()
            sprints = mgr.list_all()
            return jsonify([s.to_dict() for s in sprints])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/sprint/<sprint_id>")
    def api_sprint_get(sprint_id: str):
        """Get a single sprint."""
        try:
            from apex.orchestration.sprint_pipeline import SprintManager
            mgr = SprintManager()
            sprint = mgr.get(sprint_id)
            if not sprint:
                return jsonify({"error": "Not found"}), 404
            return jsonify(sprint.to_dict())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/sprint/<sprint_id>/approve", methods=["POST"])
    def api_sprint_approve(sprint_id: str):
        """Approve current manual gate."""
        try:
            from apex.orchestration.sprint_pipeline import SprintManager
            mgr = SprintManager()
            result = mgr.approve(sprint_id)
            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/sprint/<sprint_id>/complete", methods=["POST"])
    def api_sprint_complete(sprint_id: str):
        """Mark current phase as done."""
        try:
            from apex.orchestration.sprint_pipeline import SprintManager
            data = request.get_json(silent=True) or {}
            mgr = SprintManager()
            result = mgr.complete_phase(
                sprint_id,
                hours=data.get("hours", 0.0),
                output=data.get("output", ""),
            )
            # Auto-advance if possible
            if result.get("success") and result.get("gate") == "auto":
                auto = mgr.advance_auto(sprint_id)
                result["auto_advance"] = auto
            return jsonify(result)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/sprint/create", methods=["POST"])
    def api_sprint_create():
        """Create a new sprint."""
        try:
            from apex.orchestration.sprint_pipeline import SprintManager
            data = request.get_json(silent=True) or {}
            goal = data.get("goal", "")
            mode = data.get("mode", "solo")
            if not goal:
                return jsonify({"success": False, "error": "goal is required"}), 400
            mgr = SprintManager()
            sprint = mgr.create(goal, mode)
            return jsonify({"success": True, "sprint": sprint.to_dict()})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ══════════════════════════════════════════════════════════
    # SECTION 17: 🏸 羽球宝AI — 球场预约 API
    # ══════════════════════════════════════════════════════════

    # ── 内存存储 & 种子数据 ──────────────────────────────────
    _courts = [
        {
            "id": "court-001",
            "name": "深圳体育馆羽毛球馆",
            "address": "深圳市福田区笋岗西路2006号",
            "district": "福田区",
            "price_per_hour": 80,
            "rating": 4.5,
            "image_url": "/static/courts/sztyg.jpg",
        },
        {
            "id": "court-002",
            "name": "南山文体中心羽毛球馆",
            "address": "深圳市南山区南山大道2100号",
            "district": "南山区",
            "price_per_hour": 100,
            "rating": 4.7,
            "image_url": "/static/courts/nswt.jpg",
        },
        {
            "id": "court-003",
            "name": "宝安体育馆羽毛球馆",
            "address": "深圳市宝安区新湖路2112号",
            "district": "宝安区",
            "price_per_hour": 60,
            "rating": 4.3,
            "image_url": "/static/courts/baty.jpg",
        },
    ]
    _bookings = []  # {booking_id, court_id, user_name, phone, date, time_slot, duration_hours, total_price, status}
    _next_booking_id = 1

    from datetime import datetime as dt
    import re

    def _gen_schedule(court_id):
        """Generate a default hourly schedule for a court."""
        hours = []
        for h in range(8, 22):  # 08:00 - 22:00
            start = f"{h:02d}:00"
            end = f"{h+1:02d}:00"
            # Check if any booking occupies this slot
            occupied = any(
                b["court_id"] == court_id
                and b["status"] != "cancelled"
                and b["date"] == dt.now().strftime("%Y-%m-%d")
                for b in _bookings
            )
            hours.append({
                "time": f"{start}-{end}",
                "available": not occupied,
            })
        return hours

    # ── GET /api/courts ───────────────────────────────────────
    @app.route("/api/courts")
    @request_logger
    def api_courts():
        return jsonify({"courts": _courts})

    # ── GET /api/courts/<court_id> ────────────────────────────
    @app.route("/api/courts/<court_id>")
    @request_logger
    def api_court_detail(court_id: str):
        court = next((c for c in _courts if c["id"] == court_id), None)
        if not court:
            return jsonify({"error": f"Court '{court_id}' not found"}), 404
        return jsonify({
            "court": {
                **court,
                "schedule": _gen_schedule(court_id),
            }
        })

    # ── POST /api/bookings ────────────────────────────────────
    @app.route("/api/bookings", methods=["POST"])
    @request_logger
    def api_bookings_create():
        nonlocal _next_booking_id

        data = request.get_json(silent=True) or {}
        court_id = data.get("court_id", "")
        user_name = (data.get("user_name") or "").strip()
        phone = (data.get("phone") or "").strip()
        date = (data.get("date") or "").strip()
        time_slot = (data.get("time_slot") or "").strip()
        duration_hours = data.get("duration_hours", 1)

        # ── 参数校验 ──
        errors = []
        if not court_id:
            errors.append("court_id is required")
        if not user_name:
            errors.append("user_name is required")
        if not phone:
            errors.append("phone is required")
        if not date:
            errors.append("date is required")
        if not time_slot:
            errors.append("time_slot is required")

        # 校验 date 格式 YYYY-MM-DD
        if date and not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            errors.append("date must be YYYY-MM-DD format")

        # 校验 time_slot 格式 HH:MM
        if time_slot and not re.match(r"^\d{2}:\d{2}$", time_slot):
            errors.append("time_slot must be HH:MM format (e.g. 14:00)")

        if errors:
            return jsonify({"error": "; ".join(errors)}), 400

        # 校验 court_id 必须存在
        court = next((c for c in _courts if c["id"] == court_id), None)
        if not court:
            return jsonify({"error": f"Court '{court_id}' not found"}), 404

        # 校验 duration_hours
        try:
            duration_hours = int(duration_hours)
        except (ValueError, TypeError):
            duration_hours = 1
        if duration_hours < 1:
            duration_hours = 1
        if duration_hours > 8:
            return jsonify({"error": "duration_hours must be between 1 and 8"}), 400

        # ── 时间段冲突检测 ──
        try:
            slot_hour = int(time_slot.split(":")[0])
            slot_minute = int(time_slot.split(":")[1])
        except (ValueError, IndexError):
            return jsonify({"error": "time_slot must be HH:MM format"}), 400

        # Check if this time slot conflicts with any existing booking for this court+date
        for b in _bookings:
            if b["court_id"] != court_id or b["date"] != date or b["status"] == "cancelled":
                continue
            try:
                b_hour = int(b["time_slot"].split(":")[0])
                b_minute = int(b["time_slot"].split(":")[1])
            except (ValueError, IndexError):
                continue
            b_start = b_hour * 60 + b_minute
            b_end = b_start + b["duration_hours"] * 60
            req_start = slot_hour * 60 + slot_minute
            req_end = req_start + duration_hours * 60
            # Overlap: !(req_end <= b_start or req_start >= b_end)
            if not (req_end <= b_start or req_start >= b_end):
                return jsonify({
                    "error": f"Time slot conflict: {time_slot} for {duration_hours}h overlaps with existing booking (booking_id={b['booking_id']}, {b['time_slot']} for {b['duration_hours']}h)"
                }), 409

        # ── 创建预订 ──
        total_price = court["price_per_hour"] * duration_hours
        booking = {
            "booking_id": f"bk-{_next_booking_id:04d}",
            "court_id": court_id,
            "court_name": court["name"],
            "user_name": user_name,
            "phone": phone,
            "date": date,
            "time_slot": time_slot,
            "duration_hours": duration_hours,
            "total_price": total_price,
            "status": "confirmed",
        }
        _bookings.append(booking)
        _next_booking_id += 1

        push_event("booking", {"action": "created", "booking_id": booking["booking_id"],
                   "court": court["name"], "user": user_name})
        log_event("info", f"Booking created: {booking['booking_id']} by {user_name} at {court['name']}")

        return jsonify({
            "booking_id": booking["booking_id"],
            "status": "confirmed",
            "total_price": total_price,
        }), 201

    # ── GET /api/bookings ─────────────────────────────────────
    @app.route("/api/bookings")
    @request_logger
    def api_bookings_list():
        user_name = (request.args.get("user_name") or "").strip()
        if user_name:
            filtered = [b for b in _bookings if b["user_name"] == user_name]
        else:
            filtered = list(_bookings)
        return jsonify({
            "bookings": [
                {
                    "booking_id": b["booking_id"],
                    "court_id": b["court_id"],
                    "court_name": b["court_name"],
                    "date": b["date"],
                    "time_slot": b["time_slot"],
                    "status": b["status"],
                }
                for b in filtered
            ]
        })

    # ══════════════════════════════════════════
    # Project Registry — 立项审批 + 模块架构 + Agent档案
    # ══════════════════════════════════════════

    @app.route("/api/projects/approved")
    def api_projects_approved():
        """List approved projects (only 始祖Agent审批过的)"""
        try:
            from apex.interface.project_registry import list_approved_projects
            return jsonify(list_approved_projects())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/projects/<name>")
    def api_project_detail(name: str):
        """Project detail: goal + modules + sub-functions + agent assignments"""
        try:
            from apex.interface.project_registry import get_project_detail
            return jsonify(get_project_detail(name))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/projects/propose", methods=["POST"])
    def api_project_propose():
        """Propose a new project"""
        try:
            from apex.interface.project_registry import propose_project
            data = request.get_json(force=True) or {}
            return jsonify(propose_project(
                name=data.get("name", ""),
                goal=data.get("goal", ""),
                modules=data.get("modules", None),
            ))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/projects/approve", methods=["POST"])
    def api_project_approve():
        """Approve a project (始祖Agent)"""
        try:
            from apex.interface.project_registry import approve_project
            data = request.get_json(force=True) or {}
            return jsonify(approve_project(
                name=data.get("name", ""),
                approver=data.get("approver", "始祖Agent·小卢"),
            ))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/projects/module", methods=["POST"])
    def api_project_add_module():
        """Add a module to a project"""
        try:
            from apex.interface.project_registry import add_project_module
            data = request.get_json(force=True) or {}
            return jsonify(add_project_module(
                project=data.get("project", ""),
                module_name=data.get("module_name", ""),
                description=data.get("description", ""),
            ))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/projects/subfunction", methods=["POST"])
    def api_project_add_subfunction():
        """Add a sub-function to a module"""
        try:
            from apex.interface.project_registry import add_sub_function
            data = request.get_json(force=True) or {}
            return jsonify(add_sub_function(
                project=data.get("project", ""),
                module_name=data.get("module_name", ""),
                func_name=data.get("func_name", ""),
                description=data.get("description", ""),
                assigned_agent=data.get("assigned_agent", ""),
            ))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/agents/<agent_id>")
    def api_agent_profile(agent_id: str):
        """Agent capability profile: skills, projects, model comparison"""
        try:
            from apex.interface.project_registry import get_agent_profile
            return jsonify(get_agent_profile(agent_id))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/agents")
    def api_agents_summary():
        """All agent summaries"""
        try:
            from apex.interface.project_registry import get_all_agent_summaries
            return jsonify(get_all_agent_summaries())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ══════════════════════════════════════════
    # Project Factory — 模块库 + SKILL进化 + Pipeline
    # ══════════════════════════════════════════

    @app.route("/api/modules")
    def api_modules():
        """Module library — categories and templates"""
        try:
            from apex.interface.project_factory import get_module_library, search_modules
            q = request.args.get("q", "")
            cat = request.args.get("category", "")
            if q:
                return jsonify(search_modules(q))
            if cat:
                from apex.interface.project_factory import get_module_templates
                return jsonify(get_module_templates(cat))
            return jsonify(get_module_library())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/skills/<agent_id>")
    def api_skills_agent(agent_id: str):
        """Agent skill evolution profile"""
        try:
            from apex.interface.project_factory import get_agent_skills
            return jsonify(get_agent_skills(agent_id))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/skills/award", methods=["POST"])
    def api_skills_award():
        """Award XP to an agent"""
        try:
            from apex.interface.project_factory import award_xp
            data = request.get_json(force=True) or {}
            return jsonify(award_xp(
                agent_id=data.get("agent_id", ""),
                action=data.get("action", "done"),
                detail=data.get("detail", ""),
            ))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/skills/leaderboard")
    def api_skills_leaderboard():
        """Agent XP leaderboard"""
        try:
            from apex.interface.project_factory import get_skill_leaderboard
            return jsonify(get_skill_leaderboard())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/pipeline/<project>")
    def api_pipeline(project: str):
        """Project pipeline: dev→test→deploy→evaluate"""
        try:
            from apex.interface.project_factory import get_project_pipeline, get_project_evaluation
            pipeline = get_project_pipeline(project)
            evaluation = get_project_evaluation(project)
            return jsonify({**pipeline, "evaluation": evaluation})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ══════════════════════════════════════════
    # Agent Chat & Session History
    # ══════════════════════════════════════════

    @app.route("/api/agent/<agent_id>/sessions")
    def api_agent_sessions(agent_id: str):
        """Get recent sessions for an agent"""
        import sqlite3, os
        db = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))) / "state.db"
        if not db.exists(): return jsonify({"error":"db not found"}), 500
        conn = sqlite3.connect(str(db))
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT id,source,model,message_count,input_tokens,output_tokens,estimated_cost_usd,started_at "
                "FROM sessions WHERE source='cli' ORDER BY started_at DESC LIMIT 20"
            ).fetchall()
            return jsonify([{
                "id":r["id"],"source":r["source"],"model":r["model"],"messages":r["message_count"],
                "tokens":(r["input_tokens"] or 0)+(r["output_tokens"] or 0),
                "cost":round(r["estimated_cost_usd"] or 0,4),
                "started":r["started_at"]
            } for r in rows])
        finally: conn.close()

    @app.route("/api/session/<session_id>/messages")
    def api_session_messages(session_id: str):
        """Get messages for a session"""
        import sqlite3, os
        db = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))) / "state.db"
        if not db.exists(): return jsonify({"error":"db not found"}), 500
        conn = sqlite3.connect(str(db))
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT id,role,substr(content,1,2000) as content,tool_name,timestamp "
                "FROM messages WHERE session_id=? ORDER BY id LIMIT 100",
                (session_id,)
            ).fetchall()
            msgs = []
            for r in rows:
                msg = {"role":r["role"],"time":r["timestamp"]}
                if r["content"]:
                    try:
                        import json
                        d = json.loads(r["content"])
                        msg["preview"] = str(d.get("output",d))[:300]
                    except:
                        msg["preview"] = r["content"][:300]
                elif r["tool_name"]:
                    msg["tool"] = r["tool_name"]
                msgs.append(msg)
            return jsonify({"session_id":session_id,"messages":msgs,"total":len(msgs)})
        finally: conn.close()

    # ══════════════════════════════════════════
    # Audit & Flow — 审批审计 + 数据流时序
    # ══════════════════════════════════════════

    @app.route("/api/audit/queue")
    def api_audit_queue():
        try:
            from apex.interface.audit_flow import get_approval_queue
            return jsonify(get_approval_queue())
        except Exception as e: return jsonify({"error":str(e)}), 500

    @app.route("/api/audit/approve", methods=["POST"])
    def api_audit_approve():
        try:
            from apex.interface.audit_flow import approve_item
            d = request.get_json(force=True) or {}
            return jsonify(approve_item(d.get("id",""), d.get("approver","老卢")))
        except Exception as e: return jsonify({"error":str(e)}), 500

    @app.route("/api/audit/reject", methods=["POST"])
    def api_audit_reject():
        try:
            from apex.interface.audit_flow import reject_item
            d = request.get_json(force=True) or {}
            return jsonify(reject_item(d.get("id",""), d.get("reason",""), d.get("rejector","老卢")))
        except Exception as e: return jsonify({"error":str(e)}), 500

    @app.route("/api/audit/log")
    def api_audit_log():
        try:
            from apex.interface.audit_flow import get_audit_log, get_audit_stats
            stats = get_audit_stats()
            log = get_audit_log()
            return jsonify({**stats, "entries": log.get("entries",[])})
        except Exception as e: return jsonify({"error":str(e)}), 500

    @app.route("/api/flow/timeline")
    def api_flow_timeline():
        try:
            from apex.interface.audit_flow import get_data_flow_timeline
            project = request.args.get("project", None)
            return jsonify(get_data_flow_timeline(project))
        except Exception as e: return jsonify({"error":str(e)}), 500

    @app.route("/api/pipeline/<project>/report")
    def api_pipeline_report(project: str):
        """Generate project daily report for Pipeline evaluation stage"""
        try:
            from apex.interface.project_factory import get_project_pipeline, get_project_evaluation
            from apex.interface.live_status import get_project_dashboard
            from apex.interface.hermes_bridge import get_hermes_session_stats
            
            pipeline = get_project_pipeline(project)
            evaluation = get_project_evaluation(project)
            dashboard = get_project_dashboard(project)
            tokens = get_hermes_session_stats()
            
            return jsonify({
                "project": project,
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_tasks": pipeline["total_tasks"],
                    "done": pipeline["done"],
                    "progress": f"{pipeline['progress_pct']}%",
                    "current_stage": pipeline["current_stage"],
                },
                "stages": pipeline.get("stages", []),
                "evaluation": evaluation.get("evaluation", {}),
                "rating": evaluation.get("rating", "⭐⭐⭐"),
                "agents": dashboard.get("agents", []),
                "token_cost_today": {
                    "tokens": tokens.get("today_tokens", 0),
                    "cost_usd": tokens.get("today_cost", 0),
                },
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/status/health")
    def api_health_full():
        """Full health check — Hermes, Apex, DB status"""
        import os, sqlite3
        hermes_db = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))) / "state.db"
        hermes_ok = hermes_db.exists()
        apex_db = Path(os.path.expanduser("~/.apex")) / "kanban.db"
        apex_ok = apex_db.exists()
        
        hermes_sessions = 0
        if hermes_ok:
            try:
                c = sqlite3.connect(str(hermes_db))
                hermes_sessions = c.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
                c.close()
            except: pass
        
        return jsonify({
            "status": "ok",
            "apex_version": "0.2.0",
            "hermes_available": hermes_ok,
            "hermes_sessions": hermes_sessions,
            "apex_db_available": apex_ok,
            "requires_hermes": False,
            "note": "Apex runs standalone. Hermes integration enables real-time session tracking and token analytics." if not hermes_ok else "Hermes integrated — full analytics available.",
        })

    return app


def run_dashboard(host: str = "127.0.0.1", port: int = 8080, debug: bool = False):
    """Start Dashboard with all enhancements."""
    app = create_app()
    print(f"📊 AgentArk Dashboard: http://{host}:{port}")
    print(f"   API:   http://{host}:{port}/api/status")
    print(f"   SSE:   http://{host}:{port}/api/stream/logs")
    print(f"   OpenClaw: http://{host}:{port}/api/openclaw/status")
    print(f"   Hermes: http://{host}:{port}/api/hermes/status")
    app.run(host=host, port=port, debug=debug, threaded=True)
