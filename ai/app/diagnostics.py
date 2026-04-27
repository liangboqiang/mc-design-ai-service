from __future__ import annotations

from pathlib import Path

from workbench.note_service import MemoryAppService


def collect_diagnostics(root_dir: Path, ai_dir: Path, web_dir: Path, project_root: Path) -> dict:
    memory = MemoryAppService(project_root)
    notes = memory.list_notes(limit=1000)
    return {
        "project_root": str(project_root),
        "root_dir": str(root_dir),
        "ai_dir": str(ai_dir),
        "web_dir": str(web_dir),
        "mode": "memory-native-agent-kernel",
        "transport": "memory-workbench-direct-functions",
        "memory_note_count": len(notes),
    }
