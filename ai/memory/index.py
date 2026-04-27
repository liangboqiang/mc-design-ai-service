from __future__ import annotations

from pathlib import Path

from memory.graph import MemoryGraphProjector
from memory.lens import LensInterpreter, LensStore
from memory.store import NoteStore


class MemoryIndex:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.note_store = NoteStore(self.project_root)
        self.lens_store = LensStore(self.project_root)
        self.lens = LensInterpreter(self.lens_store)
        self.graph = MemoryGraphProjector(self.project_root, self.note_store, self.lens)

    def compile_all(self) -> dict:
        return {
            "indexes": self.note_store.write_indexes(),
            "graph": self.graph.compile(write_store=True, include_hidden=True),
        }
