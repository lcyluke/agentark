"""Apex Logo & Banner — brand identity with ASCII art and emoji variants.

Usage:
  from apex.interface.logo import render_banner, render_mini
  render_banner(console)      # Full banner on startup
  render_mini(console)        # Compact one-liner
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich import box

# ─── Logo variants ───────────────────────────────────────────────

LOGO_ASCII = r"""
     ⚡
    ╱│╲
   ╱ │ ╲   Apex
  ╱  │  ╲  Multi-Agent OS
 ╱   │   ╲
▕─────┼─────▏
 ╲   │   ╱  One person,
  ╲  │  ╱   infinite capacity.
   ╲ │ ╱
    ╲│╱
"""

LOGO_EMOJI = "⚡🛡️ ⚔️ 🏛️ 🔧 💻 🧪 🚀"

LOGO_MINI = "⚡ apex"


def render_banner(console: Console, version: str = ""):
    """Render the full Apex banner with ASCII art."""
    console.print()
    text = Text(LOGO_ASCII, style="bold cyan")
    console.print(Align.center(text))
    if version:
        console.print(Align.center(f"[dim]v{version}[/]"))
    console.print()


def render_mini(console: Console, version: str = ""):
    """Render a compact one-line banner."""
    v = f" v{version}" if version else ""
    console.print(f"[bold cyan]{LOGO_MINI}[/]{v}")


def render_startup(console: Console, version: str = "", model: str = "",
                   agents: int = 0, tools: int = 0):
    """Render the full startup dashboard."""
    from apex.core.config import get_config

    console.print()
    console.print(Panel(
        f"[bold cyan]⚡ Apex[/] [dim]v{version}[/]\n"
        f"[dim]Multi-Agent Operating System[/]",
        border_style="cyan",
        subtitle="one person, infinite capacity",
    ))

    cfg = get_config()
    lines = [
        f"[bold]Model:[/] [green]{model or cfg.model.default}[/]",
        f"[bold]Provider:[/] {cfg.model.provider}",
    ]
    if agents > 0:
        lines.append(f"[bold]Fleet:[/] [green]{agents} agents[/]")
    if tools > 0:
        lines.append(f"[bold]Tools:[/] [green]{tools} discovered[/]")

    console.print("  " + "  │  ".join(lines))
    console.print(f"  [dim]Config: ~/.apex/config.yaml[/]")
    console.print(f"  [dim]Help:   apex --help[/]")
    console.print()
