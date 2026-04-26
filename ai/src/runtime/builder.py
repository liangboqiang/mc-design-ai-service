from __future__ import annotations

from pathlib import Path
from typing import Any

from shared.paths import project_root
from .bootstrap import RuntimeBootstrap
from .types import RuntimeRequest


# Thin compatibility entrypoint for existing agent modules; not a legacy Action compatibility layer.
def build_engine(agent_id: str, **overrides: Any):
    return RuntimeBootstrap().build(
        RuntimeRequest(agent_id=agent_id, project_root=Path(overrides.pop("project_root", project_root())), **overrides)
    )
