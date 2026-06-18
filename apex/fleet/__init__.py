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
"""

from .tmux_manager import TmuxFleetManager
from .profiles import ProfileBundler

__all__ = ["TmuxFleetManager", "ProfileBundler"]
