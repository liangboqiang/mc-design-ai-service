from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class WikiStore:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.root = self.project_root / "src" / "wiki/store"
        self.jobs_dir = self.root / "jobs"
        self.attachments_dir = self.root / "attachments"
        self.index_path = self.root / "index.json"
        self.catalog_path = self.root / "catalog.json"
        self.graph_path = self.root / "graph.json"

    def ensure(self) -> None:
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.attachments_dir.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            self.index_path.write_text(json.dumps({"entities": {}}, ensure_ascii=False, indent=2), encoding="utf-8")
        if not self.catalog_path.exists():
            self.catalog_path.write_text(json.dumps({"pages": {}}, ensure_ascii=False, indent=2), encoding="utf-8")
        if not self.graph_path.exists():
            self.graph_path.write_text(json.dumps({"edges": []}, ensure_ascii=False, indent=2), encoding="utf-8")

    def read_index(self) -> dict[str, Any]:
        self.ensure()
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def read_catalog(self) -> dict[str, Any]:
        self.ensure()
        return json.loads(self.catalog_path.read_text(encoding="utf-8"))

    def read_graph(self) -> dict[str, Any]:
        self.ensure()
        return json.loads(self.graph_path.read_text(encoding="utf-8"))

    def write_index(self, payload: dict[str, Any]) -> None:
        self.ensure()
        tmp = self.index_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.index_path)

    def write_catalog(self, payload: dict[str, Any]) -> None:
        self.ensure()
        tmp = self.catalog_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.catalog_path)

    def write_graph(self, payload: dict[str, Any]) -> None:
        self.ensure()
        tmp = self.graph_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.graph_path)

    def write_job(self, job_id: str, payload: dict[str, Any]) -> None:
        self.ensure()
        path = self.jobs_dir / f"{job_id}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
