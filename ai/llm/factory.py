from __future__ import annotations

from .anthropic_client import AnthropicClient
from .hiagent_client import HiAgentClient
from .mock_client import MockClient
from .openai_client import OpenAIClient


class LLMFactory:
    @staticmethod
    def create(
        provider: str,
        model: str,
        api_key: str | None,
        base_url: str | None,
    ):
        if provider == "mock":
            return MockClient(model)
        if provider == "openai":
            return OpenAIClient(model, api_key or "", base_url or "")
        if provider == "anthropic":
            return AnthropicClient(model, api_key or "", base_url or "")
        if provider == "hiagent":
            return HiAgentClient(model, api_key, base_url)
        raise ValueError(f"Unsupported provider: {provider}")
