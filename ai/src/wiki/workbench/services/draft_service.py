from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path

from .base import WorkbenchService
from .truth_service import WikiTruthService
from wiki.workbench.git.git_adapter import GitAdapter
from wiki.page_state import is_disabled_markdown, is_locked_markdown


class WikiDraftService(WorkbenchService):
    @property
    def root(self) -> Path:
        path = self.project_root / "src/wiki/workbench/store/drafts"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_draft(self, page_id: str, markdown: str, *, author: str = "admin", reason: str = "") -> dict:
        truth = WikiTruthService(self.project_root).read_truth(page_id)
        if is_locked_markdown(truth["markdown"]) or is_disabled_markdown(truth["markdown"]):
            raise PermissionError(f"页面处于锁定或禁用状态，禁止生成草稿：{page_id}")
        draft_id = f"draft_{uuid.uuid4().hex[:12]}"
        folder = self.root / draft_id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "base.md").write_text(truth["markdown"], encoding="utf-8")
        (folder / "content.md").write_text(markdown, encoding="utf-8")
        patch = GitAdapter(self.project_root).diff_text(truth["markdown"], markdown, fromfile=truth["source_path"], tofile=f"{truth['source_path']} (draft)")
        (folder / "diff.patch").write_text(patch, encoding="utf-8")
        meta = {
            "draft_id": draft_id,
            "page_id": page_id,
            "source_path": truth["source_path"],
            "base_commit": truth["current_commit"],
            "base_hash": truth["hash"],
            "draft_hash": _sha(markdown),
            "author": author,
            "reason": reason,
            "status": "draft",
            "created_at": _now(),
            "updated_at": _now(),
            "diff_summary": _summary(patch),
        }
        (folder / "draft.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        return meta

    def get_draft(self, draft_id: str) -> dict:
        path = self.root / draft_id / "draft.json"
        if not path.exists():
            raise FileNotFoundError(draft_id)
        return json.loads(path.read_text(encoding="utf-8"))

    def read_draft(self, draft_id: str) -> str:
        return (self.root / draft_id / "content.md").read_text(encoding="utf-8")

    def read_base(self, draft_id: str) -> str:
        return (self.root / draft_id / "base.md").read_text(encoding="utf-8")

    def diff_draft(self, draft_id: str) -> dict:
        meta = self.get_draft(draft_id)
        base = self.read_base(draft_id)
        content = self.read_draft(draft_id)
        patch = GitAdapter(self.project_root).diff_text(base, content, fromfile="base", tofile="draft")
        return {"draft": meta, "patch": patch, "summary": _summary(patch)}

    def list_drafts(self, *, status: str | None = None) -> list[dict]:
        rows = []
        for p in sorted(self.root.glob("*/draft.json")):
            row = json.loads(p.read_text(encoding="utf-8"))
            if status and row.get("status") != status:
                continue
            rows.append(row)
        rows.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return rows

    def mark_status(self, draft_id: str, status: str) -> dict:
        path = self.root / draft_id / "draft.json"
        meta = json.loads(path.read_text(encoding="utf-8"))
        meta["status"] = status
        meta["updated_at"] = _now()
        path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        return meta

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def _summary(patch: str) -> dict[str, int]:
    added = len([line for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++")])
    deleted = len([line for line in patch.splitlines() if line.startswith("-") and not line.startswith("---")])
    return {"added": added, "deleted": deleted, "changed": min(added, deleted)}
