from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


TEXT_EXTENSIONS = {".md", ".markdown", ".txt", ".yaml", ".yml", ".json", ".csv", ".py", ".toml"}


@dataclass(slots=True)
class WikiConfig:
    root_dir: Path
    pages_dir: Path
    catalog_path: Path
    locks_dir: Path
    attachments_dir: Path
    max_excerpt_chars: int = 2400
    max_summary_lines: int = 8
    max_file_chars: int = 200_000

    @classmethod
    def from_project_root(cls, project_root: Path) -> "WikiConfig":
        root = (Path(project_root).resolve() / "data" / "wiki").resolve()
        return cls(
            root_dir=root,
            pages_dir=root / "pages",
            catalog_path=root / "catalog.json",
            locks_dir=root / "locks",
            attachments_dir=root / "attachments",
        )
