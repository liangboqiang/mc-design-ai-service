from __future__ import annotations

import json
from pathlib import Path

from wiki.workbench import WikiWorkbench


class WikiAppToolbox:
    """Wiki governance and Git-backed version management tools.

    These are Wiki semantic tools, not raw Git tools.
    """

    toolbox_name = "wiki_app"
    tags = ("wiki", "governance", "version")

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root.resolve() if workspace_root else None
        self.runtime = None
        self.workbench: WikiWorkbench | None = None

    def bind_runtime(self, runtime, tool_lookup=None) -> None:  # noqa: ANN001
        self.runtime = runtime
        self.workbench = WikiWorkbench(runtime.registry.project_root)

    def spawn(self, workspace_root: Path) -> "WikiAppToolbox":
        return WikiAppToolbox(workspace_root=workspace_root)

    def executors(self):
        return {
            "wiki_app.check_truth_status": self._exec_check_truth_status,
            "wiki_app.save_draft": self._exec_save_draft,
            "wiki_app.diff_draft": self._exec_diff_draft,
            "wiki_app.publish_draft": self._exec_publish_draft,
            "wiki_app.page_history": self._exec_page_history,
            "wiki_app.read_version": self._exec_read_version,
            "wiki_app.diff_versions": self._exec_diff_versions,
            "wiki_app.create_rollback_draft": self._exec_create_rollback_draft,
            "wiki_app.release_history": self._exec_release_history,
            "wiki_app.release_detail": self._exec_release_detail,
                "wiki_app.read_schema": self._exec_read_schema,
                "wiki_app.check_page_schema": self._exec_check_page_schema,
                "wiki_app.resolve_page_links": self._exec_resolve_page_links,
                "wiki_app.alias_query": self._exec_alias_query,
                "wiki_app.normalize_page_to_chinese": self._exec_normalize_page_to_chinese,

                "wiki_app.page_file_status": self._exec_page_file_status,
                "wiki_app.update_system_page_from_files": self._exec_update_system_page_from_files,
                "wiki_app.generate_user_folder_wikis": self._exec_generate_user_folder_wikis,
                "wiki_app.extract_knowledge_graph": self._exec_extract_knowledge_graph,
                "wiki_app.graph_enhanced_search": self._exec_graph_enhanced_search,
                "wiki_app.page_scope_relations": self._exec_page_scope_relations,
                "wiki_app.diagnose_page": self._exec_diagnose_page,
                "wiki_app.apply_diagnosis_fix": self._exec_apply_diagnosis_fix,
        }

    @property
    def wb(self) -> WikiWorkbench:
        if self.workbench is None:
            raise RuntimeError("WikiAppToolbox is not bound to runtime.")
        return self.workbench

    def _json(self, payload) -> str:  # noqa: ANN001
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def _exec_check_truth_status(self, args: dict):
        return self._json(self.wb.truth.truth_status(
            args.get("page_id"),
            include_worktree=bool(args.get("include_worktree", True)),
        ))

    def _exec_save_draft(self, args: dict):
        return self._json(self.wb.draft.save_draft(
            str(args["page_id"]),
            str(args["markdown"]),
            author=str(args.get("author") or "admin"),
            reason=str(args.get("reason") or ""),
        ))

    def _exec_diff_draft(self, args: dict):
        return self._json(self.wb.draft.diff_draft(str(args["draft_id"])))

    def _exec_publish_draft(self, args: dict):
        return self._json(self.wb.publish.publish_draft(
            str(args["draft_id"]),
            message=str(args.get("message") or ""),
            author=str(args.get("author") or "admin"),
            run_health_check=bool(args.get("run_health_check", True)),
        ))

    def _exec_page_history(self, args: dict):
        return self._json(self.wb.version.page_history(
            str(args["page_id"]),
            limit=int(args.get("limit") or 20),
        ))

    def _exec_read_version(self, args: dict):
        return self._json(self.wb.version.read_version(
            str(args["page_id"]),
            str(args["commit"]),
        ))

    def _exec_diff_versions(self, args: dict):
        return self._json(self.wb.version.diff_versions(
            str(args["page_id"]),
            str(args["from_commit"]),
            str(args["to_commit"]),
        ))

    def _exec_create_rollback_draft(self, args: dict):
        return self._json(self.wb.version.create_rollback_draft(
            str(args["page_id"]),
            str(args["commit"]),
            author=str(args.get("author") or "admin"),
            reason=str(args.get("reason") or ""),
        ))

    def _exec_release_history(self, args: dict):
        return self._json(self.wb.release.release_history(
            limit=int(args.get("limit") or 50),
            page_id=args.get("page_id"),
        ))

    def _exec_release_detail(self, args: dict):
        return self._json(self.wb.release.release_detail(str(args["release_id"])))


    def _exec_read_schema(self, args: dict):
        return self._json(self.wb.schema.read_schema(str(args.get("entity_type") or "系统页面")))

    def _exec_check_page_schema(self, args: dict):
        return self._json(self.wb.schema.check_page_schema(str(args["page_id"])))

    def _exec_resolve_page_links(self, args: dict):
        return self._json(self.wb.schema.resolve_page_links(str(args["page_id"])))

    def _exec_alias_query(self, args: dict):
        return self._json(self.wb.schema.alias_query(str(args["label"])))

    def _exec_normalize_page_to_chinese(self, args: dict):
        return self._json(self.wb.schema.normalize_page_to_chinese_draft(
            str(args["page_id"]),
            author=str(args.get("author") or "wiki_agent"),
        ))


    def _exec_page_file_status(self, args: dict):
        return self._json(self.wb.files.page_file_status(str(args["page_id"])))

    def _exec_update_system_page_from_files(self, args: dict):
        return self._json(self.wb.files.update_system_page_from_files(
            str(args["page_id"]),
            mode=str(args.get("mode") or "diff"),
            requirements=str(args.get("requirements") or ""),
            author=str(args.get("author") or "wiki_agent"),
        ))

    def _exec_generate_user_folder_wikis(self, args: dict):
        return self._json(self.wb.files.generate_user_folder_wikis(
            str(args["root_path"]),
            dry_run=bool(args.get("dry_run", True)),
            author=str(args.get("author") or "wiki_agent"),
        ))

    def _exec_extract_knowledge_graph(self, args: dict):
        return self._json(self.wb.graph.extract_knowledge_graph(
            include_disabled=bool(args.get("include_disabled", False)),
            write_store=bool(args.get("write_store", True)),
            include_graph=bool(args.get("include_graph", False)),
        ))

    def _exec_graph_enhanced_search(self, args: dict):
        return self._json(self.wb.graph.graph_enhanced_search(
            str(args.get("query") or args.get("q") or ""),
            limit=int(args.get("limit") or 10),
            include_disabled=bool(args.get("include_disabled", False)),
        ))

    def _exec_page_scope_relations(self, args: dict):
        return self._json(self.wb.graph.page_scope_relations(str(args["page_id"])))

    def _exec_diagnose_page(self, args: dict):
        return self._json(self.wb.diagnosis.diagnose_page(str(args["page_id"])))

    def _exec_apply_diagnosis_fix(self, args: dict):
        return self._json(self.wb.diagnosis.apply_diagnosis_fix(
            str(args["page_id"]),
            str(args["action_id"]),
            author=str(args.get("author") or "wiki_agent"),
        ))
