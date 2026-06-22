"""
Resource-Aware Fleet Scheduler — Capability-Based Task Dispatch
══════════════════════════════════════════════════════════════
Matches tasks to fleet nodes based on required resources and
node capabilities. Supports both LAN (SSH) and GitHub-based dispatch.

Architecture:
  1. TaskRegistration: define task with required resources
  2. NodeRegistry: live view of all fleet nodes + their capabilities
  3. Scheduler.match(): score-based matching algorithm
  4. Scheduler.dispatch(): SSH-based task dispatch to matched node

Scoring algorithm:
  - GPU match (40%): if task needs GPU, nodes with matching GPU rank highest
  - CPU headroom (25%): prefer nodes with more available CPU
  - Memory headroom (15%): prefer nodes with more available RAM
  - Load penalty (10%): penalize nodes with high current load
  - Proximity bonus (10%): LAN-direct nodes over GitHub-only nodes

Usage:
    from apex.fleet.scheduler import FleetScheduler
    sched = FleetScheduler()
    match = sched.find_best_node(task)
    result = sched.dispatch(task, match.node)
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─── Data Classes ─────────────────────────────────────────────


@dataclass
class ResourceRequirement:
    """What a task needs to run."""
    gpu: bool = False
    gpu_memory_mb: int = 0         # Minimum GPU memory needed
    gpu_count: int = 1              # Number of GPUs needed
    cpu_cores: int = 1              # Minimum CPU cores
    ram_mb: int = 512               # Minimum RAM
    disk_mb: int = 100              # Minimum free disk space
    network: str = ""               # "local", "china", "any"
    os: str = ""                    # "macos", "linux"
    python_version: str = ""        # e.g. "3.10"
    docker: bool = False            # Docker required?
    tags: list[str] = field(default_factory=list)  # arbitrary matching tags


@dataclass
class NodeCapability:
    """What a node can offer."""
    machine_id: str
    hostname: str
    role: str                       # "origin" or "worker"
    ip_address: str = ""
    # CPU
    cpu_cores: int = 1
    cpu_usage_pct: float = 0.0
    # RAM
    ram_total_mb: int = 0
    ram_free_mb: int = 0
    # GPU
    has_gpu: bool = False
    gpu_count: int = 0
    gpu_names: list[str] = field(default_factory=list)
    gpu_util_pct: float = 0.0
    gpu_mem_total_mb: int = 0
    gpu_mem_used_mb: int = 0
    gpu_mem_free_mb: int = 0
    temp_c: float = 0.0
    # Storage
    disk_total_gb: float = 0.0
    disk_free_gb: float = 0.0
    # Software
    os: str = "macos"
    python_version: str = ""
    has_docker: bool = False
    # Connectivity
    lan_reachable: bool = False      # SSH on LAN
    latency_ms: float = 999.0
    # Fleet
    profiles: int = 0
    skills: int = 0
    current_tasks: int = 0
    last_heartbeat: float = 0.0
    tags: list[str] = field(default_factory=list)

    @property
    def gpu_mem_free_mb(self) -> int:
        return max(0, self._gpu_mem_free_mb)

    @gpu_mem_free_mb.setter
    def gpu_mem_free_mb(self, val: int):
        self._gpu_mem_free_mb = val

    @property
    def cpu_free_cores(self) -> float:
        """Estimated free CPU cores."""
        return max(0, self.cpu_cores * (1 - self.cpu_usage_pct / 100))

    @property
    def load_score(self) -> float:
        """0-100: 0 = idle, 100 = fully loaded."""
        cpu_score = self.cpu_usage_pct
        gpu_score = self.gpu_util_pct if self.has_gpu else 0
        return max(cpu_score, gpu_score)


@dataclass
class TaskRegistration:
    """A task that needs to be dispatched."""
    task_id: str
    title: str
    description: str = ""
    command: str = ""               # Shell command or hermes chat prompt
    profile: str = ""               # Hermes profile to use
    priority: int = 5               # 0=critical, 10=lowest
    required: ResourceRequirement = field(default_factory=ResourceRequirement)
    target_machine: str = ""        # auto="" or specific machine_id
    assigned_to: str = ""           # resolved machine_id
    status: str = "pending"         # pending → matched → dispatched → running → done/failed
    created_at: str = ""
    deadline: str = ""              # ISO timestamp
    timeout: int = 600              # seconds
    result: str = ""

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "command": self.command,
            "profile": self.profile,
            "priority": self.priority,
            "required": {
                "gpu": self.required.gpu,
                "gpu_memory_mb": self.required.gpu_memory_mb,
                "cpu_cores": self.required.cpu_cores,
                "ram_mb": self.required.ram_mb,
                "tags": self.required.tags,
            },
            "target_machine": self.target_machine,
            "assigned_to": self.assigned_to,
            "status": self.status,
            "created_at": self.created_at,
            "deadline": self.deadline,
            "timeout": self.timeout,
        }


@dataclass
class DispatchMatch:
    """Result of matching a task to a node."""
    task: TaskRegistration
    node: NodeCapability
    score: float                    # 0-100 match quality
    reason: str = ""
    alternatives: list[tuple[NodeCapability, float]] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# Node Capability Prober
# ═══════════════════════════════════════════════════════════════

class NodeProber:
    """Probe local machine capabilities."""

    @staticmethod
    def probe_all() -> NodeCapability:
        """Full capability probe for the local machine."""
        mid = f"{socket.gethostname()}-{os.getlogin()}"
        cap = NodeCapability(
            machine_id=mid,
            hostname=socket.gethostname(),
            role="unknown",
            ip_address=NodeProber._get_local_ip(),
        )

        # CPU
        cap.cpu_cores = os.cpu_count() or 1
        cap.cpu_usage_pct = NodeProber._cpu_usage()

        # RAM
        cap.ram_total_mb, cap.ram_free_mb = NodeProber._ram_info()

        # GPU
        gpu = NodeProber._probe_gpu()
        if gpu:
            cap.has_gpu = True
            cap.gpu_count = gpu["gpu_count"]
            cap.gpu_names = gpu["gpu_names"]
            cap.gpu_util_pct = gpu["util_pct"]
            cap.gpu_mem_total_mb = gpu["mem_total_mb"]
            cap.gpu_mem_used_mb = gpu["mem_used_mb"]
            cap.gpu_mem_free_mb = gpu["mem_total_mb"] - gpu["mem_used_mb"]
            cap.temp_c = gpu["temp_c"]

        # Disk
        cap.disk_total_gb, cap.disk_free_gb = NodeProber._disk_info()

        # OS
        cap.os = "macos" if os.uname().sysname == "Darwin" else "linux"

        # Python
        import sys
        cap.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

        # Docker
        try:
            r = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
            cap.has_docker = r.returncode == 0
        except Exception:
            cap.has_docker = False

        return cap

    @staticmethod
    def _get_local_ip() -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    @staticmethod
    def _cpu_usage() -> float:
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            return 0.0

    @staticmethod
    def _ram_info() -> tuple[int, int]:
        try:
            import psutil
            vmem = psutil.virtual_memory()
            return int(vmem.total / 1024 / 1024), int(vmem.available / 1024 / 1024)
        except ImportError:
            return 0, 0

    @staticmethod
    def _disk_info() -> tuple[float, float]:
        try:
            import shutil
            usage = shutil.disk_usage(os.path.expanduser("~"))
            return usage.total / 1e9, usage.free / 1e9
        except Exception:
            return 0.0, 0.0

    @staticmethod
    def _probe_gpu() -> dict:
        try:
            r = subprocess.run(
                ["nvidia-smi",
                 "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,name",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode != 0 or not r.stdout.strip():
                return {}
            lines = r.stdout.strip().split("\n")
            gpus = []
            for line in lines:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 5:
                    try:
                        gpus.append({
                            "name": parts[4],
                            "util_pct": float(parts[0]),
                            "mem_used_mb": int(parts[1]),
                            "mem_total_mb": int(parts[2]),
                            "temp_c": int(parts[3]),
                        })
                    except (ValueError, IndexError):
                        continue
            if not gpus:
                return {}
            utils = [g["util_pct"] for g in gpus]
            return {
                "gpu_count": len(gpus),
                "gpu_names": [g["name"] for g in gpus],
                "util_pct": round(sum(utils) / len(utils), 1),
                "mem_used_mb": sum(g["mem_used_mb"] for g in gpus),
                "mem_total_mb": sum(g["mem_total_mb"] for g in gpus),
                "temp_c": max(g["temp_c"] for g in gpus),
            }
        except (FileNotFoundError, Exception):
            return {}


# ═══════════════════════════════════════════════════════════════
# Fleet Scheduler
# ═══════════════════════════════════════════════════════════════

class FleetScheduler:
    """Resource-aware task-to-node scheduler.

    Usage:
        sched = FleetScheduler()
        sched.update_nodes()          # refresh from fleet/nodes/ + LAN
        match = sched.find_best_node(task)
        if match and match.score > 50:
            sched.dispatch(task, match.node)
    """

    def __init__(self):
        self.nodes: dict[str, NodeCapability] = {}
        self._local = NodeProber.probe_all()

    # ─── Node Registry ────────────────────────────────────────

    def update_nodes(self) -> list[NodeCapability]:
        """Refresh node registry from fleet/nodes/ + LAN peers.

        Priority: LAN peers > GitHub-synced nodes
        """
        self.nodes = {}
        self._local = NodeProber.probe_all()

        # 1. Load from fleet/nodes/ (GitHub-synced)
        try:
            from apex.interface.fleet_multi_mac import get_all_nodes, APEX_ROOT
            gh_nodes = get_all_nodes()
            for n in gh_nodes:
                mid = n.get("machine_id", "")
                gpu = n.get("gpu", {})
                cap = NodeCapability(
                    machine_id=mid,
                    hostname=n.get("hostname", "unknown"),
                    role=n.get("role", "unknown"),
                    has_gpu=bool(gpu),
                    gpu_count=gpu.get("gpu_count", 0),
                    gpu_names=gpu.get("gpu_names", []),
                    gpu_util_pct=gpu.get("util_pct", 0.0),
                    gpu_mem_total_mb=gpu.get("mem_total_mb", 0),
                    gpu_mem_used_mb=gpu.get("mem_used_mb", 0),
                    gpu_mem_free_mb=gpu.get("mem_total_mb", 0) - gpu.get("mem_used_mb", 0),
                    temp_c=gpu.get("temp_c", 0.0),
                    profiles=n.get("profiles", 0),
                    skills=n.get("skills", 0),
                    last_heartbeat=_parse_iso(n.get("reported_at", "")),
                )
                self.nodes[mid] = cap
        except Exception as e:
            pass  # fleet/nodes/ might not exist yet

        # 2. Overlay LAN peers (fresher + SSH reachable)
        try:
            from apex.fleet.lan_discovery import LANFleetDiscovery
            lan = LANFleetDiscovery()
            peers = lan.load_peers()
            for peer in peers:
                mid = peer.machine_id
                cap = self.nodes.get(mid)
                if cap is None:
                    cap = NodeCapability(
                        machine_id=mid,
                        hostname=peer.hostname,
                        role=peer.role,
                    )
                cap.ip_address = peer.ip_address
                cap.lan_reachable = peer.ssh_reachable
                cap.latency_ms = peer.latency_ms
                cap.last_heartbeat = max(cap.last_heartbeat, peer.last_seen)
                if peer.has_gpu and not cap.has_gpu:
                    cap.has_gpu = True
                    cap.gpu_names = peer.gpu_names
                cap.profiles = max(cap.profiles, peer.profiles)
                cap.skills = max(cap.skills, peer.skills)
                self.nodes[mid] = cap
        except Exception:
            pass

        # 3. Add self
        self.nodes[self._local.machine_id] = self._local

        return list(self.nodes.values())

    def get_node(self, machine_id: str) -> Optional[NodeCapability]:
        return self.nodes.get(machine_id)

    # ─── Scoring Engine ───────────────────────────────────────

    def score_node(self, task: TaskRegistration, node: NodeCapability) -> float:
        """Score a node's fitness for a task. Returns 0-100.

        Weight breakdown:
          GPU match:     40% (only applies if task needs GPU)
          CPU headroom:  25%
          RAM headroom:  15%
          Load penalty:  10%
          LAN proximity: 10%
        """
        req = task.required

        # ── Hard constraints ──
        # Must-have checks that disqualify a node
        if req.gpu and not node.has_gpu:
            return 0.0
        if req.gpu and node.gpu_mem_free_mb < req.gpu_memory_mb:
            return 0.0
        if req.cpu_cores > node.cpu_cores:
            return 0.0
        if req.ram_mb > node.ram_free_mb and node.ram_free_mb > 0:
            return 0.0
        if req.docker and not node.has_docker:
            return 0.0
        if req.os and req.os.lower() not in node.os.lower():
            return 0.0
        if req.tags:
            if not any(t in node.tags for t in req.tags):
                return 0.0

        score = 0.0
        weights = {"gpu": 0.40, "cpu": 0.25, "ram": 0.15, "load": 0.10, "lan": 0.10}

        # If task doesn't need GPU, redistribute GPU weight to CPU+RAM
        if not req.gpu:
            weights = {"gpu": 0.0, "cpu": 0.45, "ram": 0.25, "load": 0.15, "lan": 0.15}

        # ── GPU match ──
        if req.gpu and node.has_gpu:
            # Prefer low GPU utilization (more available)
            gpu_free_pct = 100 - node.gpu_util_pct
            mem_sufficient = node.gpu_mem_free_mb >= req.gpu_memory_mb if req.gpu_memory_mb else True
            gpu_score = min(100, gpu_free_pct) if mem_sufficient else 30
            score += weights["gpu"] * gpu_score

        # ── CPU headroom ──
        cpu_headroom = max(0, 100 - node.cpu_usage_pct)
        score += weights["cpu"] * cpu_headroom

        # ── RAM headroom ──
        if node.ram_total_mb > 0:
            ram_free_pct = node.ram_free_mb / node.ram_total_mb * 100
        else:
            ram_free_pct = 50
        score += weights["ram"] * min(100, ram_free_pct)

        # ── Load penalty ──
        load_penalty = node.load_score  # higher = worse
        score += weights["load"] * (100 - load_penalty)

        # ── LAN proximity ──
        if node.lan_reachable and node.latency_ms < 10:
            score += weights["lan"] * 100  # full LAN bonus
        elif node.lan_reachable:
            score += weights["lan"] * 70
        else:
            score += weights["lan"] * 10   # GitHub-only, low bonus

        return round(score, 1)

    # ─── Matching ─────────────────────────────────────────────

    def find_best_node(
        self,
        task: TaskRegistration,
        min_score: float = 30.0,
    ) -> Optional[DispatchMatch]:
        """Find the best node for a task.

        Args:
            task: Task to match
            min_score: Minimum score threshold (0-100)

        Returns:
            DispatchMatch or None if no node qualifies
        """
        if not self.nodes:
            self.update_nodes()

        # If task specifies a target, try that first
        if task.target_machine:
            target = self.nodes.get(task.target_machine)
            if target:
                score = self.score_node(task, target)
                if score >= min_score:
                    return DispatchMatch(task=task, node=target, score=score,
                                         reason=f"Target specified: {task.target_machine}")
            return None

        # Score all nodes
        scored = []
        for mid, node in self.nodes.items():
            if mid == self._local.machine_id:
                continue  # Skip self — tasks are dispatched to other nodes
            score = self.score_node(task, node)
            if score >= min_score:
                scored.append((node, score))

        if not scored:
            # Fallback: if no remote node qualifies, use local
            local = self.nodes.get(self._local.machine_id)
            if local:
                score = self.score_node(task, local)
                if score >= min_score:
                    scored.append((local, score))

        if not scored:
            return None

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        best_node, best_score = scored[0]
        alternatives = scored[1:4]  # top 3 alternatives

        reason = (f"GPU={best_node.has_gpu} CPU={best_node.cpu_free_cores:.0f}free "
                  f"RAM={best_node.ram_free_mb}MBfree LAN={'✅' if best_node.lan_reachable else '❌'}")

        return DispatchMatch(
            task=task, node=best_node, score=best_score,
            reason=reason, alternatives=alternatives,
        )

    def find_all_matches(
        self,
        task: TaskRegistration,
        min_score: float = 30.0,
    ) -> list[DispatchMatch]:
        """Find ALL nodes that qualify for a task, sorted by score."""
        if not self.nodes:
            self.update_nodes()

        scored = []
        for mid, node in self.nodes.items():
            score = self.score_node(task, node)
            if score >= min_score:
                scored.append(DispatchMatch(
                    task=task, node=node, score=score,
                    reason=f"score={score:.0f}",
                ))

        scored.sort(key=lambda m: m.score, reverse=True)
        return scored

    # ─── Dispatch ─────────────────────────────────────────────

    def dispatch(
        self,
        task: TaskRegistration,
        node: NodeCapability,
        timeout: Optional[int] = None,
    ) -> tuple[bool, str]:
        """Dispatch a task to a node.

        Automatically uses:
          - SSH if node is LAN-reachable
          - Hermes cron injection if SSH unavailable
          - Local execution if the node is local

        Args:
            task: Task to dispatch
            node: Target node
            timeout: Override task timeout

        Returns:
            (success, output_message)
        """
        if timeout is None:
            timeout = task.timeout

        # ── Self dispatch ──
        if node.machine_id == self._local.machine_id:
            return self._dispatch_local(task, timeout)

        # ── LAN SSH dispatch ──
        if node.lan_reachable and node.hostname:
            from apex.fleet.lan_discovery import LANFleetDiscovery
            ok, output = LANFleetDiscovery.ssh_dispatch_task(
                node.hostname, task.command or task.description,
                profile=task.profile, timeout=timeout,
            )
            task.status = "done" if ok else "failed"
            task.result = output[:2000]
            return ok, output[:2000]

        # ── GitHub-based dispatch (via fleet task queue) ──
        return self._dispatch_via_queue(task, node)

    def _dispatch_local(self, task: TaskRegistration, timeout: int) -> tuple[bool, str]:
        """Execute task on the local machine via hermes chat -q."""
        import shlex
        if task.profile:
            cmd = f"hermes -p {task.profile} chat -q {shlex.quote(task.command or task.description)}"
        else:
            cmd = f"hermes chat -q {shlex.quote(task.command or task.description)}"

        try:
            r = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout,
            )
            ok = r.returncode == 0
            task.status = "done" if ok else "failed"
            task.result = (r.stdout or r.stderr)[:2000]
            return ok, task.result
        except subprocess.TimeoutExpired:
            task.status = "failed"
            task.result = f"Timeout after {timeout}s"
            return False, task.result
        except Exception as e:
            task.status = "failed"
            task.result = str(e)
            return False, str(e)

    def _dispatch_via_queue(self, task: TaskRegistration, node: NodeCapability) -> tuple[bool, str]:
        """Dispatch by writing to fleet task queue JSON (picked up by cron)."""
        task_file = Path(os.path.expanduser("~/.apex/task_queue.json"))

        tasks = []
        if task_file.exists():
            try:
                tasks = json.loads(task_file.read_text())
            except Exception:
                pass

        task.assigned_to = node.machine_id
        task.status = "dispatched"
        task.created_at = datetime.now().isoformat()
        tasks.append(task.to_dict())

        task_file.parent.mkdir(parents=True, exist_ok=True)
        task_file.write_text(json.dumps(tasks, indent=2, ensure_ascii=False))

        return True, f"Task queued for {node.machine_id} (via fleet task queue)"


# ─── Task Queue Manager ───────────────────────────────────────

class TaskQueue:
    """Persistent task queue for cross-machine dispatch."""

    QUEUE_FILE = Path(os.path.expanduser("~/.apex/task_queue.json"))

    @classmethod
    def add(cls, task: TaskRegistration):
        """Add a task to the persistent queue."""
        tasks = cls.list_all()
        tasks.append(task.to_dict())
        cls.QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
        cls.QUEUE_FILE.write_text(json.dumps(tasks, indent=2, ensure_ascii=False))

    @classmethod
    def list_all(cls) -> list[dict]:
        """List all tasks in the queue."""
        if not cls.QUEUE_FILE.exists():
            return []
        try:
            return json.loads(cls.QUEUE_FILE.read_text())
        except Exception:
            return []

    @classmethod
    def list_pending(cls) -> list[dict]:
        """List pending/dispatched tasks."""
        return [t for t in cls.list_all() if t.get("status") in ("pending", "dispatched", "matched")]

    @classmethod
    def update_status(cls, task_id: str, status: str, result: str = ""):
        """Update a task's status."""
        tasks = cls.list_all()
        for t in tasks:
            if t.get("task_id") == task_id:
                t["status"] = status
                if result:
                    t["result"] = result
                break
        cls.QUEUE_FILE.write_text(json.dumps(tasks, indent=2, ensure_ascii=False))

    @classmethod
    def remove(cls, task_id: str):
        """Remove a task from the queue."""
        tasks = [t for t in cls.list_all() if t.get("task_id") != task_id]
        cls.QUEUE_FILE.write_text(json.dumps(tasks, indent=2, ensure_ascii=False))


# ─── Utility ──────────────────────────────────────────────────

def _parse_iso(s: str) -> float:
    """Parse ISO timestamp to unix epoch."""
    try:
        return datetime.fromisoformat(s).timestamp()
    except Exception:
        return 0.0
