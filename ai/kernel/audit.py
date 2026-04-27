from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AuditRecord:
    event: str
    created_at: str
    payload: dict[str, Any] = field(default_factory=dict)


class KernelAuditLog:
    def __init__(self):
        self.records: list[AuditRecord] = []

    def record(self, event: str, **payload: Any) -> None:
        self.records.append(AuditRecord(event=event, created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), payload=payload))
