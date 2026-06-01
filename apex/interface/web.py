"""Apex — Web UI Dashboard
Flask + Jinja2 轻量级监控面板。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from datetime import datetime

try:
    from flask import Flask, render_template, jsonify, request
except ImportError:
    Flask = None


def create_app():
    """创建Flask应用"""
    if Flask is None:
        raise ImportError("Flask not installed. Run: pip install flask")

    app = Flask(__name__, template_folder=str(Path(__file__).parent / "templates"))

    from apex.core.profile import ProfileManager, APEX_HOME
    from apex.orchestration.kanban import Kanban
    from apex.core.skills import SkillManager
    from apex.economy import BudgetManager

    pm = ProfileManager()
    kanban_db = APEX_HOME / "kanban.db"
    skills_db = APEX_HOME / "skills.db"
    economy_db = APEX_HOME / "economy.db"

    @app.route("/")
    def index():
        """Dashboard首页"""
        profiles = pm.list()
        profile_data = []
        for name in profiles:
            try:
                p = pm.load(name)
                profile_data.append({
                    "name": p.name,
                    "role": p.soul.role,
                    "model": p.model.default,
                    "expertise": p.soul.expertise[:3],
                    "skills": p.skills[:3],
                })
            except Exception:
                profile_data.append({"name": name, "role": "Error", "model": "?", "expertise": [], "skills": []})

        # Kanban stats
        kanban_tasks = []
        if kanban_db.exists():
            k = Kanban(kanban_db)
            tasks = k.list_tasks()
            kanban_tasks = [
                {"id": t.id, "title": t.title[:50], "assignee": t.assignee,
                 "status": t.status, "priority": t.priority}
                for t in tasks[:20]
            ]

        # Economy stats
        economy_data = {}
        if economy_db.exists():
            bm = BudgetManager(economy_db)
            accounts = ["default"]
            for proj in accounts:
                used, limit, remaining = bm.get_balance(proj)
                economy_data[proj] = {
                    "used": round(used, 4),
                    "limit": limit,
                    "remaining": round(remaining, 4),
                    "usage_pct": round(used / limit * 100, 1) if limit > 0 else 0,
                }

        return render_template("dashboard.html",
            profiles=profile_data,
            tasks=kanban_tasks,
            economy=economy_data,
            total_profiles=len(profiles),
            total_tasks=len(kanban_tasks),
            now=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

    @app.route("/api/status")
    def api_status():
        """REST API — 状态"""
        profiles = pm.list()
        return jsonify({
            "profiles": len(profiles),
            "version": "0.1.0",
            "status": "running",
        })

    @app.route("/api/profiles")
    def api_profiles():
        """REST API — Profile列表"""
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
                })
            except Exception:
                profiles.append({"name": name, "error": True})
        return jsonify(profiles)

    return app


def run_dashboard(host: str = "127.0.0.1", port: int = 8080, debug: bool = False):
    """启动Dashboard"""
    app = create_app()
    print(f"📊 Apex Dashboard: http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
