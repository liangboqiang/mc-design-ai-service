from __future__ import annotations

from pathlib import Path
from typing import Any

from capability.types import CapabilitySpec
from memory import MemoryService


class CapabilityProjector:
    """Project executable capability contracts directly from MemoryNote + Lens.

    There is no old transition layer in the Memory-Native runtime.
    """

    def __init__(self, project_root: Path, memory: MemoryService):
        self.project_root = Path(project_root).resolve()
        self.memory = memory

    def project_from_notes(self) -> dict[str, CapabilitySpec]:
        rows: dict[str, CapabilitySpec] = {}
        for note in self.memory.note_store.list_notes():
            if note.kind not in {"Skill", "Tool", "Workflow", "MCP", "Toolbox"}:
                continue
            fields = dict(note.fields or {})
            capability_id = self._capability_id(note, fields)
            if not capability_id:
                continue
            kind = "Workflow" if note.kind == "Toolbox" else note.kind
            spec = CapabilitySpec(
                capability_id=capability_id,
                kind=kind,
                title=note.title,
                description=note.summary,
                input_schema=_as_dict(_first(fields, "input_schema", "输入结构", default={})) or {"type": "object", "properties": {}},
                output_schema=_as_dict(_first(fields, "output_schema", "输出结构", default={})),
                permission_level=_permission_level(_first(fields, "permission_level", "权限等级", default=self._default_permission(note.path, capability_id, kind))),
                categories=_categories(note, fields),
                executor_ref=self._executor_ref(note, fields, capability_id, kind),
                safety=str(_first(fields, "safety", "安全边界", "注意事项", default="") or ""),
                source_note_id=note.note_id,
                activation_mode=_activation_mode(_first(fields, "activation_mode", "activation", "激活方式", default=self._default_activation(capability_id, kind))),
                activation_rules=_as_list(_first(fields, "activation_rules", "激活规则", default=[])),
                metadata={
                    "path": note.path,
                    "status": note.status,
                    "maturity": note.maturity,
                    "toolbox": _toolbox_from_path(note.path),
                    "links": list(note.links),
                    "relations": [rel.target for rel in note.relations],
                },
            )
            rows[spec.capability_id] = spec
        self._add_executor_aliases(rows)
        return rows

    @staticmethod
    def _capability_id(note, fields: dict[str, Any]) -> str:  # noqa: ANN001
        value = str(_first(fields, "id", "唯一标识", default="") or "").strip()
        if value and "/" not in value:
            return value
        if note.kind == "Tool":
            return _tool_id_from_ref(note.note_id)
        if note.kind in {"Skill", "Toolbox", "Workflow", "MCP"}:
            return value or note.note_id
        return value or note.note_id

    @staticmethod
    def _executor_ref(note, fields: dict[str, Any], capability_id: str, kind: str) -> str | None:  # noqa: ANN001
        if kind != "Tool":
            return None
        explicit = str(_first(fields, "executor_ref", "执行器", default="") or "").strip()
        if explicit:
            return explicit
        return f"builtin:{_executor_alias(capability_id)}"

    @staticmethod
    def _default_permission(path: str, capability_id: str, kind: str) -> int:
        if kind != "Tool":
            return 1
        category = _infer_category(path)
        if category == "system":
            return 3
        if category == "workflow":
            return 2
        if any(capability_id.startswith(prefix) for prefix in ("shell.run", "version.rollback", "files.delete", "fs.delete")):
            return 4
        return 1

    @staticmethod
    def _default_activation(capability_id: str, kind: str) -> str:
        if kind == "Skill":
            return "always"
        if kind in {"Workflow", "MCP"}:
            return "manual"
        return "always" if any(x in capability_id for x in ("read", "list", "search", "answer", "inspect", "view")) else "skill"

    @staticmethod
    def _add_executor_aliases(rows: dict[str, CapabilitySpec]) -> None:
        # The legacy file notes used fs.* while Python toolbox executors use files.*.
        # Keep the public capability id from note.md and point executor_ref to the installed executor.
        for spec in rows.values():
            if spec.capability_id.startswith("fs.") and spec.executor_ref == f"builtin:{spec.capability_id}":
                spec.executor_ref = f"builtin:files.{spec.capability_id.split('.', 1)[1]}"


