"""Multi-Agent Collaboration Patterns — orchestration mode registry and exports."""
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
try:
    from .autonomous import AutonomousEngine, get_engine, AutonomousReport
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
