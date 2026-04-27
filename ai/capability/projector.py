from __future__ import annotations

from pathlib import Path

from capability.types import CapabilitySpec
from memory import MemoryService


class CapabilityProjector:
    def __init__(self, project_root: Path, memory: MemoryService):
        self.project_root = Path(project_root).resolve()
        self.memory = memory

    def project_from_notes(self) -> dict[str, CapabilitySpec]:
        rows: dict[str, CapabilitySpec] = {}
        for note in self.memory.note_store.list_notes():
            if note.kind not in {"Skill", "Tool", "Workflow", "MCP"}:
                continue
            capability_id = str(note.fields.get("id") or note.note_id).strip()
            if not capability_id:
                continue
            rows[capability_id] = CapabilitySpec(
                capability_id=capability_id,
                kind=note.kind,
                title=note.title,
                description=note.summary,
                input_schema=_as_dict(note.fields.get("input_schema")),
                output_schema=_as_dict(note.fields.get("output_schema")),
                permission_level=int(note.fields.get("permission_level") or 1),
                categories=_as_list(note.fields.get("categories")),
                executor_ref=None,
                safety=str(note.fields.get("safety") or ""),
                source_note_id=note.note_id,
                activation_mode=str(note.fields.get("activation_mode") or ("always" if note.kind == "Skill" else "skill")),
                activation_rules=_as_list(note.fields.get("activation_rules")),
                metadata={"path": note.path, "status": note.status, "maturity": note.maturity},
            )
        return rows

    @staticmethod
    def project_from_legacy_registry(legacy_registry) -> dict[str, CapabilitySpec]:  # noqa: ANN001
        rows: dict[str, CapabilitySpec] = {}
        if legacy_registry is None:
            return rows
        for skill in legacy_registry.skills.values():
            rows[skill.skill_id] = CapabilitySpec(
                capability_id=skill.skill_id,
                kind="Skill",
                title=skill.title,
                description=skill.summary or skill.context,
                categories=["skill"],
                source_note_id=skill.source_node or skill.skill_id,
                activation_mode="always",
                metadata={"refs": list(skill.refs), "tools": list(skill.tools), "children": list(skill.child_skills)},
            )
        for tool in legacy_registry.tools.values():
            rows[tool.tool_id] = CapabilitySpec(
                capability_id=tool.tool_id,
                kind="Tool",
                title=tool.title,
                description=tool.description,
                input_schema=dict(tool.input_schema or {}),
                output_schema=dict(tool.output_schema or {}),
                permission_level=int(tool.permission_level or 1),
                categories=[str(item) for item in tool.categories or ()],
                executor_ref=f"legacy:{tool.toolbox}:{tool.tool_id}",
                safety=str(tool.safety or ""),
                source_note_id=tool.source_node or tool.tool_id,
                activation_mode=str(tool.activation_mode or "skill"),
                activation_rules=[str(item) for item in tool.activation_rules or ()],
                metadata={"toolbox": tool.toolbox, "priority": tool.priority},
            )
        return rows


def _as_dict(value) -> dict:  # noqa: ANN001
    return dict(value or {}) if isinstance(value, dict) else {}


def _as_list(value) -> list[str]:  # noqa: ANN001
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and "," in value:
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(value)] if str(value).strip() else []
