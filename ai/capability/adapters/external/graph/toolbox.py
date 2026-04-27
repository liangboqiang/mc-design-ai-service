from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from memory import MemoryService


class GraphToolbox:
    toolbox_name = "graph"
    tags = ("builtin", "memory", "graph")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None
        self.project_root: Path | None = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime
        self.project_root = Path(getattr(runtime, "project_root", Path.cwd())).resolve()

    def spawn(self, workspace_root: Path) -> "GraphToolbox":
        return GraphToolbox(workspace_root=workspace_root)

    def executors(self):
        return {
            "graph.search": self._exec_search,
            "graph.neighbors": self._exec_neighbors,
            "graph.rebuild": self._exec_rebuild,
            "graph.health": self._exec_health,
        }

    def _memory(self) -> MemoryService:
        if self.project_root is None:
            raise ValueError("GraphToolbox runtime not bound")
        return MemoryService(self.project_root)

    def _exec_search(self, args: dict[str, Any]):
        rows = self._memory().search(str(args.get("query", "")), {"limit": int(args.get("limit", 20) or 20)})
        return json.dumps({"results": rows}, ensure_ascii=False, indent=2)

    def _exec_neighbors(self, args: dict[str, Any]):
        return json.dumps(self._memory().graph_neighbors(str(args["note_id"]), depth=int(args.get("depth", 1) or 1)), ensure_ascii=False, indent=2)

    def _exec_rebuild(self, args: dict[str, Any]):
        return json.dumps(self._memory().compile_indexes(), ensure_ascii=False, indent=2)

    def _exec_health(self, args: dict[str, Any]):
        graph = self._memory().graph({"write_store": False, "include_hidden": True})
        diagnostics = graph.get("diagnostics", [])
        return json.dumps({
            "nodes": len(graph.get("nodes", [])),
            "edges": len(graph.get("edges", [])),
            "diagnostics_count": len(diagnostics),
            "diagnostics": diagnostics[: int(args.get("limit", 50) or 50)],
        }, ensure_ascii=False, indent=2)
