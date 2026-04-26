from __future__ import annotations

from pathlib import Path
import json


def collect_diagnostics(root_dir: Path, ai_dir: Path, web_dir: Path, project_root: Path) -> dict:
    dist = web_dir / "dist"
    assets = dist / "assets"
    catalog_path = project_root / "src/wiki/store/catalog.json"
    catalog_count = 0
    if catalog_path.exists():
        try:
            catalog_count = len(json.loads(catalog_path.read_text(encoding="utf-8")).get("pages") or {})
        except Exception:
            catalog_count = 0
    return {
        "root_dir": str(root_dir),
        "ai_dir": str(ai_dir),
        "web_dir": str(web_dir),
        "project_root": str(project_root),
        "dist_exists": dist.exists(),
        "index_exists": (dist / "index.html").exists(),
        "assets_exists": assets.exists(),
        "asset_count": len(list(assets.glob("*"))) if assets.exists() else 0,
        "catalog_exists": catalog_path.exists(),
        "catalog_count": catalog_count,
    }
