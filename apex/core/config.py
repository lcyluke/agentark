"""Apex Configuration Engine — typed config with YAML persistence.

Layered priority (high → low):
  1. Environment variables (APEX_*)
  2. ~/.apex/config.yaml
  3. Hardcoded defaults

Usage:
  from apex.core.config import get_config, Config
  cfg = get_config()
  cfg.model.default          # "deepseek-v4-pro"
  cfg.model.set("claude-sonnet-4")
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

APEX_HOME = Path(os.environ.get("APEX_HOME", Path.home() / ".apex"))
CONFIG_PATH = APEX_HOME / "config.yaml"
CONFIG_SCHEMA_PATH = APEX_HOME / "config.schema.json"


# ─── Config Schema ────────────────────────────────────────────────

CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "version": {"type": "string"},
        "model": {
            "type": "object",
            "properties": {
                "default": {"type": "string"},
                "provider": {"type": "string"},
                "base_url": {"type": "string"},
                "api_key_env": {"type": "string"},
                "context_length": {"type": "integer"},
            },
        },
        "fleet": {
            "type": "object",
            "properties": {
                "session_name": {"type": "string", "default": "apex-fleet"},
                "window_width": {"type": "integer", "default": 160},
                "window_height": {"type": "integer", "default": 40},
                "auto_start": {"type": "boolean", "default": False},
            },
        },
        "ui": {
            "type": "object",
            "properties": {
                "theme": {"type": "string", "default": "dark"},
                "show_banner": {"type": "boolean", "default": True},
                "compact_mode": {"type": "boolean", "default": False},
                "lang": {"type": "string", "default": "zh-CN"},
            },
        },
        "notify": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "default": False},
                "macos_notifications": {"type": "boolean", "default": True},
                "slack_webhook": {"type": "string"},
                "wecom_webhook": {"type": "string"},
            },
        },
        "providers": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "api_key_env": {"type": "string"},
                    "base_url": {"type": "string"},
                },
            },
        },
    },
}

# ─── Data Models ──────────────────────────────────────────────────


@dataclass
class ModelConfig:
    default: str = "deepseek-v4-pro"
    provider: str = "deepseek"
    base_url: str = ""
    api_key_env: str = "DEEPSEEK_API_KEY"
    context_length: int = 131072

    def to_dict(self) -> dict:
        return {
            "default": self.default,
            "provider": self.provider,
            "base_url": self.base_url,
            "api_key_env": self.api_key_env,
            "context_length": self.context_length,
        }

    def set(self, model: str, provider: str = ""):
        self.default = model
        if provider:
            self.provider = provider


@dataclass
class FleetConfig:
    session_name: str = "apex-fleet"
    window_width: int = 160
    window_height: int = 40
    auto_start: bool = False


@dataclass
class UIConfig:
    theme: str = "dark"
    show_banner: bool = True
    compact_mode: bool = False
    lang: str = "zh-CN"


@dataclass
class NotifyConfig:
    enabled: bool = False
    macos_notifications: bool = True
    slack_webhook: str = ""
    wecom_webhook: str = ""


@dataclass
class Config:
    """Top-level configuration object."""

    version: str = "1.0"
    model: ModelConfig = field(default_factory=ModelConfig)
    fleet: FleetConfig = field(default_factory=FleetConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    notify: NotifyConfig = field(default_factory=NotifyConfig)
    providers: dict[str, dict] = field(default_factory=dict)

    # ── Load / Save ───────────────────────────────────────────────

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "Config":
        """Load config from YAML file, falling back to defaults."""
        cfg = cls()

        if path.exists():
            try:
                with open(path) as f:
                    data = yaml.safe_load(f) or {}
            except Exception:
                data = {}

            if "model" in data:
                m = data["model"]
                cfg.model = ModelConfig(
                    default=m.get("default", cfg.model.default),
                    provider=m.get("provider", cfg.model.provider),
                    base_url=m.get("base_url", cfg.model.base_url),
                    api_key_env=m.get("api_key_env", cfg.model.api_key_env),
                    context_length=m.get("context_length", cfg.model.context_length),
                )

            if "fleet" in data:
                f = data["fleet"]
                cfg.fleet = FleetConfig(
                    session_name=f.get("session_name", cfg.fleet.session_name),
                    window_width=f.get("window_width", cfg.fleet.window_width),
                    window_height=f.get("window_height", cfg.fleet.window_height),
                    auto_start=f.get("auto_start", cfg.fleet.auto_start),
                )

            if "ui" in data:
                u = data["ui"]
                cfg.ui = UIConfig(
                    theme=u.get("theme", cfg.ui.theme),
                    show_banner=u.get("show_banner", cfg.ui.show_banner),
                    compact_mode=u.get("compact_mode", cfg.ui.compact_mode),
                    lang=u.get("lang", cfg.ui.lang),
                )

            if "notify" in data:
                n = data["notify"]
                cfg.notify = NotifyConfig(
                    enabled=n.get("enabled", cfg.notify.enabled),
                    macos_notifications=n.get(
                        "macos_notifications", cfg.notify.macos_notifications
                    ),
                    slack_webhook=n.get("slack_webhook", cfg.notify.slack_webhook),
                    wecom_webhook=n.get("wecom_webhook", cfg.notify.wecom_webhook),
                )

            if "providers" in data:
                cfg.providers = data["providers"]

        # ── Environment variable overrides ──
        cfg._apply_env_overrides()

        return cfg

    def _apply_env_overrides(self):
        """Apply APEX_* environment variables as overrides."""
        overrides = {
            "APEX_MODEL": ("model", "default"),
            "APEX_PROVIDER": ("model", "provider"),
            "APEX_BASE_URL": ("model", "base_url"),
            "APEX_API_KEY_ENV": ("model", "api_key_env"),
            "APEX_THEME": ("ui", "theme"),
            "APEX_LANG": ("ui", "lang"),
        }
        for env_var, (section, key) in overrides.items():
            val = os.environ.get(env_var, "")
            if val:
                obj = getattr(self, section)
                if hasattr(obj, key):
                    setattr(obj, key, val)

    def save(self, path: Path = CONFIG_PATH):
        """Persist config to YAML file."""
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": self.version,
            "model": self.model.to_dict(),
            "fleet": {
                "session_name": self.fleet.session_name,
                "window_width": self.fleet.window_width,
                "window_height": self.fleet.window_height,
                "auto_start": self.fleet.auto_start,
            },
            "ui": {
                "theme": self.ui.theme,
                "show_banner": self.ui.show_banner,
                "compact_mode": self.ui.compact_mode,
                "lang": self.ui.lang,
            },
            "notify": {
                "enabled": self.notify.enabled,
                "macos_notifications": self.notify.macos_notifications,
                "slack_webhook": self.notify.slack_webhook,
                "wecom_webhook": self.notify.wecom_webhook,
            },
            "providers": self.providers,
        }
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # ── Query helpers ─────────────────────────────────────────────

    def get(self, section: str, key: str, default: Any = None) -> Any:
        obj = getattr(self, section, None)
        if obj and hasattr(obj, key):
            return getattr(obj, key)
        return default

    def set(self, section: str, key: str, value: Any):
        obj = getattr(self, section, None)
        if obj and hasattr(obj, key):
            setattr(obj, key, value)
            self.save()

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "model": self.model.to_dict(),
            "fleet": {
                "session_name": self.fleet.session_name,
                "window_width": self.fleet.window_width,
                "window_height": self.fleet.window_height,
                "auto_start": self.fleet.auto_start,
            },
            "ui": {
                "theme": self.ui.theme,
                "show_banner": self.ui.show_banner,
                "compact_mode": self.ui.compact_mode,
                "lang": self.ui.lang,
            },
            "notify": {
                "enabled": self.notify.enabled,
                "macos_notifications": self.notify.macos_notifications,
                "slack_webhook": self.notify.slack_webhook,
                "wecom_webhook": self.notify.wecom_webhook,
            },
            "providers": self.providers,
        }


# ─── Singleton ────────────────────────────────────────────────────

_config: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """Get the global config singleton."""
    global _config
    if _config is None or reload:
        _config = Config.load()
    return _config


def save_config(cfg: Config | None = None):
    """Persist the current config."""
    if cfg is None:
        cfg = get_config()
    cfg.save()


def config_exists() -> bool:
    """Check if a config file exists (used for first-run detection)."""
    return CONFIG_PATH.exists()


def config_path() -> Path:
    return CONFIG_PATH
