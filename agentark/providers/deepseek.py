"""Apex — DeepSeek and Ollama providers"""
from __future__ import annotations

import json
import httpx
from .base import BaseProvider, LLMResponse, registry


class DeepSeekProvider(BaseProvider):
    """DeepSeek API Provider"""

    BASE_URL = "https://api.deepseek.com/v1"

    def name(self) -> str:
        return "deepseek"

    def chat(self, messages: list[dict], **kwargs) -> LLMResponse:
        api_key = self.config.get("api_key", "")
        if not api_key:
            api_key = self._read_env_key()

        model = kwargs.get("model", self.config.get("model", "deepseek-v4-pro"))
        base_url = self.config.get("base_url", self.BASE_URL)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }

        with httpx.Client(timeout=120) as client:
            resp = client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]
        content = choice["message"]["content"]
        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=model,
            provider="deepseek",
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        )

    def estimate_cost(self, response: LLMResponse) -> float:
        """DeepSeek V4 Pro pricing: $1/M input, $4/M output"""
        input_cost = response.usage.get("prompt_tokens", 0) * 1.0 / 1_000_000
        output_cost = response.usage.get("completion_tokens", 0) * 4.0 / 1_000_000
        return round(input_cost + output_cost, 6)

    def _read_env_key(self) -> str:
        """Read API Key from .env or environment variables"""
        import os
        key = os.environ.get("DEEPSEEK_API_KEY", "")
        if key:
            return key
        # Try reading from .apex/.env
        env_path = os.path.expanduser("~/.apex/.env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("DEEPSEEK_API_KEY="):
                        return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
        return ""


class OllamaProvider(BaseProvider):
    """Local Ollama Provider — zero cost"""

    BASE_URL = "http://localhost:11434"

    def name(self) -> str:
        return "ollama"

    def chat(self, messages: list[dict], **kwargs) -> LLMResponse:
        base_url = self.config.get("base_url", self.BASE_URL)
        model = kwargs.get("model", self.config.get("model", "llama3"))

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
            },
        }

        with httpx.Client(timeout=300) as client:
            resp = client.post(f"{base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data.get("message", {}).get("content", "")

        return LLMResponse(
            content=content,
            model=model,
            provider="ollama",
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        )

    def estimate_cost(self, response: LLMResponse) -> float:
        return 0.0  # Local, free


# Register Providers
registry.register("deepseek", DeepSeekProvider)
registry.register("ollama", OllamaProvider)
