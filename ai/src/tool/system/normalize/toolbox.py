from __future__ import annotations

import json
from pathlib import Path


class NormalizeToolsToolbox:
    toolbox_name = "normalize"
    tags = ("governance", "normalize")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime

    def spawn(self, workspace_root: Path) -> "NormalizeToolsToolbox":
        return NormalizeToolsToolbox(workspace_root=workspace_root)

    def executors(self):
        return {
            'governance.normalize_tool_result': self._exec_governance_normalize_tool_result,
        }

    def _exec_governance_normalize_tool_result(self, args: dict):
        return json.dumps({'result': args['result']}, ensure_ascii=False, indent=2)
