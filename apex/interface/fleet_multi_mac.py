"""Apex Multi-Mac Fleet Manager — Cross-machine Hermes fleet orchestration.

Architecture:
  GitHub: hermes-fleet-config (private repo)
       ↙              ↘
  Mac-A (Origin)    Mac-B/C (Worker)
  
Origin: runs cron, dashboard, authorization
Worker: executes tasks, 1-3 projects each
"""

from __future__ import annotations

import json
import os
import subprocess
import socket
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional


# Fleet config ALWAYS lives in ~/.hermes/ (not HERMES_HOME which profiles override)
HERMES_HOME = Path(os.path.expanduser("~/.hermes"))
FLEET_CONFIG_FILE = HERMES_HOME / "fleet_config.json"
FLEET_NODES_DIR = HERMES_HOME / "nodes"
FLEET_REPO_URL = "https://github.com/lcyluke/hermes-fleet-config.git"


# ══════════════════════════════════════════
# Fleet Node Identity
# ══════════════════════════════════════════

def get_machine_id() -> str:
    """Get a unique machine identifier."""
    hostname = socket.gethostname()
    return f"{hostname}-{os.getlogin()}"


def get_fleet_config() -> dict:
    """Load fleet config, or return defaults."""
    if FLEET_CONFIG_FILE.exists():
        with open(FLEET_CONFIG_FILE) as f:
            return json.load(f)
    return {
        "fleet_name": "老卢舰队",
        "role": None,  # "origin" or "worker"
        "machine_id": get_machine_id(),
        "repo_url": FLEET_REPO_URL,
        "projects": [],
        "joined_at": None,
        "last_sync": None,
    }


def save_fleet_config(cfg: dict):
    """Persist fleet config."""
    FLEET_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FLEET_CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False, default=str)


# ══════════════════════════════════════════
# Node Heartbeat — GitHub-based discovery
# ══════════════════════════════════════════

def fleet_report() -> dict:
    """Write local node status to nodes/<machine_id>.json and push to GitHub.
    
    This is how Worker nodes make themselves visible to the Origin.
    Origin can also see all nodes by running fleet_sync('pull') first.
    """
    cfg = get_fleet_config()
    if not cfg.get("role"):
        return {"error": "Not in a fleet. Run fleet-init or fleet-join first."}

    git_dir = HERMES_HOME / ".git"
    if not git_dir.exists():
        return {"error": "~/.hermes/ is not a git repo."}

    # 1. Pull latest first (to get other nodes' statuses)
    subprocess.run(
        ["git", "pull", "--rebase", "origin", "main"],
        cwd=HERMES_HOME, capture_output=True, timeout=60,
    )

    # 2. Write node status file
    FLEET_NODES_DIR.mkdir(parents=True, exist_ok=True)
    status = fleet_status()
    status["reported_at"] = datetime.now().isoformat()
    
    node_file = FLEET_NODES_DIR / f"{get_machine_id()}.json"
    node_file.write_text(json.dumps(status, indent=2, ensure_ascii=False, default=str))

    # 3. Commit + push
    subprocess.run(
        ["git", "add", f"nodes/{get_machine_id()}.json"],
        cwd=HERMES_HOME, capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", f"📡 Node heartbeat — {get_machine_id()} ({cfg['role']})"],
        cwd=HERMES_HOME, capture_output=True,
    )
    r = subprocess.run(
        ["git", "push", "origin", "main"],
        cwd=HERMES_HOME, capture_output=True, text=True, timeout=60,
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
    """Read all node status files from nodes/ directory.
    
    Call fleet_sync('pull') first to get latest from GitHub,
    then call this to see all known nodes.
    """
    nodes = []
    if not FLEET_NODES_DIR.exists():
        return nodes

    for f in sorted(FLEET_NODES_DIR.glob("*.json")):
        try:
            node = json.loads(f.read_text())
            # Mark if this is the local machine
            node["is_local"] = (node.get("machine_id") == get_machine_id())
            nodes.append(node)
        except (json.JSONDecodeError, KeyError):
            pass

    return nodes


# ══════════════════════════════════════════
# Fleet Init (Origin)
# ══════════════════════════════════════════

def fleet_init(
    fleet_name: str = "老卢舰队",
    repo_url: str = FLEET_REPO_URL,
    projects: list = None,
    force: bool = False,
) -> dict:
    """Initialize this Mac as the fleet Origin.

    Steps:
    1. Init git in ~/.hermes/
    2. Create .gitignore
    3. Commit config, SOUL.md, skills/, profiles/
    4. Set remote + push
    5. Save fleet_config.json
    """
    cfg = get_fleet_config()
    if cfg["role"] and not force:
        return {"error": f"Already a {cfg['role']} node. Use --force to re-init."}

    results = []

    # 1. Init git if not already
    git_dir = HERMES_HOME / ".git"
    if not git_dir.exists():
        subprocess.run(["git", "init"], cwd=HERMES_HOME, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", f"老卢舰队·始祖 ({get_machine_id()})"],
            cwd=HERMES_HOME, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "lcyluke@fleet.local"],
            cwd=HERMES_HOME, capture_output=True,
        )
        results.append("✅ git init")

    # 2. Create .gitignore
    gitignore = HERMES_HOME / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("""# Hermes Fleet Config — what NOT to sync across Macs
state.db
state.db-shm
state.db-wal
*.db
logs/
.env
.env.*
*.log
audio_cache/
sessions/
hermes-agent/
.Gatekeeper
*.pid
*.lock
.DS_Store
""")
        results.append("✅ .gitignore created")

    # 3. Stage and commit fleet config files
    files_to_add = [
        ".gitignore", "config.yaml", "SOUL.md",
    ]
    dirs_to_add = ["skills/", "profiles/", "cron/"]
    
    for f in files_to_add:
        p = HERMES_HOME / f
        if p.exists():
            subprocess.run(["git", "add", f], cwd=HERMES_HOME, capture_output=True)

    for d in dirs_to_add:
        p = HERMES_HOME / d
        if p.exists():
            subprocess.run(["git", "add", d], cwd=HERMES_HOME, capture_output=True)

    # Also add fleet_teams.json if exists
    ft = HERMES_HOME / "fleet_teams.json"
    if ft.exists():
        subprocess.run(["git", "add", "fleet_teams.json"], cwd=HERMES_HOME, capture_output=True)

    subprocess.run(
        ["git", "commit", "-m", f"⚓ Fleet config — Origin {get_machine_id()} init"],
        cwd=HERMES_HOME, capture_output=True,
    )
    results.append("✅ Fleet files committed")

    # 4. Set remote
    remote_check = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=HERMES_HOME, capture_output=True, text=True,
    )
    if remote_check.returncode != 0:
        subprocess.run(
            ["git", "remote", "add", "origin", repo_url],
            cwd=HERMES_HOME, capture_output=True,
        )
        results.append(f"✅ Remote set: {repo_url}")

    # 5. Save fleet config
    cfg["role"] = "origin"
    cfg["fleet_name"] = fleet_name
    cfg["repo_url"] = repo_url
    cfg["projects"] = projects or ["badminton-coach-ai", "apex", "finopsai", "shenzhen-badminton"]
    cfg["joined_at"] = datetime.now().isoformat()
    cfg["origin_machine"] = get_machine_id()
    save_fleet_config(cfg)
    results.append(f"✅ Fleet config saved — Role: ORIGIN")

    return {
        "success": True,
        "role": "origin",
        "fleet_name": fleet_name,
        "machine_id": get_machine_id(),
        "repo_url": repo_url,
        "steps": results,
    }


