"""Runtime Adapter Protocol — abstract interface for spawning and managing runtimes.

Every concrete runtime (Docker, shell, Wasm, etc.) implements this protocol so
the orchestrator can treat them uniformly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from agentark.protocol import InstanceState, Runtime


# ── Adapter-level Types ──────────────────────────────────────────────────────

from enum import Enum


class InstanceStatus(str, Enum):
    """Lifecycle status of a runtime instance (adapter-level view)."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class SessionHandle:
    """Opaque handle to a runtime session returned by RuntimeAdapter.spawn()."""
    id: str
    name: str = ""
    runtime: Runtime = Runtime.PYTHON
    status: str = "active"
    created_at: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class SpawnSpec:
    """Input specification for RuntimeAdapter.spawn()."""
    runtime: Runtime = Runtime.PYTHON
    image: str = ""
    command: str = ""
    env: dict = field(default_factory=dict)
    workdir: str = ""
    timeout: int = 300
    labels: dict = field(default_factory=dict)


# ── Protocol ─────────────────────────────────────────────────────────────────

@runtime_checkable
class RuntimeAdapter(Protocol):
    """Protocol that every runtime adapter must satisfy.

    Implementations: DockerAdapter, ShellAdapter, WasmAdapter, etc.
    """

    def spawn(self, spec: SpawnSpec) -> SessionHandle:
        """Spawn a new runtime instance and return a handle."""
        ...

    def status(self, handle: SessionHandle) -> InstanceState:
        """Return the current state of the instance."""
        ...

    def stop(self, handle: SessionHandle) -> bool:
        """Stop the instance. Returns True on success."""
        ...

    def exec(self, handle: SessionHandle, command: str) -> tuple[int, str, str]:
        """Execute a command inside the instance. Returns (exit_code, stdout, stderr)."""
        ...
