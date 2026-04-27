from __future__ import annotations

from pathlib import Path

from memory import MemoryService


class IntakeService:
    def __init__(self, project_root: Path):
        self.memory = MemoryService(Path(project_root).resolve())

    def ingest_source(self, files: list[dict] | None = None) -> dict:
        return {"status": "ok", "summary": self.memory.ingest(files or [])}