# ══════════════════════════════════════════
# Fleet Join (Worker)
# ══════════════════════════════════════════

def fleet_join(
    repo_url: str = FLEET_REPO_URL,
    force: bool = False,
) -> dict:
    """Join an existing fleet as a Worker node.

    Steps:
    1. Clone fleet config repo to temp
    2. Merge config into ~/.hermes/ (preserve .env)
    3. Copy skills/, profiles/
    4. Save fleet_config.json
    """
    cfg = get_fleet_config()
    if cfg["role"] and not force:
        return {"error": f"Already a {cfg['role']} node. Use --force to re-join."}

    import tempfile, shutil

    results = []
    tmpdir = Path(tempfile.mkdtemp(prefix="fleet-join-"))

    try:
        # 1. Clone repo
        r = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(tmpdir)],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode != 0:
            return {"error": f"Clone failed: {r.stderr}"}
        results.append("✅ Fleet config cloned")

        # 2. Merge config (preserve local .env)
        local_env = HERMES_HOME / ".env"
        env_backup = None
        if local_env.exists():
            env_backup = local_env.read_text()

        # Copy config.yaml
        src_config = tmpdir / "config.yaml"
        if src_config.exists():
            shutil.copy2(src_config, HERMES_HOME / "config.yaml")
            results.append("✅ config.yaml synced")

        # Copy SOUL.md
        src_soul = tmpdir / "SOUL.md"
        if src_soul.exists():
            shutil.copy2(src_soul, HERMES_HOME / "SOUL.md")
            results.append("✅ SOUL.md synced")

        # Copy skills/
        src_skills = tmpdir / "skills"
        if src_skills.exists():
            dst_skills = HERMES_HOME / "skills"
            if dst_skills.exists():
                shutil.rmtree(dst_skills)
            shutil.copytree(src_skills, dst_skills)
            results.append("✅ skills/ synced")

        # Copy profiles/
        src_profiles = tmpdir / "profiles"
        if src_profiles.exists():
            dst_profiles = HERMES_HOME / "profiles"
            if dst_profiles.exists():
                shutil.rmtree(dst_profiles)
            shutil.copytree(src_profiles, dst_profiles)
            results.append("✅ profiles/ synced")

        # Copy cron/ config (but NOT cron/output/)
        src_cron = tmpdir / "cron"
        if src_cron.exists():
            dst_cron = HERMES_HOME / "cron"
            jobs_src = src_cron / "jobs.json"
            if jobs_src.exists():
                dst_cron.mkdir(parents=True, exist_ok=True)
                shutil.copy2(jobs_src, dst_cron / "jobs.json")
                results.append("✅ cron/jobs.json synced (jobs DISABLED on worker)")

        # Restore .env
        if env_backup:
            local_env.write_text(env_backup)
            results.append("✅ .env preserved (local)")

        # 3. Save fleet config
        cfg["role"] = "worker"
        cfg["repo_url"] = repo_url
        cfg["joined_at"] = datetime.now().isoformat()
        cfg["worker_machine"] = get_machine_id()
        save_fleet_config(cfg)
        results.append(f"✅ Fleet config saved — Role: WORKER")

        return {
            "success": True,
            "role": "worker",
            "machine_id": get_machine_id(),
            "repo_url": repo_url,
            "steps": results,
            "next": "Run 'apex fleet-sync' to stay updated. Worker Macs should NOT enable cron.",
        }

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ══════════════════════════════════════════
# Fleet Sync
# ══════════════════════════════════════════

