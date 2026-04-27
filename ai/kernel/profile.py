from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kernel.policy import KernelPolicy


@dataclass(slots=True)
class SkillProfile:
    skill_id: str
    title: str
    summary: str = ""
    refs: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    source_note_id: str = ""
    markdown_body: str = ""
    source_path: str = ""


@dataclass(slots=True)
class AgentProfile:
    agent_id: str
    title: str
    role: str
    root_skill_id: str
    toolboxes: list[str] = field(default_factory=list)
    llm: dict[str, Any] = field(default_factory=dict)
    policy: KernelPolicy = field(default_factory=KernelPolicy)
    memory_scope: dict[str, Any] = field(default_factory=dict)
    capability_scope: dict[str, Any] = field(default_factory=dict)
    source_note_id: str = ""
