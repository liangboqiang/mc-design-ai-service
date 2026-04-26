from __future__ import annotations

from pathlib import Path

from tool.stateful import StatefulToolbox


class IsolationCapability(StatefulToolbox):
    toolbox_name = "isolation"

    def __init__(self, mode: str = "data", workspace_root: Path | None = None):
        super().__init__(workspace_root=workspace_root)
        self.mode = mode

    def spawn(self, workspace_root: Path) -> "IsolationCapability":
        return IsolationCapability(mode=self.mode, workspace_root=workspace_root)

    def state_fragments(self) -> list[str]:
        return [f"isolation_mode: {self.mode}"]
