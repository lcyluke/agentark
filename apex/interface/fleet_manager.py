"""Apex Fleet Manager — Hermes Profile CRUD + Project Team management

Operations:
  - Read/Update Hermes Profile SOUL.md and config.yaml
  - Create new Hermes Profiles via CLI
  - Project Team definitions (grouping agents by project)
  - Team-Agent assignments with roles
"""
from __future__ import annotations

import json
import os
import subprocess
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional


HERMES_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))
PROFILES_DIR = HERMES_HOME / "profiles"
TEAMS_FILE = HERMES_HOME / "fleet_teams.json"


# ══════════════════════════════════════════
# Hermes Profile Management
# ══════════════════════════════════════════

def list_hermes_profiles() -> list[dict]:
    """List all Hermes profiles with details"""
    profiles = []
    
    # Default profile (lives in HERMES_HOME root, not profiles/)
    default_config = HERMES_HOME / "config.yaml"
    default_model = "unknown"
    if default_config.exists():
        try:
            with open(default_config) as f:
                cfg = yaml.safe_load(f) or {}
            default_model = cfg.get("model", {}).get("default", "unknown")
        except:
            pass
    
    profiles.append({
        "name": "default",
        "is_default": True,
        "model": default_model,
        "path": str(HERMES_HOME),
        "has_soul": False,
        "has_config": default_config.exists(),
    })
    
    # Named profiles
    if PROFILES_DIR.exists():
        for pdir in sorted(PROFILES_DIR.iterdir()):
            if not pdir.is_dir():
                continue
            name = pdir.name
            soul_file = pdir / "SOUL.md"
            config_file = pdir / "config.yaml"
            
            model = "unknown"
            if config_file.exists():
                try:
                    with open(config_file) as f:
                        cfg = yaml.safe_load(f) or {}
                    model = cfg.get("model", {}).get("default", "unknown")
                except:
                    pass
            
            profiles.append({
                "name": name,
                "is_default": False,
                "model": model,
                "path": str(pdir),
                "has_soul": soul_file.exists(),
                "has_config": config_file.exists(),
            })
    
    return profiles


def get_profile_detail(name: str) -> dict:
    """Get full details of a Hermes profile"""
    if name == "default":
        pdir = HERMES_HOME
    else:
        pdir = PROFILES_DIR / name
        if not pdir.exists():
            return {"error": f"Profile '{name}' not found"}
    
    soul_file = pdir / "SOUL.md"
    config_file = pdir / "config.yaml"
    env_file = pdir / ".env"
    
    soul_content = soul_file.read_text() if soul_file.exists() else None
    config_content = None
    if config_file.exists():
        try:
            with open(config_file) as f:
                config_content = yaml.safe_load(f)
        except:
            config_content = {"error": "Failed to parse config.yaml"}
    
    # Parse SOUL.md sections
    soul_sections = {}
    if soul_content:
        current_section = "header"
        for line in soul_content.split("\n"):
            if line.startswith("## "):
                current_section = line[3:].strip().lower().replace(" ", "_")
                soul_sections[current_section] = ""
            elif current_section in soul_sections:
                soul_sections[current_section] += line + "\n"
            else:
                soul_sections[current_section] = line + "\n"
    
    return {
        "name": name,
        "is_default": name == "default",
        "path": str(pdir),
        "config": config_content,
        "soul": {
            "raw": soul_content,
            "sections": soul_sections,
        },
        "has_env": env_file.exists(),
    }


def update_profile(name: str, updates: dict) -> dict:
    """Update a Hermes profile's SOUL.md or config.yaml"""
    if name == "default":
        pdir = HERMES_HOME
    else:
        pdir = PROFILES_DIR / name
        if not pdir.exists():
            return {"error": f"Profile '{name}' not found"}
    
    changed = []
    
    # Update SOUL.md
    if "soul" in updates:
        soul_file = pdir / "SOUL.md"
        soul_file.write_text(updates["soul"])
        changed.append("SOUL.md")
    
    # Update config.yaml
    if "config" in updates:
        config_file = pdir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(updates["config"], f, default_flow_style=False, allow_unicode=True)
        changed.append("config.yaml")
    
    # Update model
    if "model" in updates:
        config_file = pdir / "config.yaml"
        cfg = {}
        if config_file.exists():
            with open(config_file) as f:
                cfg = yaml.safe_load(f) or {}
        if "model" not in cfg:
            cfg["model"] = {}
        cfg["model"]["default"] = updates["model"]
        with open(config_file, "w") as f:
            yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
        changed.append("model")
    
    return {"ok": True, "profile": name, "changed": changed}


