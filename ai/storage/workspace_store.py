from __future__ import annotations

import shutil
import time
from pathlib import Path

from .json_store import JsonStore, JsonlStore


class WorkspaceStore:
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.index = JsonStore(workspace_dir / "index.json")
        self.events = JsonlStore(workspace_dir / "events.jsonl")
        if not self.index.path.exists():
            self.index.write({"workspaces": []})

    def list_all(self) -> list[dict]:
        return list(self.index.read({"workspaces": []})["workspaces"])

    def _save(self, rows: list[dict]) -> None:
        self.index.write({"workspaces": rows})

    def get(self, name: str) -> dict:
        for row in self.list_all():
            if row["name"] == name:
                return row
        raise ValueError(f"Unknown workspace {name}")

    def create(self, name: str, task_id: int | None = None) -> dict:
        path = self.workspace_dir / name
        if path.exists():
            raise ValueError(f"Workspace already exists: {name}")
        path.mkdir(parents=True)
        row = {"name": name, "path": str(path), "task_id": task_id, "status": "active"}
        rows = self.list_all()
        rows.append(row)
        self._save(rows)
        self.events.append({"ts": time.time(), "event": "workspace.create", "workspace": row})
        return row

    def keep(self, name: str) -> dict:
        rows = self.list_all()
        updated: dict | None = None
        for row in rows:
            if row["name"] == name:
                row["status"] = "kept"
                updated = row
        if updated is None:
            raise ValueError(f"Unknown workspace {name}")
        self._save(rows)
        self.events.append({"ts": time.time(), "event": "workspace.keep", "workspace": updated})
        return updated

    def remove(self, name: str) -> dict:
        rows: list[dict] = []
        removed: dict | None = None
        for row in self.list_all():
            if row["name"] == name:
                removed = row
            else:
                rows.append(row)
        if removed is None:
            raise ValueError(f"Unknown workspace {name}")
        shutil.rmtree(Path(removed["path"]), ignore_errors=True)
        self._save(rows)
        self.events.append({"ts": time.time(), "event": "workspace.remove", "workspace": removed})
        return removed
