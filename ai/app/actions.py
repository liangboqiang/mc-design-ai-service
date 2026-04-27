from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import config_loader as cfg

from app.action_specs import ActionSpec, action_catalog, build_params
from workbench.file_service import WorkspaceFileService
from workbench.graph_service import WorkbenchGraphService
from workbench.intake import IntakeService
from workbench.note_service import MemoryAppService
from workbench.preview import RuntimePreviewService
from workbench.repository_service import RepositoryConfigService
from workbench.review import ProposalReviewService
from workbench.test_service import WorkbenchTestService
from workbench.version_service import NoteVersionService


ACTIONS: dict[str, ActionSpec] = {
    # 图谱百科 / 笔记原子动作
    "graphpedia_search": ActionSpec("graphpedia_search", "graphpedia_search", defaults={"query": "", "filters": {}, "limit": 80, "include_hidden": True}, description="图谱式 + 百科式统一搜索"),
    "memory_list_notes": ActionSpec("memory_list_notes", "list_notes", defaults={"query": "", "limit": 100, "kind": ""}, description="列出笔记"),
    "memory_read_note": ActionSpec("memory_read_note", "read_note", defaults={"note_id": "", "page_id": ""}, description="读取笔记"),
    "memory_read_note_detail": ActionSpec("memory_read_note_detail", "read_note_detail", defaults={"note_id": "", "page_id": ""}, description="读取笔记详情、源码、邻居、诊断和版本"),
    "memory_save_note_draft": ActionSpec("memory_save_note_draft", "save_note_draft", required=("note_id",), defaults={"markdown": ""}, description="保存笔记草稿"),
    "memory_save_note_source": ActionSpec("memory_save_note_source", "save_note_source", required=("note_id",), defaults={"markdown": "", "commit": False, "message": "manual note update"}, description="保存 note.md 源码"),
    "memory_create_note_proposal": ActionSpec("memory_create_note_proposal", "create_note_proposal", required=("note_id",), defaults={"markdown": "", "proposal_type": "note_patch", "source": "user", "review_notes": ""}, description="创建笔记更新提案"),
    "memory_generate_note_from_file": ActionSpec("memory_generate_note_from_file", "generate_note_from_file", required=("path",), defaults={"scope": "team", "target_kind": "Document", "target_note_id": "", "mode": "proposal"}, description="从文件抽取并生成笔记候选"),
    "memory_publish_note": ActionSpec("memory_publish_note", "publish_note", required=("note_id",), defaults={"maturity": "projectable"}, description="发布笔记"),
    "memory_check_note": ActionSpec("memory_check_note", "check_note", defaults={"note_id": "", "page_id": ""}, description="诊断笔记"),
    "memory_list_lenses": ActionSpec("memory_list_lenses", "list_lenses", description="列出 Lens"),
    "memory_check_runtime_ready": ActionSpec("memory_check_runtime_ready", "check_runtime_ready", defaults={"note_id": "", "page_id": ""}, description="检查 runtime_ready"),
    "memory_compile_indexes": ActionSpec("memory_compile_indexes", "compile_indexes", description="编译 Memory 索引"),
    "memory_compile_graph": ActionSpec("memory_compile_graph", "compile_graph", defaults={"include_hidden": False, "write_store": True}, description="编译图谱索引"),
    "memory_graph_view": ActionSpec("memory_graph_view", "graph_view", defaults={"include_hidden": False}, description="读取图谱索引"),
    "memory_graph_neighbors": ActionSpec("memory_graph_neighbors", "graph_neighbors", defaults={"note_id": "", "page_id": "", "depth": 1}, description="读取图谱邻居"),
    "memory_preview_view": ActionSpec("memory_preview_view", "preview_view", defaults={"task": ""}, description="预览 MemoryView"),
    "memory_preview_runtime": ActionSpec("memory_preview_runtime", "preview_runtime", defaults={"task": "", "tool_permission_level": 1}, description="预览运行上下文"),
    "memory_list_proposals": ActionSpec("memory_list_proposals", "list_proposals", defaults={"status": "candidate"}, description="列出提案"),
    "memory_review_proposal": ActionSpec("memory_review_proposal", "review_proposal", required=("proposal_id",), defaults={"decision": "accepted", "review_notes": ""}, description="审核提案"),
    "memory_ingest_source": ActionSpec("memory_ingest_source", "ingest_source", defaults={"files": []}, description="导入证据源"),
    "memory_run_test_case": ActionSpec("memory_run_test_case", "run_test_case", required=("task",), description="运行测试用例"),

    # 记事本 / 文件 / 软模式 / 版本 / 治理原子动作
    "repo_config_read": ActionSpec("repo_config_read", "read_config", description="读取仓库与软模式配置"),
    "repo_config_save": ActionSpec("repo_config_save", "save_config", defaults={"config": {}}, description="保存仓库与软模式配置"),
    "repo_list": ActionSpec("repo_list", "list_repositories", description="列出仓库配置"),
    "repo_save": ActionSpec("repo_save", "save_repository", defaults={"repository": {}}, description="保存仓库配置"),
    "repo_delete": ActionSpec("repo_delete", "delete_repository", required=("repo_id",), description="删除仓库配置"),
    "notebook_list": ActionSpec("notebook_list", "list_notebooks", description="列出记事本"),
    "notebook_read": ActionSpec("notebook_read", "get_notebook", required=("notebook_id",), description="读取记事本摘要、笔记与源文件"),
    "notebook_save": ActionSpec("notebook_save", "save_notebook", defaults={"notebook": {}}, description="保存记事本配置"),
    "notebook_delete": ActionSpec("notebook_delete", "delete_notebook", required=("notebook_id",), description="删除记事本配置"),
    "soft_schema_list": ActionSpec("soft_schema_list", "list_soft_schemas", description="列出软模式"),
    "soft_schema_read": ActionSpec("soft_schema_read", "read_soft_schema", defaults={"schema_id": "schema.default"}, description="读取软模式"),
    "soft_schema_save": ActionSpec("soft_schema_save", "save_soft_schema", defaults={"schema": {}}, description="保存软模式"),
    "soft_schema_discover": ActionSpec("soft_schema_discover", "discover_soft_schema", defaults={"schema_id": "schema.default", "repo_id": ""}, description="自动增量发现软模式字段"),
    "soft_schema_accept_field": ActionSpec("soft_schema_accept_field", "accept_soft_schema_field", required=("field_name",), defaults={"schema_id": "schema.default", "config": {}}, description="接受候选字段到软模式"),
    "workspace_roots": ActionSpec("workspace_roots", "roots", description="读取工作区根路径配置"),
    "workspace_list_files": ActionSpec("workspace_list_files", "list_files", defaults={"scope": "team", "path": "", "recursive": False}, description="列出 Team/User 文件"),
    "workspace_read_file": ActionSpec("workspace_read_file", "read_file", required=("path",), defaults={"scope": "team"}, description="读取文件与抽取文本"),
    "workspace_write_file": ActionSpec("workspace_write_file", "write_file", required=("path",), defaults={"scope": "team", "content": "", "create_dirs": True}, description="写入文件"),
    "workspace_upload_files": ActionSpec("workspace_upload_files", "upload_files", defaults={"scope": "team", "path": "", "files": []}, description="上传文件/文件夹"),
    "workspace_make_dir": ActionSpec("workspace_make_dir", "make_dir", required=("path",), defaults={"scope": "team"}, description="新建文件夹"),
    "workspace_delete_file": ActionSpec("workspace_delete_file", "delete_file", required=("path",), defaults={"scope": "team"}, description="删除文件或文件夹"),
    "workspace_move_file": ActionSpec("workspace_move_file", "move_file", required=("source", "target"), defaults={"scope": "team"}, description="移动/重命名文件"),
    "workspace_extract_file": ActionSpec("workspace_extract_file", "extract_file", required=("path",), defaults={"scope": "team"}, description="抽取文件文本"),
    "user_workspace_create_session": ActionSpec("user_workspace_create_session", "create_user_session", defaults={"user_id": "default", "session_id": "default"}, description="创建用户临时会话目录"),
    "user_workspace_submit_to_team": ActionSpec("user_workspace_submit_to_team", "submit_user_file_to_team", required=("path",), defaults={"user_id": "default", "session_id": "default", "target": "incoming"}, description="提交用户文件到团队区"),
    "version_status": ActionSpec("version_status", "status", description="读取 note.md 版本状态"),
    "version_commit_notes": ActionSpec("version_commit_notes", "commit_notes", defaults={"message": "manual note commit", "author": "system", "scope": "all"}, description="提交 note.md 版本"),
    "version_list_commits": ActionSpec("version_list_commits", "list_commits", defaults={"limit": 50}, description="列出提交历史"),
    "version_note_history": ActionSpec("version_note_history", "note_history", defaults={"note_path": "", "note_id": "", "limit": 50}, description="读取 note 历史"),
    "version_diff_note": ActionSpec("version_diff_note", "diff_note_versions", defaults={"note_path": "", "note_id": "", "from_commit": "", "to_commit": "WORKTREE"}, description="对比 note 版本"),
    "version_restore_note": ActionSpec("version_restore_note", "restore_note_version", required=("commit_id",), defaults={"note_path": "", "note_id": "", "message": "restore note version"}, description="恢复 note 历史版本"),
    "version_create_release": ActionSpec("version_create_release", "create_release", defaults={"name": "", "message": ""}, description="创建发布快照"),
    "version_list_releases": ActionSpec("version_list_releases", "list_releases", description="列出发布快照"),
    "version_rollback_release": ActionSpec("version_rollback_release", "rollback_release", required=("release_id",), defaults={"message": "rollback release"}, description="回退发布"),
    "governance_dashboard": ActionSpec("governance_dashboard", "governance_dashboard", description="审核治理总览"),
    "governance_issue_list": ActionSpec("governance_issue_list", "issue_list", defaults={"severity": "", "kind": ""}, description="列出健康问题节点"),
    "governance_apply_fix": ActionSpec("governance_apply_fix", "apply_fix", defaults={"issue_id": "", "fix_mode": "proposal", "payload": {}}, description="根据修复建议处理问题"),
    "governance_read_proposal": ActionSpec("governance_read_proposal", "read_proposal", required=("proposal_id",), defaults={"status": ""}, description="读取提案 Diff 与影响分析"),
    "governance_conflict_report": ActionSpec("governance_conflict_report", "conflict_report", description="冲突诊断报告"),
    "governance_bulk_review": ActionSpec("governance_bulk_review", "bulk_review_proposals", defaults={"proposal_ids": [], "decision": "accepted", "review_notes": ""}, description="批量审核"),
    "governance_apply_proposal": ActionSpec("governance_apply_proposal", "apply_proposal", required=("proposal_id",), defaults={"status": "accepted", "commit_message": "apply proposal"}, description="应用已接受提案"),
    "governance_suggest_fix": ActionSpec("governance_suggest_fix", "suggest_fix", defaults={"proposal_id": "", "diagnostic_code": ""}, description="生成修复建议"),
}


