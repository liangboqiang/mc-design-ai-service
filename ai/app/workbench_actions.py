from __future__ import annotations

from pathlib import Path
from typing import Any

import config_loader as cfg

from app.action_specs import ActionSpec, action_catalog, build_params
from workbench.graph_service import WorkbenchGraphService
from workbench.intake import IntakeService
from workbench.preview import RuntimePreviewService
from workbench.review import ProposalReviewService
from workbench.test_service import WorkbenchTestService


WORKBENCH_ACTIONS: dict[str, ActionSpec] = {
    "memory_ingest_source": ActionSpec("memory_ingest_source", "ingest_source", defaults={"files": []}, description="导入证据源"),
    "memory_compile_graph": ActionSpec("memory_compile_graph", "compile_graph", defaults={"include_hidden": False, "write_store": True}, description="编译 memory graph"),
    "memory_graph_view": ActionSpec("memory_graph_view", "graph_view", defaults={"include_hidden": False}, description="读取 memory graph"),
    "memory_graph_neighbors": ActionSpec("memory_graph_neighbors", "graph_neighbors", defaults={"note_id": "", "page_id": "", "depth": 1}, description="读取图谱邻居"),
    "memory_preview_view": ActionSpec("memory_preview_view", "preview_view", defaults={"task": ""}, description="预览 MemoryView"),
    "memory_preview_runtime": ActionSpec("memory_preview_runtime", "preview_runtime", defaults={"task": "", "tool_permission_level": 1}, description="预览 runtime"),
    "memory_list_proposals": ActionSpec("memory_list_proposals", "list_proposals", defaults={"status": "candidate"}, description="列出 proposals"),
    "memory_review_proposal": ActionSpec("memory_review_proposal", "review_proposal", required=("proposal_id",), defaults={"decision": "accepted", "review_notes": ""}, description="审核 proposal"),
    "memory_run_test_case": ActionSpec("memory_run_test_case", "run_test_case", required=("task",), description="运行测试用例"),
}


class WorkbenchActionRouter:
    def __init__(self, project_root: Path | None = None):
        root = Path(project_root or cfg.PROJECT_ROOT).resolve()
        self.intake = IntakeService(root)
        self.graph = WorkbenchGraphService(root)
        self.preview = RuntimePreviewService(root)
        self.review = ProposalReviewService(root)
        self.tests = WorkbenchTestService(root)

    def dispatch(self, action: str, payload: dict[str, Any] | None = None) -> Any:
        payload = payload or {}
        spec = WORKBENCH_ACTIONS.get(action)
        if spec is None:
            raise KeyError(f"未知 Workbench Action：{action}")
        params = build_params(spec, payload)
        service = self._service_for(spec.method)
        handler = getattr(service, spec.method)
        return handler(**params)

    def catalog(self) -> list[dict[str, Any]]:
        return action_catalog(WORKBENCH_ACTIONS)

    def _service_for(self, method: str):  # noqa: ANN001
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
        raise KeyError(f"未知 Workbench service 方法：{method}")
