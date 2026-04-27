from __future__ import annotations

from pathlib import Path

from .json_store import JsonlStore


class InboxStore:
    def __init__(self, inbox_dir: Path):
        self.inbox_dir = inbox_dir
        self.inbox_dir.mkdir(parents=True, exist_ok=True)

    def _store(self, name: str) -> JsonlStore:
        return JsonlStore(self.inbox_dir / f"{name}.jsonl")

    def append(self, name: str, payload: dict) -> None:
        self._store(name).append(payload)

    def read_all(self, name: str) -> list[dict]:
        return self._store(name).read_all()

    def drain(self, name: str) -> list[dict]:
        store = self._store(name)
        rows = store.read_all()
        store.replace([])
        return rows
