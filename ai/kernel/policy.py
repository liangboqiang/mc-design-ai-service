from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class KernelPolicy:
    agent_id: str = "memory.native.kernel"
    mode: str = "runtime_preview"
    max_steps: int = 8
    tool_permission_level: int = 1
    allowed_tool_categories: tuple[str, ...] = field(default_factory=tuple)
    denied_tool_categories: tuple[str, ...] = field(default_factory=tuple)
    allowed_tools: tuple[str, ...] = field(default_factory=tuple)
    denied_tools: tuple[str, ...] = field(default_factory=tuple)
