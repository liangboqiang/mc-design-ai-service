from __future__ import annotations

from dataclasses import asdict

from protocol.types import ToolSpec
from .types import SurfaceSnapshot, ToolCard, ToolVisibility


class ToolSurface:
    """Single visible-tool resolver with explicit explainability."""

    def __init__(self, kernel):  # noqa: ANN001
        self.kernel = kernel

    def resolve(self) -> SurfaceSnapshot:
        skill_ids = self.kernel.skill_state.base_skill_ids()
        requested_tools: set[str] = set()
        for skill_id in skill_ids:
            skill = self.kernel.registry.skill(skill_id)
            requested_tools.update(skill.tools)

        visible: list[ToolSpec] = []
        reasons: list[ToolVisibility] = []
        installed_tool_ids = set(self.kernel.runtime_state.tool_registry)
        for tool_id, spec in sorted(self.kernel.runtime_state.tool_registry.items()):
            installed = tool_id in installed_tool_ids
            requested = tool_id in requested_tools
            activation = self._activation_passed(spec, requested)
            permission = self._permission_passed(spec)
            category = self._category_allowed(spec)
            is_visible = installed and activation and permission and category
            reason_rows = []
            reason_rows.append(f"installed={installed}")
            reason_rows.append(f"requested_by_skill={requested}")
            reason_rows.append(f"activation={spec.activation_mode}")
            reason_rows.append(f"permission_level={spec.permission_level}")
            if is_visible:
                visible.append(spec)
            reasons.append(
                ToolVisibility(
                    tool_id=tool_id,
                    installed=installed,
                    requested_by_skill=requested,
                    activation_passed=activation,
                    permission_passed=permission,
                    category_allowed=category,
                    visible=is_visible,
                    reasons=reason_rows,
                )
            )

        self.kernel.active_tool_ids = {spec.tool_id for spec in visible}
        cards = [asdict(self._card(spec)) for spec in visible]
        snapshot = SurfaceSnapshot(
            visible_tools=visible,
            visible_skills=self.kernel.skill_state.visible_skill_cards(skill_ids),
            visible_toolboxes=sorted({spec.toolbox for spec in visible}),
            activated_skill_ids=skill_ids,
            visible_tool_cards=cards,
            reasons=reasons,
        )
        self.kernel.runtime_state.last_surface_snapshot = snapshot
        return snapshot

    def _activation_passed(self, spec: ToolSpec, requested: bool) -> bool:
        mode = str(spec.activation_mode or "skill")
        if mode in {"always", "permanent"}:
            return True
        if mode in {"skill", "manual"}:
            return requested
        if mode == "rule":
            event_names = {event.name for event in self.kernel.events.recent()}
            state_blob = "\n".join(self.kernel.state_fragments()).lower()
            return any(rule in event_names or rule.lower() in state_blob for rule in spec.activation_rules)
        return requested

    def _permission_passed(self, spec: ToolSpec) -> bool:
        settings = self.kernel.settings
        if spec.tool_id in settings.denied_tools:
            return False
        if settings.allowed_tools and spec.tool_id not in settings.allowed_tools:
            return False
        return int(spec.permission_level or 1) <= int(settings.tool_permission_level or 1)

    def _category_allowed(self, spec: ToolSpec) -> bool:
        settings = self.kernel.settings
        categories = set(spec.categories or ())
        if categories.intersection(settings.denied_tool_categories):
            return False
        if settings.allowed_tool_categories and not categories.intersection(settings.allowed_tool_categories):
            return False
        return True

    @staticmethod
    def _card(spec: ToolSpec) -> ToolCard:
        return ToolCard(
            tool_id=spec.tool_id,
            title=spec.title,
            description=spec.description,
            input_schema=spec.input_schema,
            permission_level=spec.permission_level,
            categories=spec.categories,
            activation_mode=spec.activation_mode,
            safety=spec.safety,
        )
