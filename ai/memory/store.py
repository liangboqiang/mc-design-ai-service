from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from memory.note import parse_note_file
from memory.types import MemoryNote
from workspace_paths import data_root


class NoteStore:
    """Single-source note.md store.

    Memory only scans note.md. Only note.md is recognized as a MemoryNote source.
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.data_root = data_root(self.project_root)
        self.notes_root = self.data_root / "notes"
        self.index_root = self.data_root / "indexes"
        self._cache: dict[str, MemoryNote] | None = None

    def ensure_directories(self) -> None:
        for path in (self.notes_root, self.index_root):
            path.mkdir(parents=True, exist_ok=True)

    def refresh(self) -> dict[str, MemoryNote]:
        self.ensure_directories()
        notes: dict[str, MemoryNote] = {}
        for path in self._iter_note_files():
            note = parse_note_file(self.project_root, path)
            notes[note.note_id] = note
        self._cache = notes
        return notes

    def notes(self) -> dict[str, MemoryNote]:
        return self.refresh() if self._cache is None else self._cache

    def list_notes(self) -> list[MemoryNote]:
        return sorted(self.notes().values(), key=lambda item: (item.kind, item.note_id))

    def get(self, note_id: str) -> MemoryNote | None:
        normalized = str(note_id or "").strip()
        if not normalized:
            return None
        notes = self.notes()
        if normalized in notes:
            return notes[normalized]
        for note in notes.values():
            if note.path == normalized or note.path.endswith(normalized):
                return note
        return None

    def search(self, query: str, *, limit: int = 20, kind: str = "") -> list[MemoryNote]:
        normalized_query = str(query or "").strip().lower()
        normalized_kind = str(kind or "").strip().lower()
        scored: list[tuple[int, MemoryNote]] = []
        for note in self.notes().values():
            if normalized_kind and note.kind.lower() != normalized_kind:
                continue
            score = _score_note(note, normalized_query)
            if normalized_query and score <= 0:
                continue
            scored.append((score or 1, note))
        scored.sort(key=lambda item: (-item[0], item[1].note_id))
        return [note for _, note in scored[: max(1, int(limit or 20))]]

    def catalog(self) -> dict:
        rows = {}
        for note in self.list_notes():
            rows[note.note_id] = {
                "title": note.title,
                "kind": note.kind,
                "status": note.status,
                "maturity": note.maturity,
                "path": note.path,
                "summary": note.summary,
                "tags": list(note.tags),
            }
        return {"notes": rows, "count": len(rows)}

    def status_index(self) -> dict:
        return {
            note.note_id: {
                "status": note.status,
                "maturity": note.maturity,
                "kind": note.kind,
                "has_source_refs": bool(note.source_refs),
            }
            for note in self.list_notes()
        }

    def write_indexes(self) -> dict:
        self.ensure_directories()
        catalog = self.catalog()
        status = self.status_index()
        search = {
            "items": [
                {
                    "note_id": note.note_id,
                    "title": note.title,
                    "kind": note.kind,
                    "summary": note.summary,
                    "path": note.path,
                }
                for note in self.list_notes()
            ]
        }
        (self.index_root / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
        (self.index_root / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        (self.index_root / "search.json").write_text(json.dumps(search, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"catalog": catalog, "status": status, "search": search}

    def to_row(self, note: MemoryNote) -> dict:
        row = asdict(note)
        row["page_id"] = note.note_id
        row["source_path"] = note.path
        return row

    def _iter_note_files(self) -> list[Path]:
        files: list[Path] = []
        files.extend(_note_files(self.notes_root))
        return sorted({path.resolve() for path in files})


def _note_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [path for path in sorted(root.rglob("note.md")) if _include_note(path)]


def _include_note(path: Path) -> bool:
    rel = path.as_posix().lower()
    blocked = ("__pycache__",)
    return not any(token in rel for token in blocked)


def _score_note(note: MemoryNote, query: str) -> int:
    if not query:
        return 1
    haystacks = [note.note_id, note.title, note.summary, note.kind, note.path, json.dumps(note.fields, ensure_ascii=False)]
    score = 0
    for text in haystacks:
        low = str(text or "").lower()
        if low == query:
            score += 10
        elif query in low:
            score += 3
    return score
