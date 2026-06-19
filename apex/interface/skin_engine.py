"""Apex Skin Engine — CLI theme system with built-in themes.

Usage:
  from apex.interface.skin_engine import SkinEngine, get_skin
  skin = get_skin()           # current theme
  skin.colors.primary          # "#00ffff"
  apex config set ui.theme ocean
"""

from dataclasses import dataclass
from typing import Optional

from apex.core.config import get_config


@dataclass
class SkinColors:
    primary: str = "#00ffff"      # cyan
    secondary: str = "#3b82f6"    # blue
    success: str = "#22c55e"      # green
    warning: str = "#f59e0b"      # yellow
    danger: str = "#ef4444"       # red
    muted: str = "#6b7280"        # gray
    accent: str = "#8b5cf6"       # purple
    bg: str = "#0f172a"           # dark bg
    border: str = "#1e293b"       # border


@dataclass
class Skin:
    name: str
    display: str
    description: str
    colors: SkinColors

    def rich_theme(self) -> dict:
        """Convert to Rich theme dict."""
        return {
            "primary": self.colors.primary,
            "secondary": self.colors.secondary,
            "success": self.colors.success,
            "warning": self.colors.warning,
            "danger": self.colors.danger,
            "muted": self.colors.muted,
            "accent": self.colors.accent,
        }


# ─── Built-in themes ─────────────────────────────────────────────

THEMES = {
    "dark": Skin(
        name="dark",
        display="🌙 Dark",
        description="默认暗色主题，护眼舒适",
        colors=SkinColors(
            primary="#00ffff",
            secondary="#3b82f6",
            success="#22c55e",
            warning="#f59e0b",
            danger="#ef4444",
            muted="#6b7280",
            accent="#8b5cf6",
        ),
    ),
    "ocean": Skin(
        name="ocean",
        display="🌊 Ocean",
        description="海洋蓝调，清新冷静",
        colors=SkinColors(
            primary="#0ea5e9",
            secondary="#06b6d4",
            success="#10b981",
            warning="#f59e0b",
            danger="#ef4444",
            muted="#64748b",
            accent="#6366f1",
            bg="#0c1929",
        ),
    ),
    "sunset": Skin(
        name="sunset",
        display="🌅 Sunset",
        description="暖色日落，创意氛围",
        colors=SkinColors(
            primary="#f97316",
            secondary="#eab308",
            success="#22c55e",
            warning="#f59e0b",
            danger="#ef4444",
            muted="#78716c",
            accent="#a855f7",
            bg="#1c1917",
        ),
    ),
    "forest": Skin(
        name="forest",
        display="🌲 Forest",
        description="森林绿调，自然专注",
        colors=SkinColors(
            primary="#22c55e",
            secondary="#10b981",
            success="#4ade80",
            warning="#eab308",
            danger="#ef4444",
            muted="#6b7280",
            accent="#06b6d4",
            bg="#0f1a14",
        ),
    ),
    "mono": Skin(
        name="mono",
        display="⬜ Mono",
        description="极简黑白，专注内容",
        colors=SkinColors(
            primary="#ffffff",
            secondary="#a1a1aa",
            success="#ffffff",
            warning="#a1a1aa",
            danger="#ffffff",
            muted="#52525b",
            accent="#a1a1aa",
            bg="#000000",
        ),
    ),
}


# ─── Skin Engine ──────────────────────────────────────────────────


class SkinEngine:
    """Manage and apply CLI themes."""

    def __init__(self):
        self.themes = THEMES

    @property
    def current(self) -> Skin:
        """Get the currently active skin."""
        cfg = get_config()
        theme_name = cfg.ui.theme
        return self.themes.get(theme_name, self.themes["dark"])

    def set_theme(self, name: str) -> bool:
        """Set active theme by name."""
        if name not in self.themes:
            return False
        cfg = get_config()
        cfg.ui.theme = name
        cfg.save()
        return True

    def list_themes(self) -> list[Skin]:
        return list(self.themes.values())

    def preview(self, name: str) -> Optional[Skin]:
        """Preview a theme without applying."""
        return self.themes.get(name)


# ─── Singleton ────────────────────────────────────────────────────

_engine: Optional[SkinEngine] = None


def get_skin() -> Skin:
    global _engine
    if _engine is None:
        _engine = SkinEngine()
    return _engine.current


def get_engine() -> SkinEngine:
    global _engine
    if _engine is None:
        _engine = SkinEngine()
    return _engine
