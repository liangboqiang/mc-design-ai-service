from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any


@dataclass(slots=True)
class AuditEntry:
    decision: str
    payload: dict[str, Any]
    ts: float = field(default_factory=time)


class AuditLog:
    def __init__(self):
        self.entries: list[AuditEntry] = []

    def record(self, decision: str, **payload) -> None:
        self.entries.append(AuditEntry(decision, payload))

    def recent(self, limit: int = 10) -> list[AuditEntry]:
        return self.entries[-limit:]
