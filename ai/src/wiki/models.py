from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class WikiTask:
    task_id: str
    page_id: str
    source_id: str
    source_path: str
    source_uri: str
    source_kind: str
    title_hint: str
    prompt: str
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class WikiPage:
    page_id: str
    source_id: str
    title: str
    summary: str
    key_points: list[str]
    source_kind: str
    source_path: str
    source_uri: str
    source_hash: str
    tags: list[str]
    updated_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_catalog_entry(self) -> dict[str, Any]:
        return {
            "page_id": self.page_id,
            "source_id": self.source_id,
            "title": self.title,
            "summary": self.summary,
            "key_points": self.key_points,
            "source_kind": self.source_kind,
            "source_path": self.source_path,
            "source_uri": self.source_uri,
            "source_hash": self.source_hash,
            "tags": self.tags,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }
