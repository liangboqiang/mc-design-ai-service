from __future__ import annotations

import re
from dataclasses import asdict
from pathlib import Path

from .base import WorkbenchService
from .draft_service import WikiDraftService
from wiki.workbench.git.git_adapter import GitAdapter


LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
RUNTIME_KEYS = {"type", "id", "toolbox", "permission_level", "activation", "categories", "root_skill", "toolboxes"}


class WikiVersionService(WorkbenchService):
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.git = GitAdapter(self.project_root)

    def page_history(self, page_id: str, *, limit: int = 20) -> dict:
        source_path = self.source_path(page_id)
        commits = [asdict(item) for item in self.git.log_file(source_path, limit=limit)]
        return {
            "page_id": page_id,
            "source_path": source_path,
            "is_git_repo": self.git.is_git_repo(),
            "commits": commits,
        }

    def read_version(self, page_id: str, commit: str) -> dict:
        source_path = self.source_path(page_id)
        markdown = self.git.show_file(source_path, commit)
        return {"page_id": page_id, "source_path": source_path, "commit": commit, "markdown": markdown}

    def diff_versions(self, page_id: str, from_commit: str, to_commit: str) -> dict:
        source_path = self.source_path(page_id)
        old = self.git.show_file(source_path, from_commit)
        new = self.git.show_file(source_path, to_commit)
        patch = self.git.diff_text(old, new, fromfile=f"{source_path}@{from_commit}", tofile=f"{source_path}@{to_commit}")
        return {
            "page_id": page_id,
            "source_path": source_path,
            "from_commit": from_commit,
            "to_commit": to_commit,
            "patch": patch,
            "diff_summary": _summary(patch),
            "affected_links": sorted(set(LINK_RE.findall(old)) ^ set(LINK_RE.findall(new))),
            "affected_runtime_fields": _affected_runtime_fields(old, new),
        }

    def create_rollback_draft(self, page_id: str, commit: str, *, author: str = "admin", reason: str = "") -> dict:
        source_path = self.source_path(page_id)
        markdown = self.git.show_file(source_path, commit)
        return WikiDraftService(self.project_root).save_draft(
            page_id,
            markdown,
            author=author,
            reason=reason or f"rollback to {commit}",
        )


def _summary(patch: str) -> dict[str, int]:
    added = len([line for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++")])
    deleted = len([line for line in patch.splitlines() if line.startswith("-") and not line.startswith("---")])
    return {"added": added, "deleted": deleted, "changed": min(added, deleted)}

def _runtime_lines(text: str) -> dict[str, str]:
    rows: dict[str, str] = {}
    inside = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("## runtime"):
            inside = True
            continue
        if inside and stripped.startswith("## "):
            break
        if inside and ":" in stripped and not stripped.startswith("```"):
            key = stripped.split(":", 1)[0].strip()
            if key in RUNTIME_KEYS:
                rows[key] = stripped
    return rows

def _affected_runtime_fields(old: str, new: str) -> list[str]:
    old_rows = _runtime_lines(old)
    new_rows = _runtime_lines(new)
    keys = sorted(set(old_rows) | set(new_rows))
    return [key for key in keys if old_rows.get(key) != new_rows.get(key)]
