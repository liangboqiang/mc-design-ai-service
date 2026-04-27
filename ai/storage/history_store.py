from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .json_store import JsonlStore


class HistoryStore:
    def __init__(self, history_dir: Path):
        self.store = JsonlStore(history_dir / "messages.jsonl")

    def append_user(self, content: str, files: list[dict] | None = None) -> None:
        row = {"role": "user", "content": content}
        if files:
            row["files"] = files
        self.store.append(row)

    def append_assistant(self, content: str) -> None:
        self.store.append({"role": "assistant", "content": content})

    def append_tool(self, tool_id: str, content: str) -> None:
        self.store.append({"role": "tool", "tool_id": tool_id, "content": content})

    def append_system(self, content: str) -> None:
        self.store.append({"role": "system", "content": content})

    def read(self) -> list[dict]:
        return self.store.read_all()

    def replace(self, rows: Iterable[dict]) -> None:
        self.store.replace(rows)
