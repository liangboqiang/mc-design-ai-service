from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class WikiNode:
    node_id: str
    title: str
    body: str
    summary: str
    source_path: str
    source_type: str  # system | business | user | generated
    node_kind_hint: str | None = None
    links: list[str] = field(default_factory=list)
    sections: dict[str, str] = field(default_factory=dict)
    runtime_block: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
