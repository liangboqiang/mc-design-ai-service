from __future__ import annotations

from abc import ABC
from pathlib import Path


class StatefulToolbox(ABC):
    toolbox_name: str
    participant_name: str | None = None

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None
        self._tool_lookup = lambda name: None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime
        self._tool_lookup = tool_lookup or (lambda name: None)

    def capability(self, name: str):
        return self._tool_lookup(name)

    def spawn(self, workspace_root: Path) -> "StatefulToolbox":
        return self.__class__(workspace_root=workspace_root)

    def executors(self) -> dict[str, object]:
        return {}

    def before_user_turn(self, message: str) -> None:
        return None

    def before_model_call(self) -> None:
        return None

    def after_tool_call(self, tool_id: str, result: str) -> None:
        return None

    def state_fragments(self) -> list[str]:
        return []
