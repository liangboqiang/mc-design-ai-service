from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except Exception:  # noqa: BLE001
    def load_dotenv(*args, **kwargs):
        return False

from .errors import LLMConfigurationError


load_dotenv(override=False)

ENV_PROVIDER = "DESIGN_AGENTS_PROVIDER"
ENV_MODEL = "DESIGN_AGENTS_MODEL"
ENV_API_KEY = "DESIGN_AGENTS_API_KEY"
ENV_BASE_URL = "DESIGN_AGENTS_BASE_URL"
ENV_HIAGENT_API_KEY = "HIAGENT_API_KEY"
ENV_HIAGENT_BASE_URL = "HIAGENT_BASE_URL"
ENV_HIAGENT_PROXY_URL = "HIAGENT_PROXY_URL"

DEFAULT_PROVIDER = "mock"
DEFAULT_MODEL = "mock"


@dataclass(frozen=True, slots=True)
class LLMConfig:
    provider: str
    model: str
    api_key: str | None
    base_url: str | None


def resolve_llm_config(
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> LLMConfig:
    resolved_provider = (provider or os.getenv(ENV_PROVIDER) or DEFAULT_PROVIDER).strip().lower()
    if resolved_provider not in {"openai", "anthropic", "mock", "hiagent", "mc_design_ai"}:
        raise LLMConfigurationError(f"Unsupported provider: {resolved_provider}")

    raw_model = (model or os.getenv(ENV_MODEL) or "").strip()
    resolved_model = raw_model or (DEFAULT_MODEL if resolved_provider == "mock" else "hiagent" if resolved_provider in {"hiagent", "mc_design_ai"} else "")
    if not resolved_model:
        raise LLMConfigurationError(f"{resolved_provider} provider requires model.")

    if resolved_provider == "mock":
        return LLMConfig("mock", resolved_model, None, None)

    if resolved_provider in {"hiagent", "mc_design_ai"}:
        resolved_api_key = (
            api_key
            or os.getenv(ENV_API_KEY)
            or os.getenv(ENV_HIAGENT_API_KEY)
            or ""
        ).strip() or None
        resolved_base_url = (
            base_url
            or os.getenv(ENV_BASE_URL)
            or os.getenv(ENV_HIAGENT_PROXY_URL)
            or os.getenv(ENV_HIAGENT_BASE_URL)
            or ""
        ).strip().rstrip("/") or None
        return LLMConfig("hiagent", resolved_model, resolved_api_key, resolved_base_url)

    resolved_api_key = (api_key or os.getenv(ENV_API_KEY) or "").strip() or None
    resolved_base_url = (base_url or os.getenv(ENV_BASE_URL) or "").strip().rstrip("/") or None

    if not resolved_api_key:
        raise LLMConfigurationError(f"{resolved_provider} provider requires api_key.")
    if not resolved_base_url:
        raise LLMConfigurationError(f"{resolved_provider} provider requires base_url.")

    return LLMConfig(
        provider=resolved_provider,
        model=resolved_model,
        api_key=resolved_api_key,
        base_url=resolved_base_url,
    )
