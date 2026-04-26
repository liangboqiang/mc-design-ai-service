from __future__ import annotations

from pathlib import Path

from .base import WorkbenchService
from .draft_service import WikiDraftService
from wiki.page_state import is_disabled_markdown, is_locked_markdown


class WikiDiagnosisService(WorkbenchService):
    def diagnose_page(self, page_id: str) -> dict:
        self.ensure()
        schema_check = self._schema().check_page_schema(page_id)
        file_status = self._files().page_file_status(page_id)
        graph_scope = self._graph().page_scope_relations(page_id)
        row = self.page_row(page_id)
        text = (self.project_root / str(row.get("path") or "")).read_text(encoding="utf-8")
        locked = is_locked_markdown(text)
        disabled = is_disabled_markdown(text)
        suggestions = []
        if locked or disabled:
            suggestions.append({"action_id": "none", "title": "页面处于锁定或禁用状态", "description": "禁止自动修复，请先人工确认锁定和禁用原因。", "enabled": False})
        else:
            if schema_check.get("missing_fields"):
                suggestions.append({"action_id": "normalize_page_to_chinese", "title": "规范化中文页面", "description": "补充元结构治理记录并生成草稿。", "enabled": True})
            if file_status.get("requires_update"):
                suggestions.append({"action_id": "update_from_files", "title": "根据依赖文件差异更新页面", "description": file_status.get("update_hint"), "enabled": True})
            if not graph_scope.get("scope") or graph_scope.get("scope") == "当前页面及直接关联对象":
                suggestions.append({"action_id": "add_scope_relations", "title": "补充作用范围和局部关系", "description": "为前端小图谱补充页面局部关系描述。", "enabled": True})
            if schema_check.get("links", {}).get("missing") or schema_check.get("links", {}).get("ambiguous"):
                suggestions.append({"action_id": "link_governance_note", "title": "生成链接治理提示", "description": "把断链和歧义链接整理为修复草稿。", "enabled": True})
        status = "blocked" if locked or disabled else "warning" if suggestions else "healthy"
        return {
            "page_id": page_id,
            "status": status,
            "locked": locked,
            "disabled": disabled,
            "schema_check": schema_check,
            "file_status": file_status,
            "graph_scope": graph_scope,
            "suggestions": suggestions,
        }

    def apply_diagnosis_fix(self, page_id: str, action_id: str, *, author: str = "wiki_agent") -> dict:
        diagnosis = self.diagnose_page(page_id)
        if diagnosis["locked"] or diagnosis["disabled"]:
            return {"ok": False, "message": "页面处于锁定或禁用状态，禁止自动修复。", "diagnosis": diagnosis}
        if action_id == "normalize_page_to_chinese":
            return {"ok": True, "result": self._schema().normalize_page_to_chinese_draft(page_id, author=author)}
        if action_id == "update_from_files":
            return {"ok": True, "result": self._files().update_system_page_from_files(page_id, mode="diff", author=author)}
        if action_id == "add_scope_relations":
            row = self.page_row(page_id)
            path = self.project_root / str(row.get("path") or "")
            text = path.read_text(encoding="utf-8")
            patch = "\n\n## 局部图谱提示\n\n- 作用范围：当前页面、直接关联页面和同目录依赖文件。\n- 局部关系：页面、依赖文件、链接实体之间的关系可用于前端小图展示。\n"
            draft = WikiDraftService(self.project_root).save_draft(page_id, text.rstrip() + patch, author=author, reason="补充局部图谱提示")
            return {"ok": True, "result": {"draft": draft}}
        if action_id == "link_governance_note":
            links = diagnosis["schema_check"].get("links", {})
            note = "\n\n## 链接治理建议\n\n"
            for item in links.get("missing", []):
                note += f"- 断链：{item.get('raw')}，建议搜索对应实体后改为显式目标链接。\n"
            for item in links.get("ambiguous", []):
                note += f"- 歧义链接：{item.get('raw')}，候选目标：{item.get('targets')}。\n"
            row = self.page_row(page_id)
            text = (self.project_root / str(row.get("path") or "")).read_text(encoding="utf-8")
            draft = WikiDraftService(self.project_root).save_draft(page_id, text.rstrip() + note, author=author, reason="链接治理建议")
            return {"ok": True, "result": {"draft": draft}}
        return {"ok": False, "message": f"未知修复动作：{action_id}", "diagnosis": diagnosis}

    def _schema(self):
        return self._workbench().schema

    def _files(self):
        return self._workbench().files

    def _graph(self):
        return self._workbench().graph

    def _workbench(self):
        from wiki.workbench import WikiWorkbench
        return WikiWorkbench(self.project_root)
