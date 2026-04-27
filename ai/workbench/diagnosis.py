from __future__ import annotations

from pathlib import Path

from workbench.graph_service import WorkbenchGraphService
from workbench.note_service import MemoryAppService


class DiagnosisService:
    def __init__(self, project_root: Path):
        self.notes = MemoryAppService(Path(project_root).resolve())
        self.graph = WorkbenchGraphService(Path(project_root).resolve())

    def overview(self) -> dict:
        graph = self.graph.graph_view(include_hidden=True)
        return {
            "notes": len(self.notes.list_notes(limit=500)),
            "graph_nodes": graph.get("node_count", 0),
            "graph_edges": graph.get("edge_count", 0),
            "diagnostics": graph.get("diagnostics", [])[:50],
        }
