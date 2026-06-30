"""Apex Model Auto-Discovery — detect models from environment, tools, and cloud"""
from __future__ import annotations

import os, json, subprocess
from pathlib import Path

HOME = Path.home()

AWS_CONFIG = HOME / ".aws" / "config"
AWS_SSO_CACHE = HOME / ".aws" / "sso" / "cache"

MODEL_SIGNATURES = {
    "deepseek": {
        "env_vars": ["DEEPSEEK_API_KEY"],
        "models": ["deepseek-chat", "deepseek-v4-pro", "deepseek-r1"],
        "default": "deepseek-v4-pro",
        "base_url": "https://api.deepseek.com/v1",
    },
    "anthropic": {
        "env_vars": ["ANTHROPIC_API_KEY"],
        "models": ["claude-sonnet-4", "claude-3-opus"],
        "default": "claude-sonnet-4",
        "base_url": "https://api.anthropic.com",
    },
    "openai": {
        "env_vars": ["OPENAI_API_KEY"],
        "models": ["gpt-4o", "gpt-4o-mini"],
        "default": "gpt-4o",
        "base_url": "https://api.openai.com/v1",
    },
    "openrouter": {
        "env_vars": ["OPENROUTER_API_KEY"],
        "models": ["openai/gpt-4o", "anthropic/claude-sonnet-4", "deepseek/deepseek-chat"],
        "default": "deepseek/deepseek-chat",
        "base_url": "https://openrouter.ai/api/v1",
    },
    "aws-bedrock": {
        "check_fn": "_check_aws_sso",
        "models": ["us.anthropic.claude-sonnet-4-6", "us.anthropic.claude-opus-4-7", "us.amazon.nova-pro-v2"],
        "default": "us.anthropic.claude-sonnet-4-6",
        "base_url": None,  # Uses boto3 SDK, not HTTP
    },
    "google": {
        "env_vars": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "models": ["gemini-2.5-pro", "gemini-2.5-flash"],
        "default": "gemini-2.5-pro",
        "base_url": "https://generativelanguage.googleapis.com",
    },
}

TOOL_CONFIGS = {
    "kiro": {
        "paths": [HOME / ".kiro"],
        "description": "Kiro CLI (AWS SSO / Bedrock)",
        "model_hint": "aws-bedrock",
    },
    "claude-code": {
        "paths": [HOME / ".claude"],
        "description": "Claude Code (Anthropic API / Bedrock)",
        "model_hint": "anthropic",
    },
    "cursor": {
        "paths": [HOME / ".cursor"],
        "description": "Cursor IDE (OpenAI / Anthropic)",
        "model_hint": "openai",
    },
    "hermes": {
        "paths": [HOME / ".hermes"],
        "description": "Hermes Agent (multi-provider)",
        "model_hint": "deepseek",
    },
}


def _check_aws_sso() -> bool:
    """Check if AWS SSO is configured"""
    if not AWS_CONFIG.exists():
        return False
    content = AWS_CONFIG.read_text()
    if "sso_" in content:
        return True
    if AWS_SSO_CACHE.exists() and list(AWS_SSO_CACHE.glob("*.json")):
        return True
    return False


def _check_env(env_vars: list) -> bool:
    """Check if any of the env vars are set"""
    for var in env_vars:
        val = os.environ.get(var, "")
        if val and len(val) > 10:
            return True
    return False


def detect_models() -> dict:
    """Detect available models from environment, tools, and cloud"""
    available = {}
    tools_detected = []

    # Check tool configs
    for tool_name, tool_info in TOOL_CONFIGS.items():
        for p in tool_info["paths"]:
            if p.exists():
                tools_detected.append({
                    "name": tool_name,
                    "description": tool_info["description"],
                    "model_hint": tool_info["model_hint"],
                    "path": str(p),
                })
                break

    # Check each model provider
    for provider, info in MODEL_SIGNATURES.items():
        detected = False
        if "check_fn" in info:
            detected = globals()[info["check_fn"]]()
        elif "env_vars" in info:
            detected = _check_env(info["env_vars"])

        if detected:
            available[provider] = {
                "provider": provider,
                "models": info["models"],
                "default": info["default"],
                "base_url": info["base_url"],
                "auth_method": "env_var" if "env_vars" in info else "sso/cache",
            }

    # Also check tools for model hints
    for t in tools_detected:
        hint = t["model_hint"]
        if hint not in available and hint in MODEL_SIGNATURES:
            info = MODEL_SIGNATURES[hint]
            available[hint] = {
                "provider": hint,
                "models": info["models"],
                "default": info["default"],
                "base_url": info["base_url"],
                "auth_method": f"via {t['name']} ({t['description']})",
            }

    return {
        "available": len(available),
        "providers": available,
        "tools_detected": tools_detected,
        "recommendation": _recommend(available, tools_detected),
    }


def _recommend(available: dict, tools: list) -> str:
    """Generate recommendation based on what's available"""
    if "deepseek" in available:
        return "deepseek-v4-pro (最便宜，$1/1M input)"
    if "aws-bedrock" in available:
        return "us.anthropic.claude-sonnet-4-6 (AWS Bedrock, SSO免key)"
    if "anthropic" in available:
        return "claude-sonnet-4 (最强代码能力)"
    if "openrouter" in available:
        return "deepseek/deepseek-chat (OpenRouter, 免多key)"
    return "需要配置至少一个model provider"


def auto_configure(provider: str, model: str) -> dict:
    """Auto-configure Apex to use the selected model"""
    from agentark.core.profile import ProfileManager, AGENTARK_HOME

    pm = ProfileManager()
    profiles = pm.list()

    config_path = AGENTARK_HOME / "config.yaml"
    import yaml
    
    cfg = {}
    if config_path.exists():
        with open(config_path) as f:
            cfg = yaml.safe_load(f) or {}

    info = MODEL_SIGNATURES.get(provider, {})
    base_url = info.get("base_url", "")

    cfg["model"] = {
        "default": model,
        "provider": provider,
    }
    if base_url:
        cfg["model"]["base_url"] = base_url

    with open(config_path, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)

    return {
        "ok": True,
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "config_path": str(config_path),
        "profiles_updated": len(profiles),
    }
