from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from wiki.hub import WikiHub
from wiki.workbench import WikiWorkbench
from workbench.graph_service import WorkbenchGraphService
from workbench.user_file_service import UserFileEvidenceService
from workspace_paths import data_root

from .errors import PublishNotAllowed, MissingRequiredParam


class WikiAppSessionManager:
    def __init__(self, project_root: Path, session_root: Path):
        self.project_root = Path(project_root).resolve()
        self.session_root = Path(session_root)
        if not self.session_root.is_absolute():
            self.session_root = self.project_root / self.session_root
        self.session_root.mkdir(parents=True, exist_ok=True)

    def create_session(self, *, user_id: str = "", task_id: str = "", metadata: dict | None = None) -> dict:
        session_id = f"wiki_{uuid.uuid4().hex[:12]}"
        path = self.session_root / session_id
        path.mkdir(parents=True, exist_ok=True)
        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "task_id": task_id,
            "metadata": metadata or {},
            "created_at": _now(),
            "updated_at": _now(),
            "project_root": str(self.project_root),
        }
        (path / "session.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def get_session(self, session_id: str = "default") -> dict:
        if not session_id or session_id == "default":
            path = self.session_root / "default"
            path.mkdir(parents=True, exist_ok=True)
            meta = path / "session.json"
            if not meta.exists():
                payload = {
                    "session_id": "default",
                    "user_id": "",
                    "task_id": "",
                    "metadata": {},
                    "created_at": _now(),
                    "updated_at": _now(),
                    "project_root": str(self.project_root),
                }
                meta.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                return payload
            return json.loads(meta.read_text(encoding="utf-8"))
        meta = self.session_root / session_id / "session.json"
        if not meta.exists():
            raise FileNotFoundError(f"Wiki App session 不存在：{session_id}")
        return json.loads(meta.read_text(encoding="utf-8"))

    def list_sessions(self) -> list[dict]:
        return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(self.session_root.glob("*/session.json"))]


@dataclass(slots=True)
class WikiAppContext:
    project_root: Path
    session_root: Path
    allow_publish: bool = False


