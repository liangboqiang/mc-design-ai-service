from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from protocol.types import ToolResult


@dataclass(slots=True)
class ToolExecutionResult:
    ok: bool
    tool_id: str
    content: str
    raw_result: Any = None
    meta: dict[str, Any] = field(default_factory=dict)


class ToolDispatcher:
    def __init__(self, kernel):  # noqa: ANN001
        self.kernel = kernel

    def dispatch(self, tool_id: str, arguments: dict) -> ToolExecutionResult:
        if tool_id not in self.kernel.runtime_state.tool_registry:
            return ToolExecutionResult(False, tool_id, f"Error: unknown tool '{tool_id}'.", meta={"error_code": "unknown_tool"})
        if tool_id not in self.kernel.active_tool_ids:
            return ToolExecutionResult(False, tool_id, f"Permission denied or inactive tool: {tool_id}", meta={"error_code": "inactive_tool"})
        spec = self.kernel.runtime_state.tool_registry[tool_id]
        if spec.executor is None:
            return ToolExecutionResult(False, tool_id, f"Tool has no executor: {tool_id}", meta={"error_code": "missing_executor"})
        try:
            value = spec.executor(arguments or {})
            if isinstance(value, ToolResult):
                return ToolExecutionResult(value.ok, value.tool_id, value.content, value.raw_result, value.meta)
            return ToolExecutionResult(True, tool_id, "" if value is None else str(value), raw_result=value)
        except Exception as exc:  # noqa: BLE001
            return ToolExecutionResult(False, tool_id, f"Error while executing {tool_id}: {exc}", meta={"error_code": "tool_exception"})
