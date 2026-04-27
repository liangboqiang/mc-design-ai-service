from __future__ import annotations

from pathlib import Path
from typing import Any

import config_loader as cfg

from app.action_specs import ActionSpec, action_catalog, build_params
from workbench.graph_service import WorkbenchGraphService
from workbench.intake import IntakeService
from workbench.note_service import MemoryAppService
from workbench.preview import RuntimePreviewService
from workbench.review import ProposalReviewService
from workbench.test_service import WorkbenchTestService


MEMORY_ACTIONS: dict[str, ActionSpec] = {
    "memory_ingest_source": ActionSpec("memory_ingest_source", "ingest_source", defaults={"files": []}, description="导入证据源"),
    "memory_list_notes": ActionSpec("memory_list_notes", "list_notes", defaults={"query": "", "limit": 100, "kind": ""}, description="列出 note"),
    "memory_read_note": ActionSpec("memory_read_note", "read_note", defaults={"note_id": "", "page_id": ""}, description="读取 note"),
    "memory_save_note_draft": ActionSpec("memory_save_note_draft", "save_note_draft", required=("note_id",), defaults={"markdown": ""}, description="保存 note 草稿"),
    "memory_publish_note": ActionSpec("memory_publish_note", "publish_note", required=("note_id",), defaults={"maturity": "projectable"}, description="发布 note"),
    "memory_check_note": ActionSpec("memory_check_note", "check_note", defaults={"note_id": "", "page_id": ""}, description="诊断 note"),
    "memory_list_lenses": ActionSpec("memory_list_lenses", "list_lenses", description="列出 lens"),
    "memory_check_runtime_ready": ActionSpec("memory_check_runtime_ready", "check_runtime_ready", defaults={"note_id": "", "page_id": ""}, description="检查 runtime_ready"),
    "memory_compile_indexes": ActionSpec("memory_compile_indexes", "compile_indexes", description="编译 memory indexes"),
    "memory_compile_graph": ActionSpec("memory_compile_graph", "compile_graph", defaults={"include_hidden": False, "write_store": True}, description="编译 memory graph"),
    "memory_graph_view": ActionSpec("memory_graph_view", "graph_view", defaults={"include_hidden": False}, description="读取 memory graph"),
    "memory_graph_neighbors": ActionSpec("memory_graph_neighbors", "graph_neighbors", defaults={"note_id": "", "page_id": "", "depth": 1}, description="读取图谱邻居"),
    "memory_preview_view": ActionSpec("memory_preview_view", "preview_view", defaults={"task": ""}, description="预览 MemoryView"),
    "memory_preview_runtime": ActionSpec("memory_preview_runtime", "preview_runtime", defaults={"task": "", "tool_permission_level": 1}, description="预览 runtime"),
    "memory_list_proposals": ActionSpec("memory_list_proposals", "list_proposals", defaults={"status": "candidate"}, description="列出 proposals"),
    "memory_review_proposal": ActionSpec("memory_review_proposal", "review_proposal", required=("proposal_id",), defaults={"decision": "accepted", "review_notes": ""}, description="审核 proposal"),
    "memory_run_test_case": ActionSpec("memory_run_test_case", "run_test_case", required=("task",), description="运行测试用例"),
}


class MemoryActionRouter:
    def __init__(self, project_root: Path | None = None):
        root = Path(project_root or cfg.PROJECT_ROOT).resolve()
        self.intake = IntakeService(root)
        self.notes = MemoryAppService(root)
        self.graph = WorkbenchGraphService(root)
        self.preview = RuntimePreviewService(root)
        self.review = ProposalReviewService(root)
        self.tests = WorkbenchTestService(root)

    def dispatch(self, action: str, payload: dict[str, Any] | None = None) -> Any:
        payload = payload or {}
        spec = MEMORY_ACTIONS.get(action)
        if spec is None:
            raise KeyError(f"未知 Memory Action：{action}")
        params = build_params(spec, payload)
        service = self._service_for(spec.method)
        handler = getattr(service, spec.method)
        return handler(**params)

    def catalog(self) -> list[dict[str, Any]]:
        return action_catalog(MEMORY_ACTIONS)

    def _service_for(self, method: str):  # noqa: ANN001
        if method in {"list_notes", "read_note", "save_note_draft", "publish_note", "check_note", "list_lenses", "check_runtime_ready", "compile_indexes"}:
            return self.notes
        if method == "ingest_source":
            return self.intake
        if method in {"compile_graph", "graph_view", "graph_neighbors"}:
            return self.graph
        if method in {"preview_view", "preview_runtime"}:
            return self.preview
        if method in {"list_proposals", "review_proposal"}:
            return self.review
        if method == "run_test_case":
            return self.tests
        raise KeyError(f"未知 Memory service 方法：{method}")
