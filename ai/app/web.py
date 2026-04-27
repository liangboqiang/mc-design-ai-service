from __future__ import annotations

from pathlib import Path

from app.api import create_app


def create_web_app(*, root_dir: Path, ai_dir: Path, web_dir: Path, web_dist_dir: Path):
    return create_app(root_dir=root_dir, ai_dir=ai_dir, web_dir=web_dir, web_dist_dir=web_dist_dir)
