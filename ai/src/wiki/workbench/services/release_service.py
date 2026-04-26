from __future__ import annotations

import json
import time
from pathlib import Path

from .base import WorkbenchService


class WikiReleaseService(WorkbenchService):
    @property
    def root(self) -> Path:
        path = self.project_root / "src/wiki/workbench/store/releases"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def record_release(self, payload: dict) -> dict:
        release_id = payload.get("release_id") or f"rel_{time.strftime('%Y%m%d_%H%M%S', time.gmtime())}"
        payload["release_id"] = release_id
        payload.setdefault("created_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        (self.root / f"{release_id}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def release_history(self, *, limit: int = 50, page_id: str | None = None) -> dict:
        rows = []
        for path in sorted(self.root.glob("*.json")):
            row = json.loads(path.read_text(encoding="utf-8"))
            if page_id and page_id not in row.get("changed_pages", []):
                continue
            rows.append(row)
        rows.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return {"releases": rows[: int(limit)]}

    def release_detail(self, release_id: str) -> dict:
        path = self.root / f"{release_id}.json"
        if not path.exists():
            raise FileNotFoundError(release_id)
        return json.loads(path.read_text(encoding="utf-8"))
