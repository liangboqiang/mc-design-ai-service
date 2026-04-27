from __future__ import annotations

from pathlib import Path
from typing import Any

from kernel.policy import KernelPolicy
from kernel.profile import AgentProfile, SkillProfile
from memory import MemoryService
from memory.types import MemoryNote


class AgentProfileStore:
    def __init__(self, project_root: Path, *, memory: MemoryService | None = None):
        self.project_root = Path(project_root).resolve()
        self.memory = memory or MemoryService(self.project_root)
        self.note_store = self.memory.note_store

    def load(self, agent_id: str) -> AgentProfile:
        note = self._find_agent(agent_id)
        fields = dict(note.fields or {})
        machine_id = _agent_machine_id(note, fields)
        policy = KernelPolicy(
            agent_id=machine_id,
            mode="runtime",
            max_steps=int(_first(fields, "max_steps", "最大步骤数", default=8) or 8),
            max_prompt_chars=int(_first(fields, "max_prompt_chars", "最大上下文长度", default=18_000) or 18_000),
            tool_permission_level=_permission_level(_first(fields, "tool_permission_level", "工具权限等级", default=1)),
            allowed_tool_categories=tuple(_as_list(_first(fields, "allowed_tool_categories", "允许工具分类", default=[]))),
            denied_tool_categories=tuple(_as_list(_first(fields, "denied_tool_categories", "禁止工具分类", default=[]))),
            allowed_tools=tuple(_as_list(_first(fields, "allowed_tools", "允许工具", default=[]))),
            denied_tools=tuple(_as_list(_first(fields, "denied_tools", "禁止工具", default=[]))),
        )
        return AgentProfile(
            agent_id=machine_id,
            title=note.title,
            role=str(_first(fields, "role", "智能体使命", "角色定位", default=note.summary) or note.summary),
            root_skill_id=str(_first(fields, "root_skill", "根技能", default=self._first_skill_link(note)) or ""),
            toolboxes=_as_list(_first(fields, "toolboxes", "可用工具箱", default=[])),
            llm={
                "provider": str(_first(fields, "provider", "模型服务", default="mock") or "mock"),
                "model": str(_first(fields, "model", "模型名称", default="mock") or "mock"),
                **({"api_key": fields["api_key"]} if fields.get("api_key") else {}),
                **({"base_url": fields["base_url"]} if fields.get("base_url") else {}),
            },
            policy=policy,
            memory_scope={"source_note_id": note.note_id},
            capability_scope={"root_skill_id": str(_first(fields, "root_skill", "根技能", default="") or "")},
            source_note_id=note.note_id,
        )

    def skill(self, skill_id: str) -> SkillProfile | None:
        note = self._find_by_machine_id(skill_id, kind="Skill") or self.note_store.get(skill_id)
        if note is None:
            return None
        return self._skill_profile(note)

    def base_skill_ids(self, root_skill_id: str) -> list[str]:
        seen: set[str] = set()
        rows: list[str] = []

        def visit(skill_id: str, depth: int = 0) -> None:
            if depth > 4 or not skill_id or skill_id in seen:
                return
            seen.add(skill_id)
            rows.append(skill_id)
            skill = self.skill(skill_id)
            if skill is None:
                return
            for ref in skill.refs:
                visit(ref, depth + 1)

        visit(root_skill_id)
        return rows

    def list_children_cards(self, skill_id: str) -> list[tuple[str, str]]:
        skill = self.skill(skill_id)
        if skill is None:
            return []
        rows: list[tuple[str, str]] = []
        for ref in skill.refs:
            child = self.skill(ref)
            rows.append((ref, child.summary if child else ref))
        return rows

    def _skill_profile(self, note: MemoryNote) -> SkillProfile:
        fields = dict(note.fields or {})
        skill_id = str(_first(fields, "id", "唯一标识", default=note.note_id) or note.note_id)
        refs = [target for target in note.links if str(target).startswith("skill/")]
        tools = []
        for target in [*note.links, *[rel.target for rel in note.relations]]:
            raw = str(target or "")
            if raw.startswith("tool/") or ("." in raw and "/" not in raw):
                tools.append(_tool_id_from_ref(raw))
        for key in ("tools", "工具", "可用工具", "使用工具", "推荐工具"):
            tools.extend(_tool_id_from_ref(item) for item in _as_list(fields.get(key)))
        return SkillProfile(
            skill_id=skill_id,
            title=note.title,
            summary=note.summary,
            refs=sorted(dict.fromkeys(refs)),
            tools=sorted(dict.fromkeys(item for item in tools if item and item != "待补充")),
            source_note_id=note.note_id,
            markdown_body=note.body,
            source_path=note.path,
        )

    def _find_agent(self, agent_id: str) -> MemoryNote:
        normalized = str(agent_id or "").strip()
        candidates = [normalized, f"agent/{normalized}", f"agent.{normalized}"]
        for note_id in candidates:
            note = self.note_store.get(note_id)
            if note and note.kind == "Agent":
                return note
        found = self._find_by_machine_id(normalized, kind="Agent")
        if found is not None:
            return found
        agents = [note for note in self.note_store.list_notes() if note.kind == "Agent"]
        if agents:
            return agents[0]
        raise KeyError(f"Agent note not found: {agent_id}")

    def _find_by_machine_id(self, machine_id: str, *, kind: str) -> MemoryNote | None:
        for note in self.note_store.list_notes():
            if note.kind != kind:
                continue
            fields = dict(note.fields or {})
            if str(_first(fields, "id", "唯一标识", default="") or "") == machine_id:
                return note
            if note.note_id == machine_id or note.note_id.endswith("/" + machine_id):
                return note
        return None

    @staticmethod
    def _first_skill_link(note: MemoryNote) -> str:
        return next((link for link in note.links if str(link).startswith("skill/")), "")


def _agent_machine_id(note: MemoryNote, fields: dict[str, Any]) -> str:
    value = str(_first(fields, "id", "唯一标识", default="") or "").strip()
    if value:
        return value
    return note.note_id.rsplit("/", 1)[-1]


def _first(fields: dict[str, Any], *keys: str, default=None):  # noqa: ANN001
    for key in keys:
        if key in fields and fields.get(key) not in (None, ""):
            return fields.get(key)
    return default


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
    return [str(item).strip() for item in rows if str(item).strip()]


def _permission_level(value) -> int:  # noqa: ANN001
    if isinstance(value, int):
        return value
    raw = str(value or "").strip()
    if raw.isdigit():
        return int(raw)
    return {"只读": 1, "草稿": 1, "发布": 2, "治理": 3, "系统": 4}.get(raw, 1)


def _tool_id_from_ref(ref: str) -> str:
    raw = str(ref or "").strip()
    if not raw or raw == "待补充":
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
    return raw
