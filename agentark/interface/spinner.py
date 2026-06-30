"""Apex Spinner — animated loading indicators for long operations.

Built on Rich's Progress/Spinner, with Apex-branded styles.

Usage:
  from agentark.interface.spinner import ApexSpinner
  with ApexSpinner("Loading agents...", style="fleet") as sp:
      do_work()
      sp.update("Initializing profiles...")
"""

from contextlib import contextmanager
from typing import Optional

from rich.console import Console
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn,
    TaskProgressColumn, TimeRemainingColumn,
)
from rich.spinner import Spinner

console = Console()

# Custom spinner styles
STYLES = {
    "dots": "dots",
    "arrow": "arrow3",
    "bounce": "bouncingBar",
    "pulse": "aesthetic",
    "fleet": "dots12",
    "kaomoji": "moon",
    "minimal": "simpleDots",
}


@contextmanager
def ApexSpinner(
    message: str = "Working...",
    style: str = "dots",
    total: Optional[int] = None,
):
    """Apex-branded spinner with progress bar.

    Args:
        message: Initial status message
        style: Spinner style (dots/arrow/bounce/pulse/fleet/kaomoji/minimal)
        total: Total steps for progress bar (None = indeterminate)

    Yields:
        ApexSpinner instance with .update() method
    """
    spinner_name = STYLES.get(style, "dots")

    columns = [
        SpinnerColumn(spinner_name, style="cyan"),
        TextColumn("[progress.description]{task.description}"),
    ]
    if total:
        columns.extend([
            BarColumn(),
            TaskProgressColumn(),
        ])

    progress = Progress(*columns, console=console, transient=False)
    task = progress.add_task(f"[cyan]{message}", total=total)

    spinner = _SpinnerHandle(progress, task)
    try:
        progress.start()
        yield spinner
    finally:
        progress.stop()


class _SpinnerHandle:
    def __init__(self, progress: Progress, task_id):
        self._progress = progress
        self._task = task_id

    def update(self, message: str, advance: int = 0):
        self._progress.update(self._task, description=f"[cyan]{message}",
                              advance=advance)

    def done(self, message: str = "Done"):
        self._progress.update(self._task, description=f"[green]✅ {message}",
                              completed=True)


def spinner(message: str = "Working...", style: str = "dots"):
    """Simple non-context-manager spinner. Use ApexSpinner for progress bars."""
    return ApexSpinner(message, style)


def fleet_spinner(message: str = "Deploying fleet..."):
    """Pre-configured fleet spinner."""
    return ApexSpinner(message, style="fleet", total=7)
