from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import config_loader as cfg

from .errors import ActionNotFound, MissingRequiredParam, WikiAppError
from .service import WikiAppContext, WikiAppService


@dataclass(frozen=True)
class ActionSpec:
    name: str
    method: str
    required: tuple[str, ...] = ()
    defaults: dict[str, Any] = field(default_factory=dict)
    description: str = ""


ACTIONS: dict[str, ActionSpec] = {
    "wiki_create_session": ActionSpec("wiki_create_session", "create_session", defaults={"user_id": "wiki_app", "task_id": "frontend", "metadata_json": "{}"}, description="创建前端会话"),
    "wiki_session_info": ActionSpec("wiki_session_info", "session_info", defaults={"session_id": "default"}, description="读取会话信息"),
    "wiki_list_sessions": ActionSpec("wiki_list_sessions", "list_sessions", description="列出会话"),
    "wiki_server_status": ActionSpec("wiki_server_status", "server_status", description="读取服务状态"),
    "wiki_refresh_index": ActionSpec("wiki_refresh_index", "refresh_index", defaults={"extract_graph": True}, description="刷新 Wiki 索引"),
    "wiki_search": ActionSpec("wiki_search", "search", defaults={"query": "", "limit": 20, "include_disabled": False}, description="检索 Wiki 页面"),
    "wiki_graph_enhanced_search": ActionSpec("wiki_graph_enhanced_search", "graph_enhanced_search", defaults={"query": "", "limit": 20, "include_disabled": False}, description="图谱增强检索"),
    "wiki_read_page": ActionSpec("wiki_read_page", "read_page", required=("page_id",), description="读取渲染页面"),
    "wiki_read_source": ActionSpec("wiki_read_source", "read_source", required=("page_id",), description="读取源文"),
    "wiki_answer": ActionSpec("wiki_answer", "answer", required=("query",), defaults={"limit": 5}, description="Wiki 问答"),
    "wiki_check_truth_status": ActionSpec("wiki_check_truth_status", "check_truth_status", defaults={"page_id": "", "include_worktree": True}, description="检查真相状态"),
    "wiki_save_draft": ActionSpec("wiki_save_draft", "save_draft", required=("page_id", "markdown"), defaults={"author": "wiki_app", "reason": ""}, description="保存草稿"),
    "wiki_diff_draft": ActionSpec("wiki_diff_draft", "diff_draft", required=("draft_id",), description="草稿 Diff"),
    "wiki_publish_draft": ActionSpec("wiki_publish_draft", "publish_draft", required=("draft_id",), defaults={"message": "", "author": "wiki_app", "confirm_publish": False}, description="发布草稿"),
    "wiki_page_history": ActionSpec("wiki_page_history", "page_history", required=("page_id",), defaults={"limit": 20}, description="页面历史"),
    "wiki_read_version": ActionSpec("wiki_read_version", "read_version", required=("page_id", "commit"), description="读取历史版本"),
    "wiki_diff_versions": ActionSpec("wiki_diff_versions", "diff_versions", required=("page_id", "from_commit", "to_commit"), description="版本对比"),
    "wiki_create_rollback_draft": ActionSpec("wiki_create_rollback_draft", "create_rollback_draft", required=("page_id", "commit"), defaults={"author": "wiki_app", "reason": ""}, description="创建回滚草稿"),
    "wiki_release_history": ActionSpec("wiki_release_history", "release_history", defaults={"limit": 50, "page_id": ""}, description="发布历史"),
    "wiki_release_detail": ActionSpec("wiki_release_detail", "release_detail", required=("release_id",), description="发布详情"),
    "wiki_read_schema": ActionSpec("wiki_read_schema", "read_schema", defaults={"entity_type": "系统页面"}, description="读取页面元结构"),
    "wiki_check_page_schema": ActionSpec("wiki_check_page_schema", "check_page_schema", required=("page_id",), description="检查页面元结构"),
    "wiki_resolve_page_links": ActionSpec("wiki_resolve_page_links", "resolve_page_links", required=("page_id",), description="解析页面链接"),
    "wiki_alias_query": ActionSpec("wiki_alias_query", "alias_query", required=("label",), description="查询别名"),
    "wiki_normalize_page_to_chinese": ActionSpec("wiki_normalize_page_to_chinese", "normalize_page_to_chinese", required=("page_id",), defaults={"author": "wiki_app"}, description="规范化中文页面"),
    "wiki_page_file_status": ActionSpec("wiki_page_file_status", "page_file_status", required=("page_id",), description="页面依赖状态"),
    "wiki_update_system_page_from_files": ActionSpec("wiki_update_system_page_from_files", "update_system_page_from_files", required=("page_id",), defaults={"mode": "diff", "requirements": "", "author": "wiki_app"}, description="根据依赖文件更新页面"),
    "wiki_generate_user_folder_wikis": ActionSpec("wiki_generate_user_folder_wikis", "generate_user_folder_wikis", required=("root_path",), defaults={"dry_run": True, "author": "wiki_app"}, description="用户文件夹建页"),
    "wiki_extract_knowledge_graph": ActionSpec("wiki_extract_knowledge_graph", "extract_knowledge_graph", defaults={"include_disabled": False, "write_store": True, "include_graph": True}, description="抽取知识图谱"),
    "wiki_page_scope_relations": ActionSpec("wiki_page_scope_relations", "page_scope_relations", required=("page_id",), description="读取局部关系"),
    "wiki_diagnose_page": ActionSpec("wiki_diagnose_page", "diagnose_page", required=("page_id",), description="页面诊断"),
    "wiki_apply_diagnosis_fix": ActionSpec("wiki_apply_diagnosis_fix", "apply_diagnosis_fix", required=("page_id", "action_id"), defaults={"author": "wiki_app"}, description="执行诊断修复"),

    "wiki_app_diagnostics": ActionSpec("wiki_app_diagnostics", "app_diagnostics", description="Wiki App 综合诊断"),
    "wiki_page_update_hint": ActionSpec("wiki_page_update_hint", "page_update_hint", required=("page_id",), description="页面依赖变化更新提示"),
    "wiki_update_page_full": ActionSpec("wiki_update_page_full", "update_page_full", required=("page_id",), defaults={"requirements": "", "author": "wiki_app"}, description="全量更新页面草稿"),
    "wiki_update_page_diff": ActionSpec("wiki_update_page_diff", "update_page_diff", required=("page_id",), defaults={"requirements": "", "author": "wiki_app"}, description="差异化更新页面草稿"),
    "wiki_preview_user_folder_wikis": ActionSpec("wiki_preview_user_folder_wikis", "preview_user_folder_wikis", required=("root_path",), defaults={"author": "wiki_app"}, description="预览用户文件夹建页"),
    "wiki_graph_neighbors": ActionSpec("wiki_graph_neighbors", "graph_neighbors", required=("page_id",), defaults={"depth": 1, "include_disabled": False}, description="读取页面局部图谱邻居"),
    "wiki_batch_diagnose": ActionSpec("wiki_batch_diagnose", "batch_diagnose", defaults={"query": "", "limit": 20, "include_disabled": False}, description="批量诊断页面"),

    "wiki_page_status_summary": ActionSpec("wiki_page_status_summary", "page_status_summary", required=("page_id",), description="页面状态聚合摘要"),
    "wiki_batch_page_status": ActionSpec("wiki_batch_page_status", "batch_page_status", required=("page_ids",), description="批量页面状态聚合"),
    "wiki_search_with_status": ActionSpec("wiki_search_with_status", "search_with_status", defaults={"query": "", "limit": 20, "include_disabled": False, "entity_type": "", "stage": "", "status": "", "risk": ""}, description="带状态聚合的搜索"),
    "wiki_backend_overview": ActionSpec("wiki_backend_overview", "backend_overview", defaults={"query": "", "limit": 50, "include_disabled": False}, description="后台中心统计和排序表"),
    "wiki_batch_governance": ActionSpec("wiki_batch_governance", "batch_governance", required=("page_ids",), defaults={"operation": "diagnose", "author": "wiki_app"}, description="搜索结果批量治理"),
    "wiki_user_center_summary": ActionSpec("wiki_user_center_summary", "user_center_summary", defaults={"root_path": ""}, description="用户中心摘要"),

    "wiki_user_file_tree": ActionSpec("wiki_user_file_tree", "user_file_tree", defaults={"relative_path": ""}, description="用户文件库树"),
    "wiki_user_file_read": ActionSpec("wiki_user_file_read", "user_file_read", required=("relative_path",), description="读取用户文件"),
    "wiki_user_file_write": ActionSpec("wiki_user_file_write", "user_file_write", required=("relative_path",), defaults={"content": ""}, description="写入用户文件"),
    "wiki_user_file_mkdir": ActionSpec("wiki_user_file_mkdir", "user_file_mkdir", required=("relative_path",), description="新建用户文件夹"),
    "wiki_user_file_delete": ActionSpec("wiki_user_file_delete", "user_file_delete", required=("relative_path",), description="删除用户文件或文件夹"),
}


