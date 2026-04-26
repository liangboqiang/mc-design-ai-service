from __future__ import annotations

from pathlib import Path
from typing import Any

from protocol.registry import RuntimeRegistry
from .engine import Engine
from .kernel import RuntimeKernel
from .types import RuntimeRequest


class RuntimeBootstrap:
    """Thin bootstrap: Wiki -> ProtocolView -> RuntimeKernel -> Engine."""

    def build(self, request: RuntimeRequest) -> Engine:
        registry = RuntimeRegistry.from_wiki(request.project_root)
        errors = registry.view.errors()
        if errors:
            rendered = "\n".join(f"[{e.level}] {e.node_id}: {e.message}" for e in errors)
            raise RuntimeError(f"Protocol diagnostics contain errors:\n{rendered}")
        kernel = RuntimeKernel.create(request, registry)
        return Engine(kernel)


def build_engine(agent_id: str, *, project_root: Path, **overrides: Any) -> Engine:
    return RuntimeBootstrap().build(RuntimeRequest(agent_id=agent_id, project_root=Path(project_root), **overrides))
