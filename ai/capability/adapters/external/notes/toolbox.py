from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from memory import MemoryService
from workspace_paths import data_root


def _slug(value: str) -> str:
    raw = re.sub(r"[^0-9A-Za-z_\-.\u4e00-\u9fff]+", "_", str(value or "").strip()).strip("_")
    return raw or "untitled"


class NotesToolbox:
    toolbox_name = "notes"
    tags = ("builtin", "memory", "notes")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None
        self.project_root: Path | None = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime
        self.project_root = Path(getattr(runtime, "project_root", Path.cwd())).resolve()

    def spawn(self, workspace_root: Path) -> "NotesToolbox":
        return NotesToolbox(workspace_root=workspace_root)

    def executors(self):
        return {
            "notes.list": self._exec_list,
            "notes.read": self._exec_read,
            "notes.check": self._exec_check,
            "notes.create": self._exec_create,
            "notes.update_source": self._exec_update_source,
            "notes.generate_from_text": self._exec_generate_from_text,
        }

    def _memory(self) -> MemoryService:
        if self.project_root is None:
            raise ValueError("NotesToolbox runtime not bound")
        return MemoryService(self.project_root)

    def _notes_root(self) -> Path:
        if self.project_root is None:
            raise ValueError("NotesToolbox runtime not bound")
        return data_root(self.project_root) / "notes"

    def _exec_list(self, args: dict[str, Any]):
        rows = self._memory().list_notes(query=str(args.get("query", "")), kind=str(args.get("kind", "")), limit=int(args.get("limit", 50) or 50))
        return json.dumps({"notes": rows}, ensure_ascii=False, indent=2)

    def _exec_read(self, args: dict[str, Any]):
        row = self._memory().read_note(str(args["note_id"]))
        if row is None:
            raise KeyError(args["note_id"])
        return json.dumps(row, ensure_ascii=False, indent=2)

    def _exec_check(self, args: dict[str, Any]):
        return json.dumps(self._memory().check_note(str(args["note_id"])), ensure_ascii=False, indent=2)

    def _exec_create(self, args: dict[str, Any]):
        note_id = str(args["note_id"]).strip().replace("/", ".")
        kind = str(args.get("kind") or "Document")
        title = str(args.get("title") or note_id)
        body = str(args.get("body") or "")
        rel = Path(*note_id.split(".")) / "note.md"
        target = self._notes_root() / rel
        if target.exists() and not args.get("overwrite"):
            raise FileExistsError(rel.as_posix())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_render_note(note_id, kind, title, body, status=str(args.get("status") or "draft")), encoding="utf-8")
        return json.dumps({"status": "created", "note_id": note_id, "path": f"data/notes/{rel.as_posix()}"}, ensure_ascii=False)

    def _exec_update_source(self, args: dict[str, Any]):
        note_id = str(args["note_id"]).strip().replace("/", ".")
        rel = Path(*note_id.split(".")) / "note.md"
        target = self._notes_root() / rel
        if not target.exists():
            raise FileNotFoundError(rel.as_posix())
        content = str(args["content"])
        target.write_text(content, encoding="utf-8")
        return json.dumps({"status": "updated", "note_id": note_id, "path": f"data/notes/{rel.as_posix()}"}, ensure_ascii=False)

    def _exec_generate_from_text(self, args: dict[str, Any]):
        title = str(args.get("title") or "未命名笔记")
        kind = str(args.get("kind") or "Document")
        base_id = str(args.get("note_id") or f"business.document.{_slug(title)}").replace("/", ".")
        source_ref = str(args.get("source_ref") or "tool.notes.generate_from_text")
        text = str(args.get("text") or "")
        body = f"## Summary\n\n{text[:500].strip()}\n\n## Fields\n\n- 来源：{source_ref}\n\n## Relations\n\n\n## Evidence\n\n- {source_ref}\n\n## 正文\n\n{text.strip()}\n"
        return self._exec_create({"note_id": base_id, "kind": kind, "title": title, "body": body, "status": "draft", "overwrite": bool(args.get("overwrite", False))})


def _render_note(note_id: str, kind: str, title: str, body: str, *, status: str) -> str:
    lens = {"Agent": "lens.agent", "Skill": "lens.skill", "Tool": "lens.tool"}.get(kind, "lens.default")
    return f"""---
id: {note_id}
kind: {kind}
status: {status}
maturity: draft
lens: {lens}
source_refs:
  - tool.notes.create
tags:
  - generated
---

# {title}

{body.strip()}
"""
