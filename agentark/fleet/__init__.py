"""Apex Fleet Module — tmux-backed multi-agent session management.

Makes tmux a first-class citizen in Apex. Every `apex fleet start` launches
agents in isolated tmux windows with full lifecycle management.

Architecture:
    apex fleet init       → creates tmux session + profiles
    apex fleet start      → launches all agent windows
    apex fleet stop       → stops agents (keeps tmux session)
    apex fleet destroy    → kills tmux session entirely
    apex fleet attach     → attaches to the tmux session
    apex fleet log <agent> → shows recent output from an agent window

New in v2:
    apex fleet lan        → LAN peer discovery (mDNS + SSH)
    apex fleet dispatch   → Resource-aware task dispatch
    apex fleet probe      → Show local machine capabilities
"""

from .tmux_manager import TmuxFleetManager
from .profiles import ProfileBundler
from .lan_discovery import LANFleetDiscovery, LANPeer
from .scheduler import (
    FleetScheduler, NodeProber, TaskQueue,
    TaskRegistration, ResourceRequirement,
    NodeCapability, DispatchMatch,
)

__all__ = [
    "TmuxFleetManager",
    "ProfileBundler",
    "LANFleetDiscovery",
    "LANPeer",
    "FleetScheduler",
    "NodeProber",
    "TaskQueue",
    "TaskRegistration",
    "ResourceRequirement",
    "NodeCapability",
    "DispatchMatch",
]
