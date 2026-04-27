from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from protocol.types import ToolSpec


@dataclass(slots=True)
class RuntimePaths:
    root: Path
    history_dir: Path
    state_dir: Path
    workspace_dir: Path
    inbox_dir: Path
    logs_dir: Path
    attachments_dir: Path


@dataclass(slots=True)
class EngineSettings:
    provider: str
    model: str
    api_key: str | None
    base_url: str | None
    user_id: str
    conversation_id: str
    task_id: str
    max_steps: int = 12
    history_keep_turns: int = 24
    auto_compact_threshold: int = 30_000
    max_prompt_chars: int = 18_000
    tool_permission_level: int = 1
    allowed_tool_categories: tuple[str, ...] = ()
    denied_tool_categories: tuple[str, ...] = ()
    allowed_tools: tuple[str, ...] = ()
    denied_tools: tuple[str, ...] = ()


@dataclass(slots=True)
class EngineContext:
    engine_id: str
    root_skill_id: str
    active_skill_id: str
    settings: EngineSettings
    paths: RuntimePaths
    agent_name: str = "ad-hoc"
    agent_context: str = ""


@dataclass(slots=True)
class RuntimeRequest:
    agent_id: str
    project_root: Path
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    user_id: str = "default_user"
    conversation_id: str = "default_conversation"
    task_id: str = "default_task"
    toolboxes: list[str] | None = None
    max_steps: int = 12
    storage_base: Path | None = None
    role_name: str | None = None
    policy: dict[str, Any] | None = None


@dataclass(slots=True)
class PromptPacket:
    system_prompt: str
    messages: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class ToolVisibility:
    tool_id: str
    installed: bool
    requested_by_skill: bool
    activation_passed: bool
    permission_passed: bool
    category_allowed: bool
    visible: bool
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ToolCard:
    tool_id: str
    title: str
    description: str
    input_schema: dict[str, Any]
    permission_level: int
    categories: tuple[str, ...]
    activation_mode: str
    safety: str = ""


@dataclass(slots=True)
class SurfaceSnapshot:
    visible_tools: list[ToolSpec]
    visible_skills: list[tuple[str, str]]
    visible_toolboxes: list[str]
    activated_skill_ids: list[str] = field(default_factory=list)
    governance_notes: list[str] = field(default_factory=list)
    activated_tools: list[dict[str, str | int]] = field(default_factory=list)
    visible_tool_cards: list[dict[str, Any]] = field(default_factory=list)
    reasons: list[ToolVisibility] = field(default_factory=list)
    memory_view: Any | None = None
    capability_view: Any | None = None
    observation: str = ""


@dataclass(slots=True)
class Event:
    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    scope: str = "session"
