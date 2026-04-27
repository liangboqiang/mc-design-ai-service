from __future__ import annotations

from capability.registry import CapabilityRegistry
from capability.types import CapabilitySpec, CapabilityView


class CapabilitySurfaceResolver:
    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry

    def resolve(
        self,
        *,
        observation,  # noqa: ANN001
        memory_view,
        policy: dict | None = None,
        installed_tool_ids: set[str] | None = None,
        requested_tool_ids: set[str] | None = None,
        visible_skill_ids: set[str] | None = None,
        manually_enabled: set[str] | None = None,
    ) -> CapabilityView:
        policy = dict(policy or {})
        installed_tool_ids = set(installed_tool_ids or ())
        requested_tool_ids = set(requested_tool_ids or ())
        visible_skill_ids = set(visible_skill_ids or ())
        manually_enabled = set(manually_enabled or ())
        memory_requested = {hint.capability_id for hint in memory_view.activation_hints}

        visible_tools: list[CapabilitySpec] = []
        visible_skills: list[CapabilitySpec] = []
        visible_workflows: list[CapabilitySpec] = []
        activation_reasons: list[str] = []
        denied_reasons: list[str] = []
        reasons_by_capability: dict[str, list[str]] = {}

        for spec in sorted(self.registry.capabilities().values(), key=lambda item: (item.kind, item.capability_id)):
            reasons: list[str] = []
            requested_by_memory = spec.capability_id in memory_requested
            requested_by_skill = spec.capability_id in requested_tool_ids or spec.capability_id in visible_skill_ids
            manual = spec.capability_id in manually_enabled

            if spec.kind == "Tool":
                installed = not installed_tool_ids or spec.capability_id in installed_tool_ids
                activation = self._activation_passed(spec, requested_by_memory, requested_by_skill, manual)
                permission = self._permission_passed(spec, policy)
                category = self._category_allowed(spec, policy)
                reasons.extend(
                    [
                        f"installed={installed}",
                        f"requested_by_memory={requested_by_memory}",
                        f"requested_by_skill={requested_by_skill}",
                        f"activation={spec.activation_mode}",
                        f"permission_level={spec.permission_level}",
                        f"category_allowed={category}",
                    ]
                )
                if installed and activation and permission and category:
                    visible_tools.append(spec)
                    activation_reasons.append(f"{spec.capability_id}: {'; '.join(reasons)}")
                else:
                    denied_reasons.append(f"{spec.capability_id}: {'; '.join(reasons)}")
            elif spec.kind == "Skill":
                requested = spec.capability_id in visible_skill_ids or requested_by_memory or spec.activation_mode in {"always", "permanent"}
                reasons.extend([f"visible_skill={spec.capability_id in visible_skill_ids}", f"requested_by_memory={requested_by_memory}"])
                if requested:
                    visible_skills.append(spec)
                else:
                    denied_reasons.append(f"{spec.capability_id}: not activated by skill scope or memory hints")
            elif spec.kind in {"Workflow", "MCP"}:
                requested = requested_by_memory or manual or spec.activation_mode in {"always", "permanent"}
                reasons.extend([f"requested_by_memory={requested_by_memory}", f"manual={manual}"])
                if requested:
                    visible_workflows.append(spec)
                else:
                    denied_reasons.append(f"{spec.capability_id}: not requested")
            reasons_by_capability[spec.capability_id] = reasons

        return CapabilityView(
            visible_skills=visible_skills,
            visible_tools=visible_tools,
            visible_workflows=visible_workflows,
            activation_reasons=activation_reasons,
            denied_reasons=denied_reasons,
            reasons_by_capability=reasons_by_capability,
        )

    @staticmethod
    def _activation_passed(spec: CapabilitySpec, requested_by_memory: bool, requested_by_skill: bool, manual: bool) -> bool:
        mode = str(spec.activation_mode or "skill")
        if mode in {"always", "permanent"}:
            return True
        return requested_by_memory or requested_by_skill or manual

    @staticmethod
    def _permission_passed(spec: CapabilitySpec, policy: dict) -> bool:
        denied_tools = {str(item) for item in policy.get("denied_tools") or []}
        allowed_tools = {str(item) for item in policy.get("allowed_tools") or []}
        if spec.capability_id in denied_tools:
            return False
        if allowed_tools and spec.capability_id not in allowed_tools:
            return False
        return int(spec.permission_level or 1) <= int(policy.get("tool_permission_level") or 1)

    @staticmethod
    def _category_allowed(spec: CapabilitySpec, policy: dict) -> bool:
        categories = set(spec.categories or [])
        denied = {str(item) for item in policy.get("denied_tool_categories") or []}
        allowed = {str(item) for item in policy.get("allowed_tool_categories") or []}
        if categories.intersection(denied):
            return False
        if allowed and not categories.intersection(allowed):
            return False
        return True
