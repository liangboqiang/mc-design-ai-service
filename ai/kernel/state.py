from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Observation:
    task_brief: str
    attachments: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RuntimeStep:
    observation: str
    memory_view: Any
    capability_view: Any
    reply: Any
    tool_results: list[Any] = field(default_factory=list)


@dataclass(slots=True)
class AgentResult:
    reply: str
    proposal: Any = None
    memory_view: Any = None
    capability_view: Any = None
