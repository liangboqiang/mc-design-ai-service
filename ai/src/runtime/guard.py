from __future__ import annotations

import json
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any, Callable, Generic, TypeVar
from uuid import uuid4

T = TypeVar("T")


@dataclass(slots=True)
class RuntimeFault:
    trace_id: str
    phase: str
    source_name: str
    message: str
    exc_type: str = "RuntimeError"
    detail: str = ""
    stacktrace: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time)

    @classmethod
    def from_exception(cls, *, phase: str, source_name: str, exc: Exception, context: dict[str, Any] | None = None) -> "RuntimeFault":
        return cls(
            trace_id=f"rtf_{uuid4().hex[:12]}",
            phase=phase,
            source_name=source_name,
            message=str(exc)[:400],
            exc_type=exc.__class__.__name__,
            detail=repr(exc),
            stacktrace=traceback.format_exc(),
            context=dict(context or {}),
        )

    def user_message(self) -> str:
        return f"Runtime failure [{self.phase}] in {self.source_name} (trace_id={self.trace_id}): {self.message}"


@dataclass(slots=True)
class GuardResult(Generic[T]):
    ok: bool
    value: T | None = None
    fault: RuntimeFault | None = None


class RuntimeGuard:
    def __init__(self, *, logs_dir: Path, audit=None, events=None):  # noqa: ANN001
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.audit = audit
        self.events = events
        self.log_path = self.logs_dir / "runtime_faults.jsonl"

    def call(self, *, phase: str, source_name: str, fn: Callable[[], T], context: dict[str, Any] | None = None) -> GuardResult[T]:
        try:
            return GuardResult(ok=True, value=fn())
        except Exception as exc:  # noqa: BLE001
            fault = RuntimeFault.from_exception(phase=phase, source_name=source_name, exc=exc, context=context)
            self.record_fault(fault)
            return GuardResult(ok=False, fault=fault)

    def record_fault(self, fault: RuntimeFault) -> None:
        if self.audit is not None:
            self.audit.record("runtime.fault", trace_id=fault.trace_id, phase=fault.phase, source_name=fault.source_name, message=fault.message)
        if self.events is not None:
            self.events.emit("runtime.fault", trace_id=fault.trace_id, phase=fault.phase, source_name=fault.source_name, message=fault.message)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(fault.__dict__ if hasattr(fault, "__dict__") else {
                "trace_id": fault.trace_id, "phase": fault.phase, "source_name": fault.source_name, "message": fault.message
            }, ensure_ascii=False, default=str) + "\n")
