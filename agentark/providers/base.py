"""Apex — Provider abstraction layer"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: dict  # {"prompt_tokens": N, "completion_tokens": N, "total_tokens": N}


class BaseProvider(ABC):
    """Base class that all Providers must implement"""

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def chat(self, messages: list[dict], **kwargs) -> LLMResponse:
        """Send a chat request"""
        ...

    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        ...

    def estimate_cost(self, response: LLMResponse) -> float:
        """Estimate API call cost (USD)"""
        return 0.0


class ProviderRegistry:
    """Provider registry — supports dynamic registration"""

    def __init__(self):
        self._providers: dict[str, type[BaseProvider]] = {}
        self._instances: dict[str, BaseProvider] = {}

    def register(self, name: str, provider_cls: type[BaseProvider]):
        self._providers[name] = provider_cls

    def get(self, name: str, config: dict = None) -> BaseProvider:
        """Get Provider instance (with caching)"""
        cache_key = f"{name}:{str(config)}"
        if cache_key in self._instances:
            return self._instances[cache_key]

        if name not in self._providers:
            raise ValueError(f"Unknown provider: {name}. Available: {list(self._providers.keys())}")

        cls = self._providers[name]
        instance = cls(config or {})
        self._instances[cache_key] = instance
        return instance

    def list(self) -> list[str]:
        return list(self._providers.keys())


# Global registry
registry = ProviderRegistry()
