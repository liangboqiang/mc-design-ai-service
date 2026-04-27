from __future__ import annotations

import json
import re
from dataclasses import asdict
import time
import uuid
from pathlib import Path
from typing import Any

from memory import MemoryService
from memory.note import render_note_markdown
from workbench.file_extractors import extract_text
from workbench.version_service import NoteVersionService
from workspace_paths import data_root, workspace_root


class MemoryAppService:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.memory = MemoryService(self.project_root)
        self.versions = NoteVersionService(self.project_root)

    def list_notes(self, query: str = "", limit: int = 100, kind: str = "") -> list[dict]:
        return self.memory.list_notes(query=query, limit=int(limit or 100), kind=kind)

    def graphpedia_search(self, query: str = "", filters: dict | None = None, limit: int = 80, include_hidden: bool = True) -> dict:
        filters = filters or {}
        kind = str(filters.get("kind") or "")
        status = str(filters.get("status") or "")
        maturity = str(filters.get("maturity") or "")
        relation = str(filters.get("relation") or "")
        rows = self.memory.list_notes(query=query, limit=max(1, int(limit or 80)), kind=kind)
        if status:
            rows = [row for row in rows if str(row.get("status") or "").lower() == status.lower()]
        if maturity:
            rows = [row for row in rows if str(row.get("maturity") or "").lower() == maturity.lower()]
        graph = self.memory.graph({"include_hidden": bool(include_hidden), "write_store": False})
        selected_ids = {row.get("note_id") for row in rows}
        matched_edges = []
        if relation:
            matched_edges = [edge for edge in graph.get("edges", []) if relation.lower() in str(edge.get("predicate") or edge.get("label") or "").lower()]
            selected_ids |= {edge.get("source") for edge in matched_edges} | {edge.get("target") for edge in matched_edges}
        for edge in graph.get("edges", []):
            if edge.get("source") in selected_ids or edge.get("target") in selected_ids:
                selected_ids.add(edge.get("source"))
                selected_ids.add(edge.get("target"))
        nodes = [node for node in graph.get("nodes", []) if node.get("id") in selected_ids]
        edges = [edge for edge in graph.get("edges", []) if edge.get("source") in selected_ids and edge.get("target") in selected_ids]
        categories = self._facets(self.memory.list_notes(limit=10_000))
        return {
            "query": query,
            "filters": filters,
            "notes": rows,
            "graph": {"nodes": nodes[:300], "edges": edges[:600]},
            "facets": categories,
            "governance": self._governance_summary(graph),
        }

    def read_note(self, note_id: str = "", page_id: str = "") -> dict:
        target = str(note_id or page_id or "").strip()
        if not target:
            raise ValueError("缺少必要参数：note_id")
        note = self.memory.read_note(target)
        if note is None:
            raise FileNotFoundError(f"Note 不存在：{target}")
        return note

    def read_note_detail(self, note_id: str = "", page_id: str = "") -> dict:
        target = str(note_id or page_id or "").strip()
        row = self.read_note(target)
        path = workspace_root(self.project_root) / row.get("path", "")
        markdown = path.read_text(encoding="utf-8") if path.exists() else render_note_markdown(self.memory.note_store.get(target))
        neighbors = self.memory.graph_neighbors(target, depth=1)
        check = self.check_note(target)
        history = self.versions.note_history(note_path=row.get("path", ""), note_id=target, limit=20)
        return {
            "note": row,
            "markdown": markdown,
            "neighbors": neighbors,
            "diagnostics": check.get("diagnostics", []),
            "normalized_fields": check.get("normalized_fields", {}),
            "history": history,
            "version_status": self.versions.status(),
        }

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

    def save_note_source(self, note_id: str, markdown: str = "", commit: bool = False, message: str = "manual note update") -> dict:
        result = self.save_note_draft(note_id=note_id, markdown=markdown)
        if commit:
            result["commit"] = self.versions.commit_notes(message=message or f"update {note_id}", author="note-editor", scope=result["path"])
        result["indexes"] = self.memory.compile_indexes()
        return result

    def create_note_proposal(self, note_id: str, markdown: str = "", proposal_type: str = "note_patch", source: str = "user", review_notes: str = "") -> dict:
        payload = {
            "proposal_type": proposal_type or "note_patch",
            "source": source or "user",
            "target_note_id": note_id,
            "markdown": markdown,
            "review_notes": review_notes,
        }
        batch = self.memory.proposals.capture_runtime_step(payload)
        return {"status": "candidate", "proposal": asdict(batch.proposals[0])}

    def generate_note_from_file(self, scope: str = "team", path: str = "", target_kind: str = "Document", target_note_id: str = "", mode: str = "proposal") -> dict:
        from workbench.file_service import WorkspaceFileService

        files = WorkspaceFileService(self.project_root)
        extracted_payload = files.extract_file(scope=scope, path=path)
        item = extracted_payload.get("item") or (extracted_payload.get("items") or [{}])[0]
        title = Path(path).stem.replace("_", " ").title() or "Generated Note"
        note_id = target_note_id or f"document.{_slug(Path(path).stem or uuid.uuid4().hex[:8])}"
        markdown = _note_from_extraction(note_id=note_id, title=title, kind=target_kind, item=item, source_path=f"{scope}://{path}")
        if mode == "write":
            return self.save_note_source(note_id=note_id, markdown=markdown, commit=True, message=f"generate note from {path}")
        return self.create_note_proposal(note_id=note_id, markdown=markdown, proposal_type="note_create" if not self.memory.note_store.get(note_id) else "note_patch", source="file_extract")

    def publish_note(self, note_id: str, maturity: str = "projectable") -> dict:
        target_path = self._note_path(note_id)
        if not target_path.exists():
            raise FileNotFoundError(f"Note 不存在：{note_id}")
        text = target_path.read_text(encoding="utf-8")
        text = self._replace_frontmatter_value(text, "status", "published")
        text = self._replace_frontmatter_value(text, "maturity", str(maturity or "projectable"))
        target_path.write_text(text, encoding="utf-8")
        self.memory.note_store.refresh()
        commit = self.versions.commit_notes(message=f"publish {note_id}", author="publisher", scope=self._display_path(target_path))
        indexes = self.memory.compile_indexes()
        return {"note_id": note_id, "path": self._display_path(target_path), "status": "published", "maturity": maturity, "commit": commit, "indexes": indexes}

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

    @staticmethod
    def _facets(rows: list[dict]) -> dict[str, list[dict]]:
        facets: dict[str, dict[str, int]] = {"kind": {}, "status": {}, "maturity": {}}
        for row in rows:
            for key in facets:
                value = str(row.get(key) or "unknown")
                facets[key][value] = facets[key].get(value, 0) + 1
        return {key: [{"value": value, "count": count} for value, count in sorted(values.items())] for key, values in facets.items()}

    @staticmethod
    def _governance_summary(graph: dict) -> dict:
        diagnostics = graph.get("diagnostics", [])
        conflicts = [d for d in diagnostics if "conflict" in str(d.get("code", "")).lower() or "冲突" in str(d.get("message", ""))]
        missing = [d for d in diagnostics if "missing" in str(d.get("code", "")).lower() or "缺" in str(d.get("message", ""))]
        return {"diagnostics": len(diagnostics), "conflicts": len(conflicts), "missing": len(missing)}


def _slug(value: str) -> str:
    raw = str(value or "note").lower()
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "_", raw).strip("_") or "note"


def _note_from_extraction(note_id: str, title: str, kind: str, item: dict, source_path: str) -> str:
    body = str(item.get("markdown") or item.get("text") or "").strip()
    excerpt = body[:6000]
    return f"""---
id: {note_id}
kind: {kind or 'Document'}
status: draft
maturity: draft
lens: lens.default
source_refs:
  - {source_path}
tags:
  - generated
---

# {title}

## Summary

由文件源 `{source_path}` 自动抽取生成的 note 候选，需要人工审核后发布。

## Fields

- 来源文件：{source_path}
- 抽取器：{item.get('parser', 'local')}
- 文件类型：{item.get('suffix', '')}

## Relations


## Evidence

- {source_path}

## Extracted Content

{excerpt}
"""
