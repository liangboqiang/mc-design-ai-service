from __future__ import annotations


class WikiLinkResolver:
    def __init__(self, *, index: dict, catalog: dict):
        self.index = dict(index.get("entities") or {})
        self.catalog = dict(catalog.get("pages") or {})
        self.aliases = dict(index.get("aliases") or {})

    def parse_target(self, raw: str) -> tuple[str, str]:
        text = str(raw or "").strip()
        if "|" in text:
            label, target = text.split("|", 1)
            return label.strip(), target.strip()
        return text, text

    def resolve(self, raw: str) -> dict:
        label, target = self.parse_target(raw)
        if target in self.catalog or target in self.index:
            return {"status": "resolved", "label": label, "target": target}
        hits = list(self.aliases.get(target, []))
        if len(hits) == 1:
            return {"status": "resolved", "label": label, "target": hits[0]}
        if len(hits) > 1:
            return {"status": "ambiguous", "label": label, "target": "", "targets": hits}
        return {"status": "missing", "label": label, "target": target}

    def describe(self, target: str) -> dict[str, str] | None:
        resolved = self.resolve(target)
        if resolved.get("status") != "resolved":
            return None
        target_id = str(resolved.get("target") or target)
        row = self.catalog.get(target_id) or self.index.get(target_id)
        if row is None:
            return None
        title = str(row.get("title") or resolved.get("label") or target_id)
        summary = str(row.get("summary") or "").strip()
        path = str(row.get("path") or "")
        return {"title": title, "summary": summary, "path": path, "page_id": target_id, "label": str(resolved.get("label") or title)}
