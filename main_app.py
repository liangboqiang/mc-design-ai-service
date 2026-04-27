from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent
AI_DIR = ROOT_DIR / "ai"
WEB_DIR = ROOT_DIR / "web"
WEB_DIST_DIR = WEB_DIR / "dist"

for candidate in (ROOT_DIR, AI_DIR):
    value = str(candidate)
    if value not in sys.path:
        sys.path.insert(0, value)

import config_loader as cfg  # noqa: E402
from app.api import create_app as create_memory_native_app  # noqa: E402


def create_app():
    return create_memory_native_app(root_dir=ROOT_DIR, ai_dir=AI_DIR, web_dir=WEB_DIR, web_dist_dir=WEB_DIST_DIR)


app = create_app()
