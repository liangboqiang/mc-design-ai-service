from __future__ import annotations

import re
from pathlib import Path

from memory import MemoryService
from memory.note import render_note_markdown
from workspace_paths import data_root, workspace_root


class MemoryAppService:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.memory = MemoryService(self.project_root)

    def list_notes(self, query: str = "", limit: int = 100, kind: str = "") -> list[dict]:
        return self.memory.list_notes(query=query, limit=int(limit or 100), kind=kind)

    def read_note(self, note_id: str = "", page_id: str = "") -> dict:
        target = str(note_id or page_id or "").strip()
        if not target:
            raise ValueError("缺少必要参数：note_id")
        note = self.memory.read_note(target)
        if note is None:
            raise FileNotFoundError(f"Note 不存在：{target}")
        return note

    def save_note_draft(self, note_id: str, markdown: str = "") -> dict:
        target_path = self._note_path(note_id)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        text = str(markdown or "").strip()
        if not text:
            existing = self.memory.note_store.get(note_id)
            if existing is None:
                raise FileNotFoundError(f"Note 不存在：{note_id}")
            text = render_note_markdown(existing)
        target_path.write_text(text + ("\n" if not text.endswith("\n") else ""), encoding="utf-8")
        self.memory.note_store.refresh()
        return {"note_id": note_id, "path": self._display_path(target_path), "status": "draft_saved"}

    def publish_note(self, note_id: str, maturity: str = "projectable") -> dict:
        target_path = self._note_path(note_id)
        if not target_path.exists():
            raise FileNotFoundError(f"Note 不存在：{note_id}")
        text = target_path.read_text(encoding="utf-8")
        text = self._replace_frontmatter_value(text, "status", "published")
        text = self._replace_frontmatter_value(text, "maturity", str(maturity or "projectable"))
        target_path.write_text(text, encoding="utf-8")
        self.memory.note_store.refresh()
        return {"note_id": note_id, "path": self._display_path(target_path), "status": "published", "maturity": maturity}

    def check_note(self, note_id: str = "", page_id: str = "") -> dict:
        target = str(note_id or page_id or "").strip()
        if not target:
            raise ValueError("缺少必要参数：note_id")
        return self.memory.check_note(target)

    def list_lenses(self) -> list[dict]:
        return self.memory.list_lenses()

    def check_runtime_ready(self, note_id: str = "", page_id: str = "") -> dict:
        target = str(note_id or page_id or "").strip()
        if not target:
            raise ValueError("缺少必要参数：note_id")
        return self.memory.check_runtime_ready(target)

    def compile_indexes(self) -> dict:
        return self.memory.compile_indexes()

    def _note_path(self, note_id: str) -> Path:
        note = self.memory.note_store.get(note_id)
        base_root = workspace_root(self.project_root)
        if note is not None:
            return base_root / note.path
        normalized = str(note_id or "").strip().replace(".", "/")
        return data_root(self.project_root) / "notes" / normalized / "note.md"

    def _display_path(self, path: Path) -> str:
        return path.relative_to(workspace_root(self.project_root)).as_posix()

    @staticmethod
    def _replace_frontmatter_value(text: str, key: str, value: str) -> str:
        pattern = re.compile(rf"^(?P<prefix>{re.escape(key)}:\s*).*$", re.MULTILINE)
        if pattern.search(text):
            return pattern.sub(rf"\g<prefix>{value}", text, count=1)
        if text.startswith("---\n"):
            return text.replace("---\n", f"---\n{key}: {value}\n", 1)
        return f"---\n{key}: {value}\n---\n\n{text}"