class ActionRouter:
    """Single atomic action router.

    The frontend and backend now collaborate through one stable action surface:
    /app/action/{action}.  Actions are explicit atoms and do not cross-call
    legacy namespace routers.
    """

    def __init__(self, project_root: Path | None = None):
        self.root = Path(project_root or cfg.PROJECT_ROOT).resolve()
        self._services: dict[str, Any] = {}

    def dispatch(self, action: str, payload: dict[str, Any] | None = None) -> Any:
        spec = ACTIONS.get(action)
        if spec is None:
            raise KeyError(f"未知系统动作：{action}")
        params = build_params(spec, payload or {})
        handler = getattr(self._service_for(spec.method), spec.method)
        return handler(**params)

    def catalog(self) -> list[dict[str, Any]]:
        return action_catalog(ACTIONS)

    def _service(self, key: str, factory: Callable[[Path], Any]) -> Any:
        if key not in self._services:
            self._services[key] = factory(self.root)
        return self._services[key]

    def _service_for(self, method: str) -> Any:
        note_methods = {
            "graphpedia_search", "list_notes", "read_note", "read_note_detail", "save_note_draft",
            "save_note_source", "create_note_proposal", "generate_note_from_file", "publish_note", "check_note",
            "list_lenses", "check_runtime_ready", "compile_indexes",
        }
        graph_methods = {"compile_graph", "graph_view", "graph_neighbors"}
        preview_methods = {"preview_view", "preview_runtime"}
        repo_methods = {
            "read_config", "save_config", "list_repositories", "save_repository", "delete_repository",
            "list_notebooks", "get_notebook", "save_notebook", "delete_notebook", "list_soft_schemas",
            "read_soft_schema", "save_soft_schema", "discover_soft_schema", "accept_soft_schema_field",
        }
        file_methods = {
            "roots", "list_files", "read_file", "write_file", "upload_files", "make_dir", "delete_file",
            "move_file", "extract_file", "create_user_session", "submit_user_file_to_team",
        }
        version_methods = {
            "status", "commit_notes", "list_commits", "note_history", "diff_note_versions", "restore_note_version",
            "create_release", "list_releases", "rollback_release",
        }
        review_methods = {
            "list_proposals", "review_proposal", "governance_dashboard", "issue_list", "apply_fix", "read_proposal",
            "conflict_report", "bulk_review_proposals", "apply_proposal", "suggest_fix",
        }
        if method in note_methods:
            return self._service("note", MemoryAppService)
        if method in graph_methods:
            return self._service("graph", WorkbenchGraphService)
        if method in preview_methods:
            return self._service("preview", RuntimePreviewService)
        if method in repo_methods:
            return self._service("repo", RepositoryConfigService)
        if method in file_methods:
            return self._service("files", WorkspaceFileService)
        if method in version_methods:
            return self._service("version", NoteVersionService)
        if method in review_methods:
            return self._service("review", ProposalReviewService)
        if method == "ingest_source":
            return self._service("intake", IntakeService)
        if method == "run_test_case":
            return self._service("tests", WorkbenchTestService)
        raise KeyError(f"未知服务方法：{method}")


__all__ = ["ACTIONS", "ActionRouter"]