class WikiAppService:
    """Application-facing service for the Wiki Web UI.

    This service is internal to the unified app. It does not register MCP tools
    and does not route through a transport layer.
    """

    def __init__(self, context: WikiAppContext):
        self.context = context
        self.project_root = Path(context.project_root).resolve()
        self.workbench = WikiWorkbench(self.project_root)
        self.hub = WikiHub(project_root=self.project_root)
        self.memory_graph = WorkbenchGraphService(self.project_root)
        self.user_files = UserFileEvidenceService(self.project_root)
        self.sessions = WikiAppSessionManager(self.project_root, context.session_root)

    def create_session(self, user_id: str = "", task_id: str = "", metadata_json: str = "{}") -> dict:
        return self.sessions.create_session(user_id=user_id, task_id=task_id, metadata=_loads(metadata_json, {}))

    def session_info(self, session_id: str = "default") -> dict:
        return self.sessions.get_session(session_id)

    def list_sessions(self) -> list[dict]:
        return self.sessions.list_sessions()

    def server_status(self) -> dict:
        catalog_path = self.project_root / "src/wiki/store/catalog.json"
        index_path = self.project_root / "src/wiki/store/index.json"
        memory_catalog_path = data_root(self.project_root) / "indexes" / "catalog.json"
        catalog_count = 0
        if catalog_path.exists():
            try:
                catalog_count = len(json.loads(catalog_path.read_text(encoding="utf-8")).get("pages") or {})
            except Exception:
                catalog_count = 0
        memory_catalog_count = 0
        if memory_catalog_path.exists():
            try:
                memory_catalog_count = len(json.loads(memory_catalog_path.read_text(encoding="utf-8")).get("notes") or {})
            except Exception:
                memory_catalog_count = 0
        return {
            "project_root": str(self.project_root),
            "catalog_exists": catalog_path.exists(),
            "index_exists": index_path.exists(),
            "catalog_count": catalog_count,
            "memory_catalog_exists": memory_catalog_path.exists(),
            "memory_catalog_count": memory_catalog_count,
            "mode": "memory-native-compat",
        }

    def refresh_index(self, extract_graph: bool = True) -> dict:
        refresh = json.loads(self.hub.refresh_system())
        graph = None
        if extract_graph:
            graph = self.workbench.graph.extract_knowledge_graph(include_disabled=False, write_store=True, include_graph=False)
        return {"refresh": refresh, "graph": graph}

    def search(self, query: str = "", limit: int = 20, include_disabled: bool = False) -> list[dict]:
        rows = json.loads(self.hub.search(query or "", limit=int(limit or 20)))
        if not include_disabled:
            rows = [row for row in rows if not row.get("disabled")]
        return rows

    def graph_enhanced_search(self, query: str = "", limit: int = 20, include_disabled: bool = False) -> dict:
        try:
            graph = self.memory_graph.graph_view(include_hidden=include_disabled)
            q = str(query or "").lower()
            scored = []
            for node in graph.get("nodes", []):
                hay = " ".join([str(node.get("id")), str(node.get("title")), str(node.get("kind")), str(node.get("summary"))]).lower()
                score = hay.count(q) if q else 1
                related = [edge for edge in graph.get("edges", []) if edge.get("source") == node.get("id") or edge.get("target") == node.get("id")]
                score += len(related)
                if score > 0:
                    scored.append((score, {**node, "score": score, "related_count": len(related), "related_sample": related[:5]}))
            scored.sort(key=lambda item: (-item[0], str(item[1].get("id") or "")))
            return {"query": query, "items": [row for _, row in scored[: int(limit or 20)]], "graph": graph}
        except Exception as exc:
            graph = self._fallback_graph(query=query, limit=int(limit or 20), include_disabled=include_disabled, reason=str(exc))
            return {"query": query, "results": graph["nodes"], "graph": graph, "fallback": True, "error": str(exc)}


    def read_page(self, page_id: str) -> dict:
        page_id = _required(page_id, "page_id")
        return {"page_id": page_id, "content": self.hub.read_page(page_id)}

    def read_source(self, page_id: str) -> dict:
        page_id = _required(page_id, "page_id")
        return {"page_id": page_id, "markdown": self.hub.read_source(page_id)}

    def answer(self, query: str, limit: int = 5) -> dict:
        return {"query": query, "answer": self.hub.answer(query, limit=int(limit or 5))}

    def check_truth_status(self, page_id: str = "", include_worktree: bool = True) -> dict:
        return self.workbench.truth.truth_status(page_id or None, include_worktree=include_worktree)

    def save_draft(self, page_id: str, markdown: str, author: str = "wiki_app", reason: str = "") -> dict:
        page_id = _required(page_id, "page_id")
        return self.workbench.draft.save_draft(page_id, str(markdown or ""), author=author, reason=reason)

    def diff_draft(self, draft_id: str) -> dict:
        return self.workbench.draft.diff_draft(_required(draft_id, "draft_id"))

    def publish_draft(self, draft_id: str, message: str = "", author: str = "wiki_app", confirm_publish: bool = False) -> dict:
        if not self.context.allow_publish and not confirm_publish:
            raise PublishNotAllowed("发布已被保护：需要 confirm_publish=true。")
        return self.workbench.publish.publish_draft(_required(draft_id, "draft_id"), message=message, author=author)

    def page_history(self, page_id: str, limit: int = 20) -> dict:
        return self.workbench.version.page_history(_required(page_id, "page_id"), limit=int(limit or 20))

    def read_version(self, page_id: str, commit: str) -> dict:
        return self.workbench.version.read_version(_required(page_id, "page_id"), _required(commit, "commit"))

    def diff_versions(self, page_id: str, from_commit: str, to_commit: str) -> dict:
        return self.workbench.version.diff_versions(_required(page_id, "page_id"), _required(from_commit, "from_commit"), _required(to_commit, "to_commit"))

    def create_rollback_draft(self, page_id: str, commit: str, author: str = "wiki_app", reason: str = "") -> dict:
        return self.workbench.version.create_rollback_draft(_required(page_id, "page_id"), _required(commit, "commit"), author=author, reason=reason)

    def release_history(self, limit: int = 50, page_id: str = "") -> dict:
        return self.workbench.release.release_history(limit=int(limit or 50), page_id=page_id or None)

    def release_detail(self, release_id: str) -> dict:
        return self.workbench.release.release_detail(_required(release_id, "release_id"))

    def read_schema(self, entity_type: str = "系统页面") -> dict:
        return self.workbench.schema.read_schema(entity_type)

    def check_page_schema(self, page_id: str) -> dict:
        return self.workbench.schema.check_page_schema(_required(page_id, "page_id"))

    def resolve_page_links(self, page_id: str) -> dict:
        return self.workbench.schema.resolve_page_links(_required(page_id, "page_id"))

    def alias_query(self, label: str) -> dict:
        return self.workbench.schema.alias_query(_required(label, "label"))

    def normalize_page_to_chinese(self, page_id: str, author: str = "wiki_app") -> dict:
        return self.workbench.schema.normalize_page_to_chinese_draft(_required(page_id, "page_id"), author=author)

    def page_file_status(self, page_id: str) -> dict:
        return self.workbench.files.page_file_status(_required(page_id, "page_id"))

    def update_system_page_from_files(self, page_id: str, mode: str = "diff", requirements: str = "", author: str = "wiki_app") -> dict:
        return self.workbench.files.update_system_page_from_files(_required(page_id, "page_id"), mode=mode, requirements=requirements, author=author)

    def generate_user_folder_wikis(self, root_path: str, dry_run: bool = True, author: str = "wiki_app") -> dict:
        return self.workbench.files.generate_user_folder_wikis(_required(root_path, "root_path"), dry_run=dry_run, author=author)

    def extract_knowledge_graph(self, include_disabled: bool = False, write_store: bool = True, include_graph: bool = False) -> dict:
        try:
            data = self.memory_graph.compile_graph(include_hidden=include_disabled, write_store=write_store)
            if not include_graph:
                data = dict(data)
                data["graph"] = None
            return data
        except Exception as exc:
            graph = self._fallback_graph(query="", limit=80, include_disabled=include_disabled, reason=str(exc))
            return {**graph, "graph": graph, "error": str(exc), "message": "知识图谱抽取失败，已返回可用的降级图谱，避免前端 500。"}


    def page_scope_relations(self, page_id: str) -> dict:
        page_id = _required(page_id, "page_id")
        try:
            graph = self.memory_graph.graph_neighbors(page_id=page_id, depth=1)
            return {
                "page_id": page_id,
                "scope": "memory_graph",
                "relations": graph.get("edges", []),
                "local_relations": graph.get("edges", []),
                "links": [edge.get("target") for edge in graph.get("edges", []) if edge.get("source") == page_id],
                "disabled": False,
            }
        except Exception as exc:
            return {"page_id": page_id, "scope": "", "relations": [], "fallback": True, "error": str(exc)}


    def diagnose_page(self, page_id: str) -> dict:
        return self.workbench.diagnosis.diagnose_page(_required(page_id, "page_id"))

    def apply_diagnosis_fix(self, page_id: str, action_id: str, author: str = "wiki_app") -> dict:
        return self.workbench.diagnosis.apply_diagnosis_fix(_required(page_id, "page_id"), _required(action_id, "action_id"), author=author)


    def page_status_summary(self, page_id: str) -> dict:
        page_id = _required(page_id, "page_id")
        summary = {
            "page_id": page_id,
            "entity_type": "页面",
            "stage": "已发布",
            "locked": False,
            "disabled": False,
            "risk_level": "none",
            "update_required": False,
            "changed_file_count": 0,
            "issue_count": 0,
            "draft_count": 0,
            "has_unresolved_links": False,
            "graph_enabled": True,
            "status_labels": [],
        }
        try:
            source = self.read_source(page_id).get("markdown", "")
            summary["locked"] = "锁定状态：已锁定" in source or "锁定状态: 已锁定" in source
            summary["disabled"] = "禁用状态：已禁用" in source or "禁用状态: 已禁用" in source
            summary["graph_enabled"] = not summary["disabled"]
            for line in source.splitlines():
                if "实体类型" in line and ("：" in line or ":" in line):
                    summary["entity_type"] = line.split("：", 1)[-1].split(":", 1)[-1].strip(" -") or summary["entity_type"]
                    break
        except Exception:
            pass
        try:
            hint = self.page_update_hint(page_id)
            summary["update_required"] = bool(hint.get("requires_update"))
            summary["changed_file_count"] = len(hint.get("changed_files") or [])
        except Exception:
            pass
        try:
            diagnosis = self.diagnose_page(page_id)
            issues = diagnosis.get("issues") or diagnosis.get("diagnostics") or []
            summary["issue_count"] = len(issues) if isinstance(issues, list) else 0
            summary["has_unresolved_links"] = any("链接" in str(item) or "link" in str(item).lower() for item in issues) if isinstance(issues, list) else False
        except Exception:
            pass
        try:
            draft_root = self.project_root / "src/wiki/workbench/store/drafts"
            if draft_root.exists():
                token = page_id.replace("/", "__").replace("\\", "__")
                summary["draft_count"] = len([p for p in draft_root.rglob("*") if p.is_file() and token in p.name])
        except Exception:
            pass
        if summary["disabled"]:
            summary["status_labels"].append({"type": "disabled", "label": "已禁用", "pane": "status"})
        if summary["locked"]:
            summary["status_labels"].append({"type": "locked", "label": "已锁定", "pane": "status"})
        if summary["update_required"]:
            summary["status_labels"].append({"type": "update", "label": f"需更新 {summary['changed_file_count']}", "pane": "update"})
        if summary["issue_count"]:
            summary["status_labels"].append({"type": "issue", "label": f"问题 {summary['issue_count']}", "pane": "diagnose"})
        if summary["draft_count"]:
            summary["status_labels"].append({"type": "draft", "label": f"草稿 {summary['draft_count']}", "pane": "draft"})
        if summary["issue_count"] >= 3:
            summary["risk_level"] = "high"
        elif summary["issue_count"] or summary["update_required"]:
            summary["risk_level"] = "medium"
        elif summary["locked"] or summary["disabled"]:
            summary["risk_level"] = "low"
        if summary["risk_level"] != "none":
            summary["status_labels"].append({"type": "risk", "label": f"风险 {summary['risk_level']}", "pane": "risk"})
        if not summary["status_labels"]:
            summary["status_labels"].append({"type": "ok", "label": "正常", "pane": "overview"})
        return summary

    def batch_page_status(self, page_ids: list[str] | str) -> dict:
        if isinstance(page_ids, str):
            ids = [item.strip() for item in page_ids.split(",") if item.strip()]
        else:
            ids = [str(item).strip() for item in (page_ids or []) if str(item).strip()]
        rows = []
        for page_id in ids:
            try:
                rows.append(self.page_status_summary(page_id))
            except Exception as exc:
                rows.append({"page_id": page_id, "error": str(exc), "risk_level": "high", "status_labels": [{"type": "error", "label": "错误", "pane": "diagnose"}]})
        return {"count": len(rows), "results": rows}

    def search_with_status(
        self,
        query: str = "",
        limit: int = 20,
        include_disabled: bool = False,
        entity_type: str = "",
        stage: str = "",
        status: str = "",
        risk: str = "",
    ) -> dict:
        rows = self.search(query=query, limit=limit, include_disabled=include_disabled)
        enriched = []
        for row in rows:
            item = dict(row)
            item["status"] = self._fast_status_from_row(item)
            st = item["status"]
            if entity_type and entity_type not in {"全部", "all"} and str(st.get("entity_type") or "") != entity_type:
                continue
            if stage and stage not in {"全部", "all"} and str(st.get("stage") or "") != stage:
                continue
            if risk and risk not in {"全部", "all"} and str(st.get("risk_level") or "") != risk:
                continue
            if status and status not in {"全部", "all"}:
                labels = " ".join(label.get("type", "") + label.get("label", "") for label in st.get("status_labels", []))
                if status not in labels:
                    continue
            if not include_disabled and st.get("disabled"):
                continue
            enriched.append(item)
        stats = {
            "total": len(enriched),
            "update_required": sum(1 for x in enriched if x.get("status", {}).get("update_required")),
            "issue": sum(1 for x in enriched if x.get("status", {}).get("issue_count", 0)),
            "draft": sum(1 for x in enriched if x.get("status", {}).get("draft_count", 0)),
            "locked": sum(1 for x in enriched if x.get("status", {}).get("locked")),
            "disabled": sum(1 for x in enriched if x.get("status", {}).get("disabled")),
            "fast": True,
        }
        return {"query": query, "results": enriched, "stats": stats, "mode": "fast"}

    def backend_overview(self, query: str = "", limit: int = 50, include_disabled: bool = False) -> dict:
        data = self.search_with_status(query=query, limit=limit, include_disabled=include_disabled)
        rows = data.get("results", [])
        sorted_rows = sorted(rows, key=lambda x: (
            {"high": 0, "medium": 1, "low": 2, "none": 3}.get(x.get("status", {}).get("risk_level", "none"), 3),
            -int(x.get("status", {}).get("changed_file_count", 0) or 0),
            -int(x.get("status", {}).get("issue_count", 0) or 0),
        ))
        return {"stats": data.get("stats", {}), "rows": sorted_rows}

    def batch_governance(self, page_ids: list[str] | str, operation: str = "diagnose", author: str = "wiki_app") -> dict:
        if isinstance(page_ids, str):
            ids = [item.strip() for item in page_ids.split(",") if item.strip()]
        else:
            ids = [str(item).strip() for item in (page_ids or []) if str(item).strip()]
        results = []
        for page_id in ids:
            try:
                status = self.page_status_summary(page_id)
                if status.get("locked") or status.get("disabled"):
                    results.append({"page_id": page_id, "status": "skipped", "reason": "页面已锁定或已禁用", "summary": status})
                    continue
                if operation == "diagnose":
                    results.append({"page_id": page_id, "status": "ok", "result": self.diagnose_page(page_id)})
                elif operation == "check_update":
                    results.append({"page_id": page_id, "status": "ok", "result": self.page_update_hint(page_id)})
                elif operation == "draft_update":
                    results.append({"page_id": page_id, "status": "ok", "result": self.update_page_diff(page_id=page_id, author=author)})
                else:
                    results.append({"page_id": page_id, "status": "unknown_operation", "operation": operation})
            except Exception as exc:
                results.append({"page_id": page_id, "status": "error", "error": str(exc)})
        return {"operation": operation, "count": len(results), "results": results}

    def user_center_summary(self, root_path: str = "") -> dict:
        root = Path(root_path).resolve() if root_path else self.project_root
        allowed = self.project_root in [root, *root.parents] or root in [self.project_root, *self.project_root.parents]
        preview = None
        if root_path:
            try:
                preview = self.preview_user_folder_wikis(root_path=root_path)
            except Exception as exc:
                preview = {"error": str(exc)}
        base = self.user_files.user_center_summary(root_path=root_path)
        return {**base, "inside_project": allowed, "preview": preview}

    def _fast_status_from_row(self, row: dict) -> dict:
        page_id = str(row.get("page_id") or row.get("id") or row.get("path") or "")
        entity_type = str(row.get("entity_type") or row.get("type") or row.get("kind") or "页面")
        locked = bool(row.get("locked") or row.get("lock"))
        disabled = bool(row.get("disabled") or row.get("disable"))
        labels = []
        if disabled:
            labels.append({"type": "disabled", "label": "已禁用", "pane": "status"})
        if locked:
            labels.append({"type": "locked", "label": "已锁定", "pane": "status"})
        if not labels:
            labels.append({"type": "ok", "label": "正常", "pane": "overview"})
        return {
            "page_id": page_id,
            "entity_type": entity_type,
            "stage": "已发布",
            "locked": locked,
            "disabled": disabled,
            "risk_level": "low" if (locked or disabled) else "none",
            "update_required": False,
            "changed_file_count": 0,
            "issue_count": 0,
            "draft_count": 0,
            "has_unresolved_links": False,
            "graph_enabled": not disabled,
            "status_labels": labels,
            "fast": True,
        }

    def _fallback_graph(self, query: str = "", limit: int = 60, include_disabled: bool = False, reason: str = "") -> dict:
        try:
            rows = self.search(query=query, limit=limit, include_disabled=include_disabled)
        except Exception:
            rows = []
        nodes = []
        edges = []
        prev_id = ""
        for row in rows:
            page_id = str(row.get("page_id") or row.get("id") or row.get("path") or "")
            if not page_id:
                continue
            title = str(row.get("title") or row.get("name") or row.get("label") or page_id)
            entity_type = str(row.get("entity_type") or row.get("type") or "页面")
            nodes.append(
                {
                    "id": page_id,
                    "label": title,
                    "type": entity_type,
                    "page_id": page_id,
                    "summary": str(row.get("summary") or row.get("snippet") or ""),
                    "disabled": bool(row.get("disabled")),
                    "locked": bool(row.get("locked")),
                }
            )
            if prev_id:
                edges.append({"id": f"fallback-{len(edges)}", "source": prev_id, "target": page_id, "label": "相关"})
            prev_id = page_id
        return {
            "nodes": nodes,
            "edges": edges,
            "triples": [[edge["source"], edge["label"], edge["target"]] for edge in edges],
            "fallback": True,
            "reason": reason,
        }

    def _user_files_root(self) -> Path:
        return self.user_files._user_files_root()

    def _safe_user_path(self, relative_path: str = "") -> Path:
        return self.user_files._safe_user_path(relative_path)

    def user_file_tree(self, relative_path: str = "") -> dict:
        return self.user_files.user_file_tree(relative_path)

    def user_file_read(self, relative_path: str) -> dict:
        return self.user_files.user_file_read(relative_path)

    def user_file_write(self, relative_path: str, content: str = "") -> dict:
        return self.user_files.user_file_write(relative_path, content)

    def user_file_mkdir(self, relative_path: str) -> dict:
        return self.user_files.user_file_mkdir(relative_path)

    def user_file_delete(self, relative_path: str) -> dict:
        return self.user_files.user_file_delete(relative_path)


    def app_diagnostics(self) -> dict:
        status = self.server_status()
        graph_path = self.project_root / "src/wiki/store/knowledge_graph.json"
        memory_graph_path = data_root(self.project_root) / "indexes" / "graph.json"
        return {
            **status,
            "graph_exists": graph_path.exists(),
            "memory_graph_exists": memory_graph_path.exists(),
            "action_mode": "memory-native-compat",
            "ui_version": "memory_native_workbench_v1",
        }

    def page_update_hint(self, page_id: str) -> dict:
        page_id = _required(page_id, "page_id")
        hint = {
            "page_id": page_id,
            "requires_update": False,
            "changed_files": [],
            "suggested_actions": ["diff_update", "full_update"],
            "message": "未检测到依赖文件变化。",
        }
        try:
            status = self.page_file_status(page_id)
            files = status.get("files") or status.get("dependencies") or status.get("changed_files") or []
            changed = []
            if isinstance(files, list):
                for item in files:
                    if isinstance(item, dict):
                        state = str(item.get("status") or item.get("change") or item.get("state") or "").lower()
                        if state and state not in {"unchanged", "clean", "same", "ok", "未变化"}:
                            changed.append(item)
            if status.get("requires_update") or status.get("changed") or changed:
                hint.update(
                    {
                        "requires_update": True,
                        "changed_files": changed or files,
                        "message": f"检测到 {len(changed or files)} 个依赖文件可能发生变化，建议更新本页面。",
                    }
                )
            else:
                hint["raw_status"] = status
        except Exception as exc:
            hint.update(
                {
                    "requires_update": True,
                    "message": f"无法完整检查依赖文件，建议人工确认：{exc}",
                    "error": str(exc),
                }
            )
        return hint

    def update_page_full(self, page_id: str, requirements: str = "", author: str = "wiki_app") -> dict:
        return self.update_system_page_from_files(page_id=page_id, mode="full", requirements=requirements, author=author)

    def update_page_diff(self, page_id: str, requirements: str = "", author: str = "wiki_app") -> dict:
        return self.update_system_page_from_files(page_id=page_id, mode="diff", requirements=requirements, author=author)

    def preview_user_folder_wikis(self, root_path: str, author: str = "wiki_app") -> dict:
        return self.generate_user_folder_wikis(root_path=root_path, dry_run=True, author=author)

    def graph_neighbors(self, page_id: str, depth: int = 1, include_disabled: bool = False) -> dict:
        page_id = _required(page_id, "page_id")
        try:
            return self.memory_graph.graph_neighbors(note_id=page_id, depth=max(1, int(depth or 1)))
        except Exception:
            relations = self.page_scope_relations(page_id)
            return {"page_id": page_id, "nodes": [{"id": page_id, "label": page_id, "type": "page"}], "edges": [], "relations": relations}

    def batch_diagnose(self, query: str = "", limit: int = 20, include_disabled: bool = False) -> dict:
        pages = self.search(query=query, limit=limit, include_disabled=include_disabled)
        results = []
        for row in pages[: int(limit or 20)]:
            page_id = row.get("page_id") or row.get("id") or row.get("path")
            if not page_id:
                continue
            try:
                diagnosis = self.diagnose_page(page_id)
                issues = diagnosis.get("issues") or []
                results.append({"page_id": page_id, "title": row.get("title") or page_id, "issue_count": len(issues), "diagnosis": diagnosis})
            except Exception as exc:
                results.append({"page_id": page_id, "title": row.get("title") or page_id, "issue_count": 1, "error": str(exc)})
        return {"count": len(results), "results": results}



def _required(value: Any, name: str) -> str:
    value = str(value or "").strip()
    if not value:
        raise MissingRequiredParam(f"缺少必要参数：{name}")
    return value


def _loads(text: str, default: Any) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return default


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
