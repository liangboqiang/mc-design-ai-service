from __future__ import annotations

import json
from pathlib import Path

from .page_parser import parse_chinese_page

class WikiAliasIndex:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()

    def build(self, catalog: dict) -> dict:
        aliases: dict[str, list[str]] = {}
        for page_id, row in (catalog.get("pages") or {}).items():
            path = self.project_root / str(row.get("path") or "")
            names = {page_id, str(row.get("title") or "").strip()}
            if path.exists():
                model = parse_chinese_page(path.read_text(encoding="utf-8"))
                if model.entity_name:
                    names.add(model.entity_name)
                if model.unique_id:
                    names.add(model.unique_id)
                for key in ("别名", "关键词"):
                    value = model.fields.get(key)
                    if isinstance(value, list):
                        names.update(str(item).strip() for item in value)
                    elif value:
                        names.update(item.strip() for item in str(value).replace(",", "、").split("、"))
            for name in names:
                if not name or name == "待补充":
                    continue
                aliases.setdefault(name, [])
                if page_id not in aliases[name]:
                    aliases[name].append(page_id)
        return aliases

    @staticmethod
    def resolve(alias_map: dict, label: str) -> dict:
        hits = list(alias_map.get(label, []))
        if len(hits) == 1:
            return {"status": "resolved", "target": hits[0]}
        if len(hits) > 1:
            return {"status": "ambiguous", "targets": hits}
        return {"status": "missing", "target": ""}
