from __future__ import annotations


class LLMConfigurationError(ValueError):
    """Raised when required LLM configuration is missing."""


class LLMTransportError(RuntimeError):
    """Raised when an LLM transport call fails."""
