from __future__ import annotations

import json
from pathlib import Path


class EngineOps:
    def __init__(self, *, registry, skill_state, context, events, tool_registry):  # noqa: ANN001
        self.registry = registry
        self.skill_state = skill_state
        self.context = context
        self.events = events
        self.tool_registry = tool_registry

    def inspect_skill(self, skill: str) -> str:
        target = self.skill_state.resolve_skill_alias(skill)
        skill_spec = self.registry.skill(target)
        if skill_spec.source_path:
            path = (self.registry.project_root / skill_spec.source_path).resolve()
            if path.exists():
                return path.read_text(encoding="utf-8")
        return skill_spec.markdown_body or skill_spec.context or skill_spec.summary

    def inspect_tool(self, tool: str) -> str:
        spec = self.tool_registry[tool]
        return json.dumps(
            {
                "tool": spec.tool_id,
                "title": spec.title,
                "description": spec.description,
                "input_schema": spec.input_schema,
                "toolbox": spec.toolbox,
                "permission_level": spec.permission_level,
                "categories": spec.categories,
                "activation": spec.activation_mode,
                "safety": spec.safety,
            },
            ensure_ascii=False,
            indent=2,
        )

    def list_child_skills(self) -> str:
        rows = self.registry.list_children_cards(self.skill_state.active_skill_id)
        return json.dumps(
            [{"skill": skill_id, "summary": summary} for skill_id, summary in rows],
            ensure_ascii=False,
            indent=2,
        )

    def enter_skill(self, skill: str) -> str:
        result = self.skill_state.enter_skill(skill)
        self.context.active_skill_id = self.skill_state.active_skill_id
        self.events.emit("skill.entered", skill=self.skill_state.active_skill_id)
        return result
