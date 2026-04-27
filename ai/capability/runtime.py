from __future__ import annotations

from capability.dispatcher import CapabilityDispatcher, DispatchResult
from capability.surface import CapabilitySurfaceResolver


class RuntimeCapability:
    """Kernel-facing capability facade over registry, surface, and dispatch."""

    def __init__(self, kernel):  # noqa: ANN001
        self.kernel = kernel
        self.surface = CapabilitySurfaceResolver(kernel.capability_registry)
        self.dispatcher = CapabilityDispatcher(registry=kernel.capability_registry, executors=kernel.executor_registry)

    def orient(self, *, observation: str, memory_view):  # noqa: ANN001
        skill_ids = self.kernel.skill_state.base_skill_ids()
        requested_tools = self.kernel.capability_registry.requested_tools_for_skills(skill_ids)
        return self.surface.resolve(
            observation=observation,
            memory_view=memory_view,
            policy=self.kernel.policy_payload(),
            installed_tool_ids=set(self.kernel.executor_registry),
            requested_tool_ids=requested_tools,
            visible_skill_ids=set(skill_ids),
        )

    def dispatch(self, capability_id: str, arguments: dict, *, visible_capability_ids: set[str] | None = None) -> DispatchResult:
        return self.dispatcher.dispatch(capability_id, arguments, visible_capability_ids=visible_capability_ids)
