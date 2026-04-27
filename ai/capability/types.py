from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CapabilitySpec:
    capability_id: str
    kind: str
    title: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    permission_level: int = 1
    categories: list[str] = field(default_factory=list)
    executor_ref: str | None = None
    safety: str = ""
    source_note_id: str | None = None
    activation_mode: str = "skill"
    activation_rules: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CapabilityView:
    visible_skills: list[CapabilitySpec] = field(default_factory=list)
    visible_tools: list[CapabilitySpec] = field(default_factory=list)
    visible_workflows: list[CapabilitySpec] = field(default_factory=list)
    activation_reasons: list[str] = field(default_factory=list)
    denied_reasons: list[str] = field(default_factory=list)
    reasons_by_capability: dict[str, list[str]] = field(default_factory=dict)
