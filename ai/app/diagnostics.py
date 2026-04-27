from __future__ import annotations

from pathlib import Path

from wiki_app.diagnostics import collect_diagnostics as collect_legacy_diagnostics
from workbench.diagnosis import DiagnosisService
from workbench.note_service import MemoryAppService


def collect_diagnostics(root_dir: Path, ai_dir: Path, web_dir: Path, project_root: Path) -> dict:
    base = collect_legacy_diagnostics(root_dir, ai_dir, web_dir, project_root)
    memory = MemoryAppService(project_root)
    diagnosis = DiagnosisService(project_root)
    base.update(
        {
            "memory_note_count": len(memory.list_notes(limit=1000)),
            "memory_native": diagnosis.overview(),
        }
    )
    return base
