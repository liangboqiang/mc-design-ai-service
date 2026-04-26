from __future__ import annotations

import json
from typing import Any


class WikiIndexWriter:
    """Persist the governance protocol read model into the wiki store."""

    def __init__(self, store):  # noqa: ANN001
        self.store = store

    def write(self, protocol_result) -> dict[str, Any]:  # noqa: ANN001
        self.store.ensure()
        self.store.write_index(protocol_result.to_index_payload())
        self.store.write_catalog(protocol_result.to_catalog_payload())
        self.store.write_graph(protocol_result.to_graph_payload())
        return {
            "root": str(self.store.root),
            "index_path": str(self.store.index_path),
            "catalog_path": str(self.store.catalog_path),
            "graph_path": str(self.store.graph_path),
            "entities": len(protocol_result.entities),
            "pages": len(protocol_result.pages),
        }

    @staticmethod
    def dumps(payload: dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False, indent=2)
