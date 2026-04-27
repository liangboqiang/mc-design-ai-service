from __future__ import annotations

from pathlib import Path
import re

from memory.store import NoteStore
from .types import (
    AgentSpec,
    ProtocolDiagnostic,
    ProtocolGraph,
    ProtocolView,
    SkillSpec,
    ToolSpec,
    ToolboxSpec,
)


LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
CODE_RE = re.compile(r"`([^`]+)`")


class ProtocolCompiler:
    """Compatibility compiler: Memory Notes -> legacy ProtocolView.

    Runtime still consumes ProtocolView, but the source of truth is now
    MemoryNote/note.md with wiki.md compatibility handled by Memory.
    """

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.note_store = NoteStore(self.project_root)

    @classmethod
    def from_memory(cls, project_root: Path) -> "ProtocolCompiler":
        return cls(project_root)

    @classmethod
    def from_wiki(cls, project_root: Path) -> "ProtocolCompiler":
        return cls.from_memory(project_root)

    def compile(self) -> ProtocolView:
        view = ProtocolView()
        notes = self.note_store.list_notes()
        note_index = {note.note_id: note for note in notes}
        for note in notes:
            note_type = self._note_type(note)
            if note_type == "agent":
                self._add_agent(view, note)
            elif note_type == "skill":
                self._add_skill(view, note, note_index)
            elif note_type == "toolbox":
                self._add_toolbox(view, note)
            elif note_type == "tool":
                self._add_tool(view, note)
        self._backfill_toolboxes(view)
        self._validate(view)
        self._build_graph(view, notes)
        return view

    def _add_agent(self, view: ProtocolView, note) -> None:  # noqa: ANN001
        fields = dict(note.fields or {})
        llm = {
            key: fields[key]
            for key in ("provider", "model", "api_key", "base_url")
            if key in fields and str(fields.get(key)).strip()
        }
        policy = {
            key: fields[key]
            for key in (
                "max_prompt_chars",
                "tool_permission_level",
                "allowed_tool_categories",
                "denied_tool_categories",
                "allowed_tools",
                "denied_tools",
            )
            if key in fields
        }
        agent_id = str(fields.get("id") or note.note_id.rsplit("/", 1)[-1]).strip()
        view.agents[agent_id] = AgentSpec(
            agent_id=agent_id,
            title=str(note.title or agent_id),
            root_skill=str(fields.get("root_skill") or self._first_skill_link(note.links) or ""),
            toolboxes=self._as_list(fields.get("toolboxes")),
            context=str(note.summary or ""),
            llm=llm,
            policy=policy,
            source_node=note.note_id,
        )

    def _add_skill(self, view: ProtocolView, note, note_index: dict) -> None:  # noqa: ANN001
        skill_id = str(note.fields.get("id") or note.note_id).strip()
        skill_links = [target for target in note.links if target.startswith("skill/")]
        tool_links = self._skill_tools(note, note_index)
        knowledge_nodes = [target for target in note.links if not target.startswith(("skill/", "tool/", "agent/"))]
        view.skills[skill_id] = SkillSpec(
            skill_id=skill_id,
            title=str(note.title or skill_id),
            summary=str(note.summary or ""),
            context=str(note.summary or ""),
            child_skills=skill_links,
            refs=skill_links,
            tools=tool_links,
            knowledge_nodes=knowledge_nodes,
            source_node=note.note_id,
            markdown_body=note.body,
            source_path=note.path,
        )

    def _add_toolbox(self, view: ProtocolView, note) -> None:  # noqa: ANN001
        fields = dict(note.fields or {})
        toolbox_id = str(fields.get("id") or fields.get("toolbox") or note.note_id.rsplit("/", 1)[-1])
        if toolbox_id == "runtime":
            toolbox_id = "engine"
        view.toolboxes[toolbox_id] = ToolboxSpec(
            toolbox_id=toolbox_id,
            title=str(note.title or toolbox_id),
            module=str(fields.get("module") or ""),
            class_name=str(fields.get("class_name") or fields.get("class") or ""),
            tool_ids=self._tool_ids_from_links(note.links),
            category=self._infer_tool_category(note.path),
            source_node=note.note_id,
        )

    def _add_tool(self, view: ProtocolView, note) -> None:  # noqa: ANN001
        fields = dict(note.fields or {})
        tool_id = str(fields.get("id") or self._tool_id_from_link(note.note_id)).strip()
        if not tool_id or "/" in tool_id:
            view.diagnostics.append(ProtocolDiagnostic("error", note.note_id, "Tool note cannot infer tool id.", "Add runtime id or a dotted tool entry.", "id"))
            return
        view.tools[tool_id] = ToolSpec(
            tool_id=tool_id,
            title=str(note.title or tool_id),
            description=str(note.summary or tool_id),
            input_schema=dict(fields.get("input_schema") or {"type": "object", "properties": {}}),
            output_schema=dict(fields.get("output_schema") or {}),
            executor=None,
            toolbox=str(fields.get("toolbox") or tool_id.split(".", 1)[0] or self._infer_toolbox_from_path(note.path)),
            permission_level=int(fields.get("permission_level") or self._default_permission(note.path, tool_id)),
            categories=tuple(self._as_list(fields.get("categories")) or [self._infer_tool_category(note.path)]),
            activation_mode=str(fields.get("activation") or fields.get("activation_mode") or self._default_activation(tool_id)),
            activation_rules=tuple(self._as_list(fields.get("activation_rules"))),
            priority=int(fields.get("priority") or 50),
            safety=self._section_text(note, ["safety", "安全边界", "注意事项"]),
            context_hint=self._section_text(note, ["usage", "工具说明", "适用场景"]),
            source_node=note.note_id,
        )

    def _validate(self, view: ProtocolView) -> None:
        for agent in view.agents.values():
            if not agent.root_skill:
                view.diagnostics.append(ProtocolDiagnostic("error", agent.source_node, "Agent missing root skill.", "Add Root or Runtime root_skill.", "root_skill"))
            elif agent.root_skill not in view.skills:
                view.diagnostics.append(ProtocolDiagnostic("error", agent.source_node, f"Agent root skill not found: {agent.root_skill}", "Create the Skill Wiki Page or fix the link.", "root_skill"))
        for skill in view.skills.values():
            for tool_id in skill.tools:
                if tool_id not in view.tools:
                    view.diagnostics.append(ProtocolDiagnostic("warning", skill.source_node, f"Skill references unknown tool: {tool_id}", "Create a Tool Wiki Page or remove the reference.", "tools"))
            for child in skill.child_skills:
                if child not in view.skills:
                    view.diagnostics.append(ProtocolDiagnostic("warning", skill.source_node, f"Skill child not found: {child}", "Create the child Skill Wiki Page or fix link.", "child_skills"))
        for tool_id, spec in view.tools.items():
            if "system" in spec.categories and spec.permission_level < 3:
                view.diagnostics.append(ProtocolDiagnostic("error", spec.source_node or tool_id, f"System tool permission must be >= 3: {tool_id}", "Raise permission_level.", "permission_level"))

    def _build_graph(self, view: ProtocolView, notes: list) -> None:  # noqa: ANN001
        view.graph = ProtocolGraph(
            edges=[
                {"from": note.note_id, "to": link, "kind": "memory_link"}
                for note in notes
                for link in note.links
            ]
        )

    @staticmethod
    def _note_type(note) -> str:  # noqa: ANN001
        kind = str(note.kind or "").strip().lower()
        if kind in {"agent", "skill", "tool", "toolbox"}:
            return kind
        return "knowledge"

    @staticmethod
    def _first_skill_link(links: list[str]) -> str:
        return next((link for link in links if link.startswith("skill/")), "")

    def _skill_tools(self, note, note_index: dict) -> list[str]:  # noqa: ANN001
        tools: list[str] = []
        for link in note.links:
            if link.startswith("tool/"):
                tools.append(self._tool_id_from_link(link))
            elif link in note_index and str(note_index[link].kind).strip().lower() == "tool":
                target = note_index[link]
                tools.append(str(target.fields.get("id") or self._tool_id_from_link(target.note_id)))
        for relation in note.relations:
            target = str(relation.target or "").strip()
            if target.startswith("tool/") or ("." in target and "/" not in target):
                tools.append(self._tool_id_from_link(target))
        section_tools = self._tool_ids_from_links(self._extract_targets_from_sections(note, ["tools", "使用工具", "推荐工具", "可用工具"]))
        tools.extend(section_tools)
        return sorted(dict.fromkeys(item for item in tools if item and "/" not in item))

    def _extract_targets_from_sections(self, note, names: list[str]) -> list[str]:  # noqa: ANN001
        targets: list[str] = []
        for name in names:
            body = str(note.sections.get(name) or "")
            if not body:
                continue
            targets.extend(match.strip() for match in LINK_RE.findall(body))
            for item in CODE_RE.findall(body):
                targets.append(item.strip())
            for line in body.splitlines():
                stripped = line.strip()
                if stripped.startswith("- "):
                    targets.append(stripped[2:].strip().strip("`"))
        return [item for item in targets if item and item != "待补充"]

    def _tool_ids_from_links(self, links: list[str]) -> list[str]:
        return [self._tool_id_from_link(link) for link in links if str(link or "").startswith("tool/")]

    @staticmethod
    def _tool_id_from_link(link: str) -> str:
        raw = str(link or "").strip()
        if not raw:
            return ""
        if raw.startswith("tool/"):
            parts = raw.split("/")
            if len(parts) >= 4:
                toolbox = parts[-2]
                tool_name = parts[-1]
                if toolbox == "runtime":
                    toolbox = "engine"
                return f"{toolbox}.{tool_name}"
        if raw.startswith("[[") and raw.endswith("]]" ):
            raw = raw[2:-2].strip()
        if "|" in raw:
            _, raw = raw.split("|", 1)
            raw = raw.strip()
        return raw.replace("/", ".") if "/" in raw and raw.startswith("tool/") else raw

    def _backfill_toolboxes(self, view: ProtocolView) -> None:
        known = set(view.toolboxes)
        names = set()
        for agent in view.agents.values():
            names.update(agent.toolboxes)
        for tool in view.tools.values():
            if tool.toolbox:
                names.add(tool.toolbox)
        for name in sorted(names):
            normalized = "engine" if name == "runtime" else str(name)
            if normalized in known:
                continue
            view.toolboxes[normalized] = ToolboxSpec(
                toolbox_id=normalized,
                title=normalized,
                module="",
                class_name="",
                tool_ids=[tool.tool_id for tool in view.tools.values() if tool.toolbox == normalized],
                category=normalized,
                source_node=normalized,
            )

    @staticmethod
    def _section_text(note, names: list[str]) -> str:  # noqa: ANN001
        for name in names:
            value = str(note.sections.get(name) or "").strip()
            if value:
                return value
        return ""

    @staticmethod
    def _as_list(value) -> list[str]:  # noqa: ANN001
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        if isinstance(value, tuple):
            return [str(item) for item in value if str(item).strip()]
        if isinstance(value, str) and "," in value:
            return [item.strip() for item in value.split(",") if item.strip()]
        return [str(value)] if str(value).strip() else []

    @staticmethod
    def _infer_toolbox_from_path(path: str) -> str:
        parts = path.replace("\\", "/").split("/")
        if "tool" not in parts:
            return ""
        idx = parts.index("tool")
        if idx + 2 < len(parts) and parts[idx + 1] in {"external", "workflow", "system"}:
            name = parts[idx + 2]
            return "engine" if name == "runtime" else name
        return parts[idx + 1] if idx + 1 < len(parts) else ""

    @staticmethod
    def _infer_tool_category(path: str) -> str:
        parts = path.replace("\\", "/").split("/")
        for item in ("external", "workflow", "system"):
            if item in parts:
                return item
        return "external"

    @staticmethod
    def _default_permission(path: str, tool_id: str) -> int:
        category = ProtocolCompiler._infer_tool_category(path)
        if category == "system":
            return 3
        if category == "workflow":
            return 2
        if any(tool_id.startswith(prefix) for prefix in ("shell.", "workspace.run", "wiki_app.publish_draft")):
            return 4
        return 1

    @staticmethod
    def _default_activation(tool_id: str) -> str:
        return "always" if any(x in tool_id for x in ("read", "list", "search", "answer", "inspect")) else "skill"
