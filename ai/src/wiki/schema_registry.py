from __future__ import annotations

import re
from pathlib import Path

class WikiSchemaRegistry:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.schema_root = self.project_root / "src/wiki/schema"

    def schema_page_path(self, entity_type: str) -> Path:
        key = self._key(entity_type)
        return self.schema_root / key / "wiki.md"

    def read_schema(self, entity_type: str) -> dict:
        path = self.schema_page_path(entity_type)
        if not path.exists():
            path = self.schema_root / "common" / "wiki.md"
        text = path.read_text(encoding="utf-8")
        return {
            "entity_type": entity_type,
            "schema_key": path.parent.name,
            "source_path": path.relative_to(self.project_root).as_posix(),
            "markdown": text,
            "required_fields": self.required_fields_from_text(text),
            "optional_fields": self.optional_fields_from_text(text),
        }

    def required_fields(self, entity_type: str) -> list[str]:
        return self.read_schema(entity_type)["required_fields"]

    def optional_fields(self, entity_type: str) -> list[str]:
        return self.read_schema(entity_type)["optional_fields"]

    def required_fields_from_text(self, text: str) -> list[str]:
        return self._list_section(text, "必填字段")

    def optional_fields_from_text(self, text: str) -> list[str]:
        return self._list_section(text, "可选字段")

    def _list_section(self, text: str, title: str) -> list[str]:
        match = re.search(rf"^\\s*##\\s+{re.escape(title)}\\s*(.*?)(?=\\n\\s*##\\s+|\\Z)", text, flags=re.S | re.M)
        if not match:
            return []
        rows = []
        for line in match.group(1).splitlines():
            stripped = line.strip()
            if stripped.startswith("- "):
                rows.append(stripped[2:].strip())
        return rows

    def _key(self, entity_type: str) -> str:
        mapping = {
            "工具": "tool",
            "工具箱": "toolbox",
            "技能": "skill",
            "智能体": "agent",
            "元结构": "common",
            "系统页面": "common",
            "业务知识": "common",
            "tool": "tool",
            "toolbox": "toolbox",
            "skill": "skill",
            "agent": "agent",
        }
        return mapping.get(str(entity_type), "common")
