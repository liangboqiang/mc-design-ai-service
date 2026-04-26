from __future__ import annotations

import json
from pathlib import Path


class InspectToolsToolbox:
    toolbox_name = "inspect"
    tags = ("governance", "surface")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime

    def spawn(self, workspace_root: Path) -> "InspectToolsToolbox":
        return InspectToolsToolbox(workspace_root=workspace_root)

    def executors(self):
        return {
            'governance.inspect_tool_surface': self._exec_governance_inspect_tool_surface,
        }

    def _exec_governance_inspect_tool_surface(self, args: dict):
        return self._inspect()

    def _inspect(self) -> str:
        if self.runtime is None:
            return json.dumps({"visible_tools": []}, ensure_ascii=False, indent=2)
        surface = self.runtime.runtime_state.last_surface_snapshot
        if surface is None:
            return json.dumps({"visible_tools": []}, ensure_ascii=False, indent=2)
        return json.dumps(
            {
                "visible_toolboxes": surface.visible_toolboxes,
                "visible_tools": [spec.tool_id for spec in surface.visible_tools],
                "activated_skill_ids": surface.activated_skill_ids,
                "activated_tools": surface.activated_tools,
            },
            ensure_ascii=False,
            indent=2,
        )
