"""Apex — Provider抽象层
支持任意LLM Provider的热插拔。
"""
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
    """所有Provider必须实现的基类"""

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def chat(self, messages: list[dict], **kwargs) -> LLMResponse:
        """发送聊天请求"""
        ...

    @abstractmethod
    def name(self) -> str:
        """Provider名称"""
        ...

    def estimate_cost(self, response: LLMResponse) -> float:
        """估算API调用成本（美元）"""
        return 0.0


class ProviderRegistry:
    """Provider注册表 — 支持动态注册"""

    def __init__(self):
        self._providers: dict[str, type[BaseProvider]] = {}
        self._instances: dict[str, BaseProvider] = {}

    def register(self, name: str, provider_cls: type[BaseProvider]):
        self._providers[name] = provider_cls

    def get(self, name: str, config: dict = None) -> BaseProvider:
        """获取Provider实例（带缓存）"""
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


# 全局注册表
registry = ProviderRegistry()
