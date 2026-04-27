from __future__ import annotations

from pathlib import Path

from workbench.preview import RuntimePreviewService


class WorkbenchTestService:
    def __init__(self, project_root: Path):
        self.preview = RuntimePreviewService(Path(project_root).resolve())

    def run_test_case(self, task: str) -> dict:
        preview = self.preview.preview_runtime(task=task)
        return {
            "task": task,
            "memory_cards": len(preview.get("memory_view", {}).get("system_cards", [])) + len(preview.get("memory_view", {}).get("business_cards", [])),
            "visible_tools": len(preview.get("capability_view", {}).get("visible_tools", [])),
            "ok": True,
        }