class WikiAppActionRouter:
    def __init__(self, project_root: Path | None = None, allow_publish: bool | None = None):
        root = Path(project_root or cfg.PROJECT_ROOT).resolve()
        session_root = root / ".runtime_data/app/wiki/sessions"
        self.service = WikiAppService(
            WikiAppContext(
                project_root=root,
                session_root=session_root,
                allow_publish=cfg.ALLOW_PUBLISH if allow_publish is None else allow_publish,
            )
        )

    def dispatch(self, action: str, payload: dict[str, Any] | None = None) -> Any:
        payload = payload or {}
        spec = ACTIONS.get(action)
        if not spec:
            raise ActionNotFound(f"未知 Wiki App Action：{action}")
        params = _build_params(spec, payload)
        handler = getattr(self.service, spec.method)
        return handler(**params)


def _build_params(spec: ActionSpec, payload: dict[str, Any]) -> dict[str, Any]:
    params = dict(spec.defaults)
    params.update(payload)
    for name in spec.required:
        if not str(params.get(name, "")).strip():
            raise MissingRequiredParam(f"缺少必要参数：{name}")
    return params


def action_catalog() -> list[dict[str, Any]]:
    return [
        {
            "name": spec.name,
            "method": spec.method,
            "required": list(spec.required),
            "defaults": spec.defaults,
            "description": spec.description,
        }
        for spec in ACTIONS.values()
    ]


def error_response(action: str, exc: Exception) -> tuple[int, dict[str, Any]]:
    if isinstance(exc, WikiAppError):
        return exc.status_code, {"ok": False, "action": action, "error": exc.to_dict()}
    return 500, {"ok": False, "action": action, "error": {"code": "INTERNAL_ERROR", "message": str(exc), "type": type(exc).__name__}}
