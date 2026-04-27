from __future__ import annotations

from capability.surface import CapabilitySurfaceResolver
from runtime.dispatcher import ToolExecutionResult


class RuntimeCapability:
    """Runtime-facing capability facade over registry, surface, and dispatch."""

    def __init__(self, kernel):  # noqa: ANN001
        self.kernel = kernel
        self.surface = CapabilitySurfaceResolver(kernel.capability_registry)

    def orient(self, *, observation: str, memory_view):  # noqa: ANN001
        skill_ids = self.kernel.skill_state.base_skill_ids()
        requested_tools = self.kernel.capability_registry.requested_tools_for_skills(skill_ids)
        return self.surface.resolve(
            observation=observation,
            memory_view=memory_view,
            policy={
                "tool_permission_level": self.kernel.settings.tool_permission_level,
                "allowed_tool_categories": list(self.kernel.settings.allowed_tool_categories),
                "denied_tool_categories": list(self.kernel.settings.denied_tool_categories),
                "allowed_tools": list(self.kernel.settings.allowed_tools),
                "denied_tools": list(self.kernel.settings.denied_tools),
            },
            installed_tool_ids=set(self.kernel.runtime_state.tool_registry),
            requested_tool_ids=requested_tools,
            visible_skill_ids=set(skill_ids),
        )

    def dispatch(self, capability_id: str, arguments: dict) -> ToolExecutionResult:
        tool_id = str(capability_id or "").strip()
        if tool_id not in self.kernel.runtime_state.tool_registry:
            return ToolExecutionResult(False, tool_id, f"Error: unknown tool '{tool_id}'.", meta={"error_code": "unknown_tool"})
        if tool_id not in self.kernel.active_tool_ids:
            return ToolExecutionResult(False, tool_id, f"Permission denied or inactive tool: {tool_id}", meta={"error_code": "inactive_tool"})
        spec = self.kernel.runtime_state.tool_registry[tool_id]
        if spec.executor is None:
            return ToolExecutionResult(False, tool_id, f"Tool has no executor: {tool_id}", meta={"error_code": "missing_executor"})
        try:
            value = spec.executor(arguments or {})
            if hasattr(value, "ok") and hasattr(value, "tool_id") and hasattr(value, "content"):
                return ToolExecutionResult(value.ok, value.tool_id, value.content, getattr(value, "raw_result", None), getattr(value, "meta", {}))
            return ToolExecutionResult(True, tool_id, "" if value is None else str(value), raw_result=value)
        except Exception as exc:  # noqa: BLE001
            return ToolExecutionResult(False, tool_id, f"Error while executing {tool_id}: {exc}", meta={"error_code": "tool_exception"})
