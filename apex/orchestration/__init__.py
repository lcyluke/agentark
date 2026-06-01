"""Apex — Orchestration: Multi-Agent Collaboration Patterns

Available modes covering TOP10 multi-agent use cases:

| Mode | File | Use Case |
|------|------|----------|
| Single Agent | runtime.py | Individual task execution |
| Swarm | swarm.py | Parallel workers → verifier → synthesizer |
| Crew | crew.py | Role-based real-time collaboration |
| Chain | chain.py | Sequential pipeline with handoff verification |
| Debate | debate.py | Multi-perspective analysis and refinement |
| Router | router.py | Task classification and dispatch routing |
| Supervisor | supervisor.py | Hierarchical delegation with review gates |
| Monitor | monitor.py | Passive anomaly detection → reactive agents |
| Kanban | kanban.py | Smart task board with dependency management |
| Healing | healing.py | Self-healing with 3-strike auto-recovery |
"""
from .swarm import Swarm, SwarmResult
from .crew import Crew, CrewResult, DynamicTeamDesigner
from .kanban import Kanban, Task
from .healing import SelfHealingExecutor, HealingResult

# New modes
try:
    from .chain import Chain, ChainStage, ChainResult
except ImportError:
    pass
try:
    from .debate import Debate, DebateResult
except ImportError:
    pass
try:
    from .router import Router, RouterResult
except ImportError:
    pass
try:
    from .supervisor import Supervisor, SupervisorResult
except ImportError:
    pass
try:
    from .monitor import Monitor, MonitorResult
except ImportError:
    pass

__all__ = [
    "Swarm", "SwarmResult",
    "Crew", "CrewResult", "DynamicTeamDesigner",
    "Kanban", "Task",
    "SelfHealingExecutor", "HealingResult",
    "Chain", "ChainStage", "ChainResult",
    "Debate", "DebateResult",
    "Router", "RouterResult",
    "Supervisor", "SupervisorResult",
    "Monitor", "MonitorResult",
]
