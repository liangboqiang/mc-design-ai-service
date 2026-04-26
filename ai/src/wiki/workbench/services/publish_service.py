from __future__ import annotations

import json
import time
from pathlib import Path

from protocol.registry import RuntimeRegistry
from .base import WorkbenchService
from .draft_service import WikiDraftService
from .release_service import WikiReleaseService
from .truth_service import WikiTruthService
from wiki.workbench.git.git_adapter import GitAdapter


class WikiPublishService(WorkbenchService):
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.git = GitAdapter(self.project_root)

    def publish_draft(self, draft_id: str, *, message: str = "", author: str = "admin", run_health_check: bool = True) -> dict:
        draft_service = WikiDraftService(self.project_root)
        meta = draft_service.get_draft(draft_id)
        source_path = meta["source_path"]
        truth = WikiTruthService(self.project_root).read_truth(meta["page_id"])
        if truth["hash"] != meta.get("base_hash"):
            conflict_id = self._record_conflict(draft_id, meta, truth["markdown"], draft_service.read_draft(draft_id))
            draft_service.mark_status(draft_id, "conflict")
            return {"ok": False, "message": "Draft conflicts with current truth file.", "conflict_id": conflict_id}

        current_path = self.project_root / source_path
        old_text = truth["markdown"]
        new_text = draft_service.read_draft(draft_id)
        current_path.write_text(new_text, encoding="utf-8")

        registry = RuntimeRegistry.from_wiki(self.project_root)
        errors = registry.view.errors()
        if errors:
            current_path.write_text(old_text, encoding="utf-8")
            return {"ok": False, "message": "Protocol errors after publish candidate.", "errors": [e.message for e in errors]}

        refresh_result = json.loads(self.hub.refresh_system())
        commit = self.git.commit_files(
            [source_path, "src/wiki/store/catalog.json", "src/wiki/store/index.json", "src/wiki/store/graph.json"],
            message or f"publish {draft_id}",
            author=author,
        )
        draft_service.mark_status(draft_id, "published")
        release = WikiReleaseService(self.project_root).record_release(
            {
                "release_id": f"rel_{time.strftime('%Y%m%d_%H%M%S', time.gmtime())}_{draft_id[-4:]}",
                "commit": commit,
                "author": author,
                "message": message or f"publish {draft_id}",
                "changed_pages": [meta["page_id"]],
                "draft_id": draft_id,
                "source_paths": [source_path],
                "health_summary": {"protocol_errors": 0},
                "refresh": refresh_result,
            }
        )
        return {"ok": True, "release": release, "commit": commit, "changed_pages": [meta["page_id"]]}

    def _record_conflict(self, draft_id: str, meta: dict, current: str, draft: str) -> str:
        conflict_id = f"conflict_{draft_id[-12:]}"
        root = self.project_root / "src/wiki/workbench/store/conflicts" / conflict_id
        root.mkdir(parents=True, exist_ok=True)
        (root / "current.md").write_text(current, encoding="utf-8")
        (root / "draft.md").write_text(draft, encoding="utf-8")
        (root / "conflict.json").write_text(json.dumps({"conflict_id": conflict_id, "draft_id": draft_id, "page_id": meta.get("page_id"), "source_path": meta.get("source_path")}, ensure_ascii=False, indent=2), encoding="utf-8")
        return conflict_id