def create_profile(name: str, model: str = "deepseek-chat", soul: str = None) -> dict:
    """Create a new Hermes profile via CLI"""
    try:
        result = subprocess.run(
            ["hermes", "profile", "create", name],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return {"error": result.stderr.strip() or result.stdout.strip()}
        
        # Write config.yaml
        pdir = PROFILES_DIR / name
        config = {
            "model": {"default": model, "provider": "deepseek", "base_url": "https://api.deepseek.com/v1"},
            "providers": {"deepseek": {"base_url": "https://api.deepseek.com/v1"}},
            "agent": {"max_turns": 30},
        }
        with open(pdir / "config.yaml", "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        
        # Copy API key from main config
        main_env = HERMES_HOME / ".env"
        if main_env.exists():
            env_content = main_env.read_text()
            (pdir / ".env").write_text(env_content)
        
        # Write SOUL.md if provided
        if soul:
            (pdir / "SOUL.md").write_text(soul)
        
        return {"ok": True, "profile": name, "created": True}
    except Exception as e:
        return {"error": str(e)}


def delete_profile(name: str) -> dict:
    """Delete a Hermes profile (with confirmation check)"""
    if name == "default":
        return {"error": "Cannot delete default profile"}
    
    pdir = PROFILES_DIR / name
    if not pdir.exists():
        return {"error": f"Profile '{name}' not found"}
    
    # Don't actually delete — move to .archived
    archive_dir = HERMES_HOME / ".archived_profiles" / name
    archive_dir.parent.mkdir(parents=True, exist_ok=True)
    
    import shutil
    if archive_dir.exists():
        shutil.rmtree(archive_dir)
    shutil.move(str(pdir), str(archive_dir))
    
    return {"ok": True, "profile": name, "archived_to": str(archive_dir)}


# ══════════════════════════════════════════
# Project Team Management
# ══════════════════════════════════════════

def _load_teams() -> dict:
    """Load project teams from JSON file"""
    if TEAMS_FILE.exists():
        with open(TEAMS_FILE) as f:
            return json.load(f)
    return {"teams": {}, "updated_at": None}


def _save_teams(data: dict):
    """Save project teams to JSON file"""
    data["updated_at"] = datetime.now().isoformat()
    with open(TEAMS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def list_teams() -> dict:
    """List all project teams with their agent assignments"""
    return _load_teams()


def create_team(name: str, description: str = "", project: str = "") -> dict:
    """Create a new project team"""
    data = _load_teams()
    if name in data["teams"]:
        return {"error": f"Team '{name}' already exists"}
    
    data["teams"][name] = {
        "name": name,
        "description": description,
        "project": project,
        "members": [],  # [{agent_id, role, profile_type: "hermes"|"apex"}]
        "created_at": datetime.now().isoformat(),
        "org_structure": {"type": "flat"},  # "flat" | "hierarchy" | "matrix"
    }
    _save_teams(data)
    return {"ok": True, "team": name}


def update_team(name: str, updates: dict) -> dict:
    """Update a team's config or members"""
    data = _load_teams()
    if name not in data["teams"]:
        return {"error": f"Team '{name}' not found"}
    
    team = data["teams"][name]
    
    if "description" in updates:
        team["description"] = updates["description"]
    if "project" in updates:
        team["project"] = updates["project"]
    if "org_structure" in updates:
        team["org_structure"] = updates["org_structure"]
    
    # Add member
    if "add_member" in updates:
        member = updates["add_member"]
        # Check duplicate
        if not any(m["agent_id"] == member["agent_id"] for m in team["members"]):
            team["members"].append({
                "agent_id": member["agent_id"],
                "role": member.get("role", "Member"),
                "profile_type": member.get("profile_type", "apex"),
                "joined_at": datetime.now().isoformat(),
            })
    
    # Remove member
    if "remove_member" in updates:
        agent_id = updates["remove_member"]
        team["members"] = [m for m in team["members"] if m["agent_id"] != agent_id]
    
    # Set full member list
    if "members" in updates:
        team["members"] = updates["members"]
    
    # Set org structure nodes
    if "org_nodes" in updates:
        team["org_nodes"] = updates["org_nodes"]
    
    _save_teams(data)
    return {"ok": True, "team": name, "member_count": len(team["members"])}


def delete_team(name: str) -> dict:
    """Delete a project team"""
    data = _load_teams()
    if name not in data["teams"]:
        return {"error": f"Team '{name}' not found"}
    
    del data["teams"][name]
    _save_teams(data)
    return {"ok": True, "team": name, "deleted": True}


def get_team_org_chart(name: str) -> dict:
    """Get org chart data for a team (for visualization)"""
    data = _load_teams()
    if name not in data["teams"]:
        return {"error": f"Team '{name}' not found"}
    
    team = data["teams"][name]
    members = team.get("members", [])
    org_nodes = team.get("org_nodes", [])
    
    # Auto-generate org chart from members if no explicit nodes
    if not org_nodes and members:
        org_nodes = [
            {
                "id": "root",
                "label": name,
                "type": "team",
                "children": [
                    {"id": m["agent_id"], "label": m["agent_id"], "role": m.get("role", ""), "type": m.get("profile_type", "agent")}
                    for m in members
                ]
            }
        ]
    
    return {
        "team": name,
        "description": team.get("description", ""),
        "project": team.get("project", ""),
        "member_count": len(members),
        "members": members,
        "org_chart": org_nodes,
        "org_structure": team.get("org_structure", {"type": "flat"}),
    }
