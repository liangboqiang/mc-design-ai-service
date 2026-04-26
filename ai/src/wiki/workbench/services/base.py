from __future__ import annotations

from pathlib import Path
from wiki.hub import WikiHub
from wiki.store import WikiStore

class WorkbenchService:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.hub = WikiHub(project_root=self.project_root)
        self.store = WikiStore(self.project_root)

    def ensure(self) -> None:
        self.hub.ensure_store()

    def page_row(self, page_id: str) -> dict:
        self.ensure()
        row = (self.store.read_catalog().get("pages") or {}).get(page_id)
        if row is None:
            raise FileNotFoundError(page_id)
        return row

    def source_path(self, page_id: str) -> str:
        return str(self.page_row(page_id).get("path") or "")
