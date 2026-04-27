"""Agent entrypoints backed by Memory-Native Kernel profiles."""

from __future__ import annotations

from typing import Any

from kernel.loop import KernelService
from kernel.state import KernelRequest
from shared.paths import project_root


def build_from_note(agent_name: str, overrides: dict[str, Any] | None = None):
    overrides = dict(overrides or {})
    root = overrides.pop("project_root", project_root())
    return KernelService().build(KernelRequest(agent_id=agent_name, project_root=root, **overrides))
