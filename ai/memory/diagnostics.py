from __future__ import annotations

from pathlib import Path

from memory import MemoryService


class MemoryDiagnostics:
    def __init__(self, project_root: Path):
        self.memory = MemoryService(Path(project_root).resolve())

    def overview(self) -> dict:
        graph = self.memory.graph({"write_store": False, "include_hidden": True})
        return {
            "note_count": len(self.memory.list_notes(limit=1000)),
            "graph_nodes": graph.get("node_count", 0),
            "graph_edges": graph.get("edge_count", 0),
            "diagnostics": graph.get("diagnostics", []),
        }
