from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from capability.registry import CapabilityRegistry
from capability.types import CapabilitySpec


@dataclass(slots=True)
class DispatchResult:
    ok: bool
    capability_id: str
    content: str
    raw_result: Any = None
    meta: dict[str, Any] = field(default_factory=dict)


class CapabilityDispatcher:
    def __init__(
        self,
        *,
        registry: CapabilityRegistry,
        executors: dict[str, Callable[[dict[str, Any]], Any]] | None = None,
    ):
        self.registry = registry
        self.executors = dict(executors or {})

    def dispatch(
        self,
        capability_id: str,
        arguments: dict[str, Any] | None = None,
        *,
        visible_capability_ids: set[str] | None = None,
    ) -> DispatchResult:
        capability_id = str(capability_id or "").strip()
        spec = self.registry.get(capability_id)
        if spec is None:
            return DispatchResult(False, capability_id, f"Unknown capability: {capability_id}", meta={"error_code": "unknown_capability"})
        if visible_capability_ids is not None and capability_id not in visible_capability_ids:
            return DispatchResult(False, capability_id, f"Permission denied or inactive capability: {capability_id}", meta={"error_code": "inactive_capability"})
        executor_id = self._executor_id(spec)
        executor = self.executors.get(executor_id)
        if executor is None:
            return DispatchResult(False, capability_id, f"Capability executor not installed: {executor_id}", meta={"error_code": "missing_executor", "executor_ref": spec.executor_ref or ""})
        try:
            value = executor(arguments or {})
        except Exception as exc:  # noqa: BLE001
            return DispatchResult(False, capability_id, f"Capability execution failed: {exc}", meta={"error_code": "capability_exception", "executor_ref": spec.executor_ref or ""})
        if hasattr(value, "ok") and hasattr(value, "content"):
            return DispatchResult(bool(value.ok), capability_id, str(value.content), getattr(value, "raw_result", None), getattr(value, "meta", {}))
        return DispatchResult(True, capability_id, "" if value is None else str(value), raw_result=value, meta={"executor_ref": spec.executor_ref or executor_id})

    @staticmethod
    def _executor_id(spec: CapabilitySpec) -> str:
        ref = str(spec.executor_ref or "").strip()
        if ref.startswith("builtin:"):
            return ref.split(":", 1)[1]
        if ref:
            return ref
        return spec.capability_id
