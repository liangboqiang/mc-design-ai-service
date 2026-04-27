from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class KernelEvent:
    name: str
    payload: dict[str, Any] = field(default_factory=dict)


class KernelEventBus:
    def __init__(self):
        self._events: list[KernelEvent] = []

    def emit(self, name: str, **payload: Any) -> None:
        self._events.append(KernelEvent(name=name, payload=payload))

    def recent(self) -> list[KernelEvent]:
        return list(self._events[-20:])
