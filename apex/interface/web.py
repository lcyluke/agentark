"""Apex — Web UI Dashboard v2
Flask + Dark Theme full monitoring dashboard.
Route: /(Dashboard) /traces /agents /logs /api/*
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from datetime import datetime

try:
    from flask import Flask, render_template, jsonify, request
except ImportError:
    Flask = None


def create_app():
    """Create Flask application"""
    if Flask is None:
        raise ImportError("Flask not installed. Run: pip install flask")

    app = Flask(__name__, template_folder=str(Path(__file__).parent / "templates"))

    from apex.core.profile import ProfileManager, APEX_HOME
    from apex.orchestration.kanban import Kanban
    from apex.core.skills import SkillManager
    from apex.core.evolution import EvolutionEngine
    from apex.core.knowledge import KnowledgeGraph
    from apex.economy import BudgetManager

    pm = ProfileManager()
    kanban_db = APEX_HOME / "kanban.db"
    skills_db = APEX_HOME / "skills.db"
    economy_db = APEX_HOME / "economy.db"
    evolution_db = APEX_HOME / "evolution.db"
    knowledge_db = APEX_HOME / "knowledge.db"

    def load_evolution():
        if evolution_db.exists():
            return EvolutionEngine(evolution_db)
        return None

    def load_kanban():
        if kanban_db.exists():
            return Kanban(kanban_db)
        return None

    def load_kg():
        if knowledge_db.exists():
            return KnowledgeGraph(knowledge_db)
        return None

    # ══════════════════════════════════════════
    # Dashboard Pages
    # ══════════════════════════════════════════

    @app.route("/")
    def index():
        return render_template("dashboard.html")

    @app.route("/traces")
    def traces_page():
        """Trace browsing page"""
        return render_template("dashboard.html", page="traces")

    @app.route("/agents")
    def agents_page():
        """Agent details page"""
        return render_template("dashboard.html", page="agents")

    @app.route("/logs")
    def logs_page():
        """Real-time logs page"""
        return render_template("dashboard.html", page="logs")

    # ══════════════════════════════════════════
    # REST API
    # ══════════════════════════════════════════

    @app.route("/api/status")
    def api_status():
        """Comprehensive status API"""
        profiles = pm.list()
        k = load_kanban()
        tasks = k.list_tasks() if k else []
        evo = load_evolution()
        kg = load_kg()

        # Economy data
        economy_data = {}
        if economy_db.exists():
            bm = BudgetManager(economy_db)
            used, limit, remaining = bm.get_balance("default")
            economy_data["default"] = {
                "used": round(used, 4),
                "limit": limit,
                "remaining": round(remaining, 4),
                "usage_pct": round(used / limit * 100, 1) if limit > 0 else 0,
            }

        # Evolution data
        evo_summary = evo.summary() if evo else {"patterns_discovered": 0}
        kg_stats = kg.stats() if kg else {"total_nodes": 0}

        # Company list
        companies_dir = APEX_HOME / "companies"
        companies = [f.stem for f in companies_dir.glob("*.json")] if companies_dir.exists() else []

        return jsonify({
            "profiles": len(profiles),
            "version": "0.1.0",
            "status": "running",
            "tasks": [{"id": t.id, "title": t.title[:50], "assignee": t.assignee,
                       "status": t.status, "priority": t.priority} for t in tasks[:30]],
            "economy": economy_data,
            "companies": companies,
            "patterns": evo_summary.get("patterns_discovered", 0),
            "knowledge_nodes": kg_stats.get("total_nodes", 0),
            "recent_tasks": [{"id": t.id, "title": t.title[:40], "status": t.status,
                             "assignee": t.assignee} for t in tasks[:5]],
        })

    @app.route("/api/profiles")
    def api_profiles():
        """Profile list API"""
        profiles = []
        for name in pm.list():
            try:
                p = pm.load(name)
                profiles.append({
                    "name": p.name,
                    "role": p.soul.role,
                    "model": p.model.default,
                    "expertise": p.soul.expertise,
                    "skills": p.skills,
                    "auto_improve": p.auto_improve,
                    "personality": p.soul.personality,
                    "communication": p.soul.communication,
                })
            except Exception as e:
                profiles.append({"name": name, "error": str(e)})
        return jsonify(profiles)

    @app.route("/api/profiles/<name>")
    def api_profile_detail(name: str):
        """Single Profile details"""
        try:
            p = pm.load(name)
            evo = load_evolution()
            evo_data = evo.get_agent_evolution(name) if evo else {}
            return jsonify({
                "name": p.name,
                "display": p.display,
                "model": {"default": p.model.default, "fallback": p.model.fallback, "vision": p.model.vision},
                "token_budget": p.token_budget,
                "soul": {"role": p.soul.role, "expertise": p.soul.expertise,
                         "personality": p.soul.personality, "communication": p.soul.communication},
                "skills": p.skills,
                "auto_improve": p.auto_improve,
                "evolution": evo_data,
            })
        except FileNotFoundError:
            return jsonify({"error": f"Profile '{name}' not found"}), 404

    @app.route("/api/tasks")
    def api_tasks():
        """Task list API"""
        k = load_kanban()
        if not k:
            return jsonify([])
        tasks = k.list_tasks()
        return jsonify([{
            "id": t.id, "title": t.title, "assignee": t.assignee,
            "status": t.status, "priority": t.priority,
            "created_at": t.created_at, "completed_at": t.completed_at,
            "cost": t.cost,
        } for t in tasks])

    @app.route("/api/knowledge")
    def api_knowledge():
        """Knowledge graph API"""
        kg = load_kg()
        if not kg:
            return jsonify({"nodes": 0, "edges": 0, "topics": []})
        stats = kg.stats()
        # Get recently active knowledge
        return jsonify({
            "nodes": stats.get("total_nodes", 0),
            "edges": stats.get("total_edges", 0),
            "conflicts": stats.get("unresolved_conflicts", 0),
            "distribution": stats.get("type_distribution", {}),
        })

    @app.route("/api/evolution")
    def api_evolution():
        """Evolution engine API"""
        evo = load_evolution()
        if not evo:
            return jsonify({"total_executions": 0, "patterns": 0, "agents": []})
        summary = evo.summary()
        return jsonify(summary)

    @app.route("/api/companies")
    def api_companies():
        """Company list API"""
        companies_dir = APEX_HOME / "companies"
        if not companies_dir.exists():
            return jsonify([])
        companies = []
        for c_path in sorted(companies_dir.glob("*.json"), reverse=True):
            with open(c_path) as f:
                data = json.load(f)
            companies.append({
                "name": data.get("name"),
                "industry": data.get("industry"),
                "profiles": data.get("profiles", []),
                "sop": data.get("sop", {}),
                "created_at": data.get("created_at", 0),
            })
        return jsonify(companies)

    @app.route("/api/health")
    def api_health():
        """Health check"""
        return jsonify({"status": "ok", "timestamp": time.time()})

    return app


def run_dashboard(host: str = "127.0.0.1", port: int = 8080, debug: bool = False):
    """Start Dashboard"""
    app = create_app()
    print(f"📊 Apex Dashboard: http://{host}:{port}")
    print(f"   API: http://{host}:{port}/api/status")
    app.run(host=host, port=port, debug=debug)
