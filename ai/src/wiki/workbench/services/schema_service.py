from __future__ import annotations

from pathlib import Path

from .base import WorkbenchService
from .draft_service import WikiDraftService
from wiki.alias_index import WikiAliasIndex
from wiki.page_parser import parse_chinese_page
from wiki.schema_registry import WikiSchemaRegistry


SECTION_FIELDS = {
    "摘要", "内容", "关联页面", "版本信息", "工具说明", "适用场景", "输入说明", "输出说明", "注意事项",
    "工具箱说明", "包含工具", "使用边界", "技能目标", "使用工具", "执行流程",
    "智能体使命", "能力范围", "可用技能", "可用工具箱", "安全边界",
}


class WikiSchemaService(WorkbenchService):
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.registry = WikiSchemaRegistry(project_root)

    def read_schema(self, entity_type: str) -> dict:
        return self.registry.read_schema(entity_type)

    def check_page_schema(self, page_id: str) -> dict:
        self.ensure()
        row = self.page_row(page_id)
        path = self.project_root / str(row.get("path") or "")
        text = path.read_text(encoding="utf-8")
        model = parse_chinese_page(text)
        required = self.registry.required_fields(model.entity_type or "系统页面")
        missing: list[str] = []
        for field in required:
            if field in SECTION_FIELDS:
                if field == "摘要":
                    ok = "摘要：" in text
                else:
                    ok = f"## {field}" in text
                if not ok:
                    missing.append(field)
            elif field not in model.fields or str(model.fields.get(field) or "").strip() in {"", "待补充"}:
                missing.append(field)
        links = self.resolve_page_links(page_id)
        status = "healthy" if not missing and not links["missing"] and not links["ambiguous"] else "warning"
        return {
            "page_id": page_id,
            "entity_type": model.entity_type,
            "entity_name": model.entity_name,
            "unique_id": model.unique_id,
            "status": status,
            "required_fields": required,
            "missing_fields": missing,
            "links": links,
        }

    def resolve_page_links(self, page_id: str) -> dict:
        self.ensure()
        catalog = self.store.read_catalog()
        aliases = WikiAliasIndex(self.project_root).build(catalog)
        row = self.page_row(page_id)
        text = (self.project_root / str(row.get("path") or "")).read_text(encoding="utf-8")
        model = parse_chinese_page(text)
        resolved = []
        ambiguous = []
        missing = []
        for raw in model.links:
            result = WikiAliasIndex.resolve(aliases, raw)
            item = {"raw": raw, **result}
            if result["status"] == "resolved":
                resolved.append(item)
            elif result["status"] == "ambiguous":
                ambiguous.append(item)
            else:
                missing.append(item)
        return {"resolved": resolved, "ambiguous": ambiguous, "missing": missing}

    def alias_query(self, label: str) -> dict:
        self.ensure()
        aliases = WikiAliasIndex(self.project_root).build(self.store.read_catalog())
        return {"label": label, **WikiAliasIndex.resolve(aliases, label)}

    def normalize_page_to_chinese_draft(self, page_id: str, *, author: str = "wiki_agent") -> dict:
        check = self.check_page_schema(page_id)
        row = self.page_row(page_id)
        path = self.project_root / str(row.get("path") or "")
        text = path.read_text(encoding="utf-8")
        if check["status"] == "healthy":
            normalized = text.rstrip() + "\n"
        else:
            normalized = (
                text.rstrip()
                + "\n\n## 格式治理记录\n\n"
                + "- 页面已进入中文 Wiki 元结构检查流程。\n"
                + "- 缺失字段：" + "、".join(check["missing_fields"] or ["无"]) + "\n"
            )
        draft = WikiDraftService(self.project_root).save_draft(page_id, normalized, author=author, reason="中文 Wiki 格式治理")
        return {"draft": draft, "check": check}
