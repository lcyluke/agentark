"""Apex — Web dashboard: REST API + SSE + OpenClaw + Hermes integration."""

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
        return render_template("dashboard.html")

    @app.route("/v4")
    def dashboard_v4():
        return render_template("dashboard_v4.html") if (Path(__file__).parent / "templates" / "dashboard_v4.html").exists() else render_template("dashboard.html")

    @app.route("/traces")
    def traces_page():
        return render_template("dashboard.html", page="traces")

    @app.route("/agents")
    def agents_page():
        return render_template("dashboard.html", page="agents")

    @app.route("/logs")
    def logs_page():
        return render_template("dashboard.html", page="logs")

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
            "version": "0.1.0",
            "name": "Apex",
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
            "version": "0.1.0",
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
            from apex.interface.hermes_bridge import get_gpu_status
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

    @app.route("/api/command-center")
    @request_logger
    def api_command_center():
        try:
            from apex.interface.hermes_bridge import get_command_center_data
            return jsonify(get_command_center_data())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ══════════════════════════════════════════════════════════
    # SECTION 13: OpenClaw Integration
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
            info["apex_version"] = "0.1.0"
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

    return app


def run_dashboard(host: str = "127.0.0.1", port: int = 8080, debug: bool = False):
    """Start Dashboard with all enhancements."""
    app = create_app()
    print(f"📊 Apex Dashboard: http://{host}:{port}")
    print(f"   API:   http://{host}:{port}/api/status")
    print(f"   SSE:   http://{host}:{port}/api/stream/logs")
    print(f"   OpenClaw: http://{host}:{port}/api/openclaw/status")
    print(f"   Hermes: http://{host}:{port}/api/hermes/status")
    app.run(host=host, port=port, debug=debug, threaded=True)
