from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

JsonDict = dict[str, Any]
ToolExecutor = Callable[[JsonDict], str]


@dataclass(slots=True)
class ToolSpec:
    """Executable tool contract exposed to the Agent loop.

    A ToolSpec is assembled from a Tool Wiki Page plus a Python executor.
    """

    tool_id: str
    title: str
    description: str
    input_schema: JsonDict
    executor: ToolExecutor | None
    toolbox: str
    detail: str = ""
    visible: bool = True
    tags: tuple[str, ...] = ()
    output_schema: JsonDict = field(default_factory=dict)
    permission_level: int = 1
    categories: tuple[str, ...] = ()
    activation_mode: str = "skill"
    activation_rules: tuple[str, ...] = ()
    priority: int = 50
    safety: str = ""
    context_hint: str = ""
    source_node: str = ""


@dataclass(slots=True)
class ToolCall:
    call_id: str
    tool_id: str
    arguments: JsonDict


@dataclass(slots=True)
class LLMResponse:
    assistant_message: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw_text: str = ""


@dataclass(slots=True)
class ToolResult:
    ok: bool
    tool_id: str
    content: str
    raw_result: Any = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ToolboxDescriptor:
    toolbox_name: str
    module: str
    class_name: str
    discoverable: bool = True
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ToolboxSpec:
    toolbox_id: str
    title: str
    module: str
    class_name: str
    tool_ids: list[str] = field(default_factory=list)
    category: str = ""
    source_node: str = ""


@dataclass(slots=True)
class AgentSpec:
    agent_id: str
    title: str
    root_skill: str
    toolboxes: list[str] = field(default_factory=list)
    context: str = ""
    llm: dict[str, Any] = field(default_factory=dict)
    policy: dict[str, Any] = field(default_factory=dict)
    source_node: str = ""

    @property
    def name(self) -> str:
        return self.agent_id

    def installation_names(self) -> list[str]:
        seen: set[str] = set()
        rows: list[str] = []
        for item in self.toolboxes:
            normalized = str(item).strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                rows.append(normalized)
        return rows


@dataclass(slots=True)
class SkillSpec:
    skill_id: str
    title: str
    summary: str = ""
    context: str = ""
    child_skills: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    knowledge_nodes: list[str] = field(default_factory=list)
    source_node: str = ""
    markdown_body: str = ""
    source_path: str = ""

    @property
    def name(self) -> str:
        return self.title

    @property
    def description(self) -> str:
        return self.summary

    @property
    def children(self) -> list[str]:
        return self.child_skills


@dataclass(slots=True)
class ServiceSpec:
    service_id: str
    title: str
    source_node: str = ""


@dataclass(slots=True)
class ProtocolDiagnostic:
    level: str  # error | warning | info
    node_id: str
    message: str
    repair_hint: str = ""
    field: str = ""


@dataclass(slots=True)
class ProtocolGraph:
    edges: list[dict[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class ProtocolView:
    agents: dict[str, AgentSpec] = field(default_factory=dict)
    skills: dict[str, SkillSpec] = field(default_factory=dict)
    toolboxes: dict[str, ToolboxSpec] = field(default_factory=dict)
    tools: dict[str, ToolSpec] = field(default_factory=dict)
    services: dict[str, ServiceSpec] = field(default_factory=dict)
    graph: ProtocolGraph = field(default_factory=ProtocolGraph)
    diagnostics: list[ProtocolDiagnostic] = field(default_factory=list)

    def errors(self) -> list[ProtocolDiagnostic]:
        return [d for d in self.diagnostics if d.level == "error"]
