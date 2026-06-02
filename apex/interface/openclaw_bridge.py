"""Apex — OpenClaw integration bridge.

OpenClaw is an open-source AI-native operating system layer.
This bridge exposes Apex's multi-agent capabilities as consumable
tools, workflows, and API endpoints for OpenClaw.

Integration points:
  - OpenClaw can discover and call Apex tools
  - Apex agents can leverage OpenClaw workspace context
  - Unified status and health reporting
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

from apex.core.runtime import Agent
from apex.core.profile import ProfileManager, Profile
from apex.orchestration.swarm import Swarm
from apex.orchestration.crew import Crew
from apex.orchestration.chain import Chain
from apex.orchestration.router import Router

# ════════════════════════════════════════════════════════════════
# Constants
# ════════════════════════════════════════════════════════════════

OPENCLAW_HOME = Path(os.environ.get("OPENCLAW_HOME", os.path.expanduser("~/.openclaw")))
OPENCLAW_WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", os.path.expanduser("~/.openclaw/workspace")))


# ════════════════════════════════════════════════════════════════
# OpenClaw Tool Registry
# ════════════════════════════════════════════════════════════════

def get_available_tools() -> list[dict]:
    """List all Apex tools available for OpenClaw to call.

    Each tool follows the OpenClaw tool schema:
    {name, description, parameters{properties, required}}
    """
    return [
        {
            "name": "apex.run_agent",
            "description": "Execute a task on a single Apex agent",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Task description"},
                    "profile": {"type": "string", "description": "Agent profile name (default: 'default')"},
                    "model": {"type": "string", "description": "Override model name"},
                },
                "required": ["task"],
            },
        },
        {
            "name": "apex.run_swarm",
            "description": "Execute a task using Apex Swarm mode (parallel workers → verify → synthesize)",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Task description"},
                    "workers": {"type": "integer", "description": "Number of parallel workers", "default": 3},
                },
                "required": ["task"],
            },
        },
        {
            "name": "apex.run_chain",
            "description": "Execute a task using Apex Chain pipeline (sequential stages)",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal": {"type": "string", "description": "Goal description"},
                    "pipeline": {"type": "string", "enum": ["dev", "content", "data"], "default": "dev"},
                },
                "required": ["goal"],
            },
        },
        {
            "name": "apex.query_knowledge",
            "description": "Query the Apex shared Knowledge Graph",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language query"},
                },
                "required": ["query"],
            },
        },
        {
            "name": "apex.list_profiles",
            "description": "List all available Apex agent profiles",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
        {
            "name": "apex.get_status",
            "description": "Get comprehensive Apex system status",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    ]


# ════════════════════════════════════════════════════════════════
# Tool Executors
# ════════════════════════════════════════════════════════════════

def run_agent(task: str, profile: str = "default", model: str = "") -> dict:
    """Run a single Apex agent task."""
    pm = ProfileManager()
    try:
        prof = pm.load(profile)
    except FileNotFoundError:
        prof = pm.create_default(profile)
    
    agent = Agent(prof)
    start = time.time()
    try:
        output = agent.run(task, model=model) if model else agent.run(task)
        return {
            "success": True,
            "output": output[:3000],
            "agent": profile,
            "cost": round(agent.context.cost, 6),
            "duration_ms": int((time.time() - start) * 1000),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)[:500],
            "agent": profile,
            "duration_ms": int((time.time() - start) * 1000),
        }


def run_swarm(task: str, workers: int = 3) -> dict:
    """Run Apex Swarm mode."""
    pm = ProfileManager()
    # Create worker agents from templates
    worker_profiles = []
    templates = ["frontend", "backend", "pm", "devops", "content"]
    for i in range(min(workers, len(templates))):
        try:
            from apex.core.templates import get_template
            t = get_template(templates[i])
            if t:
                prof = t.to_profile(f"swarm_worker_{i}")
                pm.save(prof)
                worker_profiles.append(prof)
        except Exception:
            pass
    
    if not worker_profiles:
        # Fallback to default profile
        worker_profiles.append(pm.load("default"))
    
    swarm = Swarm(worker_profiles)
    start = time.time()
    try:
        result = swarm.run(task)
        return {
            "success": result.success,
            "output": result.output[:3000] if hasattr(result, 'output') else str(result)[:3000],
            "workers": len(worker_profiles),
            "duration_ms": int((time.time() - start) * 1000),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)[:500],
            "duration_ms": int((time.time() - start) * 1000),
        }


def query_knowledge(query: str) -> dict:
    """Query the Apex Knowledge Graph."""
    from apex.core.knowledge import KnowledgeGraph
    kg = KnowledgeGraph()
    result = kg.query(query)
    return {
        "success": result.confidence > 0,
        "answer": result.answer[:3000],
        "confidence": result.confidence,
        "evidence_count": len(result.evidence),
    }


def list_profiles() -> list[dict]:
    """List all Apex profiles."""
    pm = ProfileManager()
    profiles = []
    for name in pm.list():
        try:
            p = pm.load(name)
            profiles.append({
                "name": p.name,
                "role": p.soul.role,
                "model": p.model.default,
                "skills": p.skills,
            })
        except Exception:
            profiles.append({"name": name, "error": "load failed"})
    return profiles


def get_status_summary() -> dict:
    """Get comprehensive Apex system status for OpenClaw."""
    pm = ProfileManager()
    profiles = pm.list()
    
    from apex.core.evolution import EvolutionEngine
    from apex.core.knowledge import KnowledgeGraph
    from apex.economy import BudgetManager, APEX_HOME
    
    evo = EvolutionEngine()
    kg = KnowledgeGraph()
    
    try:
        eco = BudgetManager(APEX_HOME / "economy.db")
        used, limit, remaining = eco.get_balance("default")
    except Exception:
        used, limit, remaining = 0, 0, 0
    
    evo_summary = evo.summary()
    kg_stats = kg.stats()
    
    return {
        "profiles": len(profiles),
        "version": "0.1.0",
        "status": "running",
        "economy": {
            "used": round(used, 4),
            "limit": limit,
            "remaining": round(remaining, 4),
            "usage_pct": round(used / limit * 100, 1) if limit > 0 else 0,
        },
        "evolution": {
            "total_executions": evo_summary.get("total_executions", 0),
            "patterns": evo_summary.get("patterns_discovered", 0),
        },
        "knowledge": {
            "nodes": kg_stats.get("total_nodes", 0),
            "edges": kg_stats.get("total_edges", 0),
        },
    }


# ════════════════════════════════════════════════════════════════
# Workflow Definitions
# ════════════════════════════════════════════════════════════════

def get_workflows() -> list[dict]:
    """List predefined multi-agent workflows consumable by OpenClaw."""
    return [
        {
            "id": "research_report",
            "name": "Research & Report",
            "description": "Research a topic and generate a comprehensive report",
            "steps": [
                {"tool": "apex.run_agent", "params": {"task": "Research: {topic}", "profile": "researcher"}},
                {"tool": "apex.run_agent", "params": {"task": "Write report: {topic}", "profile": "writer"}},
            ],
        },
        {
            "id": "code_review",
            "name": "Code Review Pipeline",
            "description": "Analyze, review, and improve code quality",
            "steps": [
                {"tool": "apex.run_swarm", "params": {"task": "Review code: {path}"}},
            ],
        },
        {
            "id": "content_pipeline",
            "name": "Content Creation Pipeline",
            "description": "Draft → Review → Edit → Publish content",
            "steps": [
                {"tool": "apex.run_chain", "params": {"goal": "Create content about: {topic}", "pipeline": "content"}},
            ],
        },
        {
            "id": "system_diagnosis",
            "name": "System Health Diagnosis",
            "description": "Analyze system status and generate recommendations",
            "steps": [
                {"tool": "apex.get_status", "params": {}},
            ],
        },
    ]
