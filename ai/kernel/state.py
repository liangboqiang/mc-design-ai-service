from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Observation:
    task_brief: str
    attachments: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


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
class KernelSettings:
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


# Backwards-neutral alias for storage/session helpers. This is not a legacy runtime type.
EngineSettings = KernelSettings


@dataclass(slots=True)
class KernelRequest:
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
class KernelContext:
    engine_id: str
    root_skill_id: str
    active_skill_id: str
    settings: KernelSettings
    paths: RuntimePaths
    agent_name: str = "ad-hoc"
    agent_context: str = ""


@dataclass(slots=True)
class PromptPacket:
    system_prompt: str
    messages: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class ToolCall:
    call_id: str
    tool_id: str
    arguments: dict[str, Any]


@dataclass(slots=True)
class ParsedReply:
    assistant_message: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw_text: str = ""
    memory_requests: list[Any] = field(default_factory=list)
    proposal_hints: list[Any] = field(default_factory=list)


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


@dataclass(slots=True)
class Event:
    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    scope: str = "session"


@dataclass(slots=True)
class KernelRuntimeState:
    installed_toolboxes: dict[str, Any] = field(default_factory=dict)
    tool_results: list[str] = field(default_factory=list)
    fault_history: list[str] = field(default_factory=list)
    step: int = 0
    last_tool_result: str = ""
    last_memory_view: Any | None = None
    last_capability_view: Any | None = None
