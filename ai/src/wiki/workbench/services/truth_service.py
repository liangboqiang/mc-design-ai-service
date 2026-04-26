from __future__ import annotations

import hashlib
from pathlib import Path
from dataclasses import asdict

from .base import WorkbenchService
from wiki.workbench.git.git_adapter import GitAdapter


class WikiTruthService(WorkbenchService):
    """Wiki semantic wrapper for Markdown truth files."""

    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.git = GitAdapter(self.project_root)

    def read_truth(self, page_id: str) -> dict:
        source_path = self.source_path(page_id)
        text = (self.project_root / source_path).read_text(encoding="utf-8")
        row = self.page_row(page_id)
        return {
            "page_id": page_id,
            "title": row.get("title") or page_id,
            "source_path": source_path,
            "markdown": text,
            "hash": self.hash_text(text),
            "current_commit": self.git.current_commit(),
        }

    def truth_status(self, page_id: str | None = None, *, include_worktree: bool = True) -> dict:
        payload = {
            "is_git_repo": self.git.is_git_repo(),
            "current_commit": self.git.current_commit(),
            "current_branch": self.git.current_branch(),
            "worktree_clean": self.git.is_worktree_clean(),
            "changed_files": [asdict(item) for item in self.git.worktree_status()] if include_worktree else [],
        }
        if page_id:
            try:
                truth = self.read_truth(page_id)
                payload["page"] = {
                    "page_id": page_id,
                    "source_path": truth["source_path"],
                    "hash": truth["hash"],
                    "tracked_history_count": len(self.git.log_file(truth["source_path"], limit=50)),
                }
            except FileNotFoundError:
                payload["page"] = {"page_id": page_id, "missing": True}
        return payload

    @staticmethod
    def hash_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
