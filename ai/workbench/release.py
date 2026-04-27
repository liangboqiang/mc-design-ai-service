from __future__ import annotations

from pathlib import Path


class ReleaseService:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()

    def manifest(self) -> dict:
        return {"status": "placeholder", "project_root": str(self.project_root)}
