"""AgentArk Command Aliases — short aliases for frequent commands.

Stored in ~/.apex/aliases.yaml, editable via `apex alias add/remove/list`.

Built-in defaults:
  s  → monitor status
  fs → fleet status
  fl → fleet log
  p  → pm dashboard
  ps → pm schedule
  ph → pm health
  up → update
  v  → version
"""

import json
from pathlib import Path

from apex.core.config import APEX_HOME

ALIASES_PATH = APEX_HOME / "aliases.json"

BUILTIN_ALIASES = {
    "s": "monitor status",
    "fs": "fleet status",
    "fl": "fleet log",
    "fa": "fleet attach",
    "p": "pm dashboard",
    "ps": "pm schedule",
    "pa": "pm assign",
    "ph": "pm health",
    "pt": "pm timeline",
    "up": "update",
    "v": "version",
    "cs": "config show",
    "cm": "config model show",
}


def load_aliases() -> dict[str, str]:
    """Load aliases, merging built-ins with user overrides."""
    aliases = dict(BUILTIN_ALIASES)
    if ALIASES_PATH.exists():
        try:
            with open(ALIASES_PATH) as f:
                user_aliases = json.load(f)
            aliases.update(user_aliases)
        except Exception:
            pass
    return aliases


def save_aliases(aliases: dict[str, str]):
    """Save user aliases to disk."""
    ALIASES_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Only save non-builtin aliases
    user = {k: v for k, v in aliases.items() if k not in BUILTIN_ALIASES}
    with open(ALIASES_PATH, "w") as f:
        json.dump(user, f, indent=2, ensure_ascii=False)


def resolve_alias(name: str) -> str | None:
    """Resolve an alias to its full command."""
    aliases = load_aliases()
    return aliases.get(name)


def add_alias(name: str, command: str) -> bool:
    """Add a user alias."""
    aliases = load_aliases()
    aliases[name] = command
    save_aliases(aliases)
    return True


def remove_alias(name: str) -> bool:
    """Remove a user alias. Cannot remove built-in aliases."""
    if name in BUILTIN_ALIASES:
        return False
    aliases = load_aliases()
    if name in aliases:
        del aliases[name]
        save_aliases(aliases)
        return True
    return False


def list_aliases() -> dict[str, str]:
    """List all aliases with built-in markers."""
    aliases = load_aliases()
    result = {}
    for name, cmd in aliases.items():
        marker = "[内置]" if name in BUILTIN_ALIASES else "[自定义]"
        result[name] = (cmd, marker)
    return result
