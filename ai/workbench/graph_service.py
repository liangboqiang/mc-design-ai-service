from __future__ import annotations

from pathlib import Path

from memory import MemoryService


class WorkbenchGraphService:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.memory = MemoryService(self.project_root)

    def compile_graph(self, include_hidden: bool = False, write_store: bool = True) -> dict:
        graph = self.memory.graph({"include_hidden": include_hidden, "write_store": write_store})
        return {
            **graph,
            "graph": {"nodes": graph.get("nodes", []), "edges": graph.get("edges", []), "triples": graph.get("triples", [])},
            "sample_triples": graph.get("triples", [])[:50],
        }

    def graph_view(self, include_hidden: bool = False) -> dict:
        return self.compile_graph(include_hidden=include_hidden, write_store=False)

    def graph_neighbors(self, note_id: str = "", page_id: str = "", depth: int = 1) -> dict:
        target = str(note_id or page_id or "").strip()
        if not target:
            raise ValueError("缺少必要参数：note_id")
        return self.memory.graph_neighbors(target, depth=max(1, int(depth or 1)))