def _first(fields: dict[str, Any], *keys: str, default=None):  # noqa: ANN001
    for key in keys:
        if key in fields and fields.get(key) not in (None, ""):
            return fields.get(key)
    return default


def _as_dict(value) -> dict:  # noqa: ANN001
    return dict(value or {}) if isinstance(value, dict) else {}


def _as_list(value) -> list[str]:  # noqa: ANN001
    if value is None:
        return []
    if isinstance(value, list):
        rows = value
    elif isinstance(value, tuple):
        rows = list(value)
    elif isinstance(value, str):
        rows = value.replace("，", ",").replace("、", ",").split(",") if any(ch in value for ch in ",，、") else [value]
    else:
        rows = [value]
    return [str(item).strip() for item in rows if str(item).strip() and str(item).strip() != "待补充"]


def _permission_level(value) -> int:  # noqa: ANN001
    if isinstance(value, int):
        return value
    raw = str(value or "").strip()
    if raw.isdigit():
        return int(raw)
    return {"只读": 1, "草稿": 1, "发布": 2, "治理": 3, "系统": 4}.get(raw, 1)


def _categories(note, fields: dict[str, Any]) -> list[str]:  # noqa: ANN001
    rows = _as_list(_first(fields, "categories", "分类", "所属分类", default=[]))
    if rows:
        return rows
    toolbox = _toolbox_from_path(note.path)
    mapped = {
        "fs": ["workspace_io"],
        "files": ["workspace_io"],
        "code": ["code_search", "code_read"],
        "docs": ["document"],
        "notes": ["memory_read", "memory_write"],
        "graph": ["memory_read", "governance"],
        "version": ["version"],
        "shell": ["local_compute"],
        "design_report": ["report", "document"],
        "nx": ["cad"],
    }.get(toolbox)
    if mapped:
        return mapped
    return [_infer_category(note.path)]


def _activation_mode(value) -> str:  # noqa: ANN001
    raw = str(value or "").strip()
    return {
        "默认激活": "always",
        "永久激活": "always",
        "手动激活": "manual",
        "不主动激活": "manual",
        "规则激活": "rule",
        "按技能激活": "skill",
    }.get(raw, raw or "skill")


def _toolbox_from_path(path: str) -> str:
    parts = str(path or "").replace("\\", "/").split("/")
    if "tool" not in parts:
        return ""
    idx = parts.index("tool")
    if idx + 2 < len(parts) and parts[idx + 1] in {"external", "workflow", "system"}:
        name = parts[idx + 2]
        return "engine" if name == "runtime" else name
    return parts[idx + 1] if idx + 1 < len(parts) else ""


def _infer_category(path: str) -> str:
    parts = str(path or "").replace("\\", "/").split("/")
    for item in ("external", "workflow", "system"):
        if item in parts:
            return item
    return "external"


def _tool_id_from_ref(ref: str) -> str:
    raw = str(ref or "").strip()
    if not raw:
        return ""
    if raw.startswith("[[") and raw.endswith("]]" ):
        raw = raw[2:-2].strip()
    if "|" in raw:
        _, raw = raw.split("|", 1)
        raw = raw.strip()
    if raw.startswith("tool/"):
        parts = raw.split("/")
        if len(parts) >= 4:
            toolbox = parts[-2]
            if toolbox == "runtime":
                toolbox = "engine"
            return f"{toolbox}.{parts[-1]}"
    return raw.replace("/", ".") if raw.startswith("tool/") else raw


def _executor_alias(capability_id: str) -> str:
    if capability_id.startswith("fs."):
        return "files." + capability_id.split(".", 1)[1]
    return capability_id
