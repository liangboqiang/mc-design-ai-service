from __future__ import annotations

import json
from pathlib import Path

from .base import WorkbenchService
from wiki.page_parser import parse_chinese_page
from wiki.page_state import is_disabled_markdown, local_relations, page_scope


class WikiGraphService(WorkbenchService):
    def extract_knowledge_graph(self, *, include_disabled: bool = False, write_store: bool = True, include_graph: bool = False) -> dict:
        self.ensure()
        catalog = self.store.read_catalog()
        triples = []
        nodes = []
        for page_id, row in (catalog.get("pages") or {}).items():
            text = (self.project_root / str(row.get("path") or "")).read_text(encoding="utf-8")
            disabled = is_disabled_markdown(text)
            if disabled and not include_disabled:
                continue
            model = parse_chinese_page(text)
            nodes.append({
                "id": page_id,
                "title": row.get("title"),
                "entity_type": model.entity_type,
                "scope": page_scope(text),
                "disabled": disabled,
            })
            triples.append({"subject": page_id, "predicate": "实体类型", "object": model.entity_type or "未知"})
            triples.append({"subject": page_id, "predicate": "作用范围", "object": page_scope(text)})
            for link in model.links:
                triples.append({"subject": page_id, "predicate": "链接到", "object": link})
            for rel in local_relations(text):
                triples.append({"subject": page_id, "predicate": "局部关系", "object": rel})
            if model.fields.get("所属工具箱"):
                triples.append({"subject": page_id, "predicate": "属于工具箱", "object": str(model.fields.get("所属工具箱"))})
        graph = {"nodes": nodes, "triples": triples}
        if write_store:
            graph_path = self.project_root / "src/wiki/store/knowledge_graph.json"
            graph_path.parent.mkdir(parents=True, exist_ok=True)
            graph_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"node_count": len(nodes), "triple_count": len(triples), "sample_triples": triples[:50], "graph": graph if include_graph else None}

    def page_scope_relations(self, page_id: str) -> dict:
        self.ensure()
        row = self.page_row(page_id)
        text = (self.project_root / str(row.get("path") or "")).read_text(encoding="utf-8")
        model = parse_chinese_page(text)
        return {
            "page_id": page_id,
            "scope": page_scope(text),
            "local_relations": local_relations(text),
            "links": model.links,
            "disabled": is_disabled_markdown(text),
        }

    def graph_enhanced_search(self, query: str, *, limit: int = 10, include_disabled: bool = False) -> dict:
        graph = self.extract_knowledge_graph(include_disabled=include_disabled, write_store=False, include_graph=True)["graph"]
        q = str(query or "").lower()
        scored = []
        for node in graph["nodes"]:
            hay = " ".join([str(node.get("id")), str(node.get("title")), str(node.get("entity_type")), str(node.get("scope"))]).lower()
            score = hay.count(q) if q else 1
            related = [
                t for t in graph["triples"]
                if t["subject"] == node["id"] or str(t["object"]) == node["id"] or q in str(t["object"]).lower()
            ]
            score += len(related)
            if score > 0:
                scored.append((score, {
                    "id": node.get("id"),
                    "title": node.get("title"),
                    "entity_type": node.get("entity_type"),
                    "scope": node.get("scope"),
                    "disabled": node.get("disabled"),
                    "score": score,
                    "related_count": len(related),
                    "related_sample": related[:5],
                }))
        scored.sort(key=lambda item: (-item[0], item[1]["id"]))
        return {"query": query, "items": [row for _, row in scored[: int(limit)]]}
