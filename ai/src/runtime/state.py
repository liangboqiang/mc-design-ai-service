from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RuntimeState:
    last_surface_snapshot: Any | None = None
    tool_registry: dict[str, Any] = field(default_factory=dict)
    installed_toolboxes: dict[str, Any] = field(default_factory=dict)
    fault_history: list[str] = field(default_factory=list)


class SkillState:
    def __init__(self, registry, root_skill_id: str, audit=None):  # noqa: ANN001
        self.registry = registry
        self.root_skill_id = root_skill_id
        self.active_skill_id = root_skill_id
        self.audit = audit

    def active_skill(self):
        return self.registry.skill(self.active_skill_id)

    def base_skill_ids(self) -> list[str]:
        return self.registry.base_skill_ids(self.active_skill_id)

    def visible_skill_cards(self, activated_skill_ids: list[str]) -> list[tuple[str, str]]:
        rows = self.registry.list_children_cards(self.active_skill_id)
        for skill_id in activated_skill_ids:
            if skill_id == self.active_skill_id or skill_id not in self.registry.skills:
                continue
            skill = self.registry.skill(skill_id)
            rows.append((skill_id, skill.summary or skill.title))
        seen: set[str] = set()
        out: list[tuple[str, str]] = []
        for item in rows:
            if item[0] not in seen:
                seen.add(item[0])
                out.append(item)
        return out

    def resolve_skill_alias(self, raw_skill: str) -> str:
        raw = str(raw_skill).strip()
        if raw in {"root", self.root_skill_id, self.active_skill_id}:
            return self.root_skill_id if raw == "root" else raw
        if raw in self.registry.skills:
            return raw
        active = self.active_skill()
        for candidate in [*active.child_skills, *active.refs]:
            if candidate.endswith(raw):
                return candidate
            skill = self.registry.skill(candidate)
            if skill.title == raw:
                return candidate
        raise ValueError(f"Skill not reachable from current scope: {raw_skill}")

    def enter_skill(self, raw_skill: str) -> str:
        target = self.resolve_skill_alias(raw_skill)
        self.active_skill_id = target
        if self.audit is not None:
            self.audit.record("skill.enter", target=target)
        skill = self.registry.skill(target)
        return f"Entered skill {target}: {skill.summary or skill.title}"
