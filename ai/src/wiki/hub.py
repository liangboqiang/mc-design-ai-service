from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from wiki.adapter_bridge import WikiAdapterBridge
from wiki.render import WikiLinkRenderer
from wiki.search import WikiSearcher
from wiki.store import WikiStore
from wiki.alias_index import WikiAliasIndex
from wiki.page_state import is_disabled_markdown, is_locked_markdown, local_relations, page_scope


ATTACHMENT_INGEST_STATE = "attachment_ingest.json"


class WikiHub:
    """Unified Wiki Hub for runtime search, read, answer, refresh, and attachment ingest."""

    def __init__(self, *, project_root: Path, registry=None, session=None):  # noqa: ANN001
        self.project_root = Path(project_root).resolve()
        self.registry = registry
        self.session = session
        self.store = WikiStore(self.project_root)
        self.wiki_guard = None

    def bind_permission_guard(self, wiki_guard) -> None:  # noqa: ANN001
        self.wiki_guard = wiki_guard

    def ensure_store(self) -> None:
        self.store.ensure()
        if not (self.store.read_catalog().get("pages") or {}):
            self.refresh_system()

    def refresh_system(self) -> str:
        self.store.ensure()
        nodes = WikiAdapterBridge(self.project_root).iter_nodes()
        node_texts = {
            node.node_id: self._read_repo_text(node.source_path)
            for node in nodes
        }
        disabled_nodes = {node_id for node_id, text in node_texts.items() if is_disabled_markdown(text)}
        entities = {
            node.node_id: {
                "kind": node.node_kind_hint or "knowledge",
                "title": node.title,
                "summary": node.summary,
                "path": node.source_path,
                "source_type": node.source_type,
                "links": node.links,
                "locked": is_locked_markdown(node_texts.get(node.node_id, "")),
                "disabled": node.node_id in disabled_nodes,
                "scope": page_scope(node_texts.get(node.node_id, "")),
                "local_relations": local_relations(node_texts.get(node.node_id, "")),
            }
            for node in nodes
        }
        catalog = {
            "pages": {
                node.node_id: {
                    "title": node.title,
                    "summary": node.summary,
                    "path": node.source_path,
                    "source_type": node.source_type,
                    "locked": is_locked_markdown(node_texts.get(node.node_id, "")),
                    "disabled": node.node_id in disabled_nodes,
                    "scope": page_scope(node_texts.get(node.node_id, "")),
                }
                for node in nodes
            }
        }
        aliases = WikiAliasIndex(self.project_root).build(catalog)
        graph = {
            "edges": [
                {"from": node.node_id, "to": link, "kind": "wiki_link"}
                for node in nodes
                if node.node_id not in disabled_nodes
                for link in node.links
            ]
        }
        self.store.write_index({"entities": entities, "aliases": aliases})
        self.store.write_catalog(catalog)
        self.store.write_graph(graph)
        job_id = f"refresh_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        self.store.write_job(job_id, {"job_id": job_id, "kind": "refresh_system", "node_count": len(nodes)})
        return json.dumps({"status": "ok", "nodes": len(nodes), "root": str(self.store.root)}, ensure_ascii=False, indent=2)

    def ingest_user_files(self, files: list[dict[str, Any]] | None) -> str:
        self.store.ensure()
        files = files or []
        created: list[dict[str, str]] = []
        for index, item in enumerate(files, start=1):
            name = str(item.get("name") or item.get("filename") or item.get("path") or f"user_file_{index}")
            uri = str(item.get("url") or item.get("path") or "")
            status, stored_path = self._store_attachment(name=name, uri=uri)
            created.append({"name": name, "status": status, "stored_path": stored_path})
        result_text = json.dumps({"status": "ok", "files": created}, ensure_ascii=False, indent=2)
        if self.session is not None:
            snapshot = {
                "updated_at": self._utc_now(),
                "file_count": len(files),
                "file_names": [str(item.get("name") or "") for item in files],
                "result": self._coerce_payload(result_text),
            }
            self.session.write_state_json(ATTACHMENT_INGEST_STATE, snapshot)
        return result_text

    def search(self, query: str, limit: int = 20) -> str:
        self.ensure_store()
        rows = WikiSearcher(store=self.store, read_text=self._read_repo_text).search(query, limit=limit)
        if self.wiki_guard is not None:
            rows = self.wiki_guard.filter_rows(rows)
        return json.dumps(rows, ensure_ascii=False, indent=2)

    def read_page(self, page_id: str) -> str:
        self.ensure_store()
        if self.wiki_guard is not None:
            self.wiki_guard.require_read_page(page_id)
        catalog = self.store.read_catalog()
        row = (catalog.get("pages") or {}).get(page_id)
        if row is None:
            return f"Wiki Page not found: {page_id}"
        text = self._read_repo_text(str(row.get("path") or ""))
        return WikiLinkRenderer(index=self.store.read_index(), catalog=catalog).render(text)

    def read_source(self, page_id: str) -> str:
        self.ensure_store()
        catalog = self.store.read_catalog()
        row = (catalog.get("pages") or {}).get(page_id)
        if row is None:
            return f"Wiki Page not found: {page_id}"
        return self._read_repo_text(str(row.get("path") or ""))

    def answer(self, query: str, limit: int = 5) -> str:
        rows = json.loads(self.search(query, limit=limit))
        if not rows:
            return f"No wiki pages matched query: {query}"
        body = [f"# Wiki answer for: {query}", ""]
        for row in rows:
            body.append(f"## {row.get('title')}")
            body.append(str(row.get("summary") or ""))
            body.append(f"- Source: {row.get('path') or row.get('source_path')}")
            body.append("")
        return "\n".join(body).strip()

    def system_brief(self) -> str:
        self.ensure_store()
        catalog = self.store.read_catalog()
        return f"Unified Wiki Hub: {len(catalog.get('pages') or {})} Wiki Page node(s) searchable."

    def state_fragments(self) -> list[str]:
        if self.session is None:
            return []
        snapshot = self.session.read_state_json(ATTACHMENT_INGEST_STATE, {}) or {}
        if not snapshot:
            return []
        names = ", ".join(name for name in snapshot.get("file_names", []) if name) or "(unnamed)"
        return [
            (
                "Wiki attachment state -> "
                f"updated_at={snapshot.get('updated_at', '')}; "
                f"file_count={snapshot.get('file_count', 0)}; "
                f"files={names}"
            )
        ]

    def _read_repo_text(self, rel_path: str) -> str:
        path = (self.project_root / rel_path).resolve()
        if not path.exists():
            return f"Missing path: {rel_path}"
        return path.read_text(encoding="utf-8")

    def _store_attachment(self, *, name: str, uri: str) -> tuple[str, str]:
        target = self.store.attachments_dir / name
        parsed = urlparse(uri)
        try:
            if parsed.scheme in {"http", "https"}:
                import requests

                response = requests.get(uri, timeout=20)
                response.raise_for_status()
                target.write_bytes(response.content)
                return "stored", str(target)
            source = Path(uri.replace("file://", "")).expanduser().resolve()
            if source.exists():
                shutil.copy2(source, target)
                return "stored", str(target)
            return "metadata_only", ""
        except Exception as exc:  # noqa: BLE001
            return f"error:{exc.__class__.__name__}", ""

    @staticmethod
    def _coerce_payload(text: str) -> Any:
        try:
            return json.loads(text)
        except Exception:  # noqa: BLE001
            return {"status": "opaque", "raw_text": text}

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
