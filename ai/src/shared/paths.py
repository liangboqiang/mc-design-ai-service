from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def src_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_from_root(*parts: str) -> Path:
    return project_root().joinpath(*parts)
