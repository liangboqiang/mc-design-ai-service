from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class DispatchResult:
    ok: bool
    capability_id: str
    content: str
    raw_result: Any = None
    meta: dict[str, Any] = field(default_factory=dict)


class CapabilityDispatcher:
    def __init__(self, executors: dict[str, Callable[[dict[str, Any]], Any]] | None = None):
        self.executors = dict(executors or {})

    def dispatch(self, capability_id: str, arguments: dict[str, Any] | None = None) -> DispatchResult:
        executor = self.executors.get(str(capability_id or "").strip())
        if executor is None:
            return DispatchResult(False, str(capability_id or ""), f"Capability not installed: {capability_id}", meta={"error_code": "missing_executor"})
        try:
            value = executor(arguments or {})
        except Exception as exc:  # noqa: BLE001
            return DispatchResult(False, str(capability_id or ""), f"Capability execution failed: {exc}", meta={"error_code": "capability_exception"})
        return DispatchResult(True, str(capability_id or ""), "" if value is None else str(value), raw_result=value)