def fleet_sync(direction: str = "pull") -> dict:
    """Sync fleet config from/to the central repo.

    direction: "pull" (worker gets updates) or "push" (origin publishes)
    """
    cfg = get_fleet_config()
    if not cfg["role"]:
        return {"error": "Not in a fleet. Run 'apex fleet-init' or 'apex fleet-join' first."}

    git_dir = HERMES_HOME / ".git"
    if not git_dir.exists():
        return {"error": "~/.hermes/ is not a git repo. Run fleet-init first."}

    results = []
    
    if direction == "pull":
        # Stash local changes, pull, pop
        subprocess.run(["git", "stash"], cwd=HERMES_HOME, capture_output=True)
        r = subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            cwd=HERMES_HOME, capture_output=True, text=True, timeout=60,
        )
        subprocess.run(["git", "stash", "pop"], cwd=HERMES_HOME, capture_output=True)
        
        if r.returncode == 0:
            cfg["last_sync"] = datetime.now().isoformat()
            save_fleet_config(cfg)
            results.append("✅ Pulled latest fleet config")
        else:
            results.append(f"⚠️ Pull issues: {r.stderr[:200]}")

    elif direction == "push":
        subprocess.run(
            ["git", "add", "config.yaml", "SOUL.md", "skills/", "profiles/", "cron/jobs.json"],
            cwd=HERMES_HOME, capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", f"🔄 Fleet sync — {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
            cwd=HERMES_HOME, capture_output=True,
        )
        r = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=HERMES_HOME, capture_output=True, text=True, timeout=60,
        )
        if r.returncode == 0:
            cfg["last_sync"] = datetime.now().isoformat()
            save_fleet_config(cfg)
            results.append("✅ Pushed fleet config to origin")
        else:
            results.append(f"⚠️ Push issues: {r.stderr[:200]}")

    return {
        "success": True,
        "direction": direction,
        "role": cfg["role"],
        "last_sync": cfg.get("last_sync"),
        "steps": results,
    }


# ══════════════════════════════════════════
# Fleet Status (Multi-Mac)
# ══════════════════════════════════════════

def fleet_status() -> dict:
    """Get current fleet node status."""
    cfg = get_fleet_config()
    
    # Check git status
    git_status = "unknown"
    git_dir = HERMES_HOME / ".git"
    if git_dir.exists():
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=HERMES_HOME, capture_output=True, text=True,
        )
        if r.returncode == 0:
            dirty = len([l for l in r.stdout.split("\n") if l.strip()])
            git_status = f"clean" if dirty == 0 else f"{dirty} files modified"

    # Count profiles
    profiles_dir = HERMES_HOME / "profiles"
    profile_count = 0
    if profiles_dir.exists():
        profile_count = len([d for d in profiles_dir.iterdir() if d.is_dir()])

    # Count skills
    skills_dir = HERMES_HOME / "skills"
    skill_count = 0
    if skills_dir.exists():
        skill_count = len(list(skills_dir.rglob("SKILL.md")))

    return {
        "machine_id": get_machine_id(),
        "hostname": socket.gethostname(),
        "role": cfg.get("role", "unconfigured"),
        "fleet_name": cfg.get("fleet_name", "unknown"),
        "projects": cfg.get("projects", []),
        "joined_at": cfg.get("joined_at"),
        "last_sync": cfg.get("last_sync"),
        "git_status": git_status,
        "profiles": profile_count,
        "skills": skill_count,
        "repo_url": cfg.get("repo_url"),
    }
