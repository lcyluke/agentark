"""Apex Model Selector — auto-detect available AI models + interactive picker.

Scans environment for API keys, checks installed tools for model configs,
and provides a Rich interactive selector UI.

Usage:
  from apex.interface.model_selector import ModelSelector
  ms = ModelSelector()
  ms.detect()           # Scan for available models
  ms.interactive_pick() # Rich selector UI
  ms.set_default("deepseek-v4-pro")  # Set and save
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from typing import Optional

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

from apex.core.config import get_config, save_config

console = Console()

# ─── Provider Registry ────────────────────────────────────────────

KNOWN_PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek",
        "models": ["deepseek-v4-pro", "deepseek-chat", "deepseek-reasoner"],
        "api_key_env": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "context_length": 131072,
        "emoji": "🐋",
    },
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-4o", "gpt-4-turbo", "o4-mini"],
        "api_key_env": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "context_length": 128000,
        "emoji": "🧠",
    },
    "anthropic": {
        "name": "Anthropic",
        "models": ["claude-sonnet-4-20250514", "claude-opus-4-20250514"],
        "api_key_env": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com/v1",
        "context_length": 200000,
        "emoji": "🎭",
    },
    "openrouter": {
        "name": "OpenRouter",
        "models": ["openrouter/auto", "anthropic/claude-sonnet-4"],
        "api_key_env": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "context_length": 200000,
        "emoji": "🔀",
    },
    "xai": {
        "name": "xAI / Grok",
        "models": ["grok-3"],
        "api_key_env": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "context_length": 131072,
        "emoji": "🚀",
    },
    "google": {
        "name": "Google Gemini",
        "models": ["gemini-2.5-pro", "gemini-2.5-flash"],
        "api_key_env": "GOOGLE_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "context_length": 1048576,
        "emoji": "💎",
    },
    "nous": {
        "name": "Nous Research",
        "models": ["hermes-3-405b", "hermes-3-70b"],
        "api_key_env": "NOUS_API_KEY",
        "base_url": "https://api.nousresearch.com/v1",
        "context_length": 131072,
        "emoji": "⚕",
    },
    "zai": {
        "name": "Z.AI / GLM",
        "models": ["glm-4-plus"],
        "api_key_env": "GLM_API_KEY",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "context_length": 128000,
        "emoji": "🏯",
    },
    "moonshot": {
        "name": "Kimi / Moonshot",
        "models": ["kimi-k2"],
        "api_key_env": "KIMI_API_KEY",
        "base_url": "https://api.moonshot.cn/v1",
        "context_length": 131072,
        "emoji": "🌙",
    },
}

# ─── Detection Result ─────────────────────────────────────────────


@dataclass
class DetectedProvider:
    key: str
    name: str
    has_key: bool
    models: list[str]
    default_model: str
    emoji: str = ""


@dataclass
class DetectResult:
    available: list[DetectedProvider]
    unavailable: list[DetectedProvider]
    hermes_model: str = ""  # from Hermes config if installed
    recommended: str = ""


# ─── Model Selector ───────────────────────────────────────────────


class ModelSelector:
    """Detect available models and help user pick one."""

    def __init__(self):
        self.providers = KNOWN_PROVIDERS

    def detect(self) -> DetectResult:
        """Scan environment and installed tools for available models."""
        available = []
        unavailable = []

        for key, prov in self.providers.items():
            env_var = prov["api_key_env"]
            has_key = bool(os.environ.get(env_var, ""))

            dp = DetectedProvider(
                key=key,
                name=prov["name"],
                has_key=has_key,
                models=prov["models"],
                default_model=prov["models"][0],
                emoji=prov["emoji"],
            )

            if has_key:
                available.append(dp)
            else:
                unavailable.append(dp)

        # Try to read Hermes config
        hermes_model = self._detect_hermes_model()

        # Pick recommended provider
        recommended = ""
        if available:
            # Prefer DeepSeek if available
            for dp in available:
                if dp.key == "deepseek":
                    recommended = dp.default_model
                    break
            if not recommended:
                recommended = available[0].default_model

        return DetectResult(
            available=available,
            unavailable=unavailable,
            hermes_model=hermes_model,
            recommended=recommended,
        )

    def _detect_hermes_model(self) -> str:
        """Try to read Hermes config for current model."""
        hermes_config = Path.home() / ".hermes" / "config.yaml"
        if not hermes_config.exists():
            return ""
        try:
            with open(hermes_config) as f:
                data = __import__("yaml").safe_load(f) or {}
            return data.get("model", {}).get("default", "")
        except Exception:
            return ""

    # ── Interactive UI ────────────────────────────────────────────

    def interactive_pick(self) -> Optional[str]:
        """Rich interactive model picker. Returns chosen model or None."""
        result = self.detect()

        console.print()
        console.print(Panel(
            "[bold]🔍 检测到以下 AI 模型提供商[/]\n"
            f"[dim]扫描了 {len(self.providers)} 个提供商的环境变量[/]",
            border_style="cyan",
        ))

        # Show available providers
        if result.available:
            console.print("\n[bold green]✅ 可用提供商 (API Key 已配置):[/]")
            table = Table(box=box.SIMPLE, show_header=True)
            table.add_column("#", style="dim", width=3)
            table.add_column("提供商", style="bold")
            table.add_column("模型列表", style="green")
            table.add_column("密钥环境变量", style="dim")

            for i, dp in enumerate(result.available, 1):
                table.add_row(
                    str(i),
                    f"{dp.emoji} {dp.name}",
                    ", ".join(dp.models[:2]) + ("..." if len(dp.models) > 2 else ""),
                    dp.key,
                )

            console.print(table)

        if result.unavailable:
            console.print("\n[bold dim]❌ 未配置 (缺少 API Key):[/]")
            names = [f"{dp.emoji} {dp.name} ({dp.key})" for dp in result.unavailable]
            console.print(f"  [dim]{', '.join(names)}[/]")

        if result.hermes_model:
            console.print(f"\n[dim]📋 检测到 Hermes 正在使用: {result.hermes_model}[/]")

        # Prompt: quick or custom
        console.print()
        console.print("[bold]选择模型:[/]")

        choices = []
        for i, dp in enumerate(result.available, 1):
            choices.append(f"{i}. {dp.emoji} {dp.name} → {dp.default_model}")
        choices.append("m. 手动输入模型名")
        choices.append("q. 跳过 (使用默认)")

        console.print("\n".join(choices))

        choice = Prompt.ask(
            "\n请选择",
            default="1" if result.available else "m",
        )

        if choice == "q":
            return None

        if choice == "m":
            model = Prompt.ask("输入模型名", default=result.recommended or "deepseek-v4-pro")
            return model

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(result.available):
                return result.available[idx].default_model
        except ValueError:
            pass

        return result.recommended

    # ── Quick commands ─────────────────────────────────────────────

    def set_default(self, model: str):
        """Set the default model and persist to config."""
        cfg = get_config()

        # Try to determine provider from model name
        provider = "deepseek"
        for key, prov in self.providers.items():
            if any(model.startswith(m) for m in prov["models"]):
                provider = key
                base_url = prov["base_url"]
                api_key_env = prov["api_key_env"]
                cfg.model.provider = provider
                cfg.model.base_url = base_url
                cfg.model.api_key_env = api_key_env
                break

        cfg.model.default = model
        save_config(cfg)

        console.print(f"[green]✅ 默认模型设置为: {model}[/]")
        console.print(f"[dim]   提供商: {provider}[/]")

    def show_current(self):
        """Show the currently configured model."""
        cfg = get_config()
        console.print()
        console.print(Panel(
            f"[bold]当前模型配置[/]\n"
            f"  模型:     [green]{cfg.model.default}[/]\n"
            f"  提供商:   {cfg.model.provider}\n"
            f"  Base URL: [dim]{cfg.model.base_url or '(default)'}[/]\n"
            f"  API Key:  [dim]{cfg.model.api_key_env}[/]",
            border_style="cyan",
        ))
