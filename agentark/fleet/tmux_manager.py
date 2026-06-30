"""TmuxFleetManager — lifecycle management for Apex agent fleets via tmux.

Provides the operational backbone that turns tmux from an external tool
into Apex's native multi-agent runtime environment.

Key design decisions:
- One tmux session per fleet (default: "apex-fleet")
- One tmux window per agent
- Agents survive terminal close, SSH disconnect, sleep/wake
- All state queries via `tmux list-windows` / `tmux capture-pane`
"""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

FLEET_SESSION = "apex-fleet"
HERMES_BIN = os.path.expanduser("~/.local/bin")


@dataclass
class AgentWindow:
    """A single agent running in a tmux window."""
    name: str
    window_index: int
    active: bool = False
    pid: str = ""
    last_output: str = ""


@dataclass
class FleetState:
    """Snapshot of the entire fleet."""
    session_name: str
    exists: bool
    agents: list[AgentWindow] = field(default_factory=list)
    total_windows: int = 0


class TmuxFleetManager:
    """Manages the Apex fleet as a tmux session.

    Usage:
        fm = TmuxFleetManager()
        fm.init_fleet(["pm", "architect", "backend-dev"])
        fm.start()
        fm.status()
    """

    def __init__(self, session_name: str = FLEET_SESSION):
        self.session_name = session_name
        self._check_tmux()

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    @staticmethod
    def _check_tmux():
        """Verify tmux is installed and available."""
        try:
            subprocess.run(["tmux", "-V"], capture_output=True, timeout=3, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "tmux is not installed. Install it with: brew install tmux"
            )

    @property
    def exists(self) -> bool:
        """Check if the fleet tmux session exists."""
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", self.session_name],
                capture_output=True, timeout=3,
            )
            return result.returncode == 0
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Fleet Lifecycle
    # ------------------------------------------------------------------

    def init_fleet(self, agents: list[str], window_width: int = 160,
                   window_height: int = 40) -> FleetState:
        """Create the tmux session with one window for the first agent.

        Args:
            agents: Agent profile names (e.g. ["pm", "architect", "backend-dev"])
            window_width: tmux window width in columns
            window_height: tmux window height in rows

        Returns:
            FleetState snapshot
        """
        if not agents:
            raise ValueError("At least one agent required to init fleet")

        if self.exists:
            return self.status()

        # Create session with first agent
        first = agents[0]
        cmd = f"hermes -p {first} chat"
        subprocess.run(
            [
                "tmux", "new-session", "-d",
                "-s", self.session_name,
                "-n", first,
                "-x", str(window_width),
                "-y", str(window_height),
                cmd,
            ],
            capture_output=True, timeout=10, check=True,
        )

        # Add remaining agents as windows
        for agent in agents[1:]:
            self.add_agent(agent)

        return self.status()

    def start(self, agents: Optional[list[str]] = None) -> FleetState:
        """Start (or restart) the fleet.

        If the session doesn't exist, creates it with given agents.
        If it exists, ensures all agent windows are running.

        Args:
            agents: Agent names. If None and session exists, uses existing windows.

        Returns:
            FleetState snapshot
        """
        if not self.exists:
            if not agents:
                raise ValueError(
                    "Fleet does not exist. Provide agents list or run 'apex fleet init' first."
                )
            return self.init_fleet(agents)

        # Session exists — verify windows are alive, restart dead ones
        state = self.status()
        for agent in state.agents:
            if not agent.active:
                self.add_agent(agent.name)

        return self.status()

    def stop(self, kill_session: bool = False):
        """Stop agents (kill windows) or destroy the entire session.

        Args:
            kill_session: If True, kill the tmux session entirely.
                          If False, only kill agent windows but keep the session.
        """
        if not self.exists:
            return

        if kill_session:
            subprocess.run(
                ["tmux", "kill-session", "-t", self.session_name],
                capture_output=True, timeout=5,
            )
        else:
            # Kill all windows except window 0 (keep session alive)
            state = self.status()
            for agent in state.agents:
                if agent.window_index > 0:
                    subprocess.run(
                        ["tmux", "kill-window", "-t",
                         f"{self.session_name}:{agent.window_index}"],
                        capture_output=True, timeout=5,
                    )
            # Kill window 0 last
            if state.agents:
                subprocess.run(
                    ["tmux", "kill-window", "-t", f"{self.session_name}:0"],
                    capture_output=True, timeout=5,
                )

    def destroy(self):
        """Alias for stop(kill_session=True)."""
        self.stop(kill_session=True)

    # ------------------------------------------------------------------
    # Agent Management
    # ------------------------------------------------------------------

    def add_agent(self, agent_name: str) -> bool:
        """Add a new agent window to the running fleet.

        Args:
            agent_name: Hermes profile name

        Returns:
            True if added successfully
        """
        if not self.exists:
            return False

        try:
            subprocess.run(
                [
                    "tmux", "new-window",
                    "-t", self.session_name,
                    "-n", agent_name,
                    f"hermes -p {agent_name} chat",
                ],
                capture_output=True, timeout=10, check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def kill_agent(self, agent_name: str) -> bool:
        """Kill a specific agent window.

        Args:
            agent_name: Name of the agent window to kill

        Returns:
            True if killed successfully
        """
        if not self.exists:
            return False

        try:
            subprocess.run(
                ["tmux", "kill-window", "-t", f"{self.session_name}:{agent_name}"],
                capture_output=True, timeout=5, check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def send_to_agent(self, agent_name: str, message: str) -> bool:
        """Send a message/command to an agent window.

        Args:
            agent_name: Target agent window name
            message: Message to send (Enter is appended automatically)

        Returns:
            True if sent successfully
        """
        if not self.exists:
            return False

        try:
            subprocess.run(
                ["tmux", "send-keys", "-t", f"{self.session_name}:{agent_name}",
                 message, "Enter"],
                capture_output=True, timeout=5, check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    # ------------------------------------------------------------------
    # Status & Monitoring
    # ------------------------------------------------------------------

    def status(self) -> FleetState:
        """Get current fleet state snapshot.

        Returns:
            FleetState with all agent windows and their status
        """
        if not self.exists:
            return FleetState(
                session_name=self.session_name,
                exists=False,
                agents=[],
                total_windows=0,
            )

        # List windows
        try:
            result = subprocess.run(
                ["tmux", "list-windows", "-t", self.session_name,
                 "-F", "#{window_index}:#{window_name}:#{window_active}:#{pane_pid}"],
                capture_output=True, text=True, timeout=3,
            )
        except subprocess.CalledProcessError:
            return FleetState(
                session_name=self.session_name, exists=False, agents=[], total_windows=0
            )

        agents = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split(":", 3)
            if len(parts) < 4:
                continue
            idx, name, active, pid = parts
            agents.append(AgentWindow(
                name=name,
                window_index=int(idx),
                active=(active == "1"),
                pid=pid,
            ))

        return FleetState(
            session_name=self.session_name,
            exists=True,
            agents=agents,
            total_windows=len(agents),
        )

    def log(self, agent_name: str, lines: int = 30) -> str:
        """Capture recent output from an agent window.

        Args:
            agent_name: Agent window name
            lines: Number of lines to capture (from end)

        Returns:
            Captured pane content
        """
        if not self.exists:
            return ""

        try:
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", f"{self.session_name}:{agent_name}",
                 "-p", "-S", f"-{lines}"],
                capture_output=True, text=True, timeout=5,
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ""

    def attach_command(self) -> str:
        """Return the command string to attach to the fleet session.

        Returns:
            Shell command string like 'tmux attach -t apex-fleet'
        """
        return f"tmux attach -t {self.session_name}"

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def restart_agent(self, agent_name: str) -> bool:
        """Kill and restart an agent window.

        Args:
            agent_name: Agent to restart

        Returns:
            True if restarted successfully
        """
        if self.kill_agent(agent_name):
            time.sleep(1)
            return self.add_agent(agent_name)
        return False

    def broadcast(self, message: str):
        """Send a message to all agent windows simultaneously.

        Args:
            message: Message to broadcast
        """
        state = self.status()
        for agent in state.agents:
            self.send_to_agent(agent.name, message)
