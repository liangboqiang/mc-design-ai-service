from __future__ import annotations

from pathlib import Path

from .json_store import JsonStore


class TranscriptStore:
    def __init__(self, logs_dir: Path):
        self.store = JsonStore(logs_dir / "transcripts.json")

    def append(self, row: dict) -> None:
        rows = self.store.read([])
        rows.append(row)
        self.store.write(rows)

    def read_all(self) -> list[dict]:
        return self.store.read([])
