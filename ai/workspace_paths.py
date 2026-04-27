from __future__ import annotations

from pathlib import Path


def workspace_root(project_root: Path) -> Path:
    root = Path(project_root).resolve()
    return root.parent if root.name.lower() == "ai" else root


def data_root(project_root: Path) -> Path:
    return workspace_root(project_root) / "data"


def ai_root(project_root: Path) -> Path:
    return workspace_root(project_root) / "ai"
