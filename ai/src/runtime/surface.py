from __future__ import annotations

from dataclasses import asdict

from protocol.types import ToolSpec
from .types import SurfaceSnapshot, ToolCard, ToolVisibility


class ToolSurface:
    """Single visible-tool resolver with explicit explainability."""

    def __init__(self, kernel):  # noqa: ANN001
        self.kernel = kernel

    def resolve(self, *, observation: str = "", memory_view=None) -> SurfaceSnapshot:  # noqa: ANN001
        skill_ids = self.kernel.skill_state.base_skill_ids()
        memory_view = memory_view or self.kernel.memory.orient(observation, runtime_state=self.kernel.runtime_state)
        capability_view = self.kernel.capability.orient(observation=observation, memory_view=memory_view)

        visible: list[ToolSpec] = []
        reasons: list[ToolVisibility] = []
        installed_tool_ids = set(self.kernel.runtime_state.tool_registry)
        visible_tool_ids = {item.capability_id for item in capability_view.visible_tools}
        for tool_id, spec in sorted(self.kernel.runtime_state.tool_registry.items()):
            installed = tool_id in installed_tool_ids
            requested = tool_id in self.kernel.capability_registry.requested_tools_for_skills(skill_ids)
            is_visible = tool_id in visible_tool_ids
            reason_rows = list(capability_view.reasons_by_capability.get(tool_id) or [])
            activation = is_visible or any(row.startswith("requested_by_memory=True") or row.startswith("requested_by_skill=True") for row in reason_rows)
            permission = is_visible or not any("permission_level" in row for row in reason_rows if "False" in row)
            category = is_visible or not any(row == "category_allowed=False" for row in reason_rows)
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
            memory_view=memory_view,
            capability_view=capability_view,
            observation=observation,
        )
        self.kernel.runtime_state.last_surface_snapshot = snapshot
        return snapshot

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
