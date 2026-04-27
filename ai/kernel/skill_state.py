from __future__ import annotations

from kernel.profile_store import AgentProfileStore


class KernelSkillState:
    def __init__(self, profile_store: AgentProfileStore, root_skill_id: str, audit=None):  # noqa: ANN001
        self.profile_store = profile_store
        self.root_skill_id = root_skill_id
        self.active_skill_id = root_skill_id
        self.audit = audit

    def active_skill(self):
        return self.profile_store.skill(self.active_skill_id)

    def base_skill_ids(self) -> list[str]:
        return self.profile_store.base_skill_ids(self.active_skill_id or self.root_skill_id)

    def activated_skill_ids(self) -> list[str]:
        return self.base_skill_ids()

    def visible_skill_cards(self, activated_skill_ids: list[str]) -> list[tuple[str, str]]:
        rows = self.profile_store.list_children_cards(self.active_skill_id)
        for skill_id in activated_skill_ids:
            if skill_id == self.active_skill_id:
                continue
            skill = self.profile_store.skill(skill_id)
            if skill is not None:
                rows.append((skill_id, skill.summary or skill.title))
        seen: set[str] = set()
        out: list[tuple[str, str]] = []
        for item in rows:
            if item[0] not in seen:
                seen.add(item[0])
                out.append(item)
        return out

    def resolve_skill_alias(self, raw_skill: str) -> str:
        raw = str(raw_skill or "").strip()
        if raw in {"root", self.root_skill_id, self.active_skill_id}:
            return self.root_skill_id if raw == "root" else raw
        if self.profile_store.skill(raw) is not None:
            return raw
        active = self.active_skill()
        candidates = [] if active is None else [*active.refs]
        for candidate in candidates:
            if candidate.endswith(raw):
                return candidate
            skill = self.profile_store.skill(candidate)
            if skill and skill.title == raw:
                return candidate
        raise ValueError(f"Skill not reachable from current scope: {raw_skill}")

    def enter_skill(self, raw_skill: str) -> str:
        target = self.resolve_skill_alias(raw_skill)
        self.active_skill_id = target
        if self.audit is not None:
            self.audit.record("skill.enter", target=target)
        skill = self.profile_store.skill(target)
        return f"Entered skill {target}: {(skill.summary or skill.title) if skill else target}"
