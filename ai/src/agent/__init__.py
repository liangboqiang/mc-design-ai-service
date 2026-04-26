"""Agent entrypoints backed by Wiki Pages and RuntimeRegistry."""

from __future__ import annotations

from typing import Any

from runtime.bootstrap import RuntimeBootstrap
from runtime.types import RuntimeRequest
from shared.paths import project_root


def build_from_page(agent_name: str, overrides: dict[str, Any] | None = None):
    overrides = dict(overrides or {})
    root = overrides.pop("project_root", project_root())
    return RuntimeBootstrap().build(RuntimeRequest(agent_id=agent_name, project_root=root, **overrides))
