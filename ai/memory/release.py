from __future__ import annotations

import json
import time
from pathlib import Path

from workspace_paths import data_root


class MemoryReleaseService:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.release_root = data_root(self.project_root) / "releases"
        self.release_root.mkdir(parents=True, exist_ok=True)

    def write_manifest(self, payload: dict) -> dict:
        manifest = {
            "released_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **payload,
        }
        target = self.release_root / "release_manifest.json"
        target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return manifest
